import { API_URL } from '../utils/config.js';
import { getAuthHeaders, handleResponse } from '../utils/helpers.js';

export async function getEvaluations() {
    const response = await fetch(`${API_URL}/evaluations`, {
        headers: getAuthHeaders(),
    });
    return handleResponse(response);
} 