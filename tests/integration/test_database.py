import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.infrastructure.database.models import Base, UserModel, PlayerModel
from app.domain.value_objects.category import PlayerCategory


TEST_DATABASE_URL = "postgresql+psycopg2://padel:padel123@localhost:5432/padel_scouter"


@pytest.fixture(scope="module")
def db_session():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


class TestDatabaseConnection:

    def test_conexion_a_postgres(self, db_session):
        result = db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1

    def test_crear_usuario(self, db_session):
        user = UserModel(
            email="test@padel.com",
            username="testuser",
            hashed_password="hashed_xxx",
            role="viewer"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        assert user.id is not None
        assert user.email == "test@padel.com"

    def test_crear_jugador(self, db_session):
        user = db_session.query(UserModel).filter_by(email="test@padel.com").first()
        player = PlayerModel(
            name="Juan García",
            category=PlayerCategory.TERCERA,
            owner_id=user.id,
            derecha=70, reves=65, volea_derecha=60, volea_reves=60,
        )
        db_session.add(player)
        db_session.commit()
        db_session.refresh(player)
        assert player.id is not None
        assert player.name == "Juan García"
        assert player.category == PlayerCategory.TERCERA

    def test_jugador_pertenece_a_usuario(self, db_session):
        user = db_session.query(UserModel).filter_by(email="test@padel.com").first()
        assert len(user.players) == 1
        assert user.players[0].name == "Juan García"