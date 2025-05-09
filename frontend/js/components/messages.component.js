import api from '../services/api.service.js';
import { appState, showError } from '../utils/helpers.js';

const MessagesComponent = {
    init() {
        this.conversationsList = document.getElementById('conversationsList');
        this.messagesList = document.getElementById('messagesList');
        this.messageForm = document.getElementById('messageForm');
        this.messageInput = document.getElementById('messageInput');
        this.messageForm.addEventListener('submit', this.handleSendMessage.bind(this));
    },
    async renderConversations() {
        try {
            const conversations = await api.getConversations();
            this.conversationsList.innerHTML = conversations.map(conversation => `
                <a href="#" class="list-group-item list-group-item-action" data-conversation-id="${conversation.id}">
                    <h5 class="mb-1">${conversation.title}</h5>
                    <p class="mb-1">${conversation.last_message || 'No messages'}</p>
                    <small>${new Date(conversation.updated_at).toLocaleString()}</small>
                </a>
            `).join('');
            this.conversationsList.querySelectorAll('a').forEach(link => {
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    const conversationId = e.target.closest('a').dataset.conversationId;
                    this.renderMessages(conversationId);
                });
            });
        } catch (error) {
            this.conversationsList.innerHTML = '<div class="text-danger">Error loading conversations</div>';
        }
    },
    async renderMessages(conversationId) {
        try {
            appState.setCurrentConversationId(conversationId);
            const messages = await api.getMessages(conversationId);
            const currentUser = appState.getCurrentUser();
            this.messagesList.innerHTML = messages.map(message => `
                <div class="message ${message.sender_role === currentUser.role ? 'sent' : 'received'}">
                    <p class="mb-1">${message.content}</p>
                    <small>${new Date(message.sent_at).toLocaleString()}</small>
                </div>
            `).join('');
            this.messagesList.scrollTop = this.messagesList.scrollHeight;
            this.messageForm.classList.remove('d-none');
        } catch (error) {
            this.messagesList.innerHTML = '<div class="text-danger">Error loading messages</div>';
        }
    },
    async handleSendMessage(e) {
        e.preventDefault();
        const content = this.messageInput.value;
        const conversationId = appState.getCurrentConversationId();
        if (content && conversationId) {
            try {
                await api.sendMessage(conversationId, content);
                this.messageInput.value = '';
                this.renderMessages(conversationId);
            } catch (error) {
                showError('Error sending message: ' + error.message);
            }
        }
    }
};

export default MessagesComponent; 