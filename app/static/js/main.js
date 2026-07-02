function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/';
}

// ── Auth check ─────────────────────────────────────────────────
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

// ── Password strength checker (shared by login + reset-password) ──
function checkPasswordStrength(password) {
    const checks = {
        length:  password.length >= 12,
        upper:   /[A-Z]/.test(password),
        lower:   /[a-z]/.test(password),
        number:  /\d/.test(password),
        special: /[!@#$%^&*(),.?":{}|<>_\-]/.test(password),
    };

    Object.entries(checks).forEach(([key, met]) => {
        const el = document.getElementById(`req-${key}`);
        if (el) {
            el.className = met ? 'text-emerald-400' : 'text-red-400';
            el.textContent = (met ? '\u2713 ' : '\u2717 ') + el.textContent.slice(2);
        }
    });

    const score = Object.values(checks).filter(Boolean).length;
    const bar = document.getElementById('strength-bar');
    const label = document.getElementById('strength-label');

    if (score <= 2) {
        bar.style.width = '33%';
        bar.className = 'h-full rounded-full transition-all duration-300 bg-red-500';
        label.textContent = 'D\u00e9bil';
        label.className = 'text-red-400';
    } else if (score <= 4) {
        bar.style.width = '66%';
        bar.className = 'h-full rounded-full transition-all duration-300 bg-yellow-500';
        label.textContent = 'Media';
        label.className = 'text-yellow-400';
    } else {
        bar.style.width = '100%';
        bar.className = 'h-full rounded-full transition-all duration-300 bg-emerald-500';
        label.textContent = 'Fuerte';
        label.className = 'text-emerald-400';
    }

    return Object.values(checks).every(Boolean);
}