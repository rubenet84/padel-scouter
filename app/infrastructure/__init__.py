"""
=================================================================
Capa de Infraestructura — Adaptadores de salida
=================================================================

Contiene todas las implementaciones concretas de acceso a sistemas externos:
bases de datos, APIs de IA, sistema de archivos, caché Redis y envío de emails.

Esta capa es la única que conoce detalles tecnológicos como SQLAlchemy,
Gemini SDK, WeasyPrint o Resend. Las capas superiores (servicios, API)
interactúan con estas implementaciones sin conocer sus detalles internos.

Submódulos:
- database/       Modelos ORM (SQLAlchemy) y sesión de base de datos.
- repositories/   Funciones de acceso a datos (queries SQL parametrizadas).
- ai/             Cliente de Google Gemini y sistema RAG del reglamento.
- pdf/            Generación de informes PDF con WeasyPrint.
- cache/          Cliente Redis para caché de IA y chatbot.
- email/          Servicio de envío de emails transaccionales (Resend).
"""