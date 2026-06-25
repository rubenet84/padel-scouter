import pytest
from pydantic import ValidationError
from app.schemas.player import UserRegisterSchema


class TestPasswordValidation:

    def test_password_minimo_12_caracteres(self):
        with pytest.raises(ValidationError) as exc:
            UserRegisterSchema(
                email="test@test.com",
                username="testuser",
                password="Short1!"
            )
        assert "12" in str(exc.value)

    def test_password_requiere_mayuscula(self):
        with pytest.raises(ValidationError):
            UserRegisterSchema(
                email="test@test.com",
                username="testuser",
                password="sinmayuscula123!"
            )

    def test_password_requiere_minuscula(self):
        with pytest.raises(ValidationError):
            UserRegisterSchema(
                email="test@test.com",
                username="testuser",
                password="SINMINUSCULA123!"
            )

    def test_password_requiere_numero(self):
        with pytest.raises(ValidationError):
            UserRegisterSchema(
                email="test@test.com",
                username="testuser",
                password="SinNumeroEspecial!"
            )

    def test_password_requiere_especial(self):
        with pytest.raises(ValidationError):
            UserRegisterSchema(
                email="test@test.com",
                username="testuser",
                password="SinEspecial12345"
            )

    def test_password_valido_pasa_validacion(self):
        schema = UserRegisterSchema(
            email="test@test.com",
            username="testuser",
            password="Padel2026Scouter!"
        )
        assert schema.password == "Padel2026Scouter!"

    def test_email_se_normaliza_a_minusculas(self):
        schema = UserRegisterSchema(
            email="TEST@PADEL.COM",
            username="testuser",
            password="Padel2026Scouter!"
        )
        assert schema.email == "test@padel.com"

    def test_email_con_mayusculas_y_minusculas_mismo_resultado(self):
        schema1 = UserRegisterSchema(
            email="Ruben829@MSN.com",
            username="user1",
            password="Padel2026Scouter!"
        )
        schema2 = UserRegisterSchema(
            email="ruben829@msn.com",
            username="user2",
            password="Padel2026Scouter!"
        )
        assert schema1.email == schema2.email