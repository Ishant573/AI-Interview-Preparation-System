/**
 * AI Interview Preparation System - Main JavaScript
 * Handles common utilities, API helpers, and UI interactions
 */

// ============================================================
// Utility Functions
// ============================================================

const Utils = {
    /**
     * Show a loading spinner in a container
     * @param {HTMLElement} container - The container to show spinner in
     */
    showLoading(container) {
        container.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-3 text-muted">Loading...</p>
            </div>
        `;
    },

    /**
     * Show an error state in a container
     * @param {HTMLElement} container - The container to show error in
     * @param {string} message - Error message to display
     */
    showError(container, message = 'Something went wrong. Please try again.') {
        container.innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-exclamation-circle fa-4x text-danger mb-3"></i>
                <h4>Error</h4>
                <p class="text-muted">${message}</p>
                <button class="btn btn-primary" onclick="location.reload()">
                    <i class="fas fa-redo me-2"></i>Retry
                </button>
            </div>
        `;
    },

    /**
     * Show an empty state in a container
     * @param {HTMLElement} container - The container to show empty state in
     * @param {string} message - Message to display
     * @param {string} action - Action button text
     * @param {string} actionLink - Action button link
     */
    showEmpty(container, message, action = null, actionLink = null) {
        const actionHtml = action && actionLink 
            ? `<a href="${actionLink}" class="btn btn-primary mt-3">${action}</a>`
            : '';
        
        container.innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-inbox fa-4x text-muted mb-3"></i>
                <h4>No Data</h4>
                <p class="text-muted">${message}</p>
                ${actionHtml}
            </div>
        `;
    },

    /**
     * Format a date string to readable format
     * @param {string} dateStr - ISO date string
     * @returns {string} Formatted date
     */
    formatDate(dateStr) {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    /**
     * Truncate text to a specified length
     * @param {string} text - Text to truncate
     * @param {number} maxLength - Maximum length
     * @returns {string} Truncated text
     */
    truncateText(text, maxLength = 100) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    },

    /**
     * Get score color based on value
     * @param {number} score - Score value (0-10)
     * @returns {string} CSS color class
     */
    getScoreColor(score) {
        if (score >= 7) return 'high';
        if (score >= 5) return 'mid';
        return 'low';
    },

    /**
     * Debounce function for performance
     * @param {Function} func - Function to debounce
     * @param {number} wait - Wait time in milliseconds
     * @returns {Function} Debounced function
     */
    debounce(func, wait = 300) {
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

// ============================================================
// API Helper Functions
// ============================================================

const API = {
    /**
     * Make a GET request to the API
     * @param {string} endpoint - API endpoint
     * @returns {Promise} Response data
     */
    async get(endpoint) {
        try {
            const response = await fetch(endpoint);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }
            return data;
        } catch (error) {
            console.error(`API GET ${endpoint} failed:`, error);
            throw error;
        }
    },

    /**
     * Make a POST request to the API
     * @param {string} endpoint - API endpoint
     * @param {object} body - Request body
     * @returns {Promise} Response data
     */
    async post(endpoint, body = {}) {
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(body)
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }
            return data;
        } catch (error) {
            console.error(`API POST ${endpoint} failed:`, error);
            throw error;
        }
    },

    /**
     * Upload a file to the API
     * @param {string} endpoint - API endpoint
     * @param {FormData} formData - Form data with file
     * @param {Function} onProgress - Progress callback
     * @returns {Promise} Response data
     */
    async uploadFile(endpoint, formData, onProgress = null) {
        try {
            const xhr = new XMLHttpRequest();
            
            return new Promise((resolve, reject) => {
                xhr.upload.addEventListener('progress', (e) => {
                    if (onProgress && e.lengthComputable) {
                        const percent = (e.loaded / e.total) * 100;
                        onProgress(percent);
                    }
                });
                
                xhr.addEventListener('load', () => {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        try {
                            const data = JSON.parse(xhr.responseText);
                            if (data.error) {
                                reject(new Error(data.error));
                            } else {
                                resolve(data);
                            }
                        } catch (e) {
                            reject(new Error('Invalid response from server'));
                        }
                    } else {
                        try {
                            const errorData = JSON.parse(xhr.responseText);
                            reject(new Error(errorData.error || 'Upload failed'));
                        } catch (e) {
                            reject(new Error('Upload failed'));
                        }
                    }
                });
                
                xhr.addEventListener('error', () => {
                    reject(new Error('Network error during upload'));
                });
                
                xhr.open('POST', endpoint, true);
                xhr.send(formData);
            });
        } catch (error) {
            console.error(`API Upload ${endpoint} failed:`, error);
            throw error;
        }
    }
};

// ============================================================
// UI Enhancement Functions
// ============================================================

/**
 * Initialize tooltips
 */
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (el) {
        return new bootstrap.Tooltip(el);
    });
}

/**
 * Initialize popovers
 */
function initPopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (el) {
        return new bootstrap.Popover(el);
    });
}

/**
 * Smooth scroll to element
 * @param {string} elementId - Element ID to scroll to
 */
function smoothScrollTo(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}

/**
 * Show a toast notification
 * @param {string} message - Toast message
 * @param {string} type - Toast type (success, error, warning, info)
 */
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'} me-2"></i>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast, { autohide: true, delay: 3000 });
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

/**
 * Create toast container if it doesn't exist
 * @returns {HTMLElement} Toast container
 */
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

// ============================================================
// Animation Functions
// ============================================================

/**
 * Animate a number from 0 to target value
 * @param {HTMLElement} element - Element to update
 * @param {number} target - Target value
 * @param {number} duration - Animation duration in ms
 * @param {string} suffix - Suffix to append (e.g., '%')
 */
function animateNumber(element, target, duration = 1000, suffix = '') {
    const start = 0;
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Ease out cubic
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = Math.round(start + (target - start) * eased);
        
        element.textContent = current + suffix;
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

/**
 * Create a typing effect on an element
 * @param {HTMLElement} element - Element to type text into
 * @param {string} text - Text to type
 * @param {number} speed - Typing speed in ms per character
 */
function typeEffect(element, text, speed = 50) {
    let index = 0;
    element.textContent = '';
    
    function type() {
        if (index < text.length) {
            element.textContent += text.charAt(index);
            index++;
            setTimeout(type, speed);
        }
    }
    
    type();
}

// ============================================================
// Event Listeners
// ============================================================

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap components
    initTooltips();
    initPopovers();
    
    // Auto-dismiss alerts
    document.querySelectorAll('.alert-dismissible').forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // Add smooth scrolling to all anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            }
        });
    });
});

// ============================================================
// Export for use in other scripts
// ============================================================

// Make utilities globally available
window.Utils = Utils;
window.API = API;
window.showToast = showToast;
window.animateNumber = animateNumber;
window.smoothScrollTo = smoothScrollTo;
