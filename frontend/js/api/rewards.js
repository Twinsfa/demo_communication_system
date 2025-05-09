import { API_URL, getAuthHeader } from '../utils/config.js';

const rewardsApi = {
    async getAll() {
        const response = await fetch(`${API_URL}/rewards`, {
            headers: getAuthHeader()
        });
        if (!response.ok) {
            throw new Error('Lỗi khi tải danh sách khen thưởng/kỷ luật');
        }
        return response.json();
    },

    async getById(id) {
        const response = await fetch(`${API_URL}/rewards/${id}`, {
            headers: getAuthHeader()
        });
        if (!response.ok) {
            throw new Error('Lỗi khi tải thông tin khen thưởng/kỷ luật');
        }
        return response.json();
    },

    async create(data) {
        const response = await fetch(`${API_URL}/rewards`, {
            method: 'POST',
            headers: {
                ...getAuthHeader(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Lỗi khi thêm khen thưởng/kỷ luật');
        }
        return response.json();
    },

    async update(id, data) {
        const response = await fetch(`${API_URL}/rewards/${id}`, {
            method: 'PUT',
            headers: {
                ...getAuthHeader(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Lỗi khi cập nhật khen thưởng/kỷ luật');
        }
        return response.json();
    },

    async delete(id) {
        const response = await fetch(`${API_URL}/rewards/${id}`, {
            method: 'DELETE',
            headers: getAuthHeader()
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Lỗi khi xóa khen thưởng/kỷ luật');
        }
        return response.json();
    },

    async getStudentStatistics(studentId) {
        const response = await fetch(`${API_URL}/rewards/statistics/student/${studentId}`, {
            headers: getAuthHeader()
        });
        if (!response.ok) {
            throw new Error('Lỗi khi tải thống kê học sinh');
        }
        return response.json();
    },

    async getClassStatistics(classId) {
        const response = await fetch(`${API_URL}/rewards/statistics/class/${classId}`, {
            headers: getAuthHeader()
        });
        if (!response.ok) {
            throw new Error('Lỗi khi tải thống kê lớp');
        }
        return response.json();
    },

    async getSchoolStatistics() {
        const response = await fetch(`${API_URL}/rewards/statistics/school`, {
            headers: getAuthHeader()
        });
        if (!response.ok) {
            throw new Error('Lỗi khi tải thống kê toàn trường');
        }
        return response.json();
    }
};

export default rewardsApi; 