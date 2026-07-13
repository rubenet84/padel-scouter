/**
 * player_render.js
 *
 * Core render functions for the player detail page.
 * PR #6A — Extracted from player_detail.html inline script.
 *
 * Restricciones:
 * - No fetch
 * - No estado (recibe datos como parámetros)
 * - Accede al DOM via window.DOM (expuesto por player_detail.js)
 * - Script clásico (no module) — compatible con inline script legacy
 */

// ── Render Player (main entry) ─────────────────────────────────

function renderPlayer(p, analyses) {
    const D = window.DOM;

    D.loadingState().classList.add('hidden');
    D.mainContent().classList.remove('hidden');

    // Breadcrumb & name
    D.breadcrumbName().textContent = p.name;
    D.playerName().textContent = p.name;

    const catDisplay = p.category;
    const levelInfo = CATEGORY_LEVELS[catDisplay];
    const badgeText = levelInfo
        ? `${levelInfo.icon} ${catDisplay} · Nivel ${levelInfo.min}  –  ${levelInfo.max}`
        : catDisplay;
    D.badgeCategory().textContent = badgeText;

    // Avatar
    setAvatar(p.avatar_url);

    // Aggregate bars (misma fórmula que dashboard: 10 stats, voleas separadas)
    const tecnica = Math.round(((p.derecha||50)+(p.reves||50)+(p.volea_derecha||50)+(p.volea_reves||50)+(p.bandeja||50)+(p.vibora||50)+(p.remate||50)+(p.globo||50)+(p.saque||50)+(p.bajada_pared||50)) / 10);
    const fisico  = Math.round(((p.velocidad||50)+(p.resistencia||50)+(p.reflejos||50)) / 3);
    const mental  = Math.round(((p.tactica||50)+(p.presion||50)+(p.trabajo_en_pareja||50)) / 3);

    D.barTecnica().style.width = Math.min(tecnica, 100) + '%';
    D.barTecnicaVal().textContent = Math.min(tecnica, 100);
    D.barFisico().style.width = Math.min(fisico, 100) + '%';
    D.barFisicoVal().textContent = Math.min(fisico, 100);
    D.barMental().style.width = Math.min(mental, 100) + '%';
    D.barMentalVal().textContent = Math.min(mental, 100);

    // Computed stats — fetch async and populate stats card + competitive bar
    renderComputedStats(playerId);

    // Individual stats
    D.valRemate().textContent = p.remate || 50;
    D.valBandeja().textContent = p.bandeja || 50;
    D.valVoleaDerecha().textContent = p.volea_derecha || 50;
    D.valVoleaReves().textContent = p.volea_reves || 50;

    // Radar
    drawRadar(p);

    // Analysis
    const latest = analyses && analyses.length > 0 ? analyses[analyses.length - 1] : null;

    if (latest) {
        // Power level
        const power = latest.power_level;
        animatePower(power);
        D.powerBar().style.width = Math.min((power / 9999) * 100, 100) + '%';

        // Categoría sugerida según power level (misma tabla que classify_by_power)
        const suggestedEl = D.badgeSuggested();
        if (suggestedEl) {
          const ranges = [
            { max: 1500, label: 'Iniciación' },
            { max: 3000, label: '5ª Categoría' },
            { max: 4500, label: '4ª Categoría' },
            { max: 6000, label: '3ª Categoría' },
            { max: 7500, label: '2ª Categoría' },
            { max: 9000, label: '1ª Categoría' },
            { max: Infinity, label: 'Profesional' },
          ];
          const suggested = ranges.find(r => power < r.max)?.label || 'Profesional';
          suggestedEl.textContent = `Sugerida: ${suggested}`;
          suggestedEl.classList.remove('hidden');
        }

        // AI description
        D.aiDescCard().classList.remove('hidden');
        D.aiDescription().textContent = '"' + latest.ai_description + '"';

        // Strengths & Weaknesses
        const strengths = typeof latest.strengths === 'string' ? JSON.parse(latest.strengths) : latest.strengths;
        const weaknesses = typeof latest.weaknesses === 'string' ? JSON.parse(latest.weaknesses) : latest.weaknesses;

        D.swSection().classList.remove('hidden');
        D.swSection().classList.add('grid');

        const slist = D.strengthsList();
        slist.innerHTML = (strengths || []).map(s => `
            <li class="flex items-start gap-2.5">
                <div class="w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5" style="background:rgba(0,255,135,0.1);">
                    <span style="color:#00FF87;font-size:10px;">✓</span>
                </div>
                <p class="text-sm text-white">${escapeHtml(s)}</p>
            </li>`).join('');

        const wlist = D.weaknessesList();
        wlist.innerHTML = (weaknesses || []).map(w => `
            <li class="flex items-start gap-2.5">
                <div class="w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5" style="background:rgba(255,45,45,0.1);">
                    <span style="color:#FF2D2D;font-size:10px;">✗</span>
                </div>
                <p class="text-sm text-white">${escapeHtml(w)}</p>
            </li>`).join('');

        // Improvement plan + objectives + projection
        D.planCard().classList.remove('hidden');
        const planText = latest.improvement_plan || '';
        const descEl = D.improvementPlan();
        const objContainer = document.getElementById('plan-objectives');
        const projContainer = document.getElementById('plan-projection');
        const projText = document.getElementById('plan-projection-text');
        
        // Parse structured plan: sections separated by ---
        const sections = planText.split(/\n---\n/);
        if (sections.length >= 2) {
          // First section is the description text
          descEl.textContent = sections[0].trim();
          
          // Middle sections are objectives (1, 2, 3)
          const objSections = sections.slice(1, -1);
          const projectionSection = sections[sections.length - 1];
          
          // Render objectives
          const objColors = [
            { bg: 'rgba(249,115,22,0.15)', border: 'rgba(249,115,22,0.25)', text: '#f97316', line: 'rgba(249,115,22,0.4)', nameColor: '#f97316', freqColor: '#f97316' },
            { bg: 'rgba(59,130,246,0.1)', border: 'rgba(59,130,246,0.2)', text: '#60a5fa', line: 'rgba(59,130,246,0.4)', nameColor: '#60a5fa', freqColor: '#60a5fa' },
            { bg: 'rgba(168,85,247,0.15)', border: 'rgba(168,85,247,0.25)', text: '#a78bfa', line: 'rgba(168,85,247,0.4)', nameColor: '#a78bfa', freqColor: '#a78bfa' },
          ];
          objContainer.innerHTML = objSections.map((sec, i) => {
            const lines = sec.trim().split('\n').map(l => l.trim()).filter(Boolean);
            const num = lines[0] || (i + 1).toString();
            const name = lines[1] || 'Objetivo';
            const rawDetail = lines.slice(2).join(' ') || 'Ejercicio específico';
            const c = objColors[i] || objColors[objColors.length - 1];
            let detail = rawDetail;
            let freq = '';
            // Separar frecuencia del texto descriptivo (buscar patrón "X sesión/es/semana")
            const freqMatch = rawDetail.match(/(\d+\s+sesi(?:o\u0301?|ó)nes?\/semana(?:\s*\([^)]*\))?\s*(?:[—–\-─]\s*)?)/i);
            if (freqMatch) {
              freq = freqMatch[1].trim();
              detail = rawDetail.replace(freqMatch[1], '').trim();
            }
            return `
              <div class="rounded-2xl overflow-hidden card-hover" style="background:#12121A;border:1px solid ${c.border};">
                <div class="h-0.5" style="background:linear-gradient(90deg,transparent,${c.line},transparent);"></div>
                <div class="flex gap-4 p-4">
                  <div class="w-10 h-10 rounded-xl flex items-center justify-center font-orbitron font-black text-base flex-shrink-0" style="background:${c.bg};border:1px solid ${c.border};color:${c.text};">${num}</div>
                  <div class="min-w-0 flex-1">
                    <div class="text-sm font-bold font-orbitron" style="color:${c.nameColor};">${escapeHtml(name)}</div>
                    <div class="text-xs mt-1.5 leading-relaxed" style="color:#E2E8F0;">${escapeHtml(detail)}</div>
                    ${freq ? `<div class="text-[10px] mt-1 font-medium" style="color:${c.freqColor};">${escapeHtml(freq)}</div>` : ''}
                  </div>
                </div>
              </div>`;
          }).join('');
          
          // Parse projection section
          if (projectionSection) {
            const projLines = projectionSection.trim().split('\n').map(l => l.trim()).filter(Boolean);
            if (projLines.length >= 2) {
              const projMatch = projLines[1]?.match(/(\d[\d,.]*)\s*→\s*(\d[\d,.]*)/);
              if (projMatch) {
                const current = projMatch[1];
                const target = projMatch[2];
                document.getElementById('plan-current-pl').textContent = current;
                document.getElementById('plan-target-pl').textContent = target;
                projContainer.classList.remove('hidden');
                // Update visual with proper styling
                document.getElementById('plan-current-pl').style.cssText = 'font-orbitron;font-weight:900;font-size:1.25rem;color:white';
                document.getElementById('plan-target-pl').style.cssText = 'font-orbitron;font-weight:900;font-size:1.5rem';
              }
            }
          }
        } else {
          // No structured format, just show text
          descEl.textContent = planText;
        }

    } else {
        D.powerDisplay().textContent = '???';
        D.noAnalysisCta().classList.remove('hidden');
    }

    // Golpe definitivo (stats del jugador + análisis IA si existe)
    renderGolpeDefinitivo(latest, p);
}

// ── Stat Fields (for findStrongestStatFromPlayer) ──────────────

const SCOUTER_STAT_FIELDS = [
    ['derecha','Derecha'], ['reves','Revés'],
    ['volea_derecha','Volea Derecha'], ['volea_reves','Volea Revés'],
    ['bandeja','Bandeja'],
    ['vibora','Víbora'], ['remate','Remate'], ['globo','Globo'], ['saque','Saque'],
    ['bajada_pared','Bajada de pared'], ['velocidad','Velocidad'], ['resistencia','Resistencia'],
    ['reflejos','Reflejos'], ['tactica','Táctica'], ['presion','Presión'],
    ['trabajo_en_pareja','Trabajo en pareja'],
];

function findStrongestStatFromPlayer(p) {
    let best = { key: 'derecha', label: 'Derecha', value: p.derecha ?? 0 };
    for (const [key, label] of SCOUTER_STAT_FIELDS) {
        const val = p[key] ?? 0;
        if (val > best.value) best = { key, label, value: val };
    }
    return best;
}

// ── Avatar Upload ─────────────────────────────────────────────

function uploadAvatar(event) {
    const file = event.target.files?.[0];
    if (!file) return;

    // Client-side validation
    const allowed = ['image/jpeg','image/png','image/gif','image/webp'];
    if (!allowed.includes(file.type)) {
        showToast('Formato no permitido. Usá JPG, PNG, GIF o WebP.', 'error');
        return;
    }
    if (file.size > 5 * 1024 * 1024) {
        showToast('La imagen es demasiado grande (máx 5MB).', 'error');
        return;
    }

    // Show spinner overlay WITHOUT destroying the DOM
    const D = window.DOM;
    const spinner = D.avatarSpinner();
    spinner.classList.remove('hidden');

    const formData = new FormData();
    formData.append('file', file);

    fetch(`/api/v1/players/${playerId}/avatar`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
    })
    .then(r => {
        if (!r.ok) return r.json().then(e => { throw new Error(e.detail || 'Error al subir') });
        return r.json();
    })
    .then(p => {
        // Image needs a cache-buster bust most browsers will see the same URL
        const cacheBuster = p.avatar_url + (p.avatar_url.includes('?') ? '&' : '?') + Date.now();
        return new Promise((resolve, reject) => {
            setAvatar(cacheBuster, () => {
                showToast('✅ Foto actualizada', 'success');
                spinner.classList.add('hidden');
                resolve();
            });
        });
    })
    .catch(err => {
        spinner.classList.add('hidden');
        showToast(err.message, 'error');
        setAvatar(null); // back to placeholder
    });
}

function setAvatar(url, onload) {
    const D = window.DOM;
    const img = D.avatarImg();
    const placeholder = D.avatarPlaceholder();
    if (url) {
        img.onload = function() {
            img.classList.remove('hidden');
            img.style.display = 'block';
            placeholder.style.display = 'none';
            if (onload) onload();
        };
        img.onerror = function() {
            // fallback to placeholder
            img.classList.add('hidden');
            img.style.display = 'none';
            placeholder.style.display = 'block';
            if (onload) onload();
        };
        img.src = url;
    } else {
        img.onload = null;
        img.onerror = null;
        img.src = '';
        img.classList.add('hidden');
        img.style.display = 'none';
        placeholder.style.display = 'block';
        if (onload) onload();
    }
}


