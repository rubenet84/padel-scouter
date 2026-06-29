# Spec: Tournament System

**Change**: `tournament-system`  
**Proposal**: `openspec/changes/tournament-system/proposal.md`  
**Status**: Draft  
**Created**: 2026-06-29  
**Depends on**: Alembic migration, Computed Stats Service

---

## 1. Tournament Entity

### 1.1 Domain Entity (`app/domain/entities/tournament.py` — NEW)

```python
@dataclass
class Tournament:
    id: UUID
    name: str            # max 200, immutable after creation
    date: date           # required
    fep_points: int      # nullable, >= 0, default 0
    owner_id: UUID       # FK → users.id, required
    created_at: datetime
```

### 1.2 SQLAlchemy Model (`app/infrastructure/database/models.py` — NEW)

```python
class TournamentModel(Base):
    __tablename__ = "tournaments"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name       = Column(String(200), nullable=False)
    date       = Column(Date, nullable=False)
    fep_points = Column(Integer, default=0, nullable=True)
    owner_id   = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    owner   = relationship("UserModel")
    matches = relationship("MatchModel", back_populates="tournament")
```

**Constraints**:
- `name` NOT NULL, max 200 chars
- `date` NOT NULL
- `fep_points` >= 0 (validate at schema level), nullable, default 0
- `owner_id` NOT NULL, FK → users.id
- `created_at` NOT NULL, auto-set

### 1.3 OWASP: Tournament Input Validation

| Check | Implementation |
|-------|----------------|
| Name length | Pydantic `Field(max_length=200)` |
| HTML stripping | `strip_html()` helper on name before persistence |
| Parameterized queries | SQLAlchemy ORM (inherent) |
| Ownership guard | All mutations check `TournamentModel.owner_id == current_user.id` |
| Name immutability | `PUT` endpoint rejects name field |

### 1.4 Name Immutability Rule

Once created, `name` cannot be updated via PUT. Rationale:
- Referential integrity: matches reference tournaments by FK, not by name
- Migration safety: legacy `torneo` column preserves old free-text names

If the user needs to rename, they must DELETE and re-create.

---

## 2. MatchModel Changes

### 2.1 Schema Changes (`app/infrastructure/database/models.py`)

Add to `MatchModel`:

```python
tournament_id = Column(UUID(as_uuid=True), ForeignKey("tournaments.id"), nullable=True)
ronda         = Column(String(100), nullable=True)  # Fase de grupos, 32avos, 16avos, Octavos, Cuartos, Semifinal, Final
```

**Do NOT remove** the `torneo` column (kept as nullable for migration safety).

Add relationship:

```python
tournament = relationship("TournamentModel", back_populates="matches")
```

### 2.2 Tournament FK Semantics

| `tournament_id` | Meaning |
|-----------------|---------|
| `NULL` | Amistoso (friendly match) |
| Valid UUID | Tournament match |

### 2.3 `ronda` Valid Values

- `"Fase de grupos"`
- `"32avos"`
- `"16avos"`
- `"Octavos"`
- `"Cuartos"`
- `"Semifinal"`
- `"Final"`

Validate at schema level — Pydantic enum or `Field(pattern=...)` on the string.

### 2.4 Relationship Update

```python
# In TournamentModel
matches = relationship("MatchModel", back_populates="tournament")

# In MatchModel
tournament = relationship("TournamentModel", back_populates="matches")
```

---

## 3. Remove Competitive Fields from PlayerModel

### 3.1 Columns to Drop

From `PlayerModel` in `models.py`:

| Column | Type | Default |
|--------|------|---------|
| `torneos_jugados` | Integer | 0 |
| `victorias` | Integer | 0 |
| `puntos_ranking_fep` | Integer | 0 |

Alembic migration: `ALTER TABLE players DROP COLUMN torneos_jugados, victorias, puntos_ranking_fep`

### 3.2 PlayerStats Entity (`app/domain/entities/player.py`)

Remove these fields from the `PlayerStats` dataclass:

```python
# Remove:
torneos_jugados:     int = 0
victorias:           int = 0
puntos_ranking_fep:  int = 0
```

Also remove the `win_rate` method from `Player`:

```python
# Remove entire method:
def win_rate(self) -> float:
    if self.stats.torneos_jugados == 0:
        return 0.0
    return self.stats.victorias / self.stats.torneos_jugados
```

### 3.3 PlayerStatsSchema (`app/schemas/player.py`)

Remove:

```python
torneos_jugados:    int = Field(default=0, ge=0)
victorias:          int = Field(default=0, ge=0)
puntos_ranking_fep: int = Field(default=0, ge=0)
```

### 3.4 PlayerPublicSchema (`app/schemas/player.py`)

Remove:

```python
torneos_jugados:    int = 0
victorias:          int = 0
puntos_ranking_fep: int = 0
```

### 3.5 Stats Modal (`player_detail.html`)

Remove the "Historial Competitivo" section from `openStatsModal()` — replaces with computed stats.

### 3.6 Edit Modal Fields (`player_detail.html`)

Remove inputs for:
- `e-torneos_jugados`
- `e-victorias`
- `e-puntos_ranking_fep`

Remove from `statFields` arrays in both `openEditModal()` and `saveAndAnalyze()`.
Remove from `resetNewPlayerForm()` in `dashboard.html`.
Remove from `STATS` constant in `dashboard.html`.
Remove "Historial Competitivo" section in both new player and edit forms.

---

## 4. Computed Stats Service

### 4.1 New Module: `app/domain/use_cases/computed_stats.py`

```python
@dataclass
class ComputedStats:
    torneos:   int     # COUNT(DISTINCT tournament_id)
    win_rate:  float   # 0.0 - 100.0
    fep_points: int    # SUM(DISTINCT t.fep_points)


def get_computed_stats(db: Session, player_id: UUID) -> ComputedStats:
    """
    Compute competitive stats directly from match + tournament data.
    Returns (0, 0.0, 0) if no matches exist.
    """
    result = db.execute(text("""
        SELECT
            COUNT(DISTINCT m.tournament_id) as torneos,
            COALESCE(
                COUNT(*) FILTER (WHERE m.ganado = true)::float
                / NULLIF(COUNT(*), 0) * 100,
                0.0
            ) as win_rate,
            COALESCE(SUM(DISTINCT t.fep_points), 0) as fep_points
        FROM matches m
        LEFT JOIN tournaments t ON m.tournament_id = t.id
        WHERE m.player1_id = :player_id
    """), {"player_id": player_id}).one()

    return ComputedStats(
        torneos=result.torneos or 0,
        win_rate=round(result.win_rate or 0.0, 1),
        fep_points=result.fep_points or 0,
    )
```

### 4.2 Edge Cases

| Scenario | Result |
|----------|--------|
| No matches at all | `(0, 0.0, 0)` |
| Matches with no tournament (amistosos) | `torneos=0`, win_rate computed from all matches, `fep_points=0` |
| Multiple matches in same tournament | `torneos` counts distinct tournaments only |
| Tournament with fep_points=50, 3 matches | fep_points = 50 (DISTINCT sum) |
| Win rate calculation | `COUNT(*) FILTER (WHERE ganado=true) / COUNT(*) * 100` |

### 4.3 API Endpoint

New endpoint in `players.py`:

```python
@router.get("/{player_id}/stats")
def get_player_stats(
    player_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> ComputedStats:
    # Ownership check
    player = db.query(PlayerModel).filter(
        PlayerModel.id == player_id,
        PlayerModel.owner_id == current_user.id,
    ).first()
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    return get_computed_stats(db, player_id)
```

Schema:

```python
class ComputedStatsSchema(BaseModel):
    torneos:    int
    win_rate:   float  # 0.0 - 100.0
    fep_points: int
```

---

## 5. API Changes

### 5.1 Tournament CRUD — `app/api/v1/tournaments.py` (NEW)

All endpoints require JWT (`Depends(get_current_user)`). All mutations check ownership.

```
POST   /api/v1/tournaments/       → create tournament
GET    /api/v1/tournaments/       → list own tournaments
GET    /api/v1/tournaments/{id}   → get one tournament
PUT    /api/v1/tournaments/{id}   → update (date, fep_points only)
DELETE /api/v1/tournaments/{id}   → delete (set tournament_id=NULL on related matches)
```

#### TournamentCreateSchema / TournamentUpdateSchema

```python
class TournamentCreateSchema(BaseModel):
    name:       str = Field(min_length=2, max_length=200)
    date:       date
    fep_points: int | None = Field(default=0, ge=0)

    @field_validator("name")
    @classmethod
    def strip_html(cls, v: str) -> str:
        import re
        return re.sub(r"<[^>]*>", "", v).strip()


class TournamentUpdateSchema(BaseModel):
    date:       date
    fep_points: int | None = Field(default=0, ge=0)
```

**Name is EXCLUDED from update schema** — immutable.

#### TournamentPublicSchema

```python
class TournamentPublicSchema(BaseModel):
    id:         UUID
    name:       str
    date:       date
    fep_points: int | None
    owner_id:   UUID
    created_at: datetime
    match_count: int = 0  # computed, not persisted

    model_config = {"from_attributes": True}
```

#### Endpoint Details

**POST /api/v1/tournaments/** — create tournament

```python
@router.post("/", response_model=TournamentPublicSchema, status_code=201)
def create_tournament(...):
    # OWASP A01: owner_id = current_user.id
    # OWASP A03: validated by Pydantic schema, HTML stripped from name
    tournament = TournamentModel(
        name=data.name,
        date=data.date,
        fep_points=data.fep_points or 0,
        owner_id=current_user.id,
    )
    db.add(tournament)
    db.commit()
    db.refresh(tournament)
    return tournament
```

**GET /api/v1/tournaments/** — list with match count, ordered by date desc

```python
@router.get("/", response_model=list[TournamentPublicSchema])
def list_tournaments(...):
    return db.query(
        TournamentModel,
        func.count(MatchModel.id).label("match_count")
    ).outerjoin(
        MatchModel, MatchModel.tournament_id == TournamentModel.id
    ).filter(
        TournamentModel.owner_id == current_user.id
    ).group_by(TournamentModel.id).order_by(
        TournamentModel.date.desc()
    ).all()
```

**GET /api/v1/tournaments/{id}** — get one with ownership check

```python
@router.get("/{tournament_id}", response_model=TournamentPublicSchema)
def get_tournament(...):
    tournament = db.query(TournamentModel).filter(
        TournamentModel.id == tournament_id,
        TournamentModel.owner_id == current_user.id,
    ).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Torneo no encontrado")
    return tournament
```

**PUT /api/v1/tournaments/{id}** — update date/fep_points only, name immutable

```python
@router.put("/{tournament_id}", response_model=TournamentPublicSchema)
def update_tournament(...):
    tournament = db.query(TournamentModel).filter(
        TournamentModel.id == tournament_id,
        TournamentModel.owner_id == current_user.id,
    ).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Torneo no encontrado")
    # name is NOT updated — it's immutable
    tournament.date = data.date
    if data.fep_points is not None:
        tournament.fep_points = data.fep_points
    db.commit()
    db.refresh(tournament)
    return tournament
```

**DELETE /api/v1/tournaments/{id}** — set FK to NULL on related matches, then delete

Strategy: SET NULL (cascade) rather than blocking. Rationale: preserves match history even after tournament is deleted.

```python
@router.delete("/{tournament_id}", status_code=204)
def delete_tournament(...):
    tournament = db.query(TournamentModel).filter(
        TournamentModel.id == tournament_id,
        TournamentModel.owner_id == current_user.id,
    ).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Torneo no encontrado")

    # Set tournament_id = NULL on related matches
    db.query(MatchModel).filter(
        MatchModel.tournament_id == tournament_id
    ).update({"tournament_id": None})

    db.delete(tournament)
    db.commit()
```

### 5.2 Match Schema Modifications

#### MatchCreateSchema

Replace `torneo` field:

```python
# Remove:
torneo: str | None = Field(default=None, max_length=150)

# Add:
tournament_id: UUID | None = Field(default=None)  # FK → tournaments.id
ronda: str | None = Field(default=None, max_length=100)
```

#### MatchPublicSchema

Replace `torneo`:

```python
# Remove:
torneo: str | None = None

# Add:
tournament_id: UUID | None = None
ronda: str | None = None
```

### 5.3 Match Endpoint Modifications

**POST /{player_id}/matches** — accept `tournament_id` and `ronda` instead of `torneo`.

```python
match = MatchModel(
    player1_id=player_id,
    player2_id=player_id,
    rival_nombre=data.rival_nombre,
    # torneo is NOT set — will be NULL
    tournament_id=data.tournament_id,
    ronda=data.ronda,
    resultado=data.resultado,
    ganado=data.ganado,
    scoring_method=data.scoring_method,
    result=data.resultado,
    winner_id=player_id if data.ganado else None,
    notes=data.notes,
)
```

**PUT /{player_id}/matches/{match_id}** — update `tournament_id` and `ronda` instead of `torneo`.

```python
match.tournament_id = data.tournament_id
match.ronda = data.ronda
# match.torneo is NOT updated — kept as legacy
```

**GET /{player_id}/matches** — also accept optional `tournament_id` query param for filtering:

```python
@router.get("/{player_id}/matches")
def get_matches(
    player_id: UUID,
    tournament_id: UUID | None = None,  # NEW: optional filter
    ...
):
    query = db.query(MatchModel).filter(
        or_(MatchModel.player1_id == player_id,
            MatchModel.player2_id == player_id)
    )
    if tournament_id is not None:
        query = query.filter(MatchModel.tournament_id == tournament_id)
    elif tournament_id == UUID("00000000-0000-0000-0000-000000000000"):
        # Special: show only amistosos (no tournament matches)
        query = query.filter(MatchModel.tournament_id == None)
    matches = query.order_by(MatchModel.played_at.desc()).limit(20).all()
    return matches
```

To support the frontend filter, the endpoint should accept:
- `?tournament_id=<uuid>` → filter by specific tournament
- `?tournament_id=none` or `?tipo=amistoso` → filter amistosos only
- no filter → all matches (default)

### 5.4 Router Registration (`app/main.py`)

```python
from app.api.v1.tournaments import router as tournaments_router
app.include_router(tournaments_router, prefix="/api/v1")
```

---

## 6. Power Level Adjustment

### 6.1 Updated `calculate_power_level` signature

```python
def calculate_power_level(
    stats: PlayerStats,
    category: PlayerCategory,
    computed_stats: ComputedStats | None = None,  # NEW optional
) -> int:
```

### 6.2 Logic Change

Replace the current competitive component:

```python
# OLD (removed):
win_rate         = stats.victorias / max(stats.torneos_jugados, 1)
competitive      = (
    (stats.puntos_ranking_fep / 10) +
    (win_rate * 300) +
    (category.weight() * 100)
)

# NEW:
if computed_stats:
    win_rate = computed_stats.win_rate / 100  # convert 0-100 to 0-1
    fep_pts  = computed_stats.fep_points
else:
    win_rate = 0.0
    fep_pts  = 0

competitive = (
    (fep_pts / 10) +
    (win_rate * 300) +
    (category.weight() * 100)
)
```

### 6.3 Impact Analysis

| Scenario | Old behavior | New behavior (with computed_stats) |
|----------|-------------|-----------------------------------|
| No matches | win_rate=0, fep=0 | win_rate=0, fep=0 (same) |
| 5 matches, 3 wins, 1 tournament with 50 fep_points | Manual entry | win_rate=60%, fep=50 |
| Caller doesn't pass computed_stats | N/A | win_rate=0, fep=0 (graceful fallback) |

### 6.4 Call Sites

All callers of `calculate_power_level` must be updated:

| File | Current call | Updated call |
|------|-------------|-------------|
| `analyze_player.py` | `calculate_power_level(player.stats, player.category)` | Pass `computed_stats` fetched from DB |
| Unit tests | Direct call | Pass `None` or mock `ComputedStats` |

In `analyze_player.py`, the use case needs DB access to fetch computed stats. Options:
1. Pass `db: Session` to the use case  
2. Fetch computed stats in the API handler and pass to use case

**Recommendation**: Option 2 — keep the use case independent of infrastructure:

```python
# In analysis.py API handler:
computed_stats = get_computed_stats(db, player_id)
result = use_case.execute(player, computed_stats=computed_stats)

# In AnalyzePlayerUseCase.execute:
def execute(self, player: Player, computed_stats: ComputedStats | None = None) -> AnalysisResult:
    power_level = calculate_power_level(player.stats, player.category, computed_stats)
    ...
```

---

## 7. Frontend Spec

### 7.1 Stats Card Relabel (`player_detail.html`)

In `renderPlayer()`:

```javascript
// OLD:
document.getElementById('stat-torneos').textContent = torneos;
document.getElementById('stat-torneos').nextElementSibling.textContent = 'Torneos';

// NEW:
renderComputedStats(playerId).then(stats => {
    document.getElementById('stat-torneos').textContent = stats.torneos;
    document.getElementById('stat-torneos').nextElementSibling.textContent = 'Torneos';
    document.getElementById('stat-winrate').textContent = stats.win_rate.toFixed(1) + '%';
    document.getElementById('stat-fep').textContent = stats.fep_points.toLocaleString();
});
```

Where `renderComputedStats(playerId)` calls `GET /api/v1/players/{id}/stats`.

### 7.2 New Player Form (`dashboard.html`)

Remove "Historial Competitivo" section entirely (lines 72-89 in the template):

```html
<!-- REMOVE THIS ENTIRE SECTION -->
<p class="text-emerald-400 font-semibold text-sm mt-4">Historial Competitivo</p>
<div class="grid grid-cols-3 gap-3">
    <div>...</div>  <!-- Torneos -->
    <div>...</div>  <!-- Victorias -->
    <div>...</div>  <!-- Puntos FEP -->
</div>
```

Update `STATS` constant:

```javascript
// Remove 'torneos_jugados', 'victorias', 'puntos_ranking_fep'
const STATS = [
    'derecha','reves','volea_derecha','volea_reves','bandeja','vibora',
    'remate','globo','saque','bajada_pared',
    'velocidad','resistencia','reflejos','tactica','presion','trabajo_en_pareja'
];
```

Update `resetNewPlayerForm()`:

```javascript
// Remove the ternary for competitive fields
STATS.forEach(s => {
    document.getElementById(`s-${s}`).value = '50';
});
```

Update `createPlayer()` validation:

```javascript
// Remove the competitive field special-case (lines about torneos_jugados/victorias/puntos_ranking_fep)
if (value < 0 || value > 100) {
    errEl.textContent = `El valor de ${s.replace('_', ' ')} debe estar entre 0 y 100.`;
    ...
}
```

### 7.3 Edit Player Form (`player_detail.html`)

Remove lines 529-547 (Historial Competitivo section in the edit modal):

```html
<!-- REMOVE -->
<p class="text-xs font-bold tracking-widest uppercase mb-3" style="color:rgba(168,85,247,0.6);">
    🏆 Historial Competitivo</p>
<div class="grid grid-cols-3 gap-3 mb-6">
    ... (torneos_jugados, victorias, puntos_ranking_fep)
</div>
```

Update `statFields` in both `openEditModal()` and `saveAndAnalyze()`:

```javascript
// Remove 'torneos_jugados', 'victorias', 'puntos_ranking_fep'
const statFields = ['derecha','reves','volea_derecha','volea_reves','bandeja','vibora',
    'remate','globo','saque','bajada_pared','velocidad','resistencia','reflejos',
    'tactica','presion','trabajo_en_pareja'];
```

Remove competitive field validation in `saveAndAnalyze()`:

```javascript
// Remove this special-case block:
if (f === 'torneos_jugados' || f === 'victorias' || f === 'puntos_ranking_fep') {
    if (value < 0) { ... }
}
```

### 7.4 Match Create Modal

**Current behavior**: Tipo de partido toggle (Amistoso / Torneo) → shows free-text torneo name + ronda selector.

**New behavior**:

Replace the toggle with a dropdown:

```html
<select id="m-tournament" onchange="onTournamentChange()">
    <option value="">🎾 Partido amistoso</option>
    <option value="__new__">🏆 Nuevo torneo...</option>
    <!-- dynamically loaded tournaments from API -->
    <option value="<uuid>">🏆 <name> — <date></option>
</select>
```

**When "Nuevo torneo..." is selected**, show an inline form with:
- Name (required, max 200)
- Date (defaults to today)
- FEP Points (optional, default 0)

**When a specific tournament is selected**, show:
- Ronda selector (dropdown with valid ronda values)
- No pareja rival field (use `rival_nombre` for both amistosos and torneos)

**When "Partido amistoso" is selected**, show:
- Rival field (as before)
- No ronda selector

**Loading tournaments** on page load:

```javascript
async function loadTournaments() {
    const res = await fetch('/api/v1/tournaments/', {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    const tournaments = await res.json();
    const select = document.getElementById('m-tournament');
    tournaments.forEach(t => {
        const opt = document.createElement('option');
        opt.value = t.id;
        opt.textContent = `🏆 ${t.name} — ${new Date(t.date).toLocaleDateString('es-ES')}`;
        select.appendChild(opt);
    });
}
```

**Create tournament inline**:

```javascript
async function createTournamentInline(name, date, fepPoints) {
    const res = await fetch('/api/v1/tournaments/', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, date, fep_points: fepPoints })
    });
    const tournament = await res.json();
    // Add to dropdown and select it
    const select = document.getElementById('m-tournament');
    const opt = document.createElement('option');
    opt.value = tournament.id;
    opt.textContent = `🏆 ${tournament.name} — ...`;
    select.appendChild(opt);
    select.value = tournament.id;
    onTournamentChange();
}
```

**Save match payload changes**:

```javascript
// Replace:
body: JSON.stringify({
    rival_nombre: rival,
    resultado: resultado,
    ganado: ganado,
    torneo: torneoInfo,
    scoring_method: ...,
})

// With:
body: JSON.stringify({
    rival_nombre: rival,
    resultado: resultado,
    ganado: ganado,
    tournament_id: selectedTournamentId,  // null for amistosos
    ronda: selectedRonda,                 // null for amistosos
    scoring_method: ...,
})
```

### 7.5 Match History Filter

Add filter above the match list:

```html
<div class="flex items-center gap-3 mb-4">
    <select id="match-filter" onchange="onMatchFilterChange()"
            class="rounded-lg px-3 py-2 text-sm text-white"
            style="background:#0A0A0F;border:1px solid rgba(168,85,247,0.2);">
        <option value="all">📋 Todos</option>
        <option value="amistoso">🎾 Amistosos</option>
        <!-- dynamically loaded tournament options -->
    </select>
</div>
```

Filter logic:

```javascript
async function onMatchFilterChange() {
    const filter = document.getElementById('match-filter').value;
    let url = `/api/v1/players/${playerId}/matches`;
    if (filter === 'amistoso') {
        url += '?tournament_id=none';
    } else if (filter !== 'all') {
        url += `?tournament_id=${filter}`;
    }
    const res = await fetch(url, { headers: { 'Authorization': `Bearer ${token}` } });
    const matches = await res.json();
    renderMatches(matches);
}
```

Initial load of tournament options:

```javascript
async function loadTournamentFilterOptions() {
    const res = await fetch('/api/v1/tournaments/', {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    const tournaments = await res.json();
    const select = document.getElementById('match-filter');
    tournaments.forEach(t => {
        const opt = document.createElement('option');
        opt.value = t.id;
        opt.textContent = `🏆 ${t.name}`;
        select.appendChild(opt);
    });
}
```

### 7.6 Stats Modal Update

In `openStatsModal()`, replace the competitive stats section:

```javascript
// OLD (torneos_jugados, victorias, puntos_ranking_fep from playerData):
document.getElementById('stats-comp').innerHTML = `
    <div>...${p.torneos_jugados || 0}...Torneos</div>
    <div>...${p.victorias || 0}...Victorias</div>
    <div>...${(p.puntos_ranking_fep || 0).toLocaleString()}...Pts FEP</div>`;

// NEW (fetch from computed stats endpoint):
fetch(`/api/v1/players/${playerId}/stats`, {
    headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json()).then(stats => {
    document.getElementById('stats-comp').innerHTML = `
        <div class="text-center p-3 rounded-xl" ...>
            <p class="text-xl font-bold text-white">${stats.torneos}</p>
            <p class="text-xs mt-1" style="color:#475569;">Torneos</p>
        </div>
        <div class="text-center p-3 rounded-xl" ...>
            <p class="text-xl font-bold" style="color:#00FF87;">${stats.win_rate.toFixed(1)}%</p>
            <p class="text-xs mt-1" style="color:#475569;">Porcentaje de Victorias</p>
        </div>
        <div class="text-center p-3 rounded-xl" ...>
            <p class="text-xl font-bold" style="color:#FF6B00;">${stats.fep_points.toLocaleString()}</p>
            <p class="text-xs mt-1" style="color:#475569;">Pts FEP</p>
        </div>`;
});
```

### 7.7 Competitive Bar Update

In `renderPlayer()`, simplify the competitive bar to use computed stats:

```javascript
// OLD:
const comp = torneos > 0 ? Math.round((victorias / torneos) * 100) : 0;
document.getElementById('bar-comp').style.width = compFinal + '%';
document.getElementById('bar-comp-val').textContent = compFinal + '%';

// NEW: fetch async
fetch(`/api/v1/players/${playerId}/stats`, {
    headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json()).then(stats => {
    const compPct = Math.min(stats.win_rate, 100);
    document.getElementById('bar-comp').style.width = compPct + '%';
    document.getElementById('bar-comp-val').textContent = compPct.toFixed(1) + '%';
});
```

---

## 8. Data Migration

### 8.1 Alembic Migration Steps

Migration revision: `tournament_system_v1` (after `5b1dcc84d45e`)

**Step 1**: Create `tournaments` table.

```python
op.create_table('tournaments',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('fep_points', sa.Integer(), nullable=True),
    sa.Column('owner_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
)
```

**Step 2**: Add columns to `matches` table.

```python
op.add_column('matches', sa.Column('tournament_id', sa.UUID(), nullable=True))
op.add_column('matches', sa.Column('ronda', sa.String(length=100), nullable=True))
op.create_foreign_key('fk_matches_tournament_id', 'matches', 'tournaments', ['tournament_id'], ['id'])
```

**Step 3**: Drop columns from `players` table.

```python
op.drop_column('players', 'torneos_jugados')
op.drop_column('players', 'victorias')
op.drop_column('players', 'puntos_ranking_fep')
```

**Step 4**: Data migration (backfill tournaments from legacy `torneo` values).

```python
# Get all distinct, non-null, non-empty torneo values
conn = op.get_bind()
result = conn.execute(
    sa.text("""
        SELECT DISTINCT m.torneo, MIN(m.played_at) as first_played, m.player1_id
        FROM matches m
        WHERE m.torneo IS NOT NULL AND m.torneo != ''
        GROUP BY m.torneo, m.player1_id
    """)
)

# For each unique torneo name, create a Tournament
# Owner: find the owner of the player who played in that tournament
for row in result:
    torneo_name = row[0]
    first_played = row[1].date() if row[1] else None
    
    # Get owner_id from player
    player_result = conn.execute(
        sa.text("SELECT owner_id FROM players WHERE id = :pid"),
        {"pid": row[2]}
    ).first()
    owner_id = player_result[0] if player_result else None
    
    if not torneo_name or not first_played or not owner_id:
        continue
    
    # Insert tournament
    tournament_id = uuid4()
    conn.execute(
        sa.text("""
            INSERT INTO tournaments (id, name, date, fep_points, owner_id, created_at)
            VALUES (:id, :name, :date, 0, :owner_id, NOW())
        """),
        {"id": tournament_id, "name": torneo_name, "date": first_played, "owner_id": owner_id}
    )
    
    # Update matches with this torneo name
    conn.execute(
        sa.text("""
            UPDATE matches SET tournament_id = :tournament_id
            WHERE torneo = :torneo_name
            AND (tournament_id IS NULL OR tournament_id != :tournament_id2)
        """),
        {"tournament_id": tournament_id, "torneo_name": torneo_name, "tournament_id2": tournament_id}
    )
```

**Step 5**: Keep `torneo` column as nullable — do NOT drop it.

### 8.2 Migration Risks & Safeguards

| Risk | Mitigation |
|------|------------|
| Duplicate torneo names across users | Group by torneo name AND owner_id |
| Backfill fails on large dataset | Add `WHERE tournament_id IS NULL` to avoid double-setting |
| Rollback needed | Add `DROP COLUMN tournament_id` and `DROP TABLE tournaments` in downgrade |
| Tournaments with same name but different dates | `GROUP BY torneo, player1_id` partitions by player |

### 8.3 Downgrade (rollback)

```python
def downgrade():
    # 1. Remove FK and columns from matches
    op.drop_constraint('fk_matches_tournament_id', 'matches', type_='foreignkey')
    op.drop_column('matches', 'ronda')
    op.drop_column('matches', 'tournament_id')
    
    # 2. Restore player competitive columns
    op.add_column('players', sa.Column('torneos_jugados', sa.Integer(), nullable=True))
    op.add_column('players', sa.Column('victorias', sa.Integer(), nullable=True))
    op.add_column('players', sa.Column('puntos_ranking_fep', sa.Integer(), nullable=True))
    
    # 3. Drop tournaments table
    op.drop_table('tournaments')
```

---

## 9. OWASP Checklist

| ID | Category | What | Where |
|----|----------|------|-------|
| A01 | Broken Access Control | Ownership guard on all tournament CRUD operations | `tournaments.py` — all endpoints filter by `current_user.id` |
| A01 | Broken Access Control | Ownership guard on computed stats endpoint | `players.py` — `get_player_stats` checks player ownership |
| A01 | Broken Access Control | Match tournament_id respects player ownership | Match endpoints already check owner via player ownership |
| A03 | Injection | Pydantic validation on all input schemas | `TournamentCreateSchema`, `TournamentUpdateSchema` |
| A03 | Injection | HTML stripping on tournament name | `TournamentCreateSchema.strip_html()` validator |
| A03 | Injection | Parameterized queries via SQLAlchemy ORM | All queries use ORM or `text()` with bind params |
| A03 | Injection | Name length capped at 200 chars | `Field(max_length=200)` |
| A05 | Security Misconfiguration | No sensitive data in tournament responses | `TournamentPublicSchema` exposes only name, date, fep_points, metadata |
| A05 | Security Misconfiguration | Match responses don't expose tournament details unless scoped | `MatchPublicSchema` only shows `tournament_id` |
| A07 | Authentication | JWT required on all tournament endpoints | `Depends(get_current_user)` on every endpoint |
| A07 | Authentication | JWT required on computed stats endpoint | `Depends(get_current_user)` |
| XSS | Cross-Site Scripting | All user-controlled values rendered via `textContent` | Frontend uses `textContent` or `escapeHtml()` |
| XSS | Cross-Site Scripting | Tournament name escaped in filter dropdown and match history | `escapeHtml()` wrapper |

---

## 10. Implementation Order

This is the recommended order of implementation to minimize risk and enable incremental testing.

### Phase 1: Database & Domain
1. Create `TournamentModel` in `models.py`
2. Create `Tournament` domain entity (`app/domain/entities/tournament.py`)
3. Add `tournament_id` and `ronda` to `MatchModel`
4. Write Alembic migration (create tournament table, add columns)
5. Write data migration (backfill tournaments from legacy `torneo`)

### Phase 2: Computed Stats & Power Level
6. Create `ComputedStats` dataclass and `get_computed_stats()` function
7. Update `calculate_power_level()` to accept optional `computed_stats`
8. Update `AnalyzePlayerUseCase` / API handler to pass computed stats
9. Add `GET /api/v1/players/{id}/stats` endpoint

### Phase 3: API
10. Create tournament CRUD endpoints (`app/api/v1/tournaments.py`)
11. Modify match schemas (`MatchCreateSchema`, `MatchPublicSchema`)
12. Modify match POST/PUT endpoints
13. Register tournament router in `main.py`

### Phase 4: Frontend
14. Update match create modal with tournament selector
15. Update match history filter
16. Update stats card and competitive bar
17. Update stats modal
18. Update new player and edit player forms

### Phase 5: Cleanup
19. Drop competitive columns from `PlayerModel` (models.py + migration)
20. Remove competitive fields from `PlayerStats`, `PlayerStatsSchema`, `PlayerPublicSchema`
21. Remove old `torneo` field from schemas and forms
22. Update tests

---

## 11. Success Criteria

- [ ] Stats display correctly without any manual competitive field input
- [ ] Adding a match with tournament_id auto-updates computed stats
- [ ] Match history filter works: Todos / Amistosos / Torneo: X
- [ ] Creating a tournament via match modal creates and selects it inline
- [ ] Power level output unchanged for same técnica/físico/mental values (when computed stats match old manual entries)
- [ ] All existing matches with free-text `torneo` are migrated to proper tournaments
- [ ] Matches with null/empty `torneo` remain as amistosos (`tournament_id = NULL`)
- [ ] Removing competitive fields from forms does not break player creation/editing
- [ ] OWASP: ownership checks on all tournament CRUD, input validation on name, XSS-safe output
- [ ] Tests pass: unit tests (`tests/unit/`), integration tests (`tests/integration/`)
