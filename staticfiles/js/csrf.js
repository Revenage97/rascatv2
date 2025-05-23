// CSRF token handling for AJAX requests

// Function to get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Function to get CSRF token from meta tag or cookie
function getCSRFToken() {
    // First try to get from cookie
    const csrftoken = getCookie('csrftoken');
    if (csrftoken) {
        return csrftoken;
    }
    
    // If not in cookie, try to get from meta tag
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (metaTag) {
        return metaTag.getAttribute('content');
    }
    
    // If not in meta tag, try to get from hidden input
    const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (csrfInput) {
        return csrfInput.value;
    }
    
    console.error('CSRF token not found!');
    return null;
}

// Setup AJAX CSRF headers for fetch and XMLHttpRequest
function setupAjaxCSRF() {
    // Add CSRF token to all fetch requests
    const originalFetch = window.fetch;
    window.fetch = function(url, options = {}) {
        // Only add CSRF token for same-origin POST, PUT, DELETE, PATCH requests
        if (options.method && ['POST', 'PUT', 'DELETE', 'PATCH'].includes(options.method.toUpperCase())) {
            const csrftoken = getCSRFToken();
            if (csrftoken) {
                if (!options.headers) {
                    options.headers = {};
                }
                // Convert headers to regular object if it's Headers instance
                if (options.headers instanceof Headers) {
                    const plainHeaders = {};
                    for (const [key, value] of options.headers.entries()) {
                        plainHeaders[key] = value;
                    }
                    options.headers = plainHeaders;
                }
                options.headers['X-CSRFToken'] = csrftoken;
            }
        }
        return originalFetch(url, options);
    };
    
    // Add CSRF token to all XMLHttpRequest
    const originalOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function() {
        const method = arguments[0];
        if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method.toUpperCase())) {
            this.addEventListener('readystatechange', function() {
                if (this.readyState === 1) { // OPENED
                    const csrftoken = getCSRFToken();
                    if (csrftoken) {
                        this.setRequestHeader('X-CSRFToken', csrftoken);
                    }
                }
            });
        }
        originalOpen.apply(this, arguments);
    };
    
    console.log('CSRF protection initialized for AJAX requests');
}

// Initialize CSRF protection when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    setupAjaxCSRF();
});
