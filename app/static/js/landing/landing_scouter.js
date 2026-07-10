export function init() {
    const timeEl = document.getElementById('scouterTime');
    const powerEl = document.getElementById('powerLevel');

    // Scouter Time Counter (HH:MM:SS from system time)
    function updateScouterTime() {
        if (!timeEl) return;
        const now = new Date();
        const h = String(now.getHours()).padStart(2, '0');
        const m = String(now.getMinutes()).padStart(2, '0');
        const s = String(now.getSeconds()).padStart(2, '0');
        timeEl.textContent = `${h}:${m}:${s}`;
    }
    if (timeEl) {
        setInterval(updateScouterTime, 1000);
        updateScouterTime();
    }

    // Power Level Fluctuation
    if (powerEl) {
        const base = 8999;
        function fluctuatePower() {
            const variation = Math.floor(Math.random() * 40) - 20; // -20 to +20
            const value = base + variation;
            powerEl.textContent = value.toLocaleString();
        }
        setInterval(fluctuatePower, 2000);
    }
}
