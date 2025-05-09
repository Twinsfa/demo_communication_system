import api from '../services/api.service.js';

const NotificationsComponent = {
    async render() {
        const notificationsList = document.getElementById('notificationsList');
        try {
            const notifications = await api.getNotifications();
            notificationsList.innerHTML = notifications.map(notification => `
                <div class="list-group-item notification-item ${notification.is_read ? '' : 'unread'}">
                    <h5 class="mb-1">${notification.title}</h5>
                    <p class="mb-1">${notification.content}</p>
                    <small>${new Date(notification.created_time).toLocaleString()}</small>
                </div>
            `).join('');
        } catch (error) {
            notificationsList.innerHTML = '<div class="text-danger">Error loading notifications</div>';
        }
    }
};

export default NotificationsComponent; 