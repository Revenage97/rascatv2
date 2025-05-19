// Main JavaScript for Stock Management Dashboard

// Get CSRF token for AJAX requests
let csrfToken = '';
document.addEventListener('DOMContentLoaded', function() {
    // Initialize CSRF token
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    
    if (metaTag) {
        csrfToken = metaTag.getAttribute('content');
    } else if (csrfInput) {
        csrfToken = csrfInput.value;
    } else {
        console.error('CSRF token not found in page!');
    }
    // Toggle sidebar on mobile
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            document.querySelector('.sidebar').classList.toggle('show');
        });
    }

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const closeButton = alert.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            }
        }, 5000);
    });

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Format currency inputs
    const currencyInputs = document.querySelectorAll('.currency-input');
    currencyInputs.forEach(function(input) {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/[^\d]/g, '');
            if (value) {
                value = parseInt(value, 10).toLocaleString('id-ID');
                e.target.value = value;
            }
        });
    });

    // Handle minimum stock changes
    const minStockInputs = document.querySelectorAll('.min-stock-input');
    minStockInputs.forEach(function(input) {
        input.addEventListener('change', function(e) {
            const itemId = e.target.getAttribute('data-item-id');
            const saveButton = document.querySelector(`.save-min-stock[data-item-id="${itemId}"]`);
            if (saveButton) {
                saveButton.classList.add('btn-primary');
                saveButton.classList.remove('btn-outline-secondary');
            }
        });
    });

    // Check for items below minimum stock
    function checkLowStock() {
        const rows = document.querySelectorAll('tbody tr');
        let lowStockCount = 0;
        
        rows.forEach(function(row) {
            const currentStock = parseInt(row.querySelector('td:nth-child(5)').textContent, 10);
            const minStock = parseInt(row.querySelector('.min-stock-input').value, 10);
            
            if (currentStock < minStock) {
                row.classList.add('table-danger');
                lowStockCount++;
            } else {
                row.classList.remove('table-danger');
            }
        });
        
        // Update low stock badge if exists
        const lowStockBadge = document.getElementById('lowStockBadge');
        if (lowStockBadge && lowStockCount > 0) {
            lowStockBadge.textContent = lowStockCount;
            lowStockBadge.style.display = 'inline-block';
        } else if (lowStockBadge) {
            lowStockBadge.style.display = 'none';
        }
    }
    
    // Run on page load
    if (document.querySelector('tbody tr')) {
        checkLowStock();
    }
});
