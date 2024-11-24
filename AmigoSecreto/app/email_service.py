from sib_api_v3_sdk import ApiClient, Configuration, TransactionalEmailsApi, SendSmtpEmail
from sib_api_v3_sdk.rest import ApiException

def enviar_email(destinatario, assunto, conteudo_html, remetente_email="lab@alexandrino.dev.br", remetente_nome="Amigo Secreto"):
    """
    Função para enviar e-mail usando a API da Brevo.
    
    :param destinatario: Email do destinatário.
    :param assunto: Assunto do e-mail.
    :param conteudo_html: Conteúdo HTML do e-mail.
    :param remetente_email: E-mail do remetente (padrão: "lab@alexandrino.dev.br").
    :param remetente_nome: Nome do remetente (padrão: "Amigo Secreto").
    :return: Retorna True se enviado com sucesso, caso contrário, levanta uma exceção.
    """
    print("Função enviar_email chamada com os seguintes parâmetros:")
    print(f"Destinatário: {destinatario}, Assunto: {assunto}, Remetente: {remetente_email}")


    configuration = Configuration()
    configuration.api_key['api-key'] = ""


    api_client = ApiClient(configuration)
    api_instance = TransactionalEmailsApi(api_client)

    email = SendSmtpEmail(
        sender={"name": remetente_nome, "email": remetente_email},
        to=[{"email": destinatario, "name": destinatario.split("@")[0]}],
        subject=assunto,
        html_content=conteudo_html
    )

    try:

        response = api_instance.send_transac_email(email)
        print("E-mail enviado com sucesso. Detalhes:", response)
        return True
    except ApiException as e:
        print(f"Erro ao enviar e-mail: {e}")
        raise
