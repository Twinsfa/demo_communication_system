const API_BASE_URL = 'http://localhost:5000/api';
import { getAuthHeaders, handleResponse } from '../utils/helpers.js';

export async function getEvaluations() {
    const response = await fetch(`${API_BASE_URL}/evaluations`, {
        headers: getAuthHeaders(),
    });
    return handleResponse(response);
} 