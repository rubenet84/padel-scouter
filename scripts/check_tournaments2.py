import sys
sys.path.insert(0, '.')
from uuid import UUID
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.models import TournamentModel, MatchModel, PlayerModel, UserModel
from sqlalchemy import and_, func, or_

db = SessionLocal()
owner = db.query(UserModel).first()

pid = UUID("84a8d8b2-f915-45d4-b7a9-5b03b8d13401")
p = db.query(PlayerModel).filter(PlayerModel.id == pid).first()
print("Jugador: " + p.name)

# Direct query: torneos con player_id = Araceli
t = db.query(TournamentModel).filter(TournamentModel.player_id == pid).first()
if t:
    cnt = db.query(func.count(MatchModel.id)).filter(MatchModel.tournament_id == t.id).scalar() or 0
    print("Torneo con player_id=Araceli: " + t.name + " | partidos=" + str(cnt))
else:
    print("NO HAY torneo con player_id=Araceli")

# Full filter test
has_player_match = (
    db.query(MatchModel.id)
    .filter(
        MatchModel.tournament_id == TournamentModel.id,
        MatchModel.player1_id == pid,
    )
    .exists()
)

has_any_match = (
    db.query(MatchModel.id)
    .filter(MatchModel.tournament_id == TournamentModel.id)
    .exists()
)

q = db.query(TournamentModel).filter(
    TournamentModel.owner_id == owner.id,
    or_(
        has_player_match,
        TournamentModel.player_id == pid,
        and_(TournamentModel.player_id.is_(None), ~has_any_match),
    )
)

res = q.all()
print("Full filter returns: " + str(len(res)) + " torneos")
for x in res:
    cnt = db.query(func.count(MatchModel.id)).filter(MatchModel.tournament_id == x.id).scalar() or 0
    pid_str = str(x.player_id)[:8] if x.player_id else "None"
    is_araceli = " [ARACELI]" if x.player_id == pid else ""
    print("  " + str(x.id)[:8] + " | " + x.name + " | partidos=" + str(cnt) + " | player=" + pid_str + is_araceli)

db.close()
