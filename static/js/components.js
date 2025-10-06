// Reusable UI Components

class UIComponents {
    constructor() {
        this.init();
    }
    
    init() {
        this.setupGlobalEventListeners();
        this.initializeComponents();
    }
    
    setupGlobalEventListeners() {
        // Handle all dropdown toggles
        document.addEventListener('click', (e) => {
            if (e.target.matches('.dropdown-toggle')) {
                e.stopPropagation();
                this.toggleDropdown(e.target.closest('.dropdown'));
            } else {
                this.closeAllDropdowns();
            }
        });
        
        // Handle tab switching
        document.addEventListener('click', (e) => {
            if (e.target.matches('.tab-link')) {
                e.preventDefault();
                this.switchTab(e.target);
            }
        });
        
        // Handle form validation
        document.addEventListener('submit', (e) => {
            if (e.target.matches('.needs-validation')) {
                if (!this.validateForm(e.target)) {
                    e.preventDefault();
                    e.stopPropagation();
                }
            }
        });
        
        // Handle tooltips
        document.addEventListener('mouseenter', (e) => {
            if (e.target.hasAttribute('title') && !e.target.hasAttribute('data-tooltip-shown')) {
                this.showTooltip(e.target);
            }
        });
        
        document.addEventListener('mouseleave', (e) => {
            if (e.target.hasAttribute('data-tooltip-shown')) {
                this.hideTooltip(e.target);
            }
        });
    }
    
    initializeComponents() {
        this.initializeProgressBars();
        this.initializeCounters();
        this.initializeCharts();
    }
    
    // Dropdown Component
    toggleDropdown(dropdown) {
        const isActive = dropdown.classList.contains('active');
        this.closeAllDropdowns();
        
        if (!isActive) {
            dropdown.classList.add('active');
        }
    }
    
    closeAllDropdowns() {
        document.querySelectorAll('.dropdown.active').forEach(dropdown => {
            dropdown.classList.remove('active');
        });
    }
    
    // Tab Component
    switchTab(tabLink) {
        const tabContainer = tabLink.closest('.tabs');
        const targetId = tabLink.getAttribute('href').substring(1);
        
        // Remove active class from all tabs and contents
        tabContainer.querySelectorAll('.tab-link').forEach(link => {
            link.classList.remove('active');
        });
        
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        
        // Add active class to clicked tab and target content
        tabLink.classList.add('active');
        const targetContent = document.getElementById(targetId);
        if (targetContent) {
            targetContent.classList.add('active');
        }
    }
    
    // Modal Component
    createModal(options) {
        const {
            id,
            title,
            content,
            size = '',
            buttons = [],
            closable = true
        } = options;
        
        const modal = document.createElement('div');
        modal.id = id;
        modal.className = 'modal';
        
        modal.innerHTML = `
            <div class="modal-dialog ${size}">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3 class="modal-title">${title}</h3>
                        ${closable ? '<button class="modal-close"><i class="fas fa-times"></i></button>' : ''}
                    </div>
                    <div class="modal-body">
                        ${content}
                    </div>
                    ${buttons.length > 0 ? `
                        <div class="modal-footer">
                            ${buttons.map(btn => `
                                <button class="btn ${btn.class || 'btn-secondary'}" 
                                        onclick="${btn.onclick || ''}"
                                        ${btn.attributes || ''}>
                                    ${btn.icon ? `<i class="${btn.icon}"></i>` : ''} 
                                    ${btn.text}
                                </button>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Setup close handlers
        if (closable) {
            modal.querySelector('.modal-close').addEventListener('click', () => {
                this.closeModal(id);
            });
            
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal(id);
                }
            });
        }
        
        return modal;
    }
    
    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    }
    
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
    }
    
    // Toast Component
    showToast(message, type = 'info', options = {}) {
        const {
            title = '',
            duration = 5000,
            position = 'top-right',
            closable = true
        } = options;
        
        const container = this.getToastContainer(position);
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        toast.innerHTML = `
            <div class="toast-icon">
                <i class="fas ${this.getToastIcon(type)}"></i>
            </div>
            <div class="toast-content">
                ${title ? `<div class="toast-title">${title}</div>` : ''}
                <div class="toast-message">${message}</div>
            </div>
            ${closable ? '<button class="toast-close"><i class="fas fa-times"></i></button>' : ''}
        `;
        
        container.appendChild(toast);
        
        // Show animation
        setTimeout(() => toast.classList.add('show'), 100);
        
        // Auto remove
        if (duration > 0) {
            setTimeout(() => this.removeToast(toast), duration);
        }
        
        // Manual close
        if (closable) {
            toast.querySelector('.toast-close').addEventListener('click', () => {
                this.removeToast(toast);
            });
        }
        
        return toast;
    }
    
    removeToast(toast) {
        toast.classList.remove('show');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }
    
    getToastContainer(position) {
        let container = document.querySelector(`.toast-container.${position}`);
        
        if (!container) {
            container = document.createElement('div');
            container.className = `toast-container ${position}`;
            document.body.appendChild(container);
        }
        
        return container;
    }
    
    getToastIcon(type) {
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };
        return icons[type] || 'fa-info-circle';
    }
    
    // Progress Bar Component
    initializeProgressBars() {
        document.querySelectorAll('.progress-bar[data-value]').forEach(bar => {
            const value = parseInt(bar.dataset.value);
            const duration = parseInt(bar.dataset.duration) || 1000;
            
            this.animateProgressBar(bar, value, duration);
        });
    }
    
    animateProgressBar(bar, targetValue, duration) {
        let currentValue = 0;
        const increment = targetValue / (duration / 16); // 60fps
        
        const animate = () => {
            currentValue += increment;
            if (currentValue >= targetValue) {
                currentValue = targetValue;
            }
            
            bar.style.width = `${currentValue}%`;
            
            if (currentValue < targetValue) {
                requestAnimationFrame(animate);
            }
        };
        
        animate();
    }
    
    // Counter Component
    initializeCounters() {
        document.querySelectorAll('.counter[data-target]').forEach(counter => {
            const target = parseInt(counter.dataset.target);
            const duration = parseInt(counter.dataset.duration) || 2000;
            
            this.animateCounter(counter, target, duration);
        });
    }
    
    animateCounter(element, target, duration) {
        let current = 0;
        const increment = target / (duration / 16); // 60fps
        
        const animate = () => {
            current += increment;
            if (current >= target) {
                current = target;
            }
            
            element.textContent = Math.floor(current);
            
            if (current < target) {
                requestAnimationFrame(animate);
            }
        };
        
        animate();
    }
    
    // Chart Component (using Chart.js)
    initializeCharts() {
        document.querySelectorAll('.chart-container[data-chart]').forEach(container => {
            const chartData = JSON.parse(container.dataset.chart);
            this.createChart(container, chartData);
        });
    }
    
    createChart(container, config) {
        const canvas = container.querySelector('canvas');
        if (!canvas || !window.Chart) return;
        
        const ctx = canvas.getContext('2d');
        return new Chart(ctx, config);
    }
    
    // Form Validation Component
    validateForm(form) {
        let isValid = true;
        const inputs = form.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            if (!this.validateInput(input)) {
                isValid = false;
            }
        });
        
        return isValid;
    }
    
    validateInput(input) {
        const value = input.value.trim();
        const type = input.type;
        const required = input.hasAttribute('required');
        let isValid = true;
        let errorMessage = '';
        
        // Clear previous errors
        this.clearInputError(input);
        
        // Required validation
        if (required && !value) {
            isValid = false;
            errorMessage = 'This field is required';
        }
        
        // Type-specific validation
        if (value && !isValid) {
            switch (type) {
                case 'email':
                    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
                        isValid = false;
                        errorMessage = 'Please enter a valid email address';
                    }
                    break;
                    
                case 'tel':
                    if (!/^\+?[\d\s\-\(\)]+$/.test(value)) {
                        isValid = false;
                        errorMessage = 'Please enter a valid phone number';
                    }
                    break;
                    
                case 'url':
                    if (!/^https?:\/\/.+/.test(value)) {
                        isValid = false;
                        errorMessage = 'Please enter a valid URL';
                    }
                    break;
                    
                case 'number':
                    const min = input.getAttribute('min');
                    const max = input.getAttribute('max');
                    const numValue = parseFloat(value);
                    
                    if (isNaN(numValue)) {
                        isValid = false;
                        errorMessage = 'Please enter a valid number';
                    } else if (min && numValue < parseFloat(min)) {
                        isValid = false;
                        errorMessage = `Value must be at least ${min}`;
                    } else if (max && numValue > parseFloat(max)) {
                        isValid = false;
                        errorMessage = `Value must be at most ${max}`;
                    }
                    break;
            }
        }
        
        // Custom validation patterns
        const pattern = input.getAttribute('pattern');
        if (value && pattern && !new RegExp(pattern).test(value)) {
            isValid = false;
            errorMessage = input.getAttribute('data-pattern-message') || 'Invalid format';
        }
        
        // Show error if invalid
        if (!isValid) {
            this.showInputError(input, errorMessage);
        }
        
        return isValid;
    }
    
    showInputError(input, message) {
        input.classList.add('is-invalid');
        
        let errorElement = input.parentNode.querySelector('.invalid-feedback');
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.className = 'invalid-feedback';
            input.parentNode.appendChild(errorElement);
        }
        
        errorElement.textContent = message;
    }
    
    clearInputError(input) {
        input.classList.remove('is-invalid');
        const errorElement = input.parentNode.querySelector('.invalid-feedback');
        if (errorElement) {
            errorElement.remove();
        }
    }
    
    // Tooltip Component
    showTooltip(element) {
        const text = element.getAttribute('title');
        element.removeAttribute('title');
        element.setAttribute('data-original-title', text);
        element.setAttribute('data-tooltip-shown', 'true');
        
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.textContent = text;
        
        document.body.appendChild(tooltip);
        
        const rect = element.getBoundingClientRect();
        const tooltipRect = tooltip.getBoundingClientRect();
        
        tooltip.style.left = `${rect.left + (rect.width - tooltipRect.width) / 2}px`;
        tooltip.style.top = `${rect.top - tooltipRect.height - 8}px`;
        
        element.tooltipElement = tooltip;
        
        setTimeout(() => tooltip.classList.add('show'), 10);
    }
    
    hideTooltip(element) {
        const tooltip = element.tooltipElement;
        if (tooltip) {
            tooltip.classList.remove('show');
            setTimeout(() => {
                if (tooltip.parentNode) {
                    tooltip.parentNode.removeChild(tooltip);
                }
            }, 200);
        }
        
        const originalTitle = element.getAttribute('data-original-title');
        if (originalTitle) {
            element.setAttribute('title', originalTitle);
            element.removeAttribute('data-original-title');
        }
        element.removeAttribute('data-tooltip-shown');
        delete element.tooltipElement;
    }
    
    // Loading Component
    showLoading(target, message = 'Loading...') {
        const loading = document.createElement('div');
        loading.className = 'loading-overlay';
        loading.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner"></div>
                <p>${message}</p>
            </div>
        `;
        
        if (target === 'body' || !target) {
            document.body.appendChild(loading);
        } else {
            const targetElement = typeof target === 'string' ? document.querySelector(target) : target;
            targetElement.style.position = 'relative';
            targetElement.appendChild(loading);
        }
        
        setTimeout(() => loading.classList.add('active'), 10);
        
        return loading;
    }
    
    hideLoading(loadingElement) {
        if (loadingElement) {
            loadingElement.classList.remove('active');
            setTimeout(() => {
                if (loadingElement.parentNode) {
                    loadingElement.parentNode.removeChild(loadingElement);
                }
            }, 300);
        }
    }
    
    // Confirmation Dialog
    showConfirmDialog(options) {
        const {
            title = 'Confirm Action',
            message = 'Are you sure?',
            confirmText = 'Confirm',
            cancelText = 'Cancel',
            type = 'warning'
        } = options;
        
        return new Promise((resolve) => {
            const modal = this.createModal({
                id: 'confirmDialog',
                title: title,
                content: `
                    <div class="alert alert-${type}">
                        <i class="fas fa-exclamation-triangle"></i>
                        ${message}
                    </div>
                `,
                buttons: [
                    {
                        text: cancelText,
                        class: 'btn-secondary',
                        onclick: () => {
                            this.closeModal('confirmDialog');
                            resolve(false);
                        }
                    },
                    {
                        text: confirmText,
                        class: `btn-${type === 'danger' ? 'danger' : 'primary'}`,
                        onclick: () => {
                            this.closeModal('confirmDialog');
                            resolve(true);
                        }
                    }
                ]
            });
            
            this.showModal('confirmDialog');
        });
    }
    
    // Utility Methods
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
    }
    
    formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }
    
    copyToClipboard(text) {
        if (navigator.clipboard) {
            return navigator.clipboard.writeText(text);
        } else {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            return Promise.resolve();
        }
    }
    
    downloadFile(url, filename) {
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
    
    // Animation helpers
    fadeIn(element, duration = 300) {
        element.style.opacity = '0';
        element.style.display = 'block';
        
        let start = null;
        const animate = (timestamp) => {
            if (!start) start = timestamp;
            const progress = timestamp - start;
            
            element.style.opacity = Math.min(progress / duration, 1);
            
            if (progress < duration) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }
    
    fadeOut(element, duration = 300) {
        let start = null;
        const animate = (timestamp) => {
            if (!start) start = timestamp;
            const progress = timestamp - start;
            
            element.style.opacity = Math.max(1 - (progress / duration), 0);
            
            if (progress < duration) {
                requestAnimationFrame(animate);
            } else {
                element.style.display = 'none';
            }
        };
        
        requestAnimationFrame(animate);
    }
    
    slideUp(element, duration = 300) {
        element.style.transitionProperty = 'height, margin, padding';
        element.style.transitionDuration = duration + 'ms';
        element.style.boxSizing = 'border-box';
        element.style.height = element.offsetHeight + 'px';
        element.offsetHeight;
        element.style.overflow = 'hidden';
        element.style.height = 0;
        element.style.paddingTop = 0;
        element.style.paddingBottom = 0;
        element.style.marginTop = 0;
        element.style.marginBottom = 0;
        
        setTimeout(() => {
            element.style.display = 'none';
            element.style.removeProperty('height');
            element.style.removeProperty('padding-top');
            element.style.removeProperty('padding-bottom');
            element.style.removeProperty('margin-top');
            element.style.removeProperty('margin-bottom');
            element.style.removeProperty('overflow');
            element.style.removeProperty('transition-duration');
            element.style.removeProperty('transition-property');
        }, duration);
    }
    
    slideDown(element, duration = 300) {
        element.style.removeProperty('display');
        let display = window.getComputedStyle(element).display;
        if (display === 'none') display = 'block';
        element.style.display = display;
        
        const height = element.offsetHeight;
        element.style.overflow = 'hidden';
        element.style.height = 0;
        element.style.paddingTop = 0;
        element.style.paddingBottom = 0;
        element.style.marginTop = 0;
        element.style.marginBottom = 0;
        element.offsetHeight;
        element.style.boxSizing = 'border-box';
        element.style.transitionProperty = 'height, margin, padding';
        element.style.transitionDuration = duration + 'ms';
        element.style.height = height + 'px';
        element.style.removeProperty('padding-top');
        element.style.removeProperty('padding-bottom');
        element.style.removeProperty('margin-top');
        element.style.removeProperty('margin-bottom');
        
        setTimeout(() => {
            element.style.removeProperty('height');
            element.style.removeProperty('overflow');
            element.style.removeProperty('transition-duration');
            element.style.removeProperty('transition-property');
        }, duration);
    }
}

// Initialize UI Components
document.addEventListener('DOMContentLoaded', () => {
    window.uiComponents = new UIComponents();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UIComponents;
}
