from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from flask_socketio import emit, join_room, leave_room
from .email_service import enviar_email
from . import socketio
from .forms import RegistrationForm, LoginForm, GroupForm, GiftForm
from .models import User, Group, Participant, Gift, Message
from . import db
import random
import requests
import os
from .utils import gerar_link_acesso_direto

main = Blueprint('main', __name__)


def user_can_access_group(group, require_creator=False):

    if require_creator:
        return group.creator_id == current_user.id
    return current_user.id == group.creator_id or any(
        participant.email == current_user.email for participant in group.members
    )

@main.route('/')
def intro():
    return render_template('intro.html')

@main.route('/home')
@login_required
def home():

    user_groups = Group.query.join(Participant, isouter=True)\
        .filter(
            (Group.creator_id == current_user.id) |
            (Participant.email == current_user.email)
        ).all()


    user_groups_serialized = [
        {"id": group.id, "name": group.name, "description": group.description}
        for group in user_groups
    ]

    return render_template('home.html', user_groups=user_groups_serialized)


@main.route('/register', methods=['GET', 'POST'])
def register():
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(name=form.name.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Conta criada com sucesso! Faça login para continuar.', 'success')
        return redirect(url_for('main.login'))
    return render_template('cadastro.html', form=form)


@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('main.home'))
        flash('Credenciais inválidas. Tente novamente.', 'danger')
    return render_template('login.html', form=form)


@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout realizado com sucesso.', 'success')
    return redirect(url_for('main.home'))


@main.route('/group/new', methods=['GET', 'POST'])
@login_required
def new_group():
    form = GroupForm()
    if form.validate_on_submit():
        group = Group(
            name=form.name.data,
            description=form.description.data,
            creator_id=current_user.id
        )
        db.session.add(group)
        db.session.commit()


        creator_participant = Participant(
            user_id=current_user.id,
            group_id=group.id,
            name=current_user.name,
            email=current_user.email
        )
        db.session.add(creator_participant)
        db.session.commit()


        link_acesso = gerar_link_acesso_direto(current_user.email, group.id)
        enviar_email(
            destinatario=current_user.email,
            assunto=f'Grupo "{group.name}" criado com sucesso!',
            conteudo_html=f"""
                <h1>Grupo "{group.name}" foi criado!</h1>
                <p>Você é o administrador deste grupo. Clique no link abaixo para acessá-lo:</p>
                <a href="{link_acesso}">Acessar Grupo</a>
            """
        )

        flash('Grupo criado com sucesso! Você pode começar a conversar no chat.', 'success')
        return redirect(url_for('main.group_details', group_id=group.id))
    return render_template('grupo.html', form=form)



def get_random_harry_potter_name():
    try:
        response = requests.get("https://hp-api.onrender.com/api/characters")
        if response.status_code == 200:
            characters = response.json()

            return random.choice([character["name"] for character in characters if "name" in character])
    except Exception as e:
        print(f"Erro ao obter nomes de Harry Potter: {e}")

    return random.choice(["Harry Potter", "Hermione Granger", "Ron Weasley", "Draco Malfoy"])

def assign_character_name(participant):

    if not participant.character_name:
        participant.character_name = get_random_harry_potter_name()
        db.session.commit()


@socketio.on('join_group_chat')
def handle_group_chat(data):
    group_id = data.get('group_id')
    room = f"group_{group_id}"
    join_room(room)

    participant = Participant.query.filter_by(email=current_user.email, group_id=group_id).first()
    if not participant:
        emit('error', {'msg': 'Você não está neste grupo.'})
        return

    if not participant.character_name:
        participant.character_name = get_random_harry_potter_name()
        db.session.commit()

    emit('message', {'msg': f"{participant.character_name} entrou no chat do grupo."}, room=room)


@socketio.on("group_message")
def handle_group_message(data):
    group_id = data.get("group_id")
    message_content = data.get("message")


    participant = Participant.query.filter_by(email=current_user.email, group_id=group_id).first()
    if not participant:
        emit('error', {'msg': 'Você não está neste grupo.'})
        return

    sender_name = participant.character_name  


    message = Message(group_id=group_id, sender_name=sender_name, content=message_content)
    db.session.add(message)
    db.session.commit()


    socketio.emit(
        f"message_group_{group_id}",
        {"sender_name": sender_name, "msg": message_content},
        room=f"group_{group_id}",
    )


@main.route('/group/<int:group_id>/add_participant', methods=['GET', 'POST'])
@login_required
def add_participant(group_id):
    group = Group.query.get_or_404(group_id)

    if group.creator_id != current_user.id:
        flash('Apenas o criador do grupo pode adicionar participantes.', 'danger')
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')


        if any(p.email == email for p in group.members):
            flash(f'O participante com email "{email}" já foi adicionado ao grupo.', 'warning')
            return redirect(url_for('main.group_details', group_id=group_id))


        participant = Participant(name=name, email=email, group_id=group.id)
        db.session.add(participant)
        db.session.commit()


        link_acesso = gerar_link_acesso_direto(email=email, group_id=group.id)


        conteudo_html = f"""
        <h1 style="color: #4CAF50;">🎉 Você foi adicionado ao grupo {group.name}! 🎉</h1>
        <p>Olá <strong>{name}</strong>,</p>
        <p>Você foi adicionado ao grupo <strong>{group.name}</strong> no sistema Amigo Secreto.</p>
        <p>Para acessar o grupo diretamente, clique no link abaixo:</p>
        <p style="margin-top: 20px; text-align: center;">
            <a href="{link_acesso}" 
               style="background-color: #4CAF50; color: white; text-decoration: none; padding: 10px 20px; border-radius: 5px;">
               Acessar Grupo
            </a>
        </p>
        <p style="font-size: 14px; color: #555;">Este link é válido por 1 hora.</p>
        <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
        <footer style="text-align: center; font-size: 12px; color: #999;">
            <p><strong>Amigo Secreto</strong> - Torne seu sorteio mais especial!</p>
        </footer>
        """


        enviar_email(
            destinatario=email,
            assunto=f'Você foi adicionado ao grupo "{group.name}"!',
            conteudo_html=conteudo_html
        )

        flash(f'Participante "{name}" foi adicionado ao grupo "{group.name}".', 'success')
        return redirect(url_for('main.group_details', group_id=group_id))

    return render_template('add_participant.html', group=group)



@main.route('/group/<int:group_id>/draw', methods=['POST'])
@login_required
def draw(group_id):
    group = Group.query.get_or_404(group_id)

    if group.creator_id != current_user.id:
        flash('Apenas o criador do grupo pode realizar o sorteio.', 'danger')
        return redirect(url_for('main.group_details', group_id=group_id))

    participants = Participant.query.filter_by(group_id=group_id).all()

    if len(participants) < 2:
        flash('O grupo precisa de pelo menos 2 participantes para realizar o sorteio.', 'warning')
        return redirect(url_for('main.group_details', group_id=group_id))

    shuffled = participants[:]
    random.shuffle(shuffled)

    for i, participant in enumerate(shuffled):
        drawn_participant = shuffled[(i + 1) % len(shuffled)]
        participant.drawn_participant_id = drawn_participant.id


        link_acesso = gerar_link_acesso_direto(participant.email, group.id)


        conteudo_html = f"""
        <h1 style="color: #FF5722; text-align: center;">✨ Sorteio Realizado! ✨</h1>
        <p>Olá <strong>{participant.name}</strong>,</p>
        <p>O sorteio do grupo <strong>{group.name}</strong> foi concluído!</p>
        <p style="font-size: 16px;">
        <span style="color: #4CAF50;"><strong>🎁 Você tirou:</strong></span> <strong>{drawn_participant.name}</strong>.
        </p>
        <p style="font-size: 14px; color: #555;">
        Clique no link abaixo para acessar diretamente o grupo e ver mais detalhes:
        </p>
        <p style="text-align: center; margin: 20px 0;">
            <a href="{link_acesso}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Acessar Grupo</a>
        </p>
        <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
        <footer style="text-align: center; font-size: 12px; color: #999;">
            <p><strong>Amigo Secreto</strong> - Divirta-se e boas compras!</p>
        </footer>
        """
        enviar_email(
            destinatario=participant.email,
            assunto="Sorteio realizado!",
            conteudo_html=conteudo_html
        )

    db.session.commit()
    flash('Sorteio realizado com sucesso e e-mails enviados!', 'success')
    return redirect(url_for('main.group_details', group_id=group_id))




@main.route('/group/<int:group_id>', methods=['GET'])
@login_required
def group_details(group_id):
    group = Group.query.get_or_404(group_id)


    if not user_can_access_group(group):
        flash('Você não tem permissão para acessar este grupo.', 'danger')
        return redirect(url_for('main.home'))


    messages = Message.query.filter_by(group_id=group_id).order_by(Message.timestamp).all()

    return render_template('group_details.html', group=group, messages=messages)


@main.route('/my_draw', methods=['GET'])
@login_required
def my_draw():

    user_groups = Group.query.join(Participant, isouter=True)\
        .filter(
            (Group.creator_id == current_user.id) |
            (Participant.email == current_user.email)
        ).all()

    sorteios = []  
    for group in user_groups:

        participant = Participant.query.filter_by(email=current_user.email, group_id=group.id).first()
        drawn = Participant.query.get(participant.drawn_participant_id) if participant and participant.drawn_participant_id else None

        sorteios.append({
            "group": group,
            "participant": participant,
            "drawn": drawn
        })

    return render_template('my_draw.html', sorteios=sorteios)



@main.route('/my_gifts', methods=['GET', 'POST'])
@login_required
def my_gifts():
    participant = Participant.query.filter_by(email=current_user.email).first()

    if not participant:
        flash('Você ainda não está participando de nenhum grupo.', 'warning')
        return redirect(url_for('main.home'))

    gifts = Gift.query.filter_by(participant_id=participant.id).all()

    if request.method == 'POST':
        if 'add_gift' in request.form:
            # Adicionar novo presente
            gift_name = request.form.get('gift_name')
            gift_link = request.form.get('gift_link')

            if gift_name:
                new_gift = Gift(
                    name=gift_name,
                    link=gift_link,
                    participant_id=participant.id
                )
                db.session.add(new_gift)
                db.session.commit()


                drawn_by = Participant.query.filter_by(drawn_participant_id=participant.id).first()
                if drawn_by:
                    link_acesso = gerar_link_acesso_direto(drawn_by.email, participant.group_id)
                    enviar_email(
                        destinatario=drawn_by.email,
                        assunto=f"Novo presente adicionado por {participant.name}",
                        conteudo_html=f"""
                            <h1>{participant.name} adicionou um presente à lista!</h1>
                            <p>O presente adicionado foi: <strong>{gift_name}</strong>.</p>
                            <p>Clique no link abaixo para acessar o grupo e conferir os detalhes:</p>
                            <a href="{link_acesso}">Acessar Grupo</a>
                        """
                    )

                flash('Presente adicionado com sucesso e notificação enviada!', 'success')
            else:
                flash('O nome do presente é obrigatório.', 'warning')

        elif 'delete_gift' in request.form:

            gift_id = request.form.get('gift_id')
            gift = Gift.query.get(gift_id)
            if gift and gift.participant_id == participant.id:
                db.session.delete(gift)
                db.session.commit()
                flash('Presente removido com sucesso!', 'success')

        return redirect(url_for('main.my_gifts'))

    return render_template('my_gifts.html', participant=participant, gifts=gifts)




@main.route('/view_gift/<int:participant_id>', methods=['GET'])
@login_required
def view_gift(participant_id):
    participant = Participant.query.get_or_404(participant_id)

    if participant.user_id != current_user.id:
        flash('Você não tem permissão para visualizar este presente.', 'danger')
        return redirect(url_for('main.home'))

    return render_template('view_gift.html', participant=participant)


@main.route('/group/<int:group_id>/draw_result', methods=['GET'])
@login_required
def view_draw_result(group_id):
    group = Group.query.get_or_404(group_id)


    if group.creator_id != current_user.id:
        flash('Apenas o criador do grupo pode ver os resultados do sorteio.', 'danger')
        return redirect(url_for('main.group_details', group_id=group_id))


    participants = group.members
    sorteio = {p: Participant.query.get(p.drawn_user_id) for p in participants if p.drawn_user_id}

    return render_template('draw_result.html', group=group, sorteio=sorteio)


@main.app_errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@main.app_errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


@main.app_errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403

@main.route('/test-email', methods=['GET'])
def test_email():
    """
    Rota para testar o envio de e-mails usando a API da Brevo.
    """
    try:
        destinatario = "ivan.alexandrino@outlook.com"
        assunto = "Teste de Integração com a API da Brevo"
        conteudo_html = """
        <h1>Teste de Integração</h1>
        <p>Se você está vendo este e-mail, a integração com a API da Brevo foi realizada com sucesso!</p>
        """


        enviar_email(destinatario, assunto, conteudo_html)

        return "E-mail enviado com sucesso!"
    except Exception as e:
        return f"Erro ao enviar e-mail: {e}"


@main.route('/group/access/<token>', methods=['GET'])
def acesso_direto(token):
    """
    Rota para permitir acesso direto ao grupo sem autenticação via token.
    """
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        data = serializer.loads(token, max_age=3600) 
        email = data.get('email')
        group_id = data.get('group_id')


        participant = Participant.query.filter_by(email=email, group_id=group_id).first()
        if not participant:
            flash("Acesso negado. Você não faz parte deste grupo.", "danger")
            return redirect(url_for('main.intro'))

        group = Group.query.get_or_404(group_id)


        flash(f"Acesso concedido ao grupo {group.name}.", "success")
        return render_template('group_details.html', group=group)
    except Exception as e:
        print(f"Erro ao acessar o token: {e}")
        flash("O link de acesso expirou ou é inválido.", "danger")
        return redirect(url_for('main.intro'))
