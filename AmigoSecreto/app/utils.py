from itsdangerous import URLSafeTimedSerializer
from flask import current_app, url_for


def gerar_link_acesso_direto(email, group_id):
    """Gera um link com token de acesso direto ao grupo."""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    token = serializer.dumps({'email': email, 'group_id': group_id})
    link = url_for('main.acesso_direto', token=token, _external=True)
    return link
