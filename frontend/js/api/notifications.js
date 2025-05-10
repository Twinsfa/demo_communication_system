import { getAuthHeaders, handleResponse } from '../utils/helpers.js';
import { API_URL } from '../utils/config.js';

// Lấy danh sách thông báo
export async function getNotifications() {
    const response = await fetch(`${API_URL}/notifications`, {
        headers: getAuthHeaders(),
    });
    return handleResponse(response);
}

// Tạo mới thông báo
export async function createNotification(data) {
    const response = await fetch(`${API_URL}/notifications`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(data),
    });
    return handleResponse(response);
}

// Đánh dấu đã đọc
export async function markAsRead(notificationId) {
    const response = await fetch(`${API_URL}/notifications/${notificationId}/read`, {
        method: 'POST',
        headers: getAuthHeaders(),
    });
    return handleResponse(response);
}

// Xóa thông báo
export async function deleteNotification(notificationId) {
    const response = await fetch(`${API_URL}/notifications/${notificationId}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
    });
    return handleResponse(response);
}