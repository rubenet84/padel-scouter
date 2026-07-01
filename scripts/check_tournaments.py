import sys
sys.path.insert(0, '.')
import os
os.chdir('.')

from uuid import UUID
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.models import TournamentModel, MatchModel, PlayerModel, UserModel
from sqlalchemy import and_, func

db = SessionLocal()
owner = db.query(UserModel).first()
print(f"Owner: {owner.id}")

# All tournaments
torneos = db.query(TournamentModel).all()
print(f"\n=== ALL TOURNAMENTS ({len(torneos)}) ===")
for t in torneos:
    cnt = db.query(func.count(MatchModel.id)).filter(MatchModel.tournament_id == t.id).scalar() or 0
    pname = "---"
    if t.player_id:
        p = db.query(PlayerModel).filter(PlayerModel.id == t.player_id).first()
        pname = p.name if p else "DEL"
    print(f"  {t.id} | {t.name} | {t.date} | owner={str(t.owner_id)[:8]} | player={pname} | partidos={cnt}")

# Check Araceli matches
tid = UUID("9e746930-8b45-403e-8c86-40972d1c9916")
matches = db.query(MatchModel).filter(MatchModel.tournament_id == tid).all()
print(f"\n=== ARACELI TOURNAMENT MATCHES ({len(matches)}) ===")
for m in matches:
    p1 = db.query(PlayerModel).filter(PlayerModel.id == m.player1_id).first()
    p2 = db.query(PlayerModel).filter(PlayerModel.id == m.player2_id).first()
    print(f"  player1={p1.name if p1 else '?'} ({str(m.player1_id)[:8]}) | player2={p2.name if p2 else '?'} ({str(m.player2_id)[:8]})")
    print(f"  tournament_id={m.tournament_id}")

# Simulate the API filter for Araceli
pid = UUID("84a8d8b2-f915-45d4-b7a9-5b03b8d13401")
p = db.query(PlayerModel).filter(PlayerModel.id == pid).first()
print(f"\n=== FILTER TEST FOR {p.name.upper()} ({str(pid)[:8]}) ===")

# Check: does the tournament have player_id = pid?
torneo = db.query(TournamentModel).filter(TournamentModel.id == tid).first()
print(f"Tournament player_id == Araceli? {torneo.player_id == pid if torneo and torneo.player_id else 'NO (player_id is None)'}")
print(f"Tournament owner_id == owner? {torneo.owner_id == owner.id if torneo else 'NO'}")

# Check: does Araceli have matches as player1 or player2 in this tournament?
has_p1 = db.query(MatchModel.id).filter(
    MatchModel.tournament_id == tid,
    MatchModel.player1_id == pid,
).first()
has_p2 = db.query(MatchModel.id).filter(
    MatchModel.tournament_id == tid,
    MatchModel.player2_id == pid,
).first()
print(f"Araceli has matches as player1 in tournament: {has_p1 is not None}")
print(f"Araceli has matches as player2 in tournament: {has_p2 is not None}")

# Now test with the full filter
has_player_match_p1 = (
    db.query(MatchModel.id)
    .filter(
        MatchModel.tournament_id == TournamentModel.id,
        MatchModel.player1_id == pid,
    )
    .exists()
)

has_player_match_both = (
    db.query(MatchModel.id)
    .filter(
        MatchModel.tournament_id == TournamentModel.id,
        or_(
            MatchModel.player1_id == pid,
            MatchModel.player2_id == pid,
        ),
    )
    .exists()
)

has_any = (
    db.query(MatchModel.id)
    .filter(MatchModel.tournament_id == TournamentModel.id)
    .exists()
)

# OLD filter
q_old = db.query(TournamentModel).filter(
    TournamentModel.owner_id == owner.id,
    or_(
        has_player_match_p1,
        TournamentModel.player_id == pid,
        and_(TournamentModel.player_id.is_(None), ~has_any),
    )
)

# NEW filter
q_new = db.query(TournamentModel).filter(
    TournamentModel.owner_id == owner.id,
    or_(
        has_player_match_both,
        TournamentModel.player_id == pid,
        and_(TournamentModel.player_id.is_(None), ~has_any),
    )
)

old_res = q_old.all()
new_res = q_new.all()

print(f"\nOLD filter (player1 only): {len(old_res)} tournaments")
for t in old_res:
    found = "[ARACELI]" if t.player_id == pid else ""
    print(f"  {str(t.id)[:8]} | {t.name} | partidos={db.query(func.count(MatchModel.id)).filter(MatchModel.tournament_id == t.id).scalar() or 0} {found}")

print(f"\nNEW filter (player1 OR player2): {len(new_res)} tournaments")
for t in new_res:
    found = "[ARACELI]" if t.player_id == pid else ""
    cnt = db.query(func.count(MatchModel.id)).filter(MatchModel.tournament_id == t.id).scalar() or 0
    print(f"  {str(t.id)[:8]} | {t.name} | partidos={cnt} {found}")

db.close()
