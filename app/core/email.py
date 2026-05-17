from email.message import EmailMessage
import smtplib

import dns.resolver
from fastapi import HTTPException

from app.core.config import get_settings

DNS_PUBLICOS = ("1.1.1.1", "8.8.8.8")


def _resolver_mx(dominio: str, nameservers: tuple[str, ...] | None = None) -> list[str]:
    resolver = dns.resolver.Resolver()
    if nameservers:
        resolver.nameservers = list(nameservers)
    resolver.timeout = 3
    resolver.lifetime = 5

    respuestas = resolver.resolve(dominio, "MX")
    return [str(respuesta.exchange).rstrip(".").lower() for respuesta in respuestas]


def validar_dominio_email_con_mx(email: str) -> None:
    dominio = email.rsplit("@", 1)[-1].strip().lower()
    if not dominio or dominio == email:
        raise HTTPException(status_code=400, detail="Correo invalido")

    intentos = (None, DNS_PUBLICOS)

    for nameservers in intentos:
        try:
            mx_records = _resolver_mx(dominio, nameservers)
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            break
        except (dns.resolver.Timeout, dns.exception.DNSException):
            continue

        if any(record and record != "." for record in mx_records):
            return

    raise HTTPException(status_code=400, detail="El dominio del correo no tiene registros MX validos")


def enviar_correo_bienvenida(destinatario: str, nombre: str) -> None:
    settings = get_settings()
    remitente = settings.EMAIL_FROM or settings.EMAIL_USER

    if not settings.EMAIL_USER or not settings.EMAIL_PASSWORD or not remitente:
        return

    mensaje = EmailMessage()
    mensaje["Subject"] = "Bienvenido a Kali-Entes Kanban"
    mensaje["From"] = remitente
    mensaje["To"] = destinatario
    mensaje.set_content(
        "\n".join(
            [
                f"Hola {nombre},",
                "",
                "Tu cuenta fue creada en el mini Kanban vulnerable Kali-Entes.",
                "Este sistema es un laboratorio academico para pruebas controladas de API Hacking.",
                "",
                "Saludos.",
            ]
        )
    )

    with smtplib.SMTP_SSL(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=10) as smtp:
        smtp.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
        smtp.send_message(mensaje)
