import { init as initScroll } from './landing_scroll.js';
import { init as initScouter } from './landing_scouter.js';

export function init() {
    initScroll();
    // Small delay for DOM to be ready
    setTimeout(() => {
        initScouter();
    }, 100);
}

// Auto-init when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
