import api from '../services/api.service.js';

const FormsComponent = {
    async render() {
        const formsList = document.getElementById('formsList');
        try {
            const forms = await api.getForms();
            formsList.innerHTML = forms.map(form => `
                <div class="list-group-item form-item ${form.status}">
                    <h5 class="mb-1">${form.type}</h5>
                    <p class="mb-1">${form.content}</p>
                    <small>Status: ${form.status} - ${new Date(form.submission_date).toLocaleString()}</small>
                </div>
            `).join('');
        } catch (error) {
            formsList.innerHTML = '<div class="text-danger">Error loading forms</div>';
        }
    }
};

export default FormsComponent; 