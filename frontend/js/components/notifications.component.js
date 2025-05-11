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
                    <button onclick="markAsRead(${notification.id})">Đánh dấu đã đọc</button>
                    <button onclick="deleteNotification(${notification.id})">Xóa</button>
                </div>
            `).join('');
        } catch (error) {
            notificationsList.innerHTML = '<div class="text-danger">Error loading notifications</div>';
        }
    }
};

// Ví dụ: thêm các hàm thao tác vào window để gọi từ HTML (hoặc dùng event delegation)
window.markAsRead = async function(id) {
    await api.markAsRead(id);
    NotificationsComponent.render();
};
window.deleteNotification = async function(id) {
    await api.deleteNotification(id);
    NotificationsComponent.render();
};

document.getElementById('sendOption').addEventListener('change', (e) => {
    const scheduleTimeField = document.getElementById('scheduleTimeField');
    if (e.target.value === 'schedule') {
        scheduleTimeField.classList.remove('d-none');
    } else {
        scheduleTimeField.classList.add('d-none');
    }
});

document.getElementById('createNotificationForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const title = document.getElementById('notificationTitle').value.trim();
    const content = document.getElementById('notificationContent').value.trim();
    const type = document.getElementById('notificationType').value;
    const classId = document.getElementById('classId').value.trim();
    const sendOption = document.getElementById('sendOption').value;
    const scheduleTime = document.getElementById('scheduleTime').value;

    const data = {
        title,
        content,
        type,
        class_id: type === 'specific_class' ? classId : null,
        send_option: sendOption,
        schedule_time: sendOption === 'schedule' ? scheduleTime : null,
    };

    try {
        await api.notifications.createNotification(data);
        alert('Notification created successfully');
        NotificationsComponent.render();
    } catch (error) {
        console.error('Error creating notification:', error);
        alert('Failed to create notification');
    }
});

export default NotificationsComponent;