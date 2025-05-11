import { ERROR_MESSAGES } from './config.js';

// Helpers & State
const token = localStorage.getItem('token');

export function getToken() {
    return token;       
}


export function getAuthHeaders() {
    return {
        Accept: 'application/json',
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`
    };
}

export async function handleResponse(response) {
    if (!response.ok) {
        // Xử lý các mã lỗi khác nhau
        if (response.status === 401) {
            // Unauthorized
            throw new Error('Unauthorized');
        } else if (response.status === 403) {
            // Forbidden
            throw new Error('Forbidden');
        } else {
            // Các lỗi khác
            const errorText = await response.text();
            throw new Error(`Request failed with status ${response.status}: ${errorText}`);
        }
    }

    // Kiểm tra xem response có body không
    const text = await response.text();
    if (text) {
        // Nếu có body, parse JSON
        try {
            return JSON.parse(text);
        } catch (error) {
            console.error('Error parsing JSON:', error);
            throw new Error('Invalid JSON response');
        }
    } else {
        // Nếu không có body, trả về null hoặc một giá trị mặc định
        return null;
    }
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

// Show toast message
export function showToast(message, type = 'info') {
    // Tạo một div toast và thêm vào DOM, tuỳ chỉnh giao diện theo type
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerText = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
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

