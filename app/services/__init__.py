"""
============================================================
Capa de Servicios — Orquestación de la lógica de aplicación
============================================================

Los servicios son el punto medio entre la capa API (routers HTTP) y las capas
de dominio (reglas de negocio puras) e infraestructura (repositorios, IA, PDF).

Responsabilidades de esta capa:
- Recibir parámetros desde los endpoints de la API.
- Llamar a repositorios para obtener datos de la base de datos.
- Delegar el cómputo de reglas de negocio a funciones puras del dominio.
- Ensamblar y devolver schemas de respuesta (Pydantic).

Esta capa NO debe:
- Contener lógica de negocio (eso va en domain/value_objects).
- Ejecutar queries SQL directamente (eso va en infrastructure/repositories).
- Depender de FastAPI ni detalles HTTP (eso va en api/v1).

Servicios incluidos:
- badges_service:   Cálculo de insignias/logros de jugador.
- avatar_service:   Validación y procesamiento de imágenes de avatar.
- computed_stats_service: Torneos, win_rate y FEP desde partidos reales.
- analytics_service:     Analíticas detalladas de partidos (sets, rondas).
- ranking_service:       Rankings FEP y listas top de jugadores.
- comparison_service:    Comparador lado a lado e historial H2H.
- category_service:      Agregación de estadísticas por categoría.
- highlights_service:    Récords, evolución y destacados de comunidad.
- summary_service:       Resumen global agregado para el dashboard.
"""