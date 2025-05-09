import { API_URL } from '../utils/config.js';
import { getAuthHeaders, handleResponse } from '../utils/helpers.js';

export async function getForms() {
    const response = await fetch(`${API_URL}/forms`, {
        headers: getAuthHeaders(),
    });
    return handleResponse(response);
} 