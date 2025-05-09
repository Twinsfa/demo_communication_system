import api from '../services/api.service.js';
import { appState, showError } from '../utils/helpers.js';

const AuthComponent = {
    init() {
        this.loginForm = document.getElementById('login');
        this.logoutBtn = document.getElementById('logoutBtn');
        this.userInfo = document.getElementById('userInfo');
        this.dashboard = document.getElementById('dashboard');
        this.loginFormContainer = document.getElementById('loginForm');

        this.loginForm.addEventListener('submit', this.handleLogin.bind(this));
        this.logoutBtn.addEventListener('click', this.handleLogout.bind(this));
    },
    async handleLogin(e) {
        e.preventDefault();
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value.trim();
            const role = document.getElementById('role').value.trim();
        try {
            const response = await api.login(username, password, role);
            if (response.access_token) {
                localStorage.setItem('token', response.access_token);
                appState.setCurrentUser(response.user_info);
                this.showDashboard();
                this.updateUserInfo();
            } else {
                showError('Login failed: Invalid response from server');
            }
        } catch (error) {
            showError('Login failed: ' + (error.message || 'Could not connect to server'));
        }
    },
    handleLogout() {
        localStorage.removeItem('token');
        appState.clearState();
        this.showLoginForm();
    },
    showLoginForm() {
        this.loginFormContainer.classList.remove('d-none');
        this.dashboard.classList.add('d-none');
    },
    showDashboard() {
        this.loginFormContainer.classList.add('d-none');
        this.dashboard.classList.remove('d-none');
    },
    updateUserInfo() {
        const user = appState.getCurrentUser();
        this.userInfo.textContent = `Welcome, ${user?.username || 'User'}`;
    }
};

export default AuthComponent; 