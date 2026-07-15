/**
 * notifications.js — Campanita con polling + dropdown.
 * Se auto-inicializa. Busca el botón #notif-bell en el DOM.
 */
(function () {
    const BELL_SEL = '#notif-bell';
    const COUNT_SEL = '#notif-count';
    const DROP_SEL = '#notif-dropdown';
    const LIST_SEL = '#notif-list';
    const POLL_INTERVAL = 45000; // 45s

    let bell, count, dropdown, list;
    let pollingId = null;

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
                markAllRead();
                loadNotifications();
            }
        });
        // Cerrar dropdown al click fuera
        document.addEventListener('click', function () {
            dropdown.classList.remove('open');
        });
        dropdown.addEventListener('click', function (e) {
            e.stopPropagation();
        });
        // Cargar inicial
        updateCount();
        loadNotifications();
        // Polling
        pollingId = setInterval(updateCount, POLL_INTERVAL);
    }

    async function updateCount() {
        try {
            const t = localStorage.getItem('access_token');
            if (!t) return;
            const res = await fetch('/api/v1/notifications/unread-count', {
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
            const res = await fetch('/api/v1/notifications?limit=20', {
                headers: { 'Authorization': `Bearer ${t}` }
            });
            if (!res.ok) return;
            const items = await res.json();
            if (!items || items.length === 0) {
                list.innerHTML = '<div class="p-4 text-center text-xs" style="color:#64748b;">Sin notificaciones</div>';
                return;
            }
            list.innerHTML = items.map(n => `
                <a href="${escHtml(n.related_url || '#')}" class="block px-4 py-3 transition-colors hover:bg-white/5 ${n.is_read ? '' : 'border-l-2'}"
                   style="${n.is_read ? 'opacity:0.6;' : 'border-left-color:#a855f7;'}">
                    <div class="text-xs font-bold text-white">${escHtml(n.title)}</div>
                    <div class="text-[10px] mt-0.5" style="color:#94a3b8;">${escHtml(n.message || '')}</div>
                    <div class="text-[9px] mt-1" style="color:#64748b;">${timeAgo(n.created_at)}</div>
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
            await fetch('/api/v1/notifications/read-all', {
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
})();
