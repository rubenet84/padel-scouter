export function init() {
    const powerEl = document.querySelector('.landing-power-value');
    if (!powerEl) return;

    const target = parseInt(powerEl.dataset.target, 10);
    if (isNaN(target)) return;

    const duration = 2000;
    const start = performance.now();

    function step(now) {
        const elapsed = now - start;
        const progress = Math.min(elapsed / duration, 1);
        const eased = progress * (2 - progress);
        const current = Math.round(eased * target);
        powerEl.textContent = current.toLocaleString();

        if (progress < 1) {
            requestAnimationFrame(step);
        } else {
            // Add glow-pulse class when done (CSS keyframe loops)
            powerEl.classList.add('landing-glow-active');
        }
    }
    requestAnimationFrame(step);
}
