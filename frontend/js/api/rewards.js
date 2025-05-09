const API_BASE_URL = 'http://localhost:5000/api';
import { getAuthHeaders, handleResponse } from '../utils/helpers.js';

export async function getRewards() {
    const response = await fetch(`${API_BASE_URL}/rewards`, {
        headers: getAuthHeaders(),
    });
    return handleResponse(response);
} 