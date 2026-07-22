"""
Configuración de rate limiting global vía slowapi.

Usa la dirección IP remota como clave de identificación del cliente.
Los límites por defecto aplican a TODOS los endpoints que no tengan
un límite explícito más restrictivo.

Límites por defecto:
- 200 requests por día.
- 50 requests por hora.

Endpoints sensibles (auth, chatbot) aplican límites adicionales
vía el decorador @limiter.limit en sus respectivos routers.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/day", "50/hour"],
)
