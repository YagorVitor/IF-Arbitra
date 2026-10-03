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
    message["Subject"] = "IF-Arbitra | Seu acesso para cadastrar o grupo"
    message.set_content(
        f"Olá, {name}.\n\n"
        "Seu acesso ao IF-Arbitra está pronto. Use os dados abaixo para cadastrar "
        "seu grupo e escolher os servidores.\n\n"
        f"E-mail de acesso: {email}\n"
        f"Senha: {password}\n"
        f"Acessar IF-Arbitra: {platform}\n\n"
        "Cadastre o grupo → envie as preferências → aguarde o resultado.\n"
        "A plataforma orienta cada etapa, conforme os prazos da rodada.\n\n"
        "Acesso exclusivo dos capitães. Não compartilhe sua senha.\n\n"
        "Equipe IF-Arbitra\nInstituto Federal de São Paulo\n"
    )
    safe_name, safe_email, safe_password, safe_url = (
        escape(value, quote=True) for value in (name, email, password, platform)
    )
    message.add_alternative(
        f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>IF-Arbitra | Seu acesso</title></head>
<body style="margin:0;background:#f4f6f5;font-family:Arial,Helvetica,sans-serif;color:#17382f;">
<div style="display:none;max-height:0;overflow:hidden;mso-hide:all;">Seu acesso de capitão está pronto. Cadastre o grupo e envie as preferências.</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:32px 12px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#ffffff;border:1px solid #e0e8e3;border-radius:16px;">
<tr><td style="padding:24px 24px 20px;border-bottom:1px solid #edf1ee;">
<div style="font-size:23px;letter-spacing:-0.7px;font-weight:bold;color:#075440;">IF-Arbitra</div>
<div style="font-size:11px;color:#60736a;margin-top:5px;">Instituto Federal de São Paulo</div></td></tr>
<tr><td style="padding:28px 24px 24px;font-size:15px;line-height:1.6;">
<p style="margin:0 0 10px;font-size:11px;letter-spacing:1.2px;font-weight:bold;color:#087553;">ACESSO DO CAPITÃO</p>
<h1 style="font-size:28px;letter-spacing:-0.7px;line-height:1.2;margin:0 0 22px;">Cadastre seu grupo.</h1>
<p style="margin:0 0 10px;">Olá, <strong>{safe_name}</strong>.</p>
<p style="margin:0 0 22px;color:#53665d;">Use os dados abaixo para cadastrar seu grupo e escolher os servidores.</p>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f5f8f6;border:1px solid #dfe9e2;border-radius:10px;">
<tr><td style="padding:18px 18px 14px;">
<div style="font-size:12px;color:#52665d;margin-bottom:5px;">E-mail de acesso</div>
<div style="font-size:15px;font-weight:bold;overflow-wrap:anywhere;word-break:break-word;">{safe_email}</div></td></tr>
<tr><td style="padding:0 18px 18px;">
<div style="font-size:12px;color:#52665d;margin-bottom:5px;">Senha</div>
<div style="font-family:Consolas,monospace;font-size:20px;line-height:1.4;overflow-wrap:anywhere;word-break:break-word;">{safe_password}</div></td></tr></table>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top:20px;"><tr><td align="center" bgcolor="#075440" style="border-radius:8px;">
<a href="{safe_url}" style="display:block;padding:15px 12px;font-size:15px;line-height:20px;text-decoration:none;font-weight:bold;color:#ffffff;">Acessar IF-Arbitra</a></td></tr></table>
<p style="margin:12px 0 0;font-size:11px;text-align:center;overflow-wrap:anywhere;word-break:break-word;"><a href="{safe_url}" style="color:#60736a;text-decoration:underline;">{safe_url}</a></p>
<div style="margin-top:26px;padding-top:20px;border-top:1px solid #edf1ee;">
<p style="margin:0 0 7px;font-size:13px;font-weight:bold;color:#17382f;">Cadastre o grupo → envie as preferências → aguarde o resultado.</p>
<p style="margin:0;font-size:12px;color:#60736a;">A plataforma orienta cada etapa, conforme os prazos da rodada.</p></div>
</td></tr>
<tr><td style="padding:0 24px 24px;font-size:11px;line-height:1.6;color:#60736a;">
Acesso exclusivo dos capitães. Não compartilhe sua senha.<br><strong style="color:#40594c;">Equipe IF-Arbitra</strong>
</td></tr></table></td></tr></table></body></html>""",
        subtype="html",
    )
    return message
