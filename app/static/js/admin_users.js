/**
 * admin_users.js — Panel de administración de usuarios.
 *
 * Solo UX: la autoridad real es el backend (/api/v1/admin/*, permiso users.read).
 * Usa exclusivamente los endpoints existentes y el patrón de auth del proyecto
 * (JWT en localStorage + fetch con Bearer). showToast/escapeHtml vienen de
 * player_utils.js (cargado antes que este fichero).
 */
(function () {
  const API = '/api/v1';
  const TOKEN = localStorage.getItem('access_token');

  let currentUser = null;
  let usersById = {};
  let target = null;
  let page = 1;
  const pageSize = 25;

  if (!TOKEN) { window.location.href = '/login'; return; }

  const $ = (id) => document.getElementById(id);

  function authHeaders() {
    return { 'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/json' };
  }

  async function api(path, opts) {
    const options = Object.assign({ headers: authHeaders() }, opts || {});
    const res = await fetch(API + path, options);
    if (res.status === 401) {
      localStorage.clear();
      window.location.href = '/login';
      throw new Error('unauthorized');
    }
    return res;
  }

  function roleBadge(role) {
    const map = {
      admin: ['#FFD700', 'rgba(255,215,0,0.10)'],
      entrenador: ['#3b82f6', 'rgba(59,130,246,0.12)'],
      jugador: ['#22c55e', 'rgba(34,197,94,0.12)'],
    };
    const c = map[role] || ['#a78bfa', 'rgba(124,95,214,0.12)'];
    return '<span class="badge" style="color:' + c[0] + ';background:' + c[1] + ';">' + escapeHtml(role) + '</span>';
  }

  function statusBadge(isActive) {
    return isActive
      ? '<span class="badge" style="color:#22c55e;background:rgba(34,197,94,0.12);">Activo</span>'
      : '<span class="badge" style="color:#ef4444;background:rgba(239,68,68,0.12);">Suspendido</span>';
  }

  function formatDate(iso) {
    if (!iso) return '—';
    const d = new Date(iso);
    return isNaN(d) ? '—' : d.toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric' });
  }

  function skeletonRows() {
    let rows = '';
    for (let i = 0; i < 5; i++) {
      rows += '<tr class="border-b border-[#2A2A3A] animate-pulse">'
        + '<td class="p-3"><div class="h-3 bg-[#2A2A3A] rounded w-24"></div></td>'
        + '<td class="p-3"><div class="h-3 bg-[#2A2A3A] rounded w-40"></div></td>'
        + '<td class="p-3"><div class="h-4 bg-[#2A2A3A] rounded-full w-16"></div></td>'
        + '<td class="p-3"><div class="h-3 bg-[#2A2A3A] rounded w-8 ml-auto"></div></td>'
        + '<td class="p-3"><div class="h-3 bg-[#2A2A3A] rounded w-8 ml-auto"></div></td>'
        + '<td class="p-3"><div class="h-4 bg-[#2A2A3A] rounded-full w-20 mx-auto"></div></td>'
        + '<td class="p-3"><div class="h-6 bg-[#2A2A3A] rounded w-20 ml-auto"></div></td>'
        + '</tr>';
    }
    return rows;
  }

  function messageRow(text) {
    return '<tr><td colspan="7" class="p-8 text-center text-gray-500">' + escapeHtml(text) + '</td></tr>';
  }

  function renderRows(items) {
    const tbody = $('admin-users-body');
    usersById = {};
    if (!items.length) { tbody.innerHTML = messageRow('No hay usuarios que coincidan con los filtros.'); return; }
    tbody.innerHTML = items.map((u) => {
      usersById[u.id] = u;
      return '<tr class="border-b border-[#2A2A3A] hover:bg-purple-800/10 transition-colors">'
        + '<td class="p-3 text-white font-medium">' + escapeHtml(u.username) + '</td>'
        + '<td class="p-3" style="color:#c4b5fd;">' + escapeHtml(u.email) + '</td>'
        + '<td class="p-3">' + roleBadge(u.role) + '</td>'
        + '<td class="p-3 text-right text-white">' + (u.players_count || 0) + '</td>'
        + '<td class="p-3 text-right text-white">' + (u.matches_count || 0) + '</td>'
        + '<td class="p-3 text-center">' + statusBadge(u.is_active) + '</td>'
        + '<td class="p-3 text-right"><button data-manage="' + u.id + '"'
        + ' class="px-3 py-1.5 rounded-lg text-xs font-bold transition-colors"'
        + ' style="background:rgba(124,95,214,0.15);border:1px solid rgba(124,95,214,0.3);color:#a78bfa;">Gestionar</button></td>'
        + '</tr>';
    }).join('');
  }

  function renderPagination(current, totalPages, total) {
    const el = $('admin-pagination');
    if (!total || totalPages <= 1) { el.classList.add('hidden'); return; }
    el.classList.remove('hidden');
    const btnStyle = 'px-4 py-2 rounded-lg text-sm font-bold transition-colors';
    const on = 'background:rgba(124,95,214,0.15);border:1px solid rgba(124,95,214,0.3);color:#a78bfa;';
    const off = 'background:rgba(100,116,139,0.08);border:1px solid rgba(100,116,139,0.2);color:#64748b;cursor:not-allowed;';
    const prevDis = current <= 1 ? off : on;
    const nextDis = current >= totalPages ? off : on;
    el.innerHTML = '<button id="pg-prev" class="' + btnStyle + '" style="' + prevDis + '">Anterior</button>'
      + '<span class="text-sm text-gray-400">Página ' + current + ' de ' + totalPages + '</span>'
      + '<button id="pg-next" class="' + btnStyle + '" style="' + nextDis + '">Siguiente</button>';
    $('pg-prev').disabled = current <= 1;
    $('pg-next').disabled = current >= totalPages;
    $('pg-prev').onclick = function () { if (page > 1) { page--; loadUsers(); } };
    $('pg-next').onclick = function () { if (page < totalPages) { page++; loadUsers(); } };
  }

  async function loadStats() {
    try {
      const res = await api('/admin/users/stats');
      if (!res.ok) return;
      const s = await res.json();
      $('stat-total').textContent = s.total;
      $('stat-entrenadores').textContent = s.entrenadores;
      $('stat-jugadores').textContent = s.jugadores;
      $('stat-suspendidos').textContent = s.suspended;
    } catch (e) {
      // 401 ya redirige a /login; en fallo de red mostramos el error existente.
      if (e && e.message === 'unauthorized') return;
      showToast('No se pudieron cargar las estadísticas.', 'error');
    }
  }

  async function loadUsers() {
    const tbody = $('admin-users-body');
    tbody.innerHTML = skeletonRows();

    const params = new URLSearchParams();
    const search = $('admin-search').value.trim();
    const role = $('admin-role').value;
    const status = $('admin-status').value;
    if (search) params.set('search', search);
    if (role) params.set('role', role);
    if (status) params.set('is_active', status);
    params.set('page', page);
    params.set('page_size', pageSize);

    try {
      const res = await api('/admin/users?' + params.toString());
      if (res.status === 403) { tbody.innerHTML = messageRow('No tienes permisos para ver los usuarios.'); return; }
      if (!res.ok) { tbody.innerHTML = messageRow('No se pudieron cargar los usuarios.'); return; }
      const data = await res.json();
      $('admin-total').textContent = data.total + ' usuario' + (data.total === 1 ? '' : 's');
      renderRows(data.items);
      renderPagination(data.page, data.total_pages, data.total);
    } catch (e) {
      // 401 ya redirige a /login; en fallo de red no dejamos el skeleton cargando.
      if (e && e.message === 'unauthorized') return;
      tbody.innerHTML = messageRow('No se pudieron cargar los usuarios.');
    }
  }

  // ── Modal ──────────────────────────────────────────────────
  function showView() {
    $('admin-modal-view').classList.remove('hidden');
    $('admin-modal-confirm').classList.add('hidden');
    $('admin-status-confirm').classList.add('hidden');
  }

  function openAdminModal(id) {
    const u = usersById[id];
    if (!u) return;
    target = u;

    $('m-username').textContent = u.username;
    $('m-email').textContent = u.email;
    $('m-role').innerHTML = roleBadge(u.role);
    $('m-status').innerHTML = statusBadge(u.is_active);
    $('m-players').textContent = u.players_count || 0;
    $('m-matches').textContent = u.matches_count || 0;
    $('m-tournaments').textContent = u.tournaments_count || 0;
    $('m-created').textContent = formatDate(u.created_at);

    const editor = $('admin-role-editor');
    const note = $('admin-role-note');
    const statusEditor = $('admin-status-editor');
    const statusBtn = $('admin-status-btn');
    if (u.role === 'admin' || (currentUser && u.id === currentUser.id)) {
      editor.classList.add('hidden');
      statusEditor.classList.add('hidden');
      note.classList.remove('hidden');
      note.textContent = u.role === 'admin'
        ? 'La gestión de administradores está fuera del alcance.'
        : 'No puedes gestionar tu propia cuenta.';
    } else {
      editor.classList.remove('hidden');
      statusEditor.classList.remove('hidden');
      note.classList.add('hidden');
      $('m-role-select').value = (u.role === 'jugador') ? 'entrenador' : 'jugador';
      statusBtn.textContent = u.is_active ? 'Suspender usuario' : 'Reactivar usuario';
      statusBtn.style.background = u.is_active
        ? 'linear-gradient(135deg,#ef4444,#b91c1c)'
        : 'linear-gradient(135deg,#22c55e,#16a34a)';
    }
    showView();
    $('admin-modal').classList.remove('hidden');
  }

  function closeAdminModal() {
    $('admin-modal').classList.add('hidden');
    target = null;
    showView();
  }

  function requestRoleChange() {
    if (!target) return;
    const sel = $('m-role-select').value;
    if (sel === target.role) { showToast('El usuario ya tiene ese rol.', 'error'); return; }
    $('c-from').textContent = target.role.toUpperCase();
    $('c-to').textContent = sel.toUpperCase();
    $('admin-modal-view').classList.add('hidden');
    $('admin-modal-confirm').classList.remove('hidden');
  }

  function cancelRoleChange() { showView(); }

  async function confirmRoleChange() {
    if (!target) return;
    const sel = $('m-role-select').value;
    const btn = $('admin-confirm-btn');
    btn.disabled = true;
    btn.textContent = 'Guardando...';
    try {
      const res = await api('/admin/users/' + target.id + '/role', {
        method: 'PATCH',
        body: JSON.stringify({ role: sel }),
      });
      if (res.ok) {
        showToast('Rol actualizado correctamente', 'success');
        closeAdminModal();
        loadUsers();
        loadStats();
        return;
      }
      let msg = 'No se pudo cambiar el rol.';
      if (res.status === 403) msg = 'No tienes permisos para esta acción.';
      else if (res.status === 422) msg = 'Rol no permitido.';
      else if (res.status === 404) msg = 'Usuario no encontrado.';
      showToast(msg, 'error');
    } catch (e) {
      showToast('Error de conexión.', 'error');
    } finally {
      btn.disabled = false;
      btn.textContent = 'Confirmar';
    }
  }

  function requestStatusChange() {
    if (!target) return;
    $('s-from').textContent = target.is_active ? 'ACTIVO' : 'SUSPENDIDO';
    $('s-to').textContent = target.is_active ? 'SUSPENDIDO' : 'ACTIVO';
    $('admin-modal-view').classList.add('hidden');
    $('admin-status-confirm').classList.remove('hidden');
  }

  function cancelStatusChange() { showView(); }

  async function confirmStatusChange() {
    if (!target) return;
    const btn = $('admin-status-confirm-btn');
    btn.disabled = true;
    btn.textContent = 'Guardando...';
    try {
      const res = await api('/admin/users/' + target.id + '/status', {
        method: 'PATCH',
        body: JSON.stringify({ is_active: !target.is_active }),
      });
      if (res.ok) {
        showToast(target.is_active ? 'Usuario suspendido' : 'Usuario reactivado', 'success');
        closeAdminModal();
        loadUsers();
        loadStats();
        return;
      }
      let msg = 'No se pudo cambiar el estado.';
      if (res.status === 403) msg = 'No tienes permisos para esta acción.';
      else if (res.status === 404) msg = 'Usuario no encontrado.';
      else if (res.status === 400) msg = 'Operación no permitida.';
      showToast(msg, 'error');
    } catch (e) {
      showToast('Error de conexión.', 'error');
    } finally {
      btn.disabled = false;
      btn.textContent = 'Confirmar';
    }
  }

  // ── Filtros y arranque ─────────────────────────────────────
  let searchTimer = null;
  function onFilterChange() { page = 1; loadUsers(); }

  function bindEvents() {
    $('admin-search').addEventListener('input', function () {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(onFilterChange, 350);
    });
    $('admin-role').addEventListener('change', onFilterChange);
    $('admin-status').addEventListener('change', onFilterChange);
    $('admin-users-body').addEventListener('click', function (ev) {
      const btn = ev.target.closest('button[data-manage]');
      if (btn) openAdminModal(btn.getAttribute('data-manage'));
    });
  }

  async function init() {
    let me;
    try {
      const res = await api('/auth/me');
      if (!res.ok) { window.location.href = '/dashboard'; return; }
      me = await res.json();
    } catch (e) {
      // 401 ya redirige a /login; en fallo de red dejamos un estado visible.
      if (e && e.message === 'unauthorized') return;
      const tbody = $('admin-users-body');
      if (tbody) tbody.innerHTML = messageRow('No se pudieron cargar los usuarios.');
      showToast('Error de conexión.', 'error');
      return;
    }

    if (!me || me.role !== 'admin') { window.location.href = '/dashboard'; return; }
    currentUser = me;
    const nav = $('nav-username');
    if (nav) nav.textContent = me.username;

    bindEvents();
    await Promise.all([loadStats(), loadUsers()]);
  }

  // Exponer en window los handlers usados por los onclick inline de
  // admin_users.html: las funciones viven dentro de esta IIFE y, sin esto,
  // no son globales (los onclick no las encontrarían).
  window.closeAdminModal = closeAdminModal;
  window.requestRoleChange = requestRoleChange;
  window.cancelRoleChange = cancelRoleChange;
  window.confirmRoleChange = confirmRoleChange;
  window.requestStatusChange = requestStatusChange;
  window.cancelStatusChange = cancelStatusChange;
  window.confirmStatusChange = confirmStatusChange;

  document.addEventListener('DOMContentLoaded', init);
})();
