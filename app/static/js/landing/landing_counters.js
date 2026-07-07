export function init() {
    const counters = document.querySelectorAll('[data-counter]');
    counters.forEach(el => {
        const target = parseInt(el.dataset.counter, 10);
        if (isNaN(target)) return;
        animate(el, target);
    });
}

function animate(el, target) {
    const duration = 2000;
    const start = performance.now();

    function step(now) {
        const elapsed = now - start;
        const progress = Math.min(elapsed / duration, 1);
        // easeOutQuad
        const eased = progress * (2 - progress);
        const current = Math.round(eased * target);
        el.textContent = current.toLocaleString();

        if (progress < 1) {
            requestAnimationFrame(step);
        }
    }
    requestAnimationFrame(step);
}
