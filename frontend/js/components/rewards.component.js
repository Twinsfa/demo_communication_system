import api from '../services/api.service.js';

const RewardsComponent = {
    async render() {
        const rewardsList = document.getElementById('rewardsList');
        try {
            const rewards = await api.getRewards();
            rewardsList.innerHTML = rewards.map(reward => `
                <div class="list-group-item ${reward.type}-item">
                    <h5 class="mb-1">${reward.type}</h5>
                    <p class="mb-1">${reward.content}</p>
                    <small>${new Date(reward.date).toLocaleString()}</small>
                </div>
            `).join('');
        } catch (error) {
            rewardsList.innerHTML = '<div class="text-danger">Error loading rewards</div>';
        }
    }
};

export default RewardsComponent; 