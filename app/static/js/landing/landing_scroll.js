export function init() {
    const sections = document.querySelectorAll('.landing-section');
    if (!sections.length) return;

    let ticking = false;
    const observer = new IntersectionObserver((entries) => {
        if (!ticking) {
            requestAnimationFrame(() => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('is-visible');
                        observer.unobserve(entry.target);
                    }
                });
                ticking = false;
            });
            ticking = true;
        }
    }, { threshold: 0.15 });

    sections.forEach(el => observer.observe(el));
}
