import AuthComponent from './components/auth.component.js';
import NotificationsComponent from './components/notifications.component.js';
import MessagesComponent from './components/messages.component.js';
import FormsComponent from './components/forms.component.js';
import EvaluationsComponent from './components/evaluations.component.js';
import RewardsComponent from './components/rewards.component.js';
import { appState } from './utils/helpers.js';

// Khởi tạo và render các component khi DOM ready

document.addEventListener('DOMContentLoaded', () => {
    AuthComponent.init();
    MessagesComponent.init();

    // Kiểm tra đăng nhập
    const token = localStorage.getItem('token');
    if (token) {
        AuthComponent.showDashboard();
        AuthComponent.updateUserInfo();
        renderAllData();
    } else {
        AuthComponent.showLoginForm();
    }

    // Navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const section = e.target.closest('.nav-link').dataset.section;
            document.querySelectorAll('.section').forEach(sectionEl => {
                sectionEl.classList.add('d-none');
            });
            document.getElementById(section).classList.remove('d-none');
            // Render lại dữ liệu khi chuyển tab
            switch (section) {
                case 'notificationsSection': NotificationsComponent.render(); break;
                case 'conversationsSection': MessagesComponent.renderConversations(); break;
                case 'formsSection': FormsComponent.render(); break;
                case 'evaluationsSection': EvaluationsComponent.render(); break;
                case 'rewardsSection': RewardsComponent.render(); break;
            }
        });
    });

    // Nút tạo form mới (nếu có)
    const newFormBtn = document.getElementById('newFormBtn');
    if (newFormBtn) {
        newFormBtn.addEventListener('click', () => {
            alert('Form creation functionality to be implemented');
        });
    }
});

function renderAllData() {
    NotificationsComponent.render();
    MessagesComponent.renderConversations();
    FormsComponent.render();
    EvaluationsComponent.render();
    RewardsComponent.render();
} 