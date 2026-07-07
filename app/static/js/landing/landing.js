import { init as initScroll } from './landing_scroll.js';
import { init as initCounters } from './landing_counters.js';
import { init as initScouter } from './landing_scouter.js';
import { init as initCharts } from './landing_charts.js';

export function init() {
    initScroll();
    // Small delay for scroll animation to set up before visible-dependent modules
    setTimeout(() => {
        initCounters();
        initScouter();
    }, 100);
    initCharts();
}

// Auto-init when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
