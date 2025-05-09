// Helpers & State

export function getAuthHeaders() {
    const token = localStorage.getItem('token');
    return {
        'Authorization': `Bearer ${token}`,
    };
}

export async function handleResponse(response) {
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Something went wrong');
    }
    return response.json();
}

// App State
export const appState = {
    currentUser: null,
    currentConversationId: null,
    setCurrentUser(user) { this.currentUser = user; },
    getCurrentUser() { return this.currentUser; },
    setCurrentConversationId(id) { this.currentConversationId = id; },
    getCurrentConversationId() { return this.currentConversationId; },
    clearState() { this.currentUser = null; this.currentConversationId = null; }
};

// Các nhóm chức năng còn lại (ví dụ: hiển thị lỗi, format, validate, ...)
export function showError(message) {
    alert(message);
} 