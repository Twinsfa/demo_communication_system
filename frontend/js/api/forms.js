// forms.js - Handle forms functionality in the School Management System
import { getForms, submitForm, getFormById, updateFormStatus, assignFormToDepartment } from './api/forms.js';
import { getCurrentUser } from './utils/auth.js';
import { showToast, formatDate } from './utils/helpers.js';

// Form types and statuses for display
const formTypes = {
    'absence': 'Absence Request',
    'complaint': 'Complaint',
    'feedback': 'Feedback',
    'permission': 'Permission Request',
    'other': 'Other'
};

const statusClasses = {
    'pending': 'bg-warning',
    'processing': 'bg-info',
    'completed': 'bg-success'
};

// DOM elements (will be initialized in init function)
let formsList;
let newFormBtn;
let newFormForm;
let formFilters;
let statusFilters;
let assignDepartmentForm;

// Initialize forms module
export function initForms() {
    // Cache DOM elements
    formsList = document.getElementById('formsList');
    newFormBtn = document.getElementById('newFormBtn');
    newFormForm = document.getElementById('newFormForm');
    formFilters = document.querySelectorAll('[data-form-filter]');
    statusFilters = document.querySelectorAll('[data-form-status]');
    assignDepartmentForm = document.getElementById('assignDepartmentForm');

    // Load initial forms
    loadForms();

    // Load departments for dropdowns
    loadDepartments();

    // Set up event listeners
    setupEventListeners();
}

// Load forms from the API
async function loadForms(filters = {}) {
    try {
        formsList.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div></div>';

        const forms = await getForms(filters);

        if (forms.length === 0) {
            formsList.innerHTML = '<div class="alert alert-info">No forms found.</div>';
            return;
        }

        displayForms(forms);
    } catch (error) {
        console.error('Error loading forms:', error);
        formsList.innerHTML = `<div class="alert alert-danger">Failed to load forms. ${error.message}</div>`;
    }
}

// Display forms in the UI
function displayForms(forms) {
    const currentUser = getCurrentUser();
    const isParent = currentUser.roles.includes('parent');
    const isDepartment = currentUser.roles.includes('department');

    const formsHTML = forms.map(form => {
        const formType = formTypes[form.type] || form.type;
        const statusClass = statusClasses[form.status] || 'bg-secondary';

        return `
            <div class="list-group-item list-group-item-action" data-form-id="${form.id}">
                <div class="d-flex w-100 justify-content-between">
                    <h5 class="mb-1">${formType}</h5>
                    <span class="badge ${statusClass}">${form.status}</span>
                </div>
                <p class="mb-1">${form.content.substring(0, 100)}${form.content.length > 100 ? '...' : ''}</p>
                <small>
                    Submitted: ${formatDate(form.submission_date)}
                    ${form.department ? ` | Department: ${form.department.name}` : ''}
                </small>
                <div class="mt-2">
                    <button class="btn btn-sm btn-outline-primary view-form-btn">View Details</button>
                    ${isDepartment && form.status === 'pending' && !form.department_id ? 
                        `<button class="btn btn-sm btn-outline-info assign-form-btn">Assign</button>` : ''}
                    ${isDepartment && form.status === 'pending' ? 
                        `<button class="btn btn-sm btn-outline-success process-form-btn">Process</button>` : ''}
                    ${isDepartment && form.status === 'processing' ? 
                        `<button class="btn btn-sm btn-outline-success complete-form-btn">Mark Complete</button>` : ''}
                </div>
            </div>
        `;
    }).join('');

    formsList.innerHTML = formsHTML;

    // Add event listeners to buttons
    addFormButtonListeners();
}

// Add event listeners to dynamically created form buttons
function addFormButtonListeners() {
    // View form details
    document.querySelectorAll('.view-form-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const formId = parseInt(e.target.closest('.list-group-item').dataset.formId);
            viewFormDetails(formId);
        });
    });

    // Assign department
    document.querySelectorAll('.assign-form-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const formId = parseInt(e.target.closest('.list-group-item').dataset.formId);
            openAssignModal(formId);
        });
    });

    // Process form
    document.querySelectorAll('.process-form-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const formId = parseInt(e.target.closest('.list-group-item').dataset.formId);
            processForm(formId);
        });
    });

    // Complete form
    document.querySelectorAll('.complete-form-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const formId = parseInt(e.target.closest('.list-group-item').dataset.formId);
            completeForm(formId);
        });
    });
}

// Set up event listeners
function setupEventListeners() {
    // New form button
    if (newFormBtn) {
        newFormBtn.addEventListener('click', () => {
            const newFormModal = new bootstrap.Modal(document.getElementById('newFormModal'));
            newFormModal.show();
        });
    }

    // Form submission
    if (newFormForm) {
        newFormForm.addEventListener('submit', submitNewForm);
    }

    // Form filters
    formFilters.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const filter = e.target.dataset.formFilter;

            // Get current status filter
            const activeStatusBtn = document.querySelector('[data-form-status].active');
            const status = activeStatusBtn ? activeStatusBtn.dataset.formStatus : '';

            // Update active state
            formFilters.forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');

            // Load forms with filters
            loadForms({
                type: filter !== 'all' ? filter : undefined,
                status: status || undefined
            });
        });
    });

    // Status filters
    statusFilters.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const status = e.target.dataset.formStatus;

            // Get current form type filter
            const activeFilterBtn = document.querySelector('[data-form-filter].active');
            const filter = activeFilterBtn ? activeFilterBtn.dataset.formFilter : 'all';

            // Update active state
            statusFilters.forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');

            // Load forms with filters
            loadForms({
                type: filter !== 'all' ? filter : undefined,
                status: status || undefined
            });
        });
    });

    // Assign department form
    if (assignDepartmentForm) {
        assignDepartmentForm.addEventListener('submit', handleAssignDepartment);
    }
}

// Handle new form submission
async function submitNewForm(e) {
    e.preventDefault();

    const formData = {
        type: document.getElementById('formType').value,
        content: document.getElementById('formContent').value
    };

    const departmentId = document.getElementById('formDepartment').value;
    if (departmentId) {
        formData.department_id = parseInt(departmentId);
    }

    try {
        const result = await submitForm(formData);
        const modal = bootstrap.Modal.getInstance(document.getElementById('newFormModal'));
        modal.hide();

        // Reset form
        document.getElementById('formType').value = '';
        document.getElementById('formContent').value = '';
        document.getElementById('formDepartment').value = '';

        showToast('Form submitted successfully', 'success');
        loadForms(); // Reload forms
    } catch (error) {
        console.error('Error submitting form:', error);
        showToast(`Failed to submit form: ${error.message}`, 'error');
    }
}

// Load departments for dropdowns
async function loadDepartments() {
    // This function would call your API to get departments
    try {
        // Example: const departments = await getDepartments();
        const departments = [
            { id: 1, name: 'Academic Affairs' },
            { id: 2, name: 'Student Affairs' },
            { id: 3, name: 'Administration' }
        ];

        // Populate department dropdowns
        const departmentDropdowns = [
            document.getElementById('formDepartment'),
            document.getElementById('assignDepartment')
        ];

        departmentDropdowns.forEach(dropdown => {
            if (dropdown) {
                const options = departments.map(dept =>
                    `<option value="${dept.id}">${dept.name}</option>`
                ).join('');

                // Keep the first option and add the departments
                const firstOption = dropdown.innerHTML;
                dropdown.innerHTML = firstOption + options;
            }
        });
    } catch (error) {
        console.error('Error loading departments:', error);
    }
}

// View form details
async function viewFormDetails(formId) {
    const detailsModal = new bootstrap.Modal(document.getElementById('formDetailsModal'));
    detailsModal.show();

    const contentDiv = document.getElementById('formDetailsContent');
    const actionButtonsDiv = document.getElementById('formActionButtons');

    contentDiv.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div></div>';
    actionButtonsDiv.innerHTML = '';

    try {
        const form = await getFormById(formId);
        const formType = formTypes[form.type] || form.type;
        const statusClass = statusClasses[form.status] || 'bg-secondary';

        contentDiv.innerHTML = `
            <div class="card mb-3">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <span>${formType}</span>
                    <span class="badge ${statusClass}">${form.status}</span>
                </div>
                <div class="card-body">
                    <h6>Content:</h6>
                    <p>${form.content}</p>
                    <hr>
                    <div class="row">
                        <div class="col-md-6">
                            <p><strong>Submitted:</strong> ${formatDate(form.submission_date)}</p>
                        </div>
                        <div class="col-md-6">
                            <p><strong>Parent:</strong> ${form.parent ? form.parent.name : 'N/A'}</p>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <p><strong>Department:</strong> ${form.department ? form.department.name : 'Not assigned'}</p>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add action buttons based on user role and form status
        const currentUser = getCurrentUser();
        const isDepartment = currentUser.roles.includes('department');

        if (isDepartment) {
            if (form.status === 'pending' && !form.department_id) {
                actionButtonsDiv.innerHTML = `
                    <button class="btn btn-info" id="detailAssignBtn">Assign</button>
                    <button class="btn btn-success" id="detailProcessBtn">Process</button>
                `;

                document.getElementById('detailAssignBtn').addEventListener('click', () => {
                    detailsModal.hide();
                    openAssignModal(formId);
                });

                document.getElementById('detailProcessBtn').addEventListener('click', () => {
                    processForm(formId);
                    detailsModal.hide();
                });
            } else if (form.status === 'pending') {
                actionButtonsDiv.innerHTML = `
                    <button class="btn btn-success" id="detailProcessBtn">Process</button>
                `;

                document.getElementById('detailProcessBtn').addEventListener('click', () => {
                    processForm(formId);
                    detailsModal.hide();
                });
            } else if (form.status === 'processing') {
                actionButtonsDiv.innerHTML = `
                    <button class="btn btn-success" id="detailCompleteBtn">Mark Complete</button>
                `;

                document.getElementById('detailCompleteBtn').addEventListener('click', () => {
                    completeForm(formId);
                    detailsModal.hide();
                });
            }
        }
    } catch (error) {
        console.error('Error loading form details:', error);
        contentDiv.innerHTML = `<div class="alert alert-danger">Failed to load form details. ${error.message}</div>`;
    }
}

// Open assign department modal
function openAssignModal(formId) {
    document.getElementById('assignFormId').value = formId;
    const assignModal = new bootstrap.Modal(document.getElementById('assignDepartmentModal'));
    assignModal.show();
}

// Handle department assignment
async function handleAssignDepartment(e) {
    e.preventDefault();

    const formId = parseInt(document.getElementById('assignFormId').value);
    const departmentId = parseInt(document.getElementById('assignDepartment').value);

    if (!formId || !departmentId) {
        showToast('Invalid form or department selection', 'error');
        return;
    }

    try {
        await assignFormToDepartment(formId, departmentId);

        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('assignDepartmentModal'));
        modal.hide();

        // Reset form
        document.getElementById('assignDepartment').value = '';

        showToast('Form assigned successfully', 'success');
        loadForms(); // Reload forms
    } catch (error) {
        console.error('Error assigning form:', error);
        showToast(`Failed to assign form: ${error.message}`, 'error');
    }
}

// Process a form (change status to processing)
async function processForm(formId) {
    try {
        await updateFormStatus(formId, 'processing');
        showToast('Form status updated to processing', 'success');
        loadForms(); // Reload forms
    } catch (error) {
        console.error('Error processing form:', error);
        showToast(`Failed to update form status: ${error.message}`, 'error');
    }
}

// Complete a form (change status to completed)
async function completeForm(formId) {
    try {
        await updateFormStatus(formId, 'completed');
        showToast('Form marked as completed', 'success');
        loadForms(); // Reload forms
    } catch (error) {
        console.error('Error completing form:', error);
        showToast(`Failed to update form status: ${error.message}`, 'error');
    }
}