export function init() {
    // Scroll reveal for elements with .landing-reveal class
    const revealElements = document.querySelectorAll('.landing-reveal');
    if (revealElements.length) {
        const revealObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('active');
                }
            });
        }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });
        revealElements.forEach(el => revealObserver.observe(el));
    }

    // Navbar background on scroll
    const nav = document.querySelector('nav');
    if (nav) {
        const onScroll = () => {
            if (window.scrollY > 50) {
                nav.style.borderBottomColor = 'rgba(249,115,22,0.1)';
                nav.style.backgroundColor = 'rgba(6,6,10,0.95)';
            } else {
                nav.style.borderBottomColor = 'rgba(255,255,255,0.05)';
                nav.style.backgroundColor = 'rgba(6,6,10,0.8)';
            }
        };
        window.addEventListener('scroll', onScroll, { passive: true });
        onScroll();
    }

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
}
