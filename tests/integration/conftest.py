"""Configuración de los tests de integración.

Deshabilita el rate limiting (slowapi) durante los tests de integración.

Motivo: la suite registra y autentica múltiples usuarios en pocos segundos,
y los límites por endpoint (3/min en /auth/register, 5/min en /auth/login)
provocan respuestas 429 que hacen fallar los tests de forma artificial.
El rate limiting se prueba por separado; aquí solo estorba.

Se deshabilita en el import del conftest (antes de coleccionar/ejecutar los
tests y sus fixtures), para evitar problemas de orden con fixtures de scope
'module' como `auth_headers`.
"""
from app.core.rate_limit import limiter

limiter.enabled = False
