import { ERROR_MESSAGES } from './config.js';

// Helpers & State

export function getAuthHeaders() {
    const token = localStorage.getItem('token');
    return {
        'Authorization': `Bearer ${token}`,
    };
}

export async function handleResponse(response) {
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || ERROR_MESSAGES.SERVER_ERROR);
    }
    return response.json();
}

// App State
export const appState = {
    currentUser: null,
    currentConversationId: null,
    setCurrentUser(user) { this.currentUser = user; },
    getCurrentUser() { return this.currentUser; },
    setCurrentConversationId(id) { this.currentConversationId = id; },
    getCurrentConversationId() { return this.currentConversationId; },
    clearState() { this.currentUser = null; this.currentConversationId = null; }
};

// Format date to Vietnamese locale
export function formatDate(date) {
    return new Date(date).toLocaleDateString('vi-VN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// Format datetime to Vietnamese locale
export function formatDateTime(date) {
    return new Date(date).toLocaleString('vi-VN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Show error message
export function showError(message) {
    alert(message);
}

// Show success message
export function showSuccess(message) {
    alert(message);
}

// Handle API error
export function handleError(error) {
    console.error('API Error:', error);
    if (error.message) {
        showError(error.message);
    } else {
        showError(ERROR_MESSAGES.SERVER_ERROR);
    }
}

// Validate form data
export function validateForm(formData, requiredFields) {
    const errors = [];
    requiredFields.forEach(field => {
        if (!formData.get(field)) {
            errors.push(`Vui lòng nhập ${field}`);
        }
    });
    return errors;
}

// Get user role label
export function getUserRoleLabel(role) {
    const labels = {
        'admin': 'Quản trị viên',
        'department': 'Phòng ban',
        'teacher': 'Giáo viên',
        'student': 'Học sinh',
        'parent': 'Phụ huynh'
    };
    return labels[role] || role;
}

// Check if user has permission
export function hasPermission(user, permission) {
    const permissions = {
        'admin': ['all'],
        'department': ['manage_rewards', 'view_statistics'],
        'teacher': ['view_statistics'],
        'student': ['view_personal'],
        'parent': ['view_children']
    };
    return permissions[user.role]?.includes(permission) || false;
}

// Format currency
export function formatCurrency(amount) {
    return new Intl.NumberFormat('vi-VN', {
        style: 'currency',
        currency: 'VND'
    }).format(amount);
}

// Format percentage
export function formatPercentage(value) {
    return new Intl.NumberFormat('vi-VN', {
        style: 'percent',
        minimumFractionDigits: 1,
        maximumFractionDigits: 1
    }).format(value / 100);
}

// Generate random ID
export function generateId() {
    return Math.random().toString(36).substr(2, 9);
}

// Debounce function
export function debounce(func, wait) {
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

// Throttle function
export function throttle(func, limit) {
    let inThrottle;
    return function executedFunction(...args) {
        if (!inThrottle) {
            func(...args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

