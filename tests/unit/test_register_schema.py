"""
Tests unitarios del schema de registro (app/schemas/player.py).

Garantizan que el cliente NO puede autoasignarse un rol a través del payload
de registro: el schema no expone el campo `role` y cualquier valor extra es
ignorado por Pydantic. La asignación real del rol ocurre en el backend
(register() -> "jugador").
"""
from app.schemas.player import UserRegisterSchema


class TestRegisterSchemaNoAceptaRol:

    def test_schema_no_tiene_campo_role(self):
        assert "role" not in UserRegisterSchema.model_fields

    def test_role_en_payload_es_ignorado(self):
        schema = UserRegisterSchema(
            email="nuevo@test.com",
            username="nuevouser",
            password="PadelScouter2026!",
            role="admin",  # intento de autoasignación → debe ignorarse
        )
        assert not hasattr(schema, "role")
        assert "role" not in schema.model_dump()

    def test_no_se_puede_colar_entrenador(self):
        schema = UserRegisterSchema(
            email="coach@test.com",
            username="coachuser",
            password="PadelScouter2026!",
            role="entrenador",
        )
        assert "role" not in schema.model_dump()

    def test_payload_valido_sin_role(self):
        schema = UserRegisterSchema(
            email="nuevo@test.com",
            username="nuevouser",
            password="PadelScouter2026!",
        )
        assert schema.email == "nuevo@test.com"
        assert schema.username == "nuevouser"
        assert set(schema.model_dump().keys()) == {"email", "username", "password"}
