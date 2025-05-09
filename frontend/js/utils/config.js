// API Configuration
export const API_URL = 'http://localhost:5000/api';

// Auth Header
export function getAuthHeaders() {
    const token = localStorage.getItem('token');
    return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    };
}

// Error Messages
export const ERROR_MESSAGES = {
    NETWORK_ERROR: 'Lỗi kết nối mạng',
    UNAUTHORIZED: 'Phiên đăng nhập hết hạn',
    FORBIDDEN: 'Không có quyền truy cập',
    NOT_FOUND: 'Không tìm thấy dữ liệu',
    SERVER_ERROR: 'Lỗi máy chủ',
    VALIDATION_ERROR: 'Dữ liệu không hợp lệ'
};

// Content Types
export const CONTENT_TYPES = {
    REWARD: {
        ACHIEVEMENT: 'achievement',
        EXCELLENCE: 'excellence',
        IMPROVEMENT: 'improvement',
        OTHER: 'other'
    },
    DISCIPLINE: {
        VIOLATION: 'violation',
        MISCONDUCT: 'misconduct',
        ATTENDANCE: 'attendance',
        OTHER: 'other'
    }
};

// Content Type Labels
export const CONTENT_TYPE_LABELS = {
    [CONTENT_TYPES.REWARD.ACHIEVEMENT]: 'Thành tích',
    [CONTENT_TYPES.REWARD.EXCELLENCE]: 'Xuất sắc',
    [CONTENT_TYPES.REWARD.IMPROVEMENT]: 'Tiến bộ',
    [CONTENT_TYPES.REWARD.OTHER]: 'Khác',
    [CONTENT_TYPES.DISCIPLINE.VIOLATION]: 'Vi phạm',
    [CONTENT_TYPES.DISCIPLINE.MISCONDUCT]: 'Hành vi',
    [CONTENT_TYPES.DISCIPLINE.ATTENDANCE]: 'Điểm danh',
    [CONTENT_TYPES.DISCIPLINE.OTHER]: 'Khác'
}; 