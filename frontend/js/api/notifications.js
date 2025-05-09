const API_BASE_URL = 'http://localhost:5000/api';
import { getAuthHeaders, handleResponse } from '../utils/helpers.js';

export async function getNotifications() {
    const response = await fetch(`${API_BASE_URL}/notifications`, {
        headers: getAuthHeaders(),
    });
    return handleResponse(response);
} 