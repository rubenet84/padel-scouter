"""
Padel Scouter — Sistema de análisis inteligente de jugadores de pádel con IA.

Arquitectura hexagonal (puertos y adaptadores):
- domain/      — Entidades, value objects y casos de uso (núcleo sin dependencias).
- services/    — Servicios de aplicación que orquestan dominio e infraestructura.
- api/         — Endpoints REST FastAPI (adaptadores de entrada).
- infrastructure/ — Base de datos, IA, caché, email, PDF (adaptadores de salida).
- schemas/     — Contratos Pydantic de entrada/salida de la API.
- core/        — Configuración, seguridad y dependencias compartidas.
"""
