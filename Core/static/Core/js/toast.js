/**
 * Toast Notification System
 * Non-blocking alerts that auto-dismiss
 */

function showToast(message, type = 'success', duration = 5000) {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    // Icon based on type
    const icons = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ'
    };
    
    toast.innerHTML = `
        <span class="toast-icon">${icons[type]}</span>
        <span class="toast-message">${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    `;
    
    // Add to container (create if doesn't exist)
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }
    
    container.appendChild(toast);
    
    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 10);
    
    // Auto dismiss
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// Convenience functions
function showSuccess(message) {
    showToast(message, 'success');
}

function showError(message) {
    showToast(message, 'error', 8000);
}

function showWarning(message) {
    showToast(message, 'warning', 6000);
}

function showInfo(message) {
    showToast(message, 'info');
}

// Django messages integration
function showDjangoMessages() {
    const messages = document.querySelectorAll('.django-message');
    messages.forEach(msg => {
        const type = msg.dataset.type || 'info';
        const text = msg.textContent;
        showToast(text, type);
        msg.remove();
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', showDjangoMessages);
