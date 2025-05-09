import { API_URL } from '../utils/config.js';

import { getAuthHeaders} from '../utils/helpers.js';


export async function register(username, password, role) {
    const response = await fetch(`${API_URL}/auth/register`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password, role }),
    });
    return handleResponse(response);
}

export async function login(username, password, role) {
    const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password, role }),
    });
    return handleResponse(response);
}

async function handleResponse(response) {
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Something went wrong');
    }
    return response.json();
} 