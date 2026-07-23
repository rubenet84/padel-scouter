/**
 * notifications.js — Campanita con polling + dropdown.
 * Se auto-inicializa. Busca el botón #notif-bell en el DOM.
 */
(function () {
    const BELL_SEL = '#notif-bell';
    const COUNT_SEL = '#notif-count';
    const DROP_SEL = '#notif-dropdown';
    const LIST_SEL = '#notif-list';
    const POLL_INTERVAL = 10000; // 10s

    let bell, count, dropdown, list;
    let pollingId = null;

    /** Detecta si estamos en una página de jugador (/player/{uuid}) */
    function getPlayerId() {
        const m = window.location.pathname.match(/^\/player\/([a-f0-9\-]+)/i);
        return m ? m[1] : null;
    }

    function playerQuery() {
        const pid = getPlayerId();
        return pid ? 'player_id=' + pid : '';
    }

    function init() {
        // CSS inline para el dropdown
        const style = document.createElement('style');
        style.textContent = '#notif-dropdown.open{display:block!important}';
        document.head.appendChild(style);

        bell = document.querySelector(BELL_SEL);
        count = document.querySelector(COUNT_SEL);
        dropdown = document.querySelector(DROP_SEL);
        list = document.querySelector(LIST_SEL);
        if (!bell || !count || !dropdown || !list) {
            // No hay campana en esta página (login, landing, etc.)
            return;
        }
        // Toggle dropdown al click
        bell.addEventListener('click', function (e) {
            e.stopPropagation();
            const isOpen = !dropdown.classList.contains('open');
            dropdown.classList.toggle('open');
            if (isOpen) {
                loadNotifications();
            } else {
                markAllRead();
            }
        });
        // Cerrar dropdown al click fuera
        document.addEventListener('click', function () {
            if (dropdown.classList.contains('open')) {
                dropdown.classList.remove('open');
                markAllRead();
            }
        });
        dropdown.addEventListener('click', function (e) {
            e.stopPropagation();
        });
        // Cargar contador inicial
        updateCount();
        // Polling
        pollingId = setInterval(updateCount, POLL_INTERVAL);
        // Actualizar timestamps "hace X" cada 30s
        setInterval(refreshTimestamps, 30000);
        // Actualizar al volver a la pestaña
        document.addEventListener('visibilitychange', function () {
            if (!document.hidden) updateCount();
        });
        // Actualizar al navegar (SPA / volver atrás)
        window.addEventListener('focus', updateCount);
    }

    function refreshTimestamps() {
        document.querySelectorAll('#notif-list [data-ts]').forEach(function (el) {
            var ts = el.getAttribute('data-ts');
            if (ts) el.textContent = timeAgo(ts);
        });
    }

    async function updateCount() {
        try {
            const t = localStorage.getItem('access_token');
            if (!t) return;
            const q = playerQuery();
            const url = '/api/v1/notifications/unread-count' + (q ? '?' + q : '');
            const res = await fetch(url, {
                headers: { 'Authorization': `Bearer ${t}` }
            });
            if (!res.ok) return;
            const data = await res.json();
            const c = data.count || 0;
            if (c > 0) {
                count.textContent = c > 9 ? '9+' : c;
                count.classList.remove('hidden');
                count.classList.add('animate-pulse');
                setTimeout(() => count.classList.remove('animate-pulse'), 3000);
            } else {
                count.classList.add('hidden');
                count.textContent = '';
            }
        } catch (_) {}
    }

    async function loadNotifications() {
        try {
            const t = localStorage.getItem('access_token');
            if (!t) return;
            const q = playerQuery();
            const url = '/api/v1/notifications?limit=20' + (q ? '&' + q : '');
            const res = await fetch(url, {
                headers: { 'Authorization': `Bearer ${t}` }
            });
            if (!res.ok) return;
            const items = await res.json();
            if (!items || items.length === 0) {
                list.innerHTML = '<div class="p-4 text-center text-xs" style="color:#64748b;">Sin notificaciones</div>';
                return;
            }
            list.innerHTML = items.map(n => `
                <a href="${escHtml(n.related_url || '#')}"
                   onclick="event.preventDefault();markNotifRead('${n.id}','${(n.related_url || '#').replace(/'/g, "\\'")}')"
                   class="block px-4 py-3 transition-colors hover:bg-white/5 ${n.is_read ? '' : 'border-l-2'}"
                   style="${n.is_read ? 'opacity:0.55;' : 'border-left:2px solid #a78bfa;'}">
                    <div class="text-xs font-bold" style="color:#e2e8f0;">${escHtml(n.title)}</div>
                    <div class="text-[11px] mt-0.5" style="color:#cbd5e1;">${n.message || ''}</div>
                    <div class="text-[9px] mt-1" style="color:#3b82f6;" data-ts="${n.created_at}">${timeAgo(n.created_at)}</div>
                </a>
            `).join('');
        } catch (_) {
            list.innerHTML = '<div class="p-4 text-center text-xs" style="color:#ef4444;">Error al cargar</div>';
        }
    }

    async function markAllRead() {
        try {
            const t = localStorage.getItem('access_token');
            if (!t) return;
            // Solo marcar como leídas las del jugador actual, no todas
            const q = playerQuery();
            const url = '/api/v1/notifications/read-all' + (q ? '?' + q : '');
            await fetch(url, {
                method: 'PUT',
                headers: { 'Authorization': `Bearer ${t}` }
            });
            updateCount();
        } catch (_) {}
    }

    function timeAgo(iso) {
        if (!iso) return '';
        const diff = Date.now() - new Date(iso).getTime();
        const mins = Math.floor(diff / 60000);
        if (mins < 1) return 'Ahora';
        if (mins < 60) return `hace ${mins} min`;
        const hrs = Math.floor(mins / 60);
        if (hrs < 24) return `hace ${hrs}h`;
        const days = Math.floor(hrs / 24);
        return `hace ${days}d`;
    }

    function escHtml(str) {
        if (!str) return '';
        const d = document.createElement('div');
        d.textContent = str;
        return d.innerHTML;
    }

    // Init cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Expuesta globalmente para el onclick inline de las notificaciones
    window.markNotifRead = async function(id, url) {
        try {
            const t = localStorage.getItem('access_token');
            if (!t) return;
            await fetch('/api/v1/notifications/' + id + '/read', {
                method: 'PUT',
                headers: { 'Authorization': 'Bearer ' + t }
            });
            // Cerrar dropdown antes de navegar
            var dd = document.querySelector('#notif-dropdown');
            if (dd) dd.classList.remove('open');
            updateCount();
            // Pequeña pausa para que el fetch termine antes de navegar
            setTimeout(function() { window.location.href = url; }, 100);
        } catch (_) {
            window.location.href = url;
        }
    };
})();
