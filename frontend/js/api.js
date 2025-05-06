// API Configuration
const API_BASE_URL = 'http://localhost:5000/api';

// API Service
const api = {
    // Authentication
    async login(username, password, role) {
        try {
            const response = await fetch(`${API_BASE_URL}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password, role_type: role })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Login failed');
            }
            
            return response.json();
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    },

    // Notifications
    async getNotifications() {
        const response = await fetch(`${API_BASE_URL}/notifications`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        return response.json();
    },

    async markNotificationAsRead(notificationId) {
        const response = await fetch(`${API_BASE_URL}/notifications/${notificationId}/read`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        return response.json();
    },

    // Messages
    async getConversations() {
        const response = await fetch(`${API_BASE_URL}/messages/conversations`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        return response.json();
    },

    async getMessages(conversationId) {
        const response = await fetch(`${API_BASE_URL}/messages/${conversationId}`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        return response.json();
    },

    async sendMessage(conversationId, content) {
        const response = await fetch(`${API_BASE_URL}/messages/${conversationId}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ content })
        });
        return response.json();
    },

    // Forms
    async getForms() {
        const response = await fetch(`${API_BASE_URL}/forms`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        return response.json();
    },

    async submitForm(type, content) {
        const response = await fetch(`${API_BASE_URL}/forms`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ type, content })
        });
        return response.json();
    },

    // Evaluations
    async getEvaluations() {
        const response = await fetch(`${API_BASE_URL}/evaluations`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        return response.json();
    },

    async createEvaluation(studentId, content) {
        const response = await fetch(`${API_BASE_URL}/evaluations`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ student_id: studentId, content })
        });
        return response.json();
    },

    // Rewards
    async getRewards() {
        const response = await fetch(`${API_BASE_URL}/rewards`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        return response.json();
    },

    async createReward(type, studentId, content, date) {
        const response = await fetch(`${API_BASE_URL}/rewards`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ type, student_id: studentId, content, date })
        });
        return response.json();
    }
}; 