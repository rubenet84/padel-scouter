/**
 * player_radar.js
 *
 * Radar chart rendering.
 * PR #4 — Extracted from player_detail.html inline script.
 *
 * Restricciones:
 * - No estado
 * - No fetch
 * - No eventos
 * - Solo renderizado radar
 */

function drawRadar(p) {
    const canvas = document.getElementById('radarChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const SIZE = 320;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = SIZE * dpr;
    canvas.height = SIZE * dpr;
    canvas.style.width = SIZE + 'px';
    canvas.style.height = SIZE + 'px';
    ctx.scale(dpr, dpr);

    const cx = SIZE / 2, cy = SIZE / 2, maxR = 105;
    const labels = ['DERECHA','VOLEA','BANDEJA','REMATE','VELOCIDAD','TÁCTICA'];
    const values = [
        p.derecha || 50, Math.round(((p.volea_derecha||50)+(p.volea_reves||50))/2) || 50, p.bandeja || 50,
        p.remate || 50, p.velocidad || 50, p.tactica || 50
    ];
    const N = labels.length;
    const step = (Math.PI * 2) / N;
    const start = -Math.PI / 2;

    ctx.clearRect(0, 0, 280, 280);

    // Grid rings
    for (let r = 1; r <= 5; r++) {
        const rad = (maxR / 5) * r;
        ctx.beginPath();
        for (let i = 0; i <= N; i++) {
            const a = start + step * i;
            const x = cx + Math.cos(a) * rad;
            const y = cy + Math.sin(a) * rad;
            i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        }
        ctx.closePath();
        ctx.strokeStyle = r === 5 ? 'rgba(255,107,0,0.15)' : 'rgba(255,255,255,0.04)';
        ctx.lineWidth = r === 5 ? 1.5 : 0.8;
        ctx.stroke();
    }

    // Axes
    for (let i = 0; i < N; i++) {
        const a = start + step * i;
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(cx + Math.cos(a) * maxR, cy + Math.sin(a) * maxR);
        ctx.strokeStyle = 'rgba(255,255,255,0.05)';
        ctx.lineWidth = 0.8;
        ctx.stroke();
    }

    // Data polygon
    ctx.beginPath();
    for (let i = 0; i <= N; i++) {
        const idx = i % N;
        const a = start + step * idx;
        const rad = (values[idx] / 100) * maxR;
        const x = cx + Math.cos(a) * rad;
        const y = cy + Math.sin(a) * rad;
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.shadowColor = '#FF6B00';
    ctx.shadowBlur = 15;
    const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, maxR);
    grad.addColorStop(0, 'rgba(255,215,0,0.2)');
    grad.addColorStop(1, 'rgba(255,107,0,0.06)');
    ctx.fillStyle = grad;
    ctx.fill();
    ctx.strokeStyle = '#FF6B00';
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.shadowBlur = 0;

    // Data points
    for (let i = 0; i < N; i++) {
        const a = start + step * i;
        const rad = (values[i] / 100) * maxR;
        const x = cx + Math.cos(a) * rad;
        const y = cy + Math.sin(a) * rad;
        ctx.beginPath(); ctx.arc(x, y, 5, 0, Math.PI*2);
        ctx.fillStyle = 'rgba(255,107,0,0.2)'; ctx.fill();
        ctx.beginPath(); ctx.arc(x, y, 3, 0, Math.PI*2);
        ctx.fillStyle = '#FF6B00'; ctx.fill();
        ctx.beginPath(); ctx.arc(x, y, 1.5, 0, Math.PI*2);
        ctx.fillStyle = '#fff'; ctx.fill();
    }

    // Labels (colores por vértice como la página principal)
    const labelColors = ['#3b82f6', '#a855f7', '#22c55e', '#f97316', '#06b6d4', '#fbbf24'];
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    for (let i = 0; i < N; i++) {
        const a = start + step * i;
        const lR = maxR + 30;
        const x = cx + Math.cos(a) * lR;
        const y = cy + Math.sin(a) * lR;
        ctx.font = '700 8px Orbitron'; ctx.fillStyle = labelColors[i];
        ctx.fillText(labels[i], x, y - 5);
        ctx.font = '900 11px Inter'; ctx.fillStyle = labelColors[i];
        ctx.fillText(values[i], x, y + 7);
    }
}
