import { API_URL } from '../utils/config.js';
import { getAuthHeaders } from '../utils/helpers.js';

export async function getConversations() {
    const response = await fetch(`${API_URL}/messages/conversations`, {
        headers: getAuthHeaders()
    });
    if (!response.ok) throw new Error('Failed to get conversations');
    return response.json();
}

export async function getMessages(conversationId) {
    const response = await fetch(`${API_URL}/messages/conversations/${conversationId}/messages`, {
        headers: getAuthHeaders()
    });
    if (!response.ok) throw new Error('Failed to get messages');
    return response.json();
}

export async function sendMessage(conversationId, content) {
    const response = await fetch(`${API_URL}/messages/conversations/${conversationId}/messages`, {
        method: 'POST',
        headers: {
            ...getAuthHeaders(),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ content })
    });
    if (!response.ok) throw new Error('Failed to send message');
    return response.json();
}

export async function createConversation(type, title, participants) {
    const response = await fetch(`${API_URL}/messages/conversations`, {
        method: 'POST',
        headers: {
            ...getAuthHeaders(),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ type, title, participants })
    });
    if (!response.ok) throw new Error('Failed to create conversation');
    return response.json();
}

export async function addParticipant(conversationId, participantId) {
    const response = await fetch(`${API_URL}/messages/conversations/${conversationId}/participants`, {
        method: 'POST',
        headers: {
            ...getAuthHeaders(),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ participant_id: participantId })
    });
    if (!response.ok) throw new Error('Failed to add participant');
    return response.json();
}

export async function removeParticipant(conversationId, participantId) {
    const response = await fetch(`${API_URL}/messages/conversations/${conversationId}/participants/${participantId}`, {
        method: 'DELETE',
        headers: getAuthHeaders()
    });
    if (!response.ok) throw new Error('Failed to remove participant');
    return response.json();
}

export async function getUsers() {
    const response = await fetch(`${API_URL}/users`, {
        headers: getAuthHeaders(),
    });
    return handleResponse(response);
} 