import api from '../services/api.service.js';

const EvaluationsComponent = {
    async render() {
        const evaluationsList = document.getElementById('evaluationsList');
        try {
            const evaluations = await api.getEvaluations();
            evaluationsList.innerHTML = evaluations.map(evaluation => `
                <div class="list-group-item evaluation-item">
                    <h5 class="mb-1">Evaluation</h5>
                    <p class="mb-1">${evaluation.content}</p>
                    <small>${new Date(evaluation.evaluation_date).toLocaleString()}</small>
                </div>
            `).join('');
        } catch (error) {
            evaluationsList.innerHTML = '<div class="text-danger">Error loading evaluations</div>';
        }
    }
};

export default EvaluationsComponent; 