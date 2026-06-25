function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/';
}

// Función global para verificar token
async function checkAuth() {
    const token = localStorage.getItem('access_token');
    if (!token) return null;

    const res = await fetch('/api/v1/auth/me', {
        headers: {'Authorization': `Bearer ${token}`}
    });

    if (res.status === 401) {
        // Token inválido o expirado — limpiar y no redirigir en bucle
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        return null;
    }

    return res.ok ? res.json() : null;
}