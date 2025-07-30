// Admin Dashboard JavaScript
class AdminDashboard {
    constructor() {
        this.apiBase = '/admin-dashboard/api/';
        this.currentPage = 'dashboard';
        this.refreshInterval = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadDashboardStats();
        this.startAutoRefresh();
        this.setupRealTimeUpdates();
        this.setupNavigation();
    }

    setupEventListeners() {
        // Search functionality
        const searchInput = document.querySelector('#searchInput');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce(this.handleSearch.bind(this), 300));
        }

        // User management actions
        document.querySelectorAll('.user-action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const action = btn.dataset.action;
                const userId = btn.dataset.userId;
                this.handleUserAction(action, userId);
            });
        });

        // Bulk actions
        const bulkActionForm = document.querySelector('#bulkActionForm');
        if (bulkActionForm) {
            bulkActionForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleBulkAction();
            });
        }

        // Notification actions
        document.querySelectorAll('.notification-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const notificationId = item.dataset.notificationId;
                this.markNotificationRead(notificationId);
            });
        });

        // System backup
        const backupForm = document.querySelector('#backupForm');
        if (backupForm) {
            backupForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.initiateBackup();
            });
        }

        // Settings form
        const settingsForm = document.querySelector('#settingsForm');
        if (settingsForm) {
            settingsForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveSettings();
            });
        }
    }

    async loadDashboardStats() {
        try {
            const response = await fetch(`${this.apiBase}stats/`);
            const data = await response.json();
            this.updateDashboardStats(data);
        } catch (error) {
            console.error('Error loading dashboard stats:', error);
            this.showToast('Error loading dashboard statistics', 'error');
        }
    }

    updateDashboardStats(stats) {
        // Update statistics cards
        const elements = {
            'totalUsers': stats.total_users,
            'activeUsers': stats.active_users,
            'totalFiles': stats.total_files,
            'totalSurveys': stats.total_surveys,
            'systemUptime': stats.system_uptime,
            'cpuUsage': `${stats.cpu_usage.toFixed(1)}%`,
            'memoryUsage': `${stats.memory_usage.toFixed(1)}%`,
            'diskUsage': `${stats.disk_usage.toFixed(1)}%`,
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });

        // Update activity feed
        this.updateActivityFeed(stats.recent_activities);

        // Update notifications count
        const notificationBadge = document.querySelector('.notification-badge');
        if (notificationBadge) {
            notificationBadge.textContent = stats.notifications_count;
        }
    }

    updateActivityFeed(activities) {
        const activityFeed = document.getElementById('activityFeed');
        if (!activityFeed) return;

        activityFeed.innerHTML = '';
        activities.forEach(activity => {
            const activityItem = this.createActivityItem(activity);
            activityFeed.appendChild(activityItem);
        });
    }

    createActivityItem(activity) {
        const item = document.createElement('div');
        item.className = 'activity-item';
        
        const iconClass = this.getActivityIconClass(activity.type);
        const timeAgo = this.getTimeAgo(activity.timestamp);
        
        item.innerHTML = `
            <div class="activity-icon ${iconClass}">
                <i class="fas ${this.getActivityIcon(activity.type)}"></i>
            </div>
            <div class="activity-content">
                <div class="activity-text">${activity.description}</div>
                <div class="activity-time">${timeAgo}</div>
            </div>
        `;
        
        return item;
    }

    getActivityIconClass(type) {
        const iconMap = {
            'user_created': 'user',
            'user_updated': 'user',
            'user_deleted': 'user',
            'file_uploaded': 'upload',
            'file_deleted': 'upload',
            'system_backup': 'system',
            'system_maintenance': 'system',
            'login': 'user',
            'logout': 'user',
            'error': 'system'
        };
        return iconMap[type] || 'system';
    }

    getActivityIcon(type) {
        const iconMap = {
            'user_created': 'fa-user-plus',
            'user_updated': 'fa-user-edit',
            'user_deleted': 'fa-user-times',
            'file_uploaded': 'fa-upload',
            'file_deleted': 'fa-trash',
            'system_backup': 'fa-database',
            'system_maintenance': 'fa-cog',
            'login': 'fa-sign-in-alt',
            'logout': 'fa-sign-out-alt',
            'error': 'fa-exclamation-triangle'
        };
        return iconMap[type] || 'fa-cog';
    }

    getTimeAgo(timestamp) {
        const now = new Date();
        const activityTime = new Date(timestamp);
        const diffMs = now - activityTime;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins} minutes ago`;
        if (diffHours < 24) return `${diffHours} hours ago`;
        return `${diffDays} days ago`;
    }

    async handleUserAction(action, userId) {
        try {
            const response = await fetch(`${this.apiBase}users/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    action: action,
                    user_ids: [parseInt(userId)]
                })
            });

            const data = await response.json();
            if (response.ok) {
                this.showToast(data.message, 'success');
                this.refreshCurrentPage();
            } else {
                this.showToast(data.error || 'Action failed', 'error');
            }
        } catch (error) {
            console.error('Error handling user action:', error);
            this.showToast('Error performing action', 'error');
        }
    }

    async handleBulkAction() {
        const form = document.getElementById('bulkActionForm');
        const formData = new FormData(form);
        const selectedUsers = Array.from(document.querySelectorAll('input[name="user_ids"]:checked'))
            .map(cb => parseInt(cb.value));
        
        if (selectedUsers.length === 0) {
            this.showToast('Please select users to perform bulk action', 'warning');
            return;
        }

        try {
            const response = await fetch(`${this.apiBase}users/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    action: formData.get('bulk_action'),
                    user_ids: selectedUsers
                })
            });

            const data = await response.json();
            if (response.ok) {
                this.showToast(data.message, 'success');
                this.refreshCurrentPage();
            } else {
                this.showToast(data.error || 'Bulk action failed', 'error');
            }
        } catch (error) {
            console.error('Error handling bulk action:', error);
            this.showToast('Error performing bulk action', 'error');
        }
    }

    async markNotificationRead(notificationId) {
        try {
            const response = await fetch(`${this.apiBase}notifications/${notificationId}/read/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (response.ok) {
                const notificationItem = document.querySelector(`[data-notification-id="${notificationId}"]`);
                if (notificationItem) {
                    notificationItem.classList.add('read');
                }
                this.loadDashboardStats(); // Refresh notification count
            }
        } catch (error) {
            console.error('Error marking notification as read:', error);
        }
    }

    async initiateBackup() {
        const form = document.getElementById('backupForm');
        const formData = new FormData(form);
        
        try {
            const response = await fetch(`${this.apiBase}backup/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    backup_type: formData.get('backup_type'),
                    include_media: formData.get('include_media') === 'on',
                    include_database: formData.get('include_database') === 'on',
                    description: formData.get('description')
                })
            });

            const data = await response.json();
            if (response.ok) {
                this.showToast('Backup initiated successfully', 'success');
                this.refreshBackupLogs();
            } else {
                this.showToast(data.error || 'Backup failed', 'error');
            }
        } catch (error) {
            console.error('Error initiating backup:', error);
            this.showToast('Error initiating backup', 'error');
        }
    }

    async saveSettings() {
        const form = document.getElementById('settingsForm');
        const formData = new FormData(form);
        
        try {
            const response = await fetch('/admin-dashboard/settings/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: formData
            });

            if (response.ok) {
                this.showToast('Settings saved successfully', 'success');
            } else {
                this.showToast('Error saving settings', 'error');
            }
        } catch (error) {
            console.error('Error saving settings:', error);
            this.showToast('Error saving settings', 'error');
        }
    }

    async handleSearch(event) {
        const searchTerm = event.target.value;
        const currentPage = this.getCurrentPage();
        
        if (currentPage === 'users') {
            await this.searchUsers(searchTerm);
        } else if (currentPage === 'surveys') {
            await this.searchSurveys(searchTerm);
        }
    }

    async searchUsers(searchTerm) {
        try {
            const response = await fetch(`${this.apiBase}users/?search=${encodeURIComponent(searchTerm)}`);
            const data = await response.json();
            this.updateUsersTable(data.users);
        } catch (error) {
            console.error('Error searching users:', error);
        }
    }

    async searchSurveys(searchTerm) {
        // Implement survey search functionality
        console.log('Searching surveys:', searchTerm);
    }

    updateUsersTable(users) {
        const tbody = document.querySelector('#usersTable tbody');
        if (!tbody) return;

        tbody.innerHTML = '';
        users.forEach(user => {
            const row = this.createUserRow(user);
            tbody.appendChild(row);
        });
    }

    createUserRow(user) {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><input type="checkbox" name="user_ids" value="${user.id}"></td>
            <td>${user.email}</td>
            <td>${user.full_name || 'N/A'}</td>
            <td>${user.is_staff ? 'Admin' : 'User'}</td>
            <td>${user.is_active ? 'Active' : 'Inactive'}</td>
            <td>${user.last_login_formatted}</td>
            <td>
                <button class="btn btn-sm btn-primary user-action-btn" data-action="activate" data-user-id="${user.id}">
                    <i class="fas fa-check"></i>
                </button>
                <button class="btn btn-sm btn-warning user-action-btn" data-action="deactivate" data-user-id="${user.id}">
                    <i class="fas fa-ban"></i>
                </button>
                <button class="btn btn-sm btn-danger user-action-btn" data-action="delete" data-user-id="${user.id}">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        return row;
    }

    setupNavigation() {
        // Set up navigation between admin pages
        const currentPath = window.location.pathname;
        const page = currentPath.split('/').pop().replace('.html', '') || 'dashboard';
        this.currentPage = page;
        
        // Update active navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[href="${page}.html"]`)?.classList.add('active');
    }

    // Navigation is now handled by Django URLs directly

    async loadPageContent(page) {
        try {
            const response = await fetch(`/admin-dashboard/${page}/`);
            const html = await response.text();
            
            // Update main content area
            const mainContent = document.getElementById('mainContent');
            if (mainContent) {
                mainContent.innerHTML = html;
            }
            
            // Reinitialize page-specific functionality
            this.initializePageSpecificFeatures(page);
        } catch (error) {
            console.error('Error loading page:', error);
        }
    }

    initializePageSpecificFeatures(page) {
        switch (page) {
            case 'dashboard':
                this.loadDashboardStats();
                break;
            case 'users':
                this.loadUsers();
                break;
            case 'surveys':
                this.loadSurveys();
                break;
            case 'system':
                this.loadSystemMetrics();
                break;
            case 'settings':
                this.loadSettings();
                break;
            case 'profile':
                this.loadProfile();
                break;
        }
    }

    async loadUsers() {
        try {
            const response = await fetch(`${this.apiBase}users/`);
            const data = await response.json();
            this.updateUsersTable(data.users);
        } catch (error) {
            console.error('Error loading users:', error);
        }
    }

    async loadSurveys() {
        // Implement survey loading
        console.log('Loading surveys...');
    }

    async loadSystemMetrics() {
        try {
            const response = await fetch(`${this.apiBase}metrics/`);
            const data = await response.json();
            this.updateSystemMetrics(data);
        } catch (error) {
            console.error('Error loading system metrics:', error);
        }
    }

    updateSystemMetrics(metrics) {
        // Update system metrics charts and displays
        console.log('Updating system metrics:', metrics);
    }

    async loadSettings() {
        // Implement settings loading
        console.log('Loading settings...');
    }

    async loadProfile() {
        // Implement profile loading
        console.log('Loading profile...');
    }

    startAutoRefresh() {
        // Refresh dashboard stats every 30 seconds
        this.refreshInterval = setInterval(() => {
            if (this.currentPage === 'dashboard') {
                this.loadDashboardStats();
            }
        }, 30000);
    }

    setupRealTimeUpdates() {
        // Setup WebSocket or polling for real-time updates
        console.log('Setting up real-time updates...');
    }

    refreshCurrentPage() {
        this.initializePageSpecificFeatures(this.currentPage);
    }

    getCurrentPage() {
        return this.currentPage;
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <i class="fas fa-${this.getToastIcon(type)}"></i>
            <span>${message}</span>
        `;
        
        const container = document.getElementById('toastContainer') || document.body;
        container.appendChild(toast);
        
        // Show toast
        setTimeout(() => toast.classList.add('show'), 100);
        
        // Hide and remove toast
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    getToastIcon(type) {
        const iconMap = {
            'success': 'check',
            'error': 'times',
            'warning': 'exclamation-triangle',
            'info': 'info'
        };
        return iconMap[type] || 'info';
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// Initialize admin dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.adminDashboard = new AdminDashboard();
});

// Export for use in other scripts
window.AdminDashboard = AdminDashboard; 