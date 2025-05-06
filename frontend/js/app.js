// DOM Elements
const loginForm = document.getElementById('loginForm');
const dashboard = document.getElementById('dashboard');
const loginFormElement = document.getElementById('login');
const userInfo = document.getElementById('userInfo');
const logoutBtn = document.getElementById('logoutBtn');
const sections = document.querySelectorAll('.section');
const navLinks = document.querySelectorAll('.nav-link');

// State
let currentUser = null;
let currentConversationId = null;

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Check if user is logged in
    const token = localStorage.getItem('token');
    if (token) {
        showDashboard();
        loadData();
    }

    // Login form submission
    loginFormElement.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const role = document.getElementById('role').value;

        try {
            const response = await api.login(username, password, role);
            if (response.token) {
                localStorage.setItem('token', response.token);
                currentUser = response.user;
                showDashboard();
                loadData();
            } else {
                alert('Login failed: Invalid response from server');
            }
        } catch (error) {
            console.error('Login error:', error);
            alert('Login failed: ' + (error.message || 'Could not connect to server. Please check if the backend is running.'));
        }
    });

    // Logout
    logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('token');
        currentUser = null;
        showLoginForm();
    });

    // Navigation
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const section = e.target.closest('.nav-link').dataset.section;
            showSection(section);
        });
    });

    // Message form submission
    document.getElementById('messageForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const content = document.getElementById('messageInput').value;
        if (content && currentConversationId) {
            try {
                await api.sendMessage(currentConversationId, content);
                document.getElementById('messageInput').value = '';
                loadMessages(currentConversationId);
            } catch (error) {
                alert('Error sending message: ' + error.message);
            }
        }
    });

    // New form button
    document.getElementById('newFormBtn').addEventListener('click', () => {
        // Show form creation modal or navigate to form creation page
        alert('Form creation functionality to be implemented');
    });
});

// UI Functions
function showLoginForm() {
    loginForm.classList.remove('d-none');
    dashboard.classList.add('d-none');
}

function showDashboard() {
    loginForm.classList.add('d-none');
    dashboard.classList.remove('d-none');
    userInfo.textContent = `Welcome, ${currentUser?.username || 'User'}`;
}

function showSection(sectionId) {
    sections.forEach(section => {
        section.classList.add('d-none');
    });
    document.getElementById(sectionId).classList.remove('d-none');
}

// Data Loading Functions
async function loadData() {
    try {
        await Promise.all([
            loadNotifications(),
            loadConversations(),
            loadForms(),
            loadEvaluations(),
            loadRewards()
        ]);
    } catch (error) {
        console.error('Error loading data:', error);
    }
}

async function loadNotifications() {
    try {
        const notifications = await api.getNotifications();
        const notificationsList = document.getElementById('notificationsList');
        notificationsList.innerHTML = notifications.map(notification => `
            <div class="list-group-item notification-item ${notification.is_read ? '' : 'unread'}">
                <h5 class="mb-1">${notification.title}</h5>
                <p class="mb-1">${notification.content}</p>
                <small>${new Date(notification.created_time).toLocaleString()}</small>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading notifications:', error);
    }
}

async function loadConversations() {
    try {
        const conversations = await api.getConversations();
        const conversationsList = document.getElementById('conversationsList');
        conversationsList.innerHTML = conversations.map(conversation => `
            <a href="#" class="list-group-item list-group-item-action" 
               data-conversation-id="${conversation.id}">
                <h5 class="mb-1">${conversation.title}</h5>
                <p class="mb-1">${conversation.last_message || 'No messages'}</p>
                <small>${new Date(conversation.updated_at).toLocaleString()}</small>
            </a>
        `).join('');

        // Add click handlers for conversations
        conversationsList.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const conversationId = e.target.closest('a').dataset.conversationId;
                loadMessages(conversationId);
            });
        });
    } catch (error) {
        console.error('Error loading conversations:', error);
    }
}

async function loadMessages(conversationId) {
    try {
        currentConversationId = conversationId;
        const messages = await api.getMessages(conversationId);
        const messagesList = document.getElementById('messagesList');
        messagesList.innerHTML = messages.map(message => `
            <div class="message ${message.sender_role === currentUser.role ? 'sent' : 'received'}">
                <p class="mb-1">${message.content}</p>
                <small>${new Date(message.sent_at).toLocaleString()}</small>
            </div>
        `).join('');
        messagesList.scrollTop = messagesList.scrollHeight;
        document.getElementById('messageForm').classList.remove('d-none');
    } catch (error) {
        console.error('Error loading messages:', error);
    }
}

async function loadForms() {
    try {
        const forms = await api.getForms();
        const formsList = document.getElementById('formsList');
        formsList.innerHTML = forms.map(form => `
            <div class="list-group-item form-item ${form.status}">
                <h5 class="mb-1">${form.type}</h5>
                <p class="mb-1">${form.content}</p>
                <small>Status: ${form.status} - ${new Date(form.submission_date).toLocaleString()}</small>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading forms:', error);
    }
}

async function loadEvaluations() {
    try {
        const evaluations = await api.getEvaluations();
        const evaluationsList = document.getElementById('evaluationsList');
        evaluationsList.innerHTML = evaluations.map(evaluation => `
            <div class="list-group-item evaluation-item">
                <h5 class="mb-1">Evaluation</h5>
                <p class="mb-1">${evaluation.content}</p>
                <small>${new Date(evaluation.evaluation_date).toLocaleString()}</small>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading evaluations:', error);
    }
}

async function loadRewards() {
    try {
        const rewards = await api.getRewards();
        const rewardsList = document.getElementById('rewardsList');
        rewardsList.innerHTML = rewards.map(reward => `
            <div class="list-group-item ${reward.type}-item">
                <h5 class="mb-1">${reward.type}</h5>
                <p class="mb-1">${reward.content}</p>
                <small>${new Date(reward.date).toLocaleString()}</small>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading rewards:', error);
    }
} 