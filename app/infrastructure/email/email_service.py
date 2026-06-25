import resend
from app.core.config import settings

resend.api_key = settings.resend_api_key.get_secret_value()


def send_welcome_email(to_email: str, username: str) -> bool:
    """
    OWASP A02 — confirmación de registro por email.
    Enviado tras registro exitoso.
    """
    try:
        resend.Emails.send({
            "from": settings.emails_from,
            "to": [to_email],
            "subject": "🎾 Bienvenido a Padel Scouter",
            "html": f"""
            <div style="font-family: Inter, sans-serif; max-width: 600px; margin: 0 auto;
                        background: #0f172a; color: #fff; padding: 40px; border-radius: 16px;">
                <div style="text-align: center; margin-bottom: 32px;">
                    <div style="font-size: 48px;">🔮</div>
                    <h1 style="color: #10b981; margin: 16px 0;">Padel Scouter</h1>
                </div>

                <h2 style="color: #f1f5f9;">¡Bienvenido, {username}! 🎾</h2>
                <p style="color: #94a3b8; line-height: 1.6;">
                    Tu cuenta ha sido creada con éxito. Ya puedes acceder al sistema
                    de análisis inteligente de jugadores de pádel con IA.
                </p>

                <div style="background: #1e293b; border: 1px solid #10b981; border-radius: 12px;
                            padding: 24px; margin: 24px 0;">
                    <p style="color: #10b981; font-weight: bold; margin: 0 0 8px;">
                        ¿Qué puedes hacer?
                    </p>
                    <ul style="color: #94a3b8; margin: 0; padding-left: 20px; line-height: 2;">
                        <li>🔮 Analizar jugadores con IA</li>
                        <li>⚡ Calcular el poder de combate</li>
                        <li>📊 Ver estadísticas en gráfico radar</li>
                        <li>🏆 Seguir el reglamento FIP 2026</li>
                    </ul>
                </div>

                <div style="text-align: center; margin-top: 32px;">
                    <a href="{settings.app_url}/login"
                       style="background: #10b981; color: white; padding: 14px 32px;
                              border-radius: 8px; text-decoration: none; font-weight: bold;">
                        Acceder ahora
                    </a>
                </div>

                <p style="color: #475569; font-size: 12px; text-align: center; margin-top: 32px;">
                    Si no has creado esta cuenta, ignora este email.
                    <br>© 2026 Padel Scouter — Basado en Reglamento FIP 2026
                </p>
            </div>
            """
        })
        return True
    except Exception as e:
        print(f"Error enviando email de bienvenida: {e}")
        return False


def send_password_reset_email(to_email: str, reset_token: str, username: str) -> bool:
    """
    OWASP A07 — reset de contraseña seguro con token de un solo uso.
    Token expira en 15 minutos.
    """
    reset_url = f"{settings.app_url}/reset-password?token={reset_token}"

    try:
        resend.Emails.send({
            "from": settings.emails_from,
            "to": [to_email],
            "subject": "🔐 Restablece tu contraseña — Padel Scouter",
            "html": f"""
            <div style="font-family: Inter, sans-serif; max-width: 600px; margin: 0 auto;
                        background: #0f172a; color: #fff; padding: 40px; border-radius: 16px;">
                <div style="text-align: center; margin-bottom: 32px;">
                    <div style="font-size: 48px;">🔐</div>
                    <h1 style="color: #10b981; margin: 16px 0;">Padel Scouter</h1>
                </div>

                <h2 style="color: #f1f5f9;">Hola, {username}</h2>
                <p style="color: #94a3b8; line-height: 1.6;">
                    Recibimos una solicitud para restablecer tu contraseña.
                    Si no fuiste tú, ignora este email — tu cuenta está segura.
                </p>

                <div style="background: #1e293b; border: 1px solid #f59e0b; border-radius: 12px;
                            padding: 24px; margin: 24px 0; text-align: center;">
                    <p style="color: #f59e0b; font-weight: bold; margin: 0 0 8px;">
                        ⚠️ Este enlace expira en 15 minutos
                    </p>
                    <p style="color: #94a3b8; font-size: 14px; margin: 0;">
                        Por seguridad, solo puedes usar este enlace una vez.
                    </p>
                </div>

                <div style="text-align: center; margin-top: 24px;">
                    <a href="{reset_url}"
                       style="background: #10b981; color: white; padding: 14px 32px;
                              border-radius: 8px; text-decoration: none; font-weight: bold;">
                        Restablecer contraseña
                    </a>
                </div>

                <p style="color: #475569; font-size: 12px; margin-top: 24px;">
                    O copia este enlace en tu navegador:<br>
                    <span style="color: #10b981;">{reset_url}</span>
                </p>

                <p style="color: #475569; font-size: 12px; text-align: center; margin-top: 32px;">
                    Si no solicitaste este cambio, tu cuenta sigue segura.
                    <br>© 2026 Padel Scouter
                </p>
            </div>
            """
        })
        return True
    except Exception as e:
        print(f"Error enviando email de reset: {e}")
        return False