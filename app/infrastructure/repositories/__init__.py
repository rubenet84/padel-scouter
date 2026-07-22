"""Repositorios — acceso a datos con consultas SQL parametrizadas.

Encapsulan todas las operaciones de lectura de base de datos. Las consultas
usan SQL crudo parametrizado con :placeholders para prevenir inyección SQL.
Son utilizados exclusivamente por la capa de servicios.
"""