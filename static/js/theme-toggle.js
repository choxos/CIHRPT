/**
 * CIHRPT Dark Theme Toggle
 * Comprehensive theme management with localStorage persistence
 */

class ThemeManager {
    constructor() {
        this.currentTheme = 'light';
        this.storageKey = 'cihrpt-theme';
        this.toggleButton = null;
        
        // Initialize theme on page load
        this.init();
    }
    
    init() {
        // Get saved theme or detect system preference
        this.currentTheme = this.getSavedTheme();
        
        // Apply theme immediately (before DOM ready to prevent flash)
        this.applyTheme(this.currentTheme);
        
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupUI());
        } else {
            this.setupUI();
        }
    }
    
    getSavedTheme() {
        // Check localStorage first
        const savedTheme = localStorage.getItem(this.storageKey);
        if (savedTheme && ['light', 'dark'].includes(savedTheme)) {
            return savedTheme;
        }
        
        // Check system preference
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        
        return 'light';
    }
    
    setupUI() {
        // Create theme toggle button
        this.createToggleButton();
        
        // Listen for system theme changes
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
                // Only auto-switch if user hasn't manually set a preference
                if (!localStorage.getItem(this.storageKey)) {
                    this.setTheme(e.matches ? 'dark' : 'light');
                }
            });
        }
        
        // Update Chart.js default colors if charts exist
        this.updateChartDefaults();
    }
    
    createToggleButton() {
        // Find the navigation container
        const nav = document.querySelector('.xera-nav');
        if (!nav) return;
        
        // Create toggle button container
        const toggleContainer = document.createElement('div');
        toggleContainer.className = 'theme-toggle-container ms-auto';
        
        // Create toggle button
        this.toggleButton = document.createElement('button');
        this.toggleButton.className = 'theme-toggle';
        this.toggleButton.setAttribute('type', 'button');
        this.toggleButton.setAttribute('title', 'Toggle dark/light theme');
        this.toggleButton.innerHTML = `
            <i class="fas fa-moon" id="theme-icon"></i>
            <span id="theme-text">Dark</span>
        `;
        
        // Add click handler
        this.toggleButton.addEventListener('click', () => this.toggleTheme());
        
        // Append to container and nav
        toggleContainer.appendChild(this.toggleButton);
        nav.appendChild(toggleContainer);
        
        // Update button state
        this.updateToggleButton();
    }
    
    updateToggleButton() {
        if (!this.toggleButton) return;
        
        const icon = this.toggleButton.querySelector('#theme-icon');
        const text = this.toggleButton.querySelector('#theme-text');
        
        if (this.currentTheme === 'dark') {
            icon.className = 'fas fa-sun';
            text.textContent = 'Light';
            this.toggleButton.setAttribute('title', 'Switch to light theme');
        } else {
            icon.className = 'fas fa-moon';
            text.textContent = 'Dark';
            this.toggleButton.setAttribute('title', 'Switch to dark theme');
        }
    }
    
    applyTheme(theme) {
        // Add transitioning class to prevent flash
        document.documentElement.classList.add('theme-transitioning');
        
        // Apply theme
        document.documentElement.setAttribute('data-theme', theme);
        this.currentTheme = theme;
        
        // Update meta theme-color
        this.updateMetaThemeColor(theme);
        
        // Save to localStorage
        localStorage.setItem(this.storageKey, theme);
        
        // Remove transitioning class after a short delay
        setTimeout(() => {
            document.documentElement.classList.remove('theme-transitioning');
        }, 100);
        
        // Dispatch custom event for other components to listen to
        window.dispatchEvent(new CustomEvent('themeChanged', { 
            detail: { theme: theme } 
        }));
    }
    
    setTheme(theme) {
        if (!['light', 'dark'].includes(theme)) return;
        
        this.applyTheme(theme);
        this.updateToggleButton();
        
        // Update charts if they exist
        this.updateChartColors();
    }
    
    toggleTheme() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.setTheme(newTheme);
        
        // Add a subtle animation to the button
        this.toggleButton.style.transform = 'scale(0.95)';
        setTimeout(() => {
            this.toggleButton.style.transform = '';
        }, 150);
    }
    
    updateMetaThemeColor(theme) {
        let metaThemeColor = document.querySelector('meta[name="theme-color"]');
        
        if (!metaThemeColor) {
            metaThemeColor = document.createElement('meta');
            metaThemeColor.setAttribute('name', 'theme-color');
            document.head.appendChild(metaThemeColor);
        }
        
        // Set theme color based on current theme
        const color = theme === 'dark' ? '#0f172a' : '#ffffff';
        metaThemeColor.setAttribute('content', color);
    }
    
    updateChartDefaults() {
        // Update Chart.js defaults if Chart is available
        if (typeof Chart !== 'undefined') {
            const updateDefaults = () => {
                const isDark = this.currentTheme === 'dark';
                
                Chart.defaults.color = isDark ? '#e2e8f0' : '#4b5563';
                Chart.defaults.borderColor = isDark ? '#334155' : '#e5e7eb';
                Chart.defaults.backgroundColor = isDark ? '#1e293b' : '#ffffff';
                
                // Update grid lines
                if (Chart.defaults.scales) {
                    Chart.defaults.scales.linear.grid.color = isDark ? '#334155' : '#f3f4f6';
                    Chart.defaults.scales.category.grid.color = isDark ? '#334155' : '#f3f4f6';
                }
            };
            
            updateDefaults();
            
            // Listen for theme changes
            window.addEventListener('themeChanged', updateDefaults);
        }
    }
    
    updateChartColors() {
        // Update existing charts if Chart is available
        if (typeof Chart !== 'undefined') {
            Chart.instances.forEach(chart => {
                if (chart && chart.update) {
                    chart.update('none'); // Update without animation
                }
            });
        }
    }
    
    // Public methods
    getTheme() {
        return this.currentTheme;
    }
    
    isDark() {
        return this.currentTheme === 'dark';
    }
    
    isLight() {
        return this.currentTheme === 'light';
    }
}

// Auto-initialize theme manager
let themeManager;

// Initialize immediately to prevent flash
(function() {
    // Quick theme application before full initialization
    const savedTheme = localStorage.getItem('cihrpt-theme') || 
        (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    document.documentElement.setAttribute('data-theme', savedTheme);
})();

// Full initialization
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        themeManager = new ThemeManager();
    });
} else {
    themeManager = new ThemeManager();
}

// Export for use in other scripts
window.ThemeManager = ThemeManager;
window.themeManager = themeManager;

// Keyboard shortcut for theme toggle (Ctrl/Cmd + Shift + D)
document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'D') {
        e.preventDefault();
        if (themeManager) {
            themeManager.toggleTheme();
        }
    }
});

// Console helper for developers
console.log('🌙 CIHRPT Dark Theme loaded. Use Ctrl/Cmd+Shift+D to toggle, or access via window.themeManager'); 