import { getAuthHeaders, handleResponse } from '../utils/helpers.js';
import { API_URL } from '../utils/config.js';
export async function getNotifications() {
    const response = await fetch(`${API_URL}/notifications`, {
        headers: getAuthHeaders(),
    });
    return handleResponse(response);
} 