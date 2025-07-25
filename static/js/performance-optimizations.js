/**
 * CIHRPT Performance Optimizations
 * Comprehensive frontend performance enhancements
 */

// Performance monitoring
const performanceObserver = {
    metrics: {},
    
    init() {
        this.measurePageLoad();
        this.observeResourceLoading();
        this.setupIntersectionObserver();
        this.preloadCriticalResources();
        this.optimizeImages();
        this.setupServiceWorker();
    },
    
    measurePageLoad() {
        // Measure core web vitals
        if ('PerformanceObserver' in window) {
            // Largest Contentful Paint
            const lcpObserver = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                const lastEntry = entries[entries.length - 1];
                this.metrics.lcp = lastEntry.startTime;
                console.log('LCP:', lastEntry.startTime);
            });
            lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
            
            // First Input Delay
            const fidObserver = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                entries.forEach((entry) => {
                    this.metrics.fid = entry.processingStart - entry.startTime;
                    console.log('FID:', this.metrics.fid);
                });
            });
            fidObserver.observe({ entryTypes: ['first-input'] });
            
            // Cumulative Layout Shift
            let clsScore = 0;
            const clsObserver = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                entries.forEach((entry) => {
                    if (!entry.hadRecentInput) {
                        clsScore += entry.value;
                    }
                });
                this.metrics.cls = clsScore;
                console.log('CLS:', clsScore);
            });
            clsObserver.observe({ entryTypes: ['layout-shift'] });
        }
        
        // Traditional timing metrics
        window.addEventListener('load', () => {
            setTimeout(() => {
                const perfData = performance.getEntriesByType('navigation')[0];
                this.metrics.loadTime = perfData.loadEventEnd - perfData.fetchStart;
                this.metrics.domContentLoaded = perfData.domContentLoadedEventEnd - perfData.fetchStart;
                console.log('Page Load Time:', this.metrics.loadTime + 'ms');
                console.log('DOM Content Loaded:', this.metrics.domContentLoaded + 'ms');
            }, 0);
        });
    },
    
    observeResourceLoading() {
        // Monitor resource loading performance
        if ('PerformanceObserver' in window) {
            const resourceObserver = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                entries.forEach((entry) => {
                    if (entry.duration > 1000) { // Resources taking more than 1s
                        console.warn('Slow resource:', entry.name, entry.duration + 'ms');
                    }
                });
            });
            resourceObserver.observe({ entryTypes: ['resource'] });
        }
    },
    
    setupIntersectionObserver() {
        // Lazy loading for non-critical content
        if ('IntersectionObserver' in window) {
            const lazyObserver = new IntersectionObserver((entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        const target = entry.target;
                        
                        // Lazy load images
                        if (target.dataset.src) {
                            target.src = target.dataset.src;
                            target.removeAttribute('data-src');
                        }
                        
                        // Lazy load content sections
                        if (target.classList.contains('lazy-content')) {
                            target.classList.add('loaded');
                            this.loadContent(target);
                        }
                        
                        lazyObserver.unobserve(target);
                    }
                });
            }, {
                rootMargin: '50px 0px',
                threshold: 0.1
            });
            
            // Observe lazy load candidates
            document.querySelectorAll('[data-src], .lazy-content').forEach((el) => {
                lazyObserver.observe(el);
            });
        }
    },
    
    preloadCriticalResources() {
        // Preload critical resources
        const criticalResources = [
            '/static/css/themes/cihrpt-theme.css',
            '/static/js/theme-toggle.js'
        ];
        
        criticalResources.forEach((resource) => {
            const link = document.createElement('link');
            link.rel = 'preload';
            link.as = resource.endsWith('.css') ? 'style' : 'script';
            link.href = resource;
            document.head.appendChild(link);
        });
    },
    
    optimizeImages() {
        // Image optimization and lazy loading
        const images = document.querySelectorAll('img');
        
        images.forEach((img) => {
            // Add loading="lazy" to images below the fold
            if (!img.hasAttribute('loading')) {
                const rect = img.getBoundingClientRect();
                if (rect.top > window.innerHeight) {
                    img.loading = 'lazy';
                }
            }
            
            // Optimize image loading
            img.addEventListener('load', () => {
                img.classList.add('loaded');
            });
            
            img.addEventListener('error', () => {
                img.classList.add('error');
                console.warn('Failed to load image:', img.src);
            });
        });
    },
    
    setupServiceWorker() {
        // Register service worker for caching
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/static/js/sw.js')
                    .then((registration) => {
                        console.log('SW registered: ', registration);
                    })
                    .catch((registrationError) => {
                        console.log('SW registration failed: ', registrationError);
                    });
            });
        }
    },
    
    loadContent(element) {
        // Dynamic content loading for below-the-fold sections
        const contentType = element.dataset.contentType;
        
        if (contentType === 'statistics') {
            this.loadStatistics(element);
        } else if (contentType === 'charts') {
            this.loadCharts(element);
        }
    },
    
    loadStatistics(element) {
        // Load statistics data asynchronously
        fetch('/api/statistics/')
            .then(response => response.json())
            .then(data => {
                this.renderStatistics(element, data);
            })
            .catch(error => {
                console.error('Failed to load statistics:', error);
            });
    },
    
    loadCharts(element) {
        // Load Chart.js only when needed
        if (!window.Chart) {
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
            script.onload = () => {
                this.initializeCharts(element);
            };
            document.head.appendChild(script);
        } else {
            this.initializeCharts(element);
        }
    },
    
    initializeCharts(element) {
        // Initialize charts with performance optimizations
        const chartElements = element.querySelectorAll('canvas[data-chart]');
        
        chartElements.forEach((canvas) => {
            const chartType = canvas.dataset.chart;
            const chartData = JSON.parse(canvas.dataset.chartData || '{}');
            
            new Chart(canvas, {
                type: chartType,
                data: chartData,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: {
                        duration: 0 // Disable animations for better performance
                    },
                    plugins: {
                        legend: {
                            display: true
                        }
                    }
                }
            });
        });
    },
    
    renderStatistics(element, data) {
        // Render statistics with minimal DOM manipulation
        const template = element.querySelector('template');
        if (template) {
            const content = template.content.cloneNode(true);
            
            // Update placeholders with actual data
            content.querySelectorAll('[data-stat]').forEach((statElement) => {
                const statKey = statElement.dataset.stat;
                if (data[statKey]) {
                    statElement.textContent = data[statKey];
                }
            });
            
            element.appendChild(content);
        }
    }
};

// Cache management
const cacheManager = {
    prefix: 'cihrpt_',
    ttl: 5 * 60 * 1000, // 5 minutes
    
    set(key, data, customTtl = null) {
        const item = {
            data: data,
            timestamp: Date.now(),
            ttl: customTtl || this.ttl
        };
        
        try {
            localStorage.setItem(this.prefix + key, JSON.stringify(item));
        } catch (e) {
            console.warn('LocalStorage quota exceeded, clearing old data');
            this.cleanup();
        }
    },
    
    get(key) {
        try {
            const item = JSON.parse(localStorage.getItem(this.prefix + key));
            if (!item) return null;
            
            if (Date.now() - item.timestamp > item.ttl) {
                this.remove(key);
                return null;
            }
            
            return item.data;
        } catch (e) {
            this.remove(key);
            return null;
        }
    },
    
    remove(key) {
        localStorage.removeItem(this.prefix + key);
    },
    
    cleanup() {
        // Remove expired items
        const keysToRemove = [];
        
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && key.startsWith(this.prefix)) {
                try {
                    const item = JSON.parse(localStorage.getItem(key));
                    if (Date.now() - item.timestamp > item.ttl) {
                        keysToRemove.push(key);
                    }
                } catch (e) {
                    keysToRemove.push(key);
                }
            }
        }
        
        keysToRemove.forEach(key => localStorage.removeItem(key));
    }
};

// Network optimizations
const networkOptimizer = {
    init() {
        this.setupConnectionAware();
        this.prefetchLinks();
        this.optimizeRequests();
    },
    
    setupConnectionAware() {
        // Adjust behavior based on connection quality
        if ('connection' in navigator) {
            const connection = navigator.connection;
            
            if (connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g') {
                // Disable non-essential features on slow connections
                document.body.classList.add('slow-connection');
                this.disableAnimations();
            }
            
            connection.addEventListener('change', () => {
                this.adjustForConnection();
            });
        }
    },
    
    disableAnimations() {
        const style = document.createElement('style');
        style.textContent = `
            *, *::before, *::after {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
                scroll-behavior: auto !important;
            }
        `;
        document.head.appendChild(style);
    },
    
    prefetchLinks() {
        // Prefetch likely navigation targets
        const importantLinks = document.querySelectorAll('a[href*="/projects/"], a[href*="/statistics/"]');
        
        const prefetchObserver = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    const link = entry.target;
                    const prefetchLink = document.createElement('link');
                    prefetchLink.rel = 'prefetch';
                    prefetchLink.href = link.href;
                    document.head.appendChild(prefetchLink);
                    
                    prefetchObserver.unobserve(link);
                }
            });
        });
        
        importantLinks.forEach(link => prefetchObserver.observe(link));
    },
    
    optimizeRequests() {
        // Request deduplication and batching
        this.requestQueue = new Map();
        this.originalFetch = window.fetch;
        
        window.fetch = (url, options = {}) => {
            const key = `${url}_${JSON.stringify(options)}`;
            
            if (this.requestQueue.has(key)) {
                return this.requestQueue.get(key);
            }
            
            const promise = this.originalFetch(url, options)
                .finally(() => {
                    this.requestQueue.delete(key);
                });
            
            this.requestQueue.set(key, promise);
            return promise;
        };
    },
    
    adjustForConnection() {
        const connection = navigator.connection;
        
        if (connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g') {
            // Reduce image quality, disable animations
            document.body.classList.add('slow-connection');
        } else {
            document.body.classList.remove('slow-connection');
        }
    }
};

// DOM optimization
const domOptimizer = {
    init() {
        this.virtualizeScrolling();
        this.optimizeFormInputs();
        this.setupEventDelegation();
    },
    
    virtualizeScrolling() {
        // Virtual scrolling for large lists
        const largeLists = document.querySelectorAll('.project-list tbody');
        
        largeLists.forEach((list) => {
            if (list.children.length > 50) {
                this.setupVirtualScrolling(list);
            }
        });
    },
    
    setupVirtualScrolling(list) {
        const itemHeight = 60; // Approximate row height
        const visibleItems = Math.ceil(window.innerHeight / itemHeight) + 5;
        const totalItems = list.children.length;
        
        let startIndex = 0;
        let endIndex = Math.min(visibleItems, totalItems);
        
        const renderVisibleItems = () => {
            Array.from(list.children).forEach((item, index) => {
                if (index >= startIndex && index < endIndex) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        };
        
        const handleScroll = () => {
            const scrollTop = window.pageYOffset;
            const newStartIndex = Math.floor(scrollTop / itemHeight);
            const newEndIndex = Math.min(newStartIndex + visibleItems, totalItems);
            
            if (newStartIndex !== startIndex || newEndIndex !== endIndex) {
                startIndex = newStartIndex;
                endIndex = newEndIndex;
                renderVisibleItems();
            }
        };
        
        window.addEventListener('scroll', this.throttle(handleScroll, 16));
        renderVisibleItems();
    },
    
    optimizeFormInputs() {
        // Debounce form inputs
        const inputs = document.querySelectorAll('input[type="search"], input[type="text"]');
        
        inputs.forEach((input) => {
            const originalHandler = input.oninput;
            
            input.oninput = this.debounce((event) => {
                if (originalHandler) {
                    originalHandler.call(input, event);
                }
            }, 300);
        });
    },
    
    setupEventDelegation() {
        // Use event delegation for better performance
        document.addEventListener('click', (event) => {
            const target = event.target;
            
            // Handle pagination clicks
            if (target.matches('.page-link')) {
                this.handlePaginationClick(event);
            }
            
            // Handle filter toggles
            if (target.matches('.filter-toggle')) {
                this.handleFilterToggle(event);
            }
        });
    },
    
    handlePaginationClick(event) {
        // Smooth pagination with loading states
        event.preventDefault();
        const link = event.target.closest('a');
        
        if (link && link.href) {
            document.body.classList.add('loading');
            window.location.href = link.href;
        }
    },
    
    handleFilterToggle(event) {
        // Optimized filter toggling
        const filter = event.target;
        filter.classList.toggle('active');
        
        // Update URL without page reload
        const url = new URL(window.location);
        const filterValue = filter.dataset.filter;
        
        if (filter.classList.contains('active')) {
            url.searchParams.set(filter.dataset.filterType, filterValue);
        } else {
            url.searchParams.delete(filter.dataset.filterType);
        }
        
        window.history.pushState({}, '', url);
    },
    
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};

// Initialize all optimizations
document.addEventListener('DOMContentLoaded', () => {
    performanceObserver.init();
    networkOptimizer.init();
    domOptimizer.init();
    
    // Cleanup cache on page load
    cacheManager.cleanup();
});

// Export for use in other scripts
window.CIHRPTPerformance = {
    performanceObserver,
    cacheManager,
    networkOptimizer,
    domOptimizer
}; 