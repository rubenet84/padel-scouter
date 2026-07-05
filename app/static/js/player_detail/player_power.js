/**
 * player_power.js
 *
 * Power level, dragon balls, shenron, and golpe definitivo rendering.
 * PR #4 — Extracted from player_detail.html inline script.
 *
 * Restricciones:
 * - No estado
 * - No fetch
 * - No eventos
 * - Solo renderizado power
 */

function animatePower(target) {
    const el = document.getElementById('power-display');
    const duration = 2000;
    const start = performance.now();
    function update(now) {
        const t = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - t, 3);
        el.textContent = Math.round(eased * target).toLocaleString();
        if (t < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

function renderDragonBalls(nivel) {
    const count = dragonBallCount(nivel);
    const sz = 44;
    const cx = sz/2, cy = sz/2, r = sz/2 - 1.5;

    // Star positions for 1 through 7 stars (matches dragon ball canon)
    const starPositions = [
        [[cx,cy]],
        [[cx-4,cy],[cx+4,cy]],
        [[cx-5,cy-3],[cx+5,cy-3],[cx,cy+4]],
        [[cx-5,cy-4],[cx+5,cy-4],[cx-5,cy+4],[cx+5,cy+4]],
        [[cx,cy-6],[cx-5,cy-1],[cx+5,cy-1],[cx-3,cy+5],[cx+3,cy+5]],
        [[cx-4,cy-7],[cx+4,cy-7],[cx-7,cy],[cx+7,cy],[cx-4,cy+6],[cx+4,cy+6]],
        [[cx,cy-7],[cx-5,cy-4],[cx+5,cy-4],[cx-7,cy+1],[cx+7,cy+1],[cx-3,cy+6],[cx+3,cy+6]],
    ];

    function starPath(px, py, r5) {
        let d = '';
        for (let i = 0; i < 10; i++) {
            const a = (i * Math.PI / 5) - Math.PI / 2;
            const rr = i % 2 === 0 ? r5 : r5 * 0.42;
            const x = px + Math.cos(a) * rr, y = py + Math.sin(a) * rr;
            d += (i === 0 ? 'M' : 'L') + x.toFixed(2) + ' ' + y.toFixed(2);
        }
        return d + 'Z';
    }

    let html = '';
    for (let i = 1; i <= count; i++) {
        const uid = i + '_' + Date.now() + '_' + Math.random().toString(36).slice(2,6);
        const pos = starPositions[i-1] || starPositions[0];
        const sr = i <= 2 ? 5.0 : i <= 4 ? 4.0 : 3.6;
        const stars = pos.map(([px, py]) =>
            `<path d="${starPath(px, py, sr)}" fill="#e60000" stroke="#fff" stroke-width="1" style="animation:starTwinkle 1.8s ease-in-out infinite;animation-delay:${(i-1)*0.15}s"/>`
        ).join('');

        html += `
            <div class="dragon-ball">
                <svg viewBox="0 0 ${sz} ${sz}" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                        <radialGradient id="bsph${uid}" cx="40%" cy="34%" r="66%">
                            <stop offset="0%"   stop-color="#ffffff"/>
                            <stop offset="10%"  stop-color="#fff3d6"/>
                            <stop offset="28%"  stop-color="#ffe082"/>
                            <stop offset="52%"  stop-color="#ffcc66"/>
                            <stop offset="75%"  stop-color="#ffa726"/>
                            <stop offset="100%" stop-color="#ff8f00"/>
                        </radialGradient>
                        <radialGradient id="bshs${uid}" cx="64%" cy="66%" r="48%">
                            <stop offset="0%"  stop-color="#5a1500" stop-opacity="0.18"/>
                            <stop offset="100%" stop-color="#5a1500" stop-opacity="0"/>
                        </radialGradient>
                        <radialGradient id="bhl${uid}" cx="28%" cy="22%" r="30%">
                            <stop offset="0%"  stop-color="#fff" stop-opacity="0.95"/>
                            <stop offset="35%" stop-color="#fff" stop-opacity="0.35"/>
                            <stop offset="100%" stop-color="#fff" stop-opacity="0"/>
                        </radialGradient>
                        <radialGradient id="bhl2${uid}" cx="72%" cy="74%" r="18%">
                            <stop offset="0%"  stop-color="#ffab40" stop-opacity="0.2"/>
                            <stop offset="100%" stop-color="#ffab40" stop-opacity="0"/>
                        </radialGradient>
                        <radialGradient id="bhl3${uid}" cx="50%" cy="50%" r="50%">
                            <stop offset="0%"  stop-color="#fff" stop-opacity="0.12"/>
                            <stop offset="100%" stop-color="#fff" stop-opacity="0"/>
                        </radialGradient>
                    </defs>
                    <circle cx="${cx}" cy="${cy}" r="${r}" fill="url(#bsph${uid})"/>
                    <circle cx="${cx}" cy="${cy}" r="${r}" fill="url(#bshs${uid})"/>
                    <circle cx="${cx}" cy="${cy}" r="${r}" fill="url(#bhl3${uid})"/>
                    ${stars}
                    <ellipse cx="${cx-4}" cy="${cy-5}" rx="7" ry="4.5" fill="url(#bhl${uid})"/>
                    <circle cx="${cx+6}" cy="${cy+6}" r="4" fill="url(#bhl2${uid})"/>
                    <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="rgba(255,255,255,0.15)" stroke-width="0.8"/>
                </svg>
            </div>`;
    }
    return html;
}

function renderShenron() {
    const cb = Date.now();
    return `<img src="/static/images/dragon-ball-shenron.png?cb=${cb}" alt="Shenron" style="width:100%;height:auto;display:block;">`;
}

function renderGolpeDefinitivo(latest, player) {
    const card = document.getElementById('golpe-card');
    if (!card || !player) return;

    let puntuacion, nombre, descripcion, nivel, statLabel;

    if (latest?.golpe_puntuacion != null) {
        puntuacion = latest.golpe_puntuacion;
        nombre = latest.golpe_definitivo || 'Por determinar';
        descripcion = latest.golpe_descripcion || '';
        nivel = latest.nivel_amenaza || nivelAmenazaFromScore(puntuacion);
        // Get the stat label from the player's strongest stat
        const best = findStrongestStatFromPlayer(player);
        statLabel = best.label;
    } else {
        const best = findStrongestStatFromPlayer(player);
        puntuacion = best.value;
        nombre = latest?.golpe_definitivo || `${best.label} Definitivo`;
        descripcion = latest?.golpe_descripcion || '';
        nivel = latest?.nivel_amenaza || nivelAmenazaFromScore(puntuacion);
        statLabel = best.label;
    }

    nivel = nivelAmenazaFromScore(puntuacion);

    const amenazaMap = {
        'BAJO':     { label: 'BAJO',     color: '#6b7280' },
        'MEDIO':    { label: 'MEDIO',    color: '#f59e0b' },
        'ALTO':     { label: 'ALTO',     color: '#ef4444' },
        'MUY ALTO': { label: 'MUY ALTO', color: '#FFD700' },
    };
    const amenaza = amenazaMap[nivel] || amenazaMap['MEDIO'];

    card.classList.remove('hidden');
    document.getElementById('golpe-nombre').textContent = nombre;
    document.getElementById('golpe-stat-sub').textContent = `${statLabel} · ${puntuacion}/100`;
    document.getElementById('nivel-amenaza-badge').textContent = amenaza.label;
    document.getElementById('nivel-amenaza-badge').style.color = amenaza.color;
    document.getElementById('nivel-amenaza-text').textContent = amenaza.label;
    document.getElementById('nivel-amenaza-text').style.color = amenaza.color;
    document.getElementById('amenaza-bar').style.width = puntuacion + '%';
    document.getElementById('amenaza-bar').style.background = `linear-gradient(90deg, #FF6B00, ${amenaza.color})`;

    const descEl = document.getElementById('golpe-descripcion');
    if (descripcion) {
        descEl.textContent = descripcion;
        descEl.classList.remove('hidden');
    } else {
        descEl.textContent = '';
        descEl.classList.add('hidden');
    }

    const ballsContainer = document.getElementById('dragon-balls-container');
    if (ballsContainer) ballsContainer.innerHTML = renderDragonBalls(nivel);

    const shenronSection = document.getElementById('shenron-section');
    const shenronContainer = document.getElementById('shenron-container');
    const shenronSvg = document.getElementById('shenron-svg');
    const mrsatanSection = document.getElementById('mrsatan-section');
    const gohanSection = document.getElementById('gohan-section');
    const goku4Section = document.getElementById('goku4-section');
    if (nivel === 'MUY ALTO') {
        if (shenronSvg) shenronSvg.innerHTML = renderShenron();
        if (shenronContainer) shenronContainer.classList.add('shenron-visible');
        if (shenronSection) shenronSection.classList.remove('hidden');
    } else {
        if (shenronContainer) shenronContainer.classList.remove('shenron-visible');
        if (shenronSection) shenronSection.classList.add('hidden');
    }
    if (nivel === 'BAJO') {
        if (mrsatanSection) mrsatanSection.classList.remove('hidden');
    } else {
        if (mrsatanSection) mrsatanSection.classList.add('hidden');
    }
    if (nivel === 'MEDIO') {
        if (gohanSection) gohanSection.classList.remove('hidden');
    } else {
        if (gohanSection) gohanSection.classList.add('hidden');
    }
    if (nivel === 'ALTO') {
        if (goku4Section) goku4Section.classList.remove('hidden');
    } else {
        if (goku4Section) goku4Section.classList.add('hidden');
    }
}
