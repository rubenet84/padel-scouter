import sys
sys.path.insert(0, '.')
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.models import TournamentModel, PlayerModel, MatchModel
from sqlalchemy import func

db = SessionLocal()
torneos = db.query(TournamentModel).all()
print("Total torneos: " + str(len(torneos)))
print()
for t in torneos:
    cnt = db.query(func.count(MatchModel.id)).filter(MatchModel.tournament_id == t.id).scalar() or 0
    pname = "---"
    pid_short = "None"
    if t.player_id:
        p = db.query(PlayerModel).filter(PlayerModel.id == t.player_id).first()
        pname = p.name if p else "DEL"
        pid_short = str(t.player_id)[:8]
    print(str(t.id)[:8] + " | " + t.name + " | " + str(t.date) + " | player=" + pname + " (" + pid_short + ") | owner=" + str(t.owner_id)[:8] + " | partidos=" + str(cnt))

# Check Ruben's ID
print()
print("Jugadores:")
for p in db.query(PlayerModel).all():
    print("  " + str(p.id)[:8] + " | " + p.name)

db.close()
