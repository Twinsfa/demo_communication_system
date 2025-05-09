import api from '../services/api.service.js';
import { appState, showError } from '../utils/helpers.js';

const MessagesComponent = {
    init() {
        this.conversationsList = document.getElementById('conversationsList');
        this.messagesList = document.getElementById('messagesList');
        this.messageForm = document.getElementById('messageForm');
        this.messageInput = document.getElementById('messageInput');
        this.participantsList = document.getElementById('participantsList');
        this.newConvBtn = document.getElementById('newConvBtn');
        this.addParticipantBtn = document.getElementById('addParticipantBtn');
        this.userList = document.getElementById('userList');

        this.messageForm.addEventListener('submit', this.handleSendMessage.bind(this));
        this.newConvBtn.addEventListener('click', () => this.showNewConversationModal());
        this.addParticipantBtn.addEventListener('click', () => this.showAddParticipantModal());
        
        document.getElementById('newConvForm').addEventListener('submit', this.handleCreateConversation.bind(this));
        document.getElementById('addParticipantForm').addEventListener('submit', this.handleAddParticipant.bind(this));
    },

    async renderConversations() {
        try {
            const conversations = await api.getConversations();
            this.conversationsList.innerHTML = conversations.map(conversation => `
                <a href="#" class="list-group-item list-group-item-action" data-conversation-id="${conversation.id}">
                    <h5 class="mb-1">${conversation.title}</h5>
                    <p class="mb-1">${conversation.last_message || 'Chưa có tin nhắn'}</p>
                    <small>${new Date(conversation.created_at).toLocaleString()}</small>
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
            this.conversationsList.innerHTML = '<div class="text-danger">Lỗi khi tải danh sách cuộc trò chuyện</div>';
            showError('Lỗi khi tải danh sách cuộc trò chuyện: ' + error.message);
        }
    },

    async renderMessages(conversationId) {
        try {
            appState.setCurrentConversationId(conversationId);
            const conversations = await api.getConversations();
            const conv = conversations.find(c => c.id == conversationId);
            
            if (this.participantsList && conv) {
                this.participantsList.innerHTML = conv.participants.map(p =>
                    `<span class="badge bg-secondary me-1">${p.username}
                        ${conv.type === 'group' && p.user_id !== appState.getCurrentUser().id
                            ? `<button onclick="MessagesComponent.handleRemoveParticipant('${p.user_id}')" class="btn btn-sm btn-danger ms-1">X</button>` : ''}
                    </span>`
                ).join('');
                
                // Show/hide add participant button based on conversation type
                this.addParticipantBtn.classList.toggle('d-none', conv.type !== 'group');
            }

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
            this.messagesList.innerHTML = '<div class="text-danger">Lỗi khi tải tin nhắn</div>';
            showError('Lỗi khi tải tin nhắn: ' + error.message);
        }
    },

    async handleSendMessage(e) {
        e.preventDefault();
        const content = this.messageInput.value.trim();
        const conversationId = appState.getCurrentConversationId();
        
        if (!content) {
            showError('Vui lòng nhập nội dung tin nhắn');
            return;
        }
        
        if (!conversationId) {
            showError('Vui lòng chọn cuộc trò chuyện');
            return;
        }

        try {
            await api.sendMessage(conversationId, content);
            this.messageInput.value = '';
            await this.renderMessages(conversationId);
        } catch (error) {
            showError('Lỗi khi gửi tin nhắn: ' + error.message);
        }
    },

    async handleCreateConversation(e) {
        e.preventDefault();
        const type = document.getElementById('newConvType').value;
        const title = document.getElementById('newConvTitle').value.trim();
        const participants = Array.from(document.querySelectorAll('input[name="newConvParticipants"]:checked')).map(i => i.value);
        
        if (!title) {
            showError('Vui lòng nhập tiêu đề cuộc trò chuyện');
            return;
        }
        
        if (participants.length < 2 && type === 'private') {
            showError('Cuộc trò chuyện riêng tư phải có đúng 2 người tham gia');
            return;
        }

        try {
            await api.createConversation(type, title, participants);
            await this.renderConversations();
            bootstrap.Modal.getInstance(document.getElementById('newConvModal')).hide();
            document.getElementById('newConvForm').reset();
        } catch (error) {
            showError('Lỗi khi tạo cuộc trò chuyện: ' + error.message);
        }
    },

    async handleAddParticipant(e) {
        e.preventDefault();
        const conversationId = appState.getCurrentConversationId();
        const participantId = document.getElementById('addParticipantId').value.trim();
        
        if (!participantId) {
            showError('Vui lòng nhập ID người tham gia');
            return;
        }

        try {
            await api.addParticipant(conversationId, participantId);
            await this.renderMessages(conversationId);
            bootstrap.Modal.getInstance(document.getElementById('addParticipantModal')).hide();
            document.getElementById('addParticipantForm').reset();
        } catch (error) {
            showError('Lỗi khi thêm người tham gia: ' + error.message);
        }
    },

    async handleRemoveParticipant(participantId) {
        if (!confirm('Bạn có chắc muốn xóa người tham gia này?')) return;
        
        const conversationId = appState.getCurrentConversationId();
        try {
            await api.removeParticipant(conversationId, participantId);
            await this.renderMessages(conversationId);
        } catch (error) {
            showError('Lỗi khi xóa người tham gia: ' + error.message);
        }
    },

    async showNewConversationModal() {
        try {
            const users = await api.getUsers();
            this.userList.innerHTML = users.map(user => `
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" name="newConvParticipants" value="${user.id}" id="user${user.id}">
                    <label class="form-check-label" for="user${user.id}">
                        ${user.username} (${user.role})
                    </label>
                </div>
            `).join('');
            new bootstrap.Modal(document.getElementById('newConvModal')).show();
        } catch (error) {
            showError('Lỗi khi tải danh sách người dùng: ' + error.message);
        }
    },

    showAddParticipantModal() {
        new bootstrap.Modal(document.getElementById('addParticipantModal')).show();
    }
};

export default MessagesComponent; 