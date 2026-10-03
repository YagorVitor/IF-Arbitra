"""Render captain access messages without sending or generating credentials."""

from email.message import EmailMessage
from html import escape


def credential_message(
    *, name: str, email: str, password: str, frontend_url: str, sender: str
) -> EmailMessage:
    platform = frontend_url.rstrip("/")
    message = EmailMessage()
    message["From"] = sender
    message["To"] = email
    message["Subject"] = "IF-Arbitra | Acesso do capitão ao sistema de grupos"
    message.set_content(
        f"Olá, {name}.\n\n"
        "Seu acesso como capitão ou capitã está disponível no IF-Arbitra, "
        "sistema de formação de grupos e escolha de servidores.\n\n"
        f"Plataforma: {platform}\n"
        f"E-mail de acesso: {email}\n"
        f"Senha: {password}\n\n"
        "O e-mail de acesso é o mesmo endereço que recebeu esta mensagem.\n\n"
        "Para participar, siga estas etapas durante os períodos da rodada:\n"
        "1. Cadastre seu grupo: você é o capitão e deve selecionar os demais integrantes.\n"
        "2. Ordene os servidores conforme a preferência do grupo e envie a lista.\n"
        "3. Aguarde a publicação do resultado na plataforma.\n\n"
        "O acesso é exclusivo dos capitães. Os demais alunos são selecionados "
        "na lista de integrantes e não precisam entrar no sistema.\n"
        "Guarde sua senha e não a compartilhe. Em caso de dúvida, procure a "
        "organização responsável pela rodada.\n\n"
        "Atenciosamente,\nEquipe IF-Arbitra\nInstituto Federal de São Paulo\n"
    )
    safe_name, safe_email, safe_password, safe_url = (
        escape(value, quote=True) for value in (name, email, password, platform)
    )
    message.add_alternative(
        f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body style="margin:0;background:#f3f6f4;font-family:Arial,Helvetica,sans-serif;color:#17382f;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:24px 12px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;border:1px solid #dce7e0;">
<tr><td style="background:#075440;padding:26px 28px;color:#ffffff;">
<div style="font-size:26px;font-weight:bold;">IF-Arbitra</div>
<div style="font-size:13px;margin-top:6px;">Instituto Federal de São Paulo</div></td></tr>
<tr><td style="padding:28px;font-size:15px;line-height:1.65;">
<h1 style="font-size:22px;line-height:1.3;margin:0 0 20px;">Seu acesso à plataforma</h1>
<p>Olá, <strong>{safe_name}</strong>.</p>
<p>Seu acesso como capitão ou capitã está disponível no <strong>IF-Arbitra</strong>, sistema de formação de grupos e escolha de servidores.</p>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f1f7f3;border:1px solid #dce7e0;margin:22px 0;">
<tr><td style="padding:18px;font-size:14px;line-height:1.8;">
<strong>E-mail de acesso</strong><br><span style="overflow-wrap:anywhere;word-break:break-word;">{safe_email}</span><br>
<strong>Senha</strong><br><span style="font-family:Consolas,monospace;font-size:18px;overflow-wrap:anywhere;">{safe_password}</span></td></tr></table>
<p style="font-size:13px;color:#52665d;">O e-mail de acesso é o mesmo endereço que recebeu esta mensagem.</p>
<p style="margin:24px 0;"><a href="{safe_url}" style="display:inline-block;background:#075440;color:#ffffff;padding:12px 22px;text-decoration:none;font-weight:bold;">Acessar IF-Arbitra</a></p>
<p style="font-size:13px;overflow-wrap:anywhere;word-break:break-word;">Link da plataforma:<br><a href="{safe_url}" style="color:#075440;">{safe_url}</a></p>
<h2 style="font-size:17px;margin:26px 0 12px;">Como participar</h2>
<ol style="padding-left:22px;">
<li style="margin-bottom:10px;"><strong>Cadastre seu grupo.</strong> Você é o capitão e deve selecionar os demais integrantes.</li>
<li style="margin-bottom:10px;"><strong>Envie as preferências.</strong> Ordene os servidores conforme a escolha do grupo e envie a lista.</li>
<li><strong>Aguarde o resultado.</strong> A alocação será publicada na plataforma.</li></ol>
<p>Realize essas etapas durante os períodos definidos para a rodada.</p>
<p style="font-size:13px;color:#52665d;">O acesso é exclusivo dos capitães. Os demais alunos são selecionados na lista de integrantes e não precisam entrar no sistema.</p>
<p style="font-size:13px;color:#52665d;">Guarde sua senha e não a compartilhe. Em caso de dúvida, procure a organização responsável pela rodada.</p>
<p style="margin-top:28px;">Atenciosamente,<br><strong>Equipe IF-Arbitra</strong><br>Instituto Federal de São Paulo</p>
</td></tr></table></td></tr></table></body></html>""",
        subtype="html",
    )
    return message
