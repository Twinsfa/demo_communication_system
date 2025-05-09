const API_BASE_URL = 'http://localhost:5000/api';
import { getAuthHeaders, handleResponse } from '../utils/helpers.js';

export async function getConversations() {
    const response = await fetch(`${API_BASE_URL}/conversations`, {
        headers: getAuthHeaders(),
    });
    return handleResponse(response);
}

export async function getMessages(conversationId) {
    const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}/messages`, {
        headers: getAuthHeaders(),
    });
    return handleResponse(response);
}

export async function sendMessage(conversationId, content) {
    const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}/messages`, {
        method: 'POST',
        headers: {
            ...getAuthHeaders(),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ content }),
    });
    return handleResponse(response);
} 