import api from '../services/api.service.js';
import { appState, showError } from '../utils/helpers.js';

class RewardsComponent {
    constructor() {
        this.rewardsList = document.getElementById('rewardsList');
        this.newRewardBtn = document.getElementById('newRewardBtn');
        this.newRewardModal = new bootstrap.Modal(document.getElementById('newRewardModal'));
        this.editRewardModal = new bootstrap.Modal(document.getElementById('editRewardModal'));
        this.newRewardForm = document.getElementById('newRewardForm');
        this.editRewardForm = document.getElementById('editRewardForm');
        this.rewardsChart = null;
        this.contentTypeChart = null;
        this.viewMode = 'all'; // all, student, class, school
        this.currentId = null; // student_id or class_id

        this.init();
    }

    async init() {
        // Load initial data
        await this.loadRewards();
        await this.loadStudents();
        this.initCharts();

        // Event listeners
        this.newRewardBtn.addEventListener('click', () => this.showNewRewardModal());
        this.newRewardForm.addEventListener('submit', (e) => this.handleCreate(e));
        this.editRewardForm.addEventListener('submit', (e) => this.handleUpdate(e));

        // Type filter buttons
        document.querySelectorAll('[data-type]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('[data-type]').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.filterRewards(e.target.dataset.type);
            });
        });

        // View mode buttons
        document.querySelectorAll('[data-view]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('[data-view]').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.changeViewMode(e.target.dataset.view);
            });
        });

        // Type change handler for content_type options
        document.querySelectorAll('select[name="type"]').forEach(select => {
            select.addEventListener('change', (e) => this.updateContentTypeOptions(e.target));
        });
    }

    async loadRewards() {
        try {
            let response;
            switch (this.viewMode) {
                case 'student':
                    response = await api.rewards.getStudentStatistics(this.currentId);
                    break;
                case 'class':
                    response = await api.rewards.getClassStatistics(this.currentId);
                    break;
                case 'school':
                    response = await api.rewards.getSchoolStatistics();
                    break;
                default:
                    response = await api.rewards.getAll();
            }
            this.rewards = response.data;
            this.renderRewards();
            this.updateCharts();
        } catch (error) {
            console.error('Lỗi khi tải danh sách khen thưởng:', error);
            showError('Lỗi khi tải danh sách khen thưởng');
        }
    }

    async loadStudents() {
        try {
            const response = await api.students.getAll();
            const students = response.data;
            
            // Update student selects
            document.querySelectorAll('select[name="student_id"]').forEach(select => {
                select.innerHTML = students.map(student => 
                    `<option value="${student.id}">${student.name}</option>`
                ).join('');
            });
        } catch (error) {
            console.error('Lỗi khi tải danh sách học sinh:', error);
            alert('Lỗi khi tải danh sách học sinh');
        }
    }

    initCharts() {
        // Initialize rewards chart
        const rewardsCtx = document.getElementById('rewardsChart').getContext('2d');
        this.rewardsChart = new Chart(rewardsCtx, {
            type: 'bar',
            data: {
                labels: ['Khen thưởng', 'Kỷ luật'],
                datasets: [{
                    label: 'Số lượng',
                    data: [0, 0],
                    backgroundColor: ['#28a745', '#dc3545']
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });

        // Initialize content type chart
        const contentTypeCtx = document.getElementById('contentTypeChart').getContext('2d');
        this.contentTypeChart = new Chart(contentTypeCtx, {
            type: 'pie',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        '#28a745', '#20c997', '#0dcaf0', '#0d6efd',
                        '#dc3545', '#fd7e14', '#ffc107', '#6f42c1'
                    ]
                }]
            },
            options: {
                responsive: true
            }
        });
    }

    updateCharts() {
        if (this.viewMode === 'all') {
            // Update rewards chart
            const rewardsCount = this.rewards.filter(r => r.type === 'reward').length;
            const disciplineCount = this.rewards.filter(r => r.type === 'discipline').length;
            
            this.rewardsChart.data.datasets[0].data = [rewardsCount, disciplineCount];
            this.rewardsChart.update();

            // Update content type chart
            const contentTypeCounts = {};
            this.rewards.forEach(reward => {
                contentTypeCounts[reward.content_type] = (contentTypeCounts[reward.content_type] || 0) + 1;
            });

            this.contentTypeChart.data.labels = Object.keys(contentTypeCounts).map(type => 
                this.getContentTypeLabel(type)
            );
            this.contentTypeChart.data.datasets[0].data = Object.values(contentTypeCounts);
            this.contentTypeChart.update();
        } else {
            // Update charts based on statistics data
            const stats = this.rewards;
            
            // Update rewards chart
            this.rewardsChart.data.datasets[0].data = [
                stats.rewards.total,
                stats.discipline.total
            ];
            this.rewardsChart.update();

            // Update content type chart
            const rewardTypes = stats.rewards.by_type;
            const disciplineTypes = stats.discipline.by_type;
            
            this.contentTypeChart.data.labels = [
                ...Object.keys(rewardTypes).map(type => this.getContentTypeLabel(type)),
                ...Object.keys(disciplineTypes).map(type => this.getContentTypeLabel(type))
            ];
            this.contentTypeChart.data.datasets[0].data = [
                ...Object.values(rewardTypes),
                ...Object.values(disciplineTypes)
            ];
            this.contentTypeChart.update();
        }
    }

    getContentTypeLabel(type) {
        const labels = {
            'achievement': 'Thành tích',
            'excellence': 'Xuất sắc',
            'improvement': 'Tiến bộ',
            'other': 'Khác',
            'violation': 'Vi phạm',
            'misconduct': 'Hành vi',
            'attendance': 'Điểm danh'
        };
        return labels[type] || type;
    }

    renderRewards(filteredRewards = null) {
        const rewards = filteredRewards || this.rewards;
        
        if (this.viewMode === 'all') {
            this.rewardsList.innerHTML = rewards.map(reward => `
                <tr>
                    <td>${reward.student_name}</td>
                    <td>${reward.department_name}</td>
                    <td>
                        <span class="badge ${reward.type === 'reward' ? 'bg-success' : 'bg-danger'}">
                            ${reward.type === 'reward' ? 'Khen thưởng' : 'Kỷ luật'}
                        </span>
                    </td>
                    <td>${reward.content}</td>
                    <td>${new Date(reward.date).toLocaleDateString('vi-VN')}</td>
                    <td>
                        <button class="btn btn-sm btn-primary" onclick="RewardsComponent.showEditModal(${reward.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="RewardsComponent.handleDelete(${reward.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `).join('');
        } else {
            // Render statistics view
            const stats = rewards;
            this.rewardsList.innerHTML = `
                <tr>
                    <td colspan="6">
                        <h5>Thống kê khen thưởng</h5>
                        <p>Tổng số: ${stats.rewards.total}</p>
                        <h6>Top học sinh được khen thưởng:</h6>
                        <ul>
                            ${stats.rewards.top_students.map(s => 
                                `<li>${s.full_name}: ${s.count} lần</li>`
                            ).join('')}
                        </ul>
                    </td>
                </tr>
                <tr>
                    <td colspan="6">
                        <h5>Thống kê kỷ luật</h5>
                        <p>Tổng số: ${stats.discipline.total}</p>
                        <h6>Top học sinh bị kỷ luật:</h6>
                        <ul>
                            ${stats.discipline.top_students.map(s => 
                                `<li>${s.full_name}: ${s.count} lần</li>`
                            ).join('')}
                        </ul>
                    </td>
                </tr>
            `;
        }
    }

    filterRewards(type) {
        if (type === 'all') {
            this.renderRewards();
        } else {
            const filtered = this.rewards.filter(reward => reward.type === type);
            this.renderRewards(filtered);
        }
    }

    showNewRewardModal() {
        this.newRewardForm.reset();
        const typeSelect = this.newRewardForm.querySelector('select[name="type"]');
        this.updateContentTypeOptions(typeSelect);
        this.newRewardModal.show();
    }

    updateContentTypeOptions(typeSelect) {
        const contentTypeSelect = typeSelect.closest('form').querySelector('select[name="content_type"]');
        const type = typeSelect.value;
        
        const options = {
            'reward': [
                { value: 'achievement', label: 'Thành tích' },
                { value: 'excellence', label: 'Xuất sắc' },
                { value: 'improvement', label: 'Tiến bộ' },
                { value: 'other', label: 'Khác' }
            ],
            'discipline': [
                { value: 'violation', label: 'Vi phạm' },
                { value: 'misconduct', label: 'Hành vi' },
                { value: 'attendance', label: 'Điểm danh' },
                { value: 'other', label: 'Khác' }
            ]
        };

        contentTypeSelect.innerHTML = options[type].map(opt => 
            `<option value="${opt.value}">${opt.label}</option>`
        ).join('');
    }

    async handleCreate(event) {
        event.preventDefault();
        const formData = new FormData(this.newRewardForm);
        const data = Object.fromEntries(formData.entries());

        try {
            await api.rewards.create(data);
            this.newRewardModal.hide();
            await this.loadRewards();
            alert('Thêm khen thưởng/kỷ luật thành công');
        } catch (error) {
            console.error('Lỗi khi thêm khen thưởng/kỷ luật:', error);
            alert('Lỗi khi thêm khen thưởng/kỷ luật');
        }
    }

    async showEditModal(id) {
        try {
            const response = await api.rewards.getById(id);
            const reward = response.data;
            
            const form = this.editRewardForm;
            form.querySelector('[name="id"]').value = reward.id;
            form.querySelector('[name="type"]').value = reward.type;
            form.querySelector('[name="content_type"]').value = reward.content_type;
            form.querySelector('[name="student_id"]').value = reward.student_id;
            form.querySelector('[name="content"]').value = reward.content;
            form.querySelector('[name="date"]').value = reward.date;

            this.updateContentTypeOptions(form.querySelector('[name="type"]'));
            this.editRewardModal.show();
        } catch (error) {
            console.error('Lỗi khi tải thông tin khen thưởng/kỷ luật:', error);
            alert('Lỗi khi tải thông tin khen thưởng/kỷ luật');
        }
    }

    async handleUpdate(event) {
        event.preventDefault();
        const formData = new FormData(this.editRewardForm);
        const data = Object.fromEntries(formData.entries());
        const id = data.id;
        delete data.id;

        try {
            await api.rewards.update(id, data);
            this.editRewardModal.hide();
            await this.loadRewards();
            alert('Cập nhật khen thưởng/kỷ luật thành công');
        } catch (error) {
            console.error('Lỗi khi cập nhật khen thưởng/kỷ luật:', error);
            alert('Lỗi khi cập nhật khen thưởng/kỷ luật');
        }
    }

    async handleDelete(id) {
        if (!confirm('Bạn có chắc chắn muốn xóa khen thưởng/kỷ luật này?')) {
            return;
        }

        try {
            await api.rewards.delete(id);
            await this.loadRewards();
            alert('Xóa khen thưởng/kỷ luật thành công');
        } catch (error) {
            console.error('Lỗi khi xóa khen thưởng/kỷ luật:', error);
            alert('Lỗi khi xóa khen thưởng/kỷ luật');
        }
    }

    async changeViewMode(mode, id = null) {
        this.viewMode = mode;
        this.currentId = id;
        await this.loadRewards();
    }
}

// Initialize component
const rewardsComponent = new RewardsComponent(); 