// Admin Dashboard JavaScript

class AdminDashboard {
    constructor() {
        this.currentOrderId = null;
        this.orders = [];
        this.stats = {};
        this.isLoading = false;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadInitialData();
        this.startAutoRefresh();
    }
    
    setupEventListeners() {
        // Sidebar navigation
        document.addEventListener('click', (e) => {
            if (e.target.matches('.nav-link')) {
                e.preventDefault();
                const section = e.target.dataset.section;
                this.showSection(section);
                this.setActiveNavItem(e.target);
            }
        });
        
        // Sidebar toggle
        const sidebarToggle = document.getElementById('sidebarToggle');
        const mobileMenuToggle = document.getElementById('mobileMenuToggle');
        const sidebar = document.getElementById('sidebar');
        
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => {
                sidebar.classList.toggle('collapsed');
                localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
            });
        }
        
        if (mobileMenuToggle) {
            mobileMenuToggle.addEventListener('click', () => {
                sidebar.classList.toggle('mobile-open');
            });
        }
        
        // Restore sidebar state
        const sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
        if (sidebarCollapsed) {
            sidebar.classList.add('collapsed');
        }
        
        // Admin dropdown
        const adminMenuToggle = document.getElementById('adminMenuToggle');
        const adminMenu = document.getElementById('adminMenu');
        
        if (adminMenuToggle && adminMenu) {
            adminMenuToggle.addEventListener('click', (e) => {
                e.stopPropagation();
                adminMenuToggle.parentElement.classList.toggle('active');
            });
            
            document.addEventListener('click', () => {
                adminMenuToggle.parentElement.classList.remove('active');
            });
        }
        
        // Refresh button
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshData();
            });
        }
        
        // Search functionality
        const orderSearch = document.getElementById('orderSearch');
        if (orderSearch) {
            orderSearch.addEventListener('input', (e) => {
                this.filterOrders(e.target.value);
            });
        }
        
        // Status filter
        const statusFilter = document.getElementById('statusFilter');
        if (statusFilter) {
            statusFilter.addEventListener('change', (e) => {
                this.filterOrdersByStatus(e.target.value);
            });
        }
        
        // Modal close handlers
        document.addEventListener('click', (e) => {
            if (e.target.matches('.modal-close') || e.target.matches('.modal')) {
                const modal = e.target.closest('.modal');
                if (modal && e.target === modal) {
                    this.closeModal(modal.id);
                }
            }
        });
        
        // File upload handlers
        this.setupFileUpload();
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeAllModals();
            }
            if (e.ctrlKey && e.key === 'r') {
                e.preventDefault();
                this.refreshData();
            }
        });
    }
    
    async loadInitialData() {
        this.showLoading(true);
        
        try {
            await Promise.all([
                this.loadDashboardStats(),
                this.loadOrders(),
                this.loadRecentActivity()
            ]);
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showToast('Error loading data', 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    async loadDashboardStats() {
        try {
            const response = await api.get('/dashboard/stats');
            this.stats = response.data;
            this.updateStatsDisplay();
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }
    
    async loadOrders() {
        try {
            const response = await api.get('/orders');
            // Handle both direct array and {success: true, data: []} response formats
            this.orders = Array.isArray(response) ? response : (response.data || []);
            this.renderOrdersTable();
            this.updatePendingOrdersBadge();
        } catch (error) {
            console.error('Error loading orders:', error);
            this.orders = []; // Fallback to empty array
        }
    }
    
    async loadRecentActivity() {
        try {
            const response = await api.get('/dashboard/activity');
            // Handle both direct array and {success: true, data: []} response formats
            const activities = Array.isArray(response) ? response : (response.data || []);
            this.renderRecentActivity(activities);
        } catch (error) {
            console.error('Error loading activity:', error);
            this.renderRecentActivity([]); // Fallback to empty array
        }
    }
    
    updateStatsDisplay() {
        const elements = {
            totalOrders: document.getElementById('totalOrders'),
            pendingOrders: document.getElementById('pendingOrders'),
            inProgressOrders: document.getElementById('inProgressOrders'),
            completedOrders: document.getElementById('completedOrders'),
            totalRevenue: document.getElementById('totalRevenue')
        };
        
        if (elements.totalOrders) elements.totalOrders.textContent = this.stats.total_orders || 0;
        if (elements.pendingOrders) elements.pendingOrders.textContent = this.stats.pending_orders || 0;
        if (elements.inProgressOrders) elements.inProgressOrders.textContent = this.stats.in_progress_orders || 0;
        if (elements.completedOrders) elements.completedOrders.textContent = this.stats.completed_orders || 0;
        if (elements.totalRevenue) elements.totalRevenue.textContent = this.formatCurrency(this.stats.total_revenue || 0);
    }
    
    updatePendingOrdersBadge() {
        const badge = document.getElementById('pendingOrdersBadge');
        if (badge) {
            const pendingCount = this.orders.filter(order => order.status === 'pending').length;
            badge.textContent = pendingCount;
            badge.style.display = pendingCount > 0 ? 'block' : 'none';
        }
    }
    
    renderOrdersTable() {
        const tbody = document.getElementById('ordersTableBody');
        const noOrders = document.getElementById('noOrders');
        
        if (!tbody) return;
        
        if (this.orders.length === 0) {
            tbody.innerHTML = '';
            if (noOrders) noOrders.style.display = 'block';
            return;
        }
        
        if (noOrders) noOrders.style.display = 'none';
        
        tbody.innerHTML = this.orders.map(order => `
            <tr>
                <td>
                    <div class="font-weight-bold">${order.order_number}</div>
                    <div class="text-muted small">${this.formatDate(order.created_at)}</div>
                </td>
                <td>
                    <div class="font-weight-bold">${order.user?.full_name || 'N/A'}</div>
                    <div class="text-muted small">${order.user?.email || ''}</div>
                </td>
                <td>
                    <div class="font-weight-bold">${this.formatServiceType(order.service_type)}</div>
                    <div class="text-muted small">${order.subject}</div>
                </td>
                <td>
                    <div class="font-weight-bold">${this.formatCurrency(order.total_price, order.currency)}</div>
                    <div class="text-muted small">${order.payment_method}</div>
                </td>
                <td>
                    <span class="status-badge ${order.payment_status}">${this.formatStatus(order.payment_status)}</span>
                </td>
                <td>
                    <span class="status-badge ${order.status}">${this.formatStatus(order.status)}</span>
                </td>
                <td>
                    <div class="small">${this.formatDate(order.created_at)}</div>
                    ${order.deadline ? `<div class="text-muted small">Due: ${this.formatDate(order.deadline)}</div>` : ''}
                </td>
                <td>
                    <div class="action-buttons">
                        <button class="btn btn-sm btn-info" onclick="adminDashboard.viewOrder(${order.id})">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-sm btn-primary" onclick="adminDashboard.manageOrder(${order.id})">
                            <i class="fas fa-cog"></i>
                        </button>
                        <button class="btn btn-sm btn-success" onclick="adminDashboard.contactCustomer(${order.id})">
                            <i class="fas fa-envelope"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }
    
    renderRecentActivity(activities) {
        const container = document.getElementById('recentActivity');
        if (!container) return;
        
        if (!activities || activities.length === 0) {
            container.innerHTML = '<div class="empty-state"><p>No recent activity</p></div>';
            return;
        }
        
        container.innerHTML = activities.map(activity => `
            <div class="activity-item">
                <div class="activity-icon">
                    <i class="fas ${this.getActivityIcon(activity.type)}"></i>
                </div>
                <div class="activity-content">
                    <div class="activity-title">${activity.title}</div>
                    <div class="activity-description">${activity.description}</div>
                </div>
                <div class="activity-time">${this.formatTimeAgo(activity.created_at)}</div>
            </div>
        `).join('');
    }
    
    showSection(sectionName) {
        // Hide all sections
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });
        
        // Show target section
        const targetSection = document.getElementById(`${sectionName}Section`);
        if (targetSection) {
            targetSection.classList.add('active');
        }
        
        // Update page title
        const pageTitle = document.getElementById('pageTitle');
        if (pageTitle) {
            pageTitle.textContent = this.formatSectionTitle(sectionName);
        }
        
        // Load section-specific data
        this.loadSectionData(sectionName);
    }
    
    setActiveNavItem(clickedLink) {
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        clickedLink.closest('.nav-item').classList.add('active');
    }
    
    async loadSectionData(sectionName) {
        switch (sectionName) {
            case 'dashboard':
                await this.loadDashboardStats();
                await this.loadRecentActivity();
                break;
            case 'orders':
                await this.loadOrders();
                break;
            // Add other sections as needed
        }
    }
    
    async viewOrder(orderId) {
        try {
            this.currentOrderId = orderId;
            const response = await api.get(`/orders/${orderId}`);
            const order = response.data;
            
            this.renderOrderDetails(order);
            this.showModal('orderModal');
        } catch (error) {
            console.error('Error loading order details:', error);
            this.showToast('Error loading order details', 'error');
        }
    }
    
    renderOrderDetails(order) {
        const content = document.getElementById('orderModalContent');
        if (!content) return;
        
        content.innerHTML = `
            <div class="order-details">
                <div class="row">
                    <div class="col-md-6">
                        <h4>Order Information</h4>
                        <table class="table table-borderless">
                            <tr><td><strong>Order Number:</strong></td><td>${order.order_number}</td></tr>
                            <tr><td><strong>Service Type:</strong></td><td>${this.formatServiceType(order.service_type)}</td></tr>
                            <tr><td><strong>Subject:</strong></td><td>${order.subject}</td></tr>
                            <tr><td><strong>Academic Level:</strong></td><td>${this.formatAcademicLevel(order.academic_level)}</td></tr>
                            <tr><td><strong>Deadline:</strong></td><td>${this.formatDate(order.deadline)}</td></tr>
                            <tr><td><strong>Status:</strong></td><td><span class="status-badge ${order.status}">${this.formatStatus(order.status)}</span></td></tr>
                        </table>
                    </div>
                    <div class="col-md-6">
                        <h4>Customer Information</h4>
                        <table class="table table-borderless">
                            <tr><td><strong>Name:</strong></td><td>${order.user?.full_name || 'N/A'}</td></tr>
                            <tr><td><strong>Email:</strong></td><td>${order.user?.email || 'N/A'}</td></tr>
                            <tr><td><strong>Student ID:</strong></td><td>${order.user?.student_id || 'N/A'}</td></tr>
                            <tr><td><strong>Language:</strong></td><td>${order.user?.language || 'en'}</td></tr>
                            <tr><td><strong>Country:</strong></td><td>${order.user?.country || 'N/A'}</td></tr>
                        </table>
                    </div>
                </div>
                
                <div class="row mt-4">
                    <div class="col-md-6">
                        <h4>Payment Information</h4>
                        <table class="table table-borderless">
                            <tr><td><strong>Total Price:</strong></td><td>${this.formatCurrency(order.total_price, order.currency)}</td></tr>
                            <tr><td><strong>Payment Method:</strong></td><td>${order.payment_method}</td></tr>
                            <tr><td><strong>Payment Status:</strong></td><td><span class="status-badge ${order.payment_status}">${this.formatStatus(order.payment_status)}</span></td></tr>
                            <tr><td><strong>Created:</strong></td><td>${this.formatDate(order.created_at)}</td></tr>
                            ${order.paid_at ? `<tr><td><strong>Paid:</strong></td><td>${this.formatDate(order.paid_at)}</td></tr>` : ''}
                        </table>
                    </div>
                    <div class="col-md-6">
                        <h4>Requirements</h4>
                        <div class="requirements-text">
                            ${order.requirements || 'No requirements specified'}
                        </div>
                        ${order.special_notes ? `
                            <h5 class="mt-3">Special Notes</h5>
                            <div class="special-notes">
                                ${order.special_notes}
                            </div>
                        ` : ''}
                    </div>
                </div>
                
                ${order.requirement_files && order.requirement_files.length > 0 ? `
                    <div class="row mt-4">
                        <div class="col-12">
                            <h4>Requirement Files</h4>
                            <div class="file-list">
                                ${order.requirement_files.map(file => `
                                    <div class="file-item">
                                        <div class="file-info">
                                            <div class="file-icon">
                                                <i class="fas fa-file"></i>
                                            </div>
                                            <div class="file-details">
                                                <div class="file-name">${file.name}</div>
                                                <div class="file-size">${this.formatFileSize(file.size)}</div>
                                            </div>
                                        </div>
                                        <a href="${file.url}" class="btn btn-sm btn-primary" download>
                                            <i class="fas fa-download"></i>
                                        </a>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                ` : ''}
                
                ${order.delivered_files && order.delivered_files.length > 0 ? `
                    <div class="row mt-4">
                        <div class="col-12">
                            <h4>Delivered Files</h4>
                            <div class="file-list">
                                ${order.delivered_files.map(file => `
                                    <div class="file-item">
                                        <div class="file-info">
                                            <div class="file-icon">
                                                <i class="fas fa-file-check"></i>
                                            </div>
                                            <div class="file-details">
                                                <div class="file-name">${file.name}</div>
                                                <div class="file-size">${this.formatFileSize(file.size)}</div>
                                            </div>
                                        </div>
                                        <a href="${file.url}" class="btn btn-sm btn-success" download>
                                            <i class="fas fa-download"></i>
                                        </a>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    manageOrder(orderId) {
        this.currentOrderId = orderId;
        const order = this.orders.find(o => o.id === orderId);
        
        if (order) {
            document.getElementById('orderStatus').value = order.status;
            document.getElementById('paymentStatus').value = order.payment_status;
        }
        
        this.showModal('statusModal');
    }
    
    contactCustomer(orderId) {
        this.currentOrderId = orderId;
        this.showModal('contactModal');
    }
    
    showUploadModal() {
        this.showModal('uploadModal');
    }
    
    showContactModal() {
        this.showModal('contactModal');
    }
    
    showStatusModal() {
        this.showModal('statusModal');
    }
    
    showResetModal() {
        this.showModal('resetModal');
    }
    
    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    }
    
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
    }
    
    closeAllModals() {
        document.querySelectorAll('.modal.active').forEach(modal => {
            modal.classList.remove('active');
        });
        document.body.style.overflow = '';
    }
    
    setupFileUpload() {
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('workFile');
        
        if (!uploadArea || !fileInput) return;
        
        uploadArea.addEventListener('click', () => fileInput.click());
        
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            
            const files = Array.from(e.dataTransfer.files);
            this.handleFileSelection(files);
        });
        
        fileInput.addEventListener('change', (e) => {
            const files = Array.from(e.target.files);
            this.handleFileSelection(files);
        });
    }
    
    handleFileSelection(files) {
        const fileList = document.getElementById('fileList');
        if (!fileList) return;
        
        fileList.innerHTML = files.map((file, index) => `
            <div class="file-item" data-index="${index}">
                <div class="file-info">
                    <div class="file-icon">
                        <i class="fas ${this.getFileIcon(file.name)}"></i>
                    </div>
                    <div class="file-details">
                        <div class="file-name">${file.name}</div>
                        <div class="file-size">${this.formatFileSize(file.size)}</div>
                    </div>
                </div>
                <button class="file-remove" onclick="adminDashboard.removeFile(${index})">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `).join('');
        
        this.selectedFiles = files;
    }
    
    removeFile(index) {
        if (this.selectedFiles) {
            this.selectedFiles = Array.from(this.selectedFiles).filter((_, i) => i !== index);
            this.handleFileSelection(this.selectedFiles);
        }
    }
    
    async uploadWork() {
        if (!this.currentOrderId || !this.selectedFiles || this.selectedFiles.length === 0) {
            this.showToast('Please select files to upload', 'warning');
            return;
        }
        
        try {
            const formData = new FormData();
            Array.from(this.selectedFiles).forEach(file => {
                formData.append('files', file);
            });
            
            await api.post(`/orders/${this.currentOrderId}/upload`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            
            this.showToast('Files uploaded successfully', 'success');
            this.closeModal('uploadModal');
            this.refreshData();
        } catch (error) {
            console.error('Error uploading files:', error);
            this.showToast('Error uploading files', 'error');
        }
    }
    
    async sendCustomerMessage() {
        const messageType = document.getElementById('messageType').value;
        const message = document.getElementById('customerMessage').value;
        
        if (!message.trim()) {
            this.showToast('Please enter a message', 'warning');
            return;
        }
        
        try {
            await api.post(`/orders/${this.currentOrderId}/contact`, {
                message_type: messageType,
                message: message
            });
            
            this.showToast('Message sent successfully', 'success');
            this.closeModal('contactModal');
            document.getElementById('customerMessage').value = '';
        } catch (error) {
            console.error('Error sending message:', error);
            this.showToast('Error sending message', 'error');
        }
    }
    
    async updateOrderStatus() {
        const orderStatus = document.getElementById('orderStatus').value;
        const paymentStatus = document.getElementById('paymentStatus').value;
        const adminNotes = document.getElementById('adminNotes').value;
        
        try {
            await api.put(`/orders/${this.currentOrderId}/status`, {
                order_status: orderStatus,
                payment_status: paymentStatus,
                admin_notes: adminNotes
            });
            
            this.showToast('Order updated successfully', 'success');
            this.closeModal('statusModal');
            this.refreshData();
        } catch (error) {
            console.error('Error updating order:', error);
            this.showToast('Error updating order', 'error');
        }
    }
    
    async deleteOrder() {
        if (!confirm('Are you sure you want to delete this order? This action cannot be undone.')) {
            return;
        }
        
        try {
            await api.delete(`/orders/${this.currentOrderId}`);
            this.showToast('Order deleted successfully', 'success');
            this.closeModal('statusModal');
            this.refreshData();
        } catch (error) {
            console.error('Error deleting order:', error);
            this.showToast('Error deleting order', 'error');
        }
    }
    
    async archiveOrder() {
        try {
            await api.put(`/orders/${this.currentOrderId}/archive`);
            this.showToast('Order archived successfully', 'success');
            this.closeModal('statusModal');
            this.refreshData();
        } catch (error) {
            console.error('Error archiving order:', error);
            this.showToast('Error archiving order', 'error');
        }
    }
    
    async resetDatabase() {
        const confirmation = document.getElementById('resetConfirmation').value;
        
        if (confirmation !== 'RESET_ALL_DATA') {
            this.showToast('Please type "RESET_ALL_DATA" to confirm', 'warning');
            return;
        }
        
        try {
            await api.post('/admin/reset-database');
            this.showToast('Database reset successfully', 'success');
            this.closeModal('resetModal');
            this.refreshData();
        } catch (error) {
            console.error('Error resetting database:', error);
            this.showToast('Error resetting database', 'error');
        }
    }
    
    filterOrders(searchTerm) {
        const filteredOrders = this.orders.filter(order => 
            order.order_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
            order.user?.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
            order.user?.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
            order.subject.toLowerCase().includes(searchTerm.toLowerCase())
        );
        
        this.renderFilteredOrders(filteredOrders);
    }
    
    filterOrdersByStatus(status) {
        const filteredOrders = status ? 
            this.orders.filter(order => order.status === status) : 
            this.orders;
        
        this.renderFilteredOrders(filteredOrders);
    }
    
    renderFilteredOrders(orders) {
        const originalOrders = this.orders;
        this.orders = orders;
        this.renderOrdersTable();
        this.orders = originalOrders;
    }
    
    async refreshData() {
        this.showLoading(true);
        await this.loadInitialData();
        this.showToast('Data refreshed', 'success');
    }
    
    startAutoRefresh() {
        setInterval(() => {
            if (!this.isLoading) {
                this.loadDashboardStats();
                this.loadOrders();
            }
        }, 30000); // Refresh every 30 seconds
    }
    
    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.toggle('active', show);
        }
        this.isLoading = show;
    }
    
    showToast(message, type = 'info', title = '') {
        const container = document.getElementById('toastContainer');
        if (!container) return;
        
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        toast.innerHTML = `
            <div class="toast-icon">
                <i class="fas ${this.getToastIcon(type)}"></i>
            </div>
            <div class="toast-content">
                ${title ? `<div class="toast-title">${title}</div>` : ''}
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        container.appendChild(toast);
        
        // Show toast
        setTimeout(() => toast.classList.add('show'), 100);
        
        // Auto remove
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => container.removeChild(toast), 300);
        }, 5000);
        
        // Manual close
        toast.querySelector('.toast-close').addEventListener('click', () => {
            toast.classList.remove('show');
            setTimeout(() => container.removeChild(toast), 300);
        });
    }
    
    // Utility methods
    formatCurrency(amount, currency = 'USD') {
        const symbols = { USD: '$', JOD: 'JD', AED: 'AED', SAR: 'SAR' };
        const symbol = symbols[currency] || currency;
        return `${symbol}${parseFloat(amount).toFixed(2)}`;
    }
    
    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
    
    formatTimeAgo(dateString) {
        const now = new Date();
        const date = new Date(dateString);
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        return `${diffDays}d ago`;
    }
    
    formatServiceType(type) {
        const types = {
            assignment: 'Assignment',
            project: 'Project',
            presentation: 'Presentation',
            redesign: 'Redesign',
            summary: 'Summary',
            express: 'Express Service'
        };
        return types[type] || type;
    }
    
    formatAcademicLevel(level) {
        const levels = {
            high_school: 'High School',
            bachelor: 'Bachelor',
            masters: 'Masters',
            phd: 'PhD'
        };
        return levels[level] || level;
    }
    
    formatStatus(status) {
        return status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
    
    formatSectionTitle(section) {
        const titles = {
            dashboard: 'Dashboard',
            orders: 'Orders Management',
            customers: 'Customers',
            payments: 'Payments',
            analytics: 'Analytics',
            settings: 'Settings'
        };
        return titles[section] || section;
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    getFileIcon(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        const icons = {
            pdf: 'fa-file-pdf',
            doc: 'fa-file-word',
            docx: 'fa-file-word',
            txt: 'fa-file-alt',
            jpg: 'fa-file-image',
            jpeg: 'fa-file-image',
            png: 'fa-file-image',
            zip: 'fa-file-archive',
            rar: 'fa-file-archive'
        };
        return icons[ext] || 'fa-file';
    }
    
    getActivityIcon(type) {
        const icons = {
            order_created: 'fa-plus',
            payment_confirmed: 'fa-credit-card',
            order_delivered: 'fa-check',
            message_sent: 'fa-envelope'
        };
        return icons[type] || 'fa-info';
    }
    
    getToastIcon(type) {
        const icons = {
            success: 'fa-check',
            error: 'fa-exclamation-triangle',
            warning: 'fa-exclamation',
            info: 'fa-info'
        };
        return icons[type] || 'fa-info';
    }
}

// Global functions for onclick handlers
window.showSection = (section) => adminDashboard.showSection(section);
window.exportData = () => console.log('Export data functionality');
window.showResetModal = () => adminDashboard.showResetModal();
window.closeModal = (modalId) => adminDashboard.closeModal(modalId);
window.showUploadModal = () => adminDashboard.showUploadModal();
window.showContactModal = () => adminDashboard.showContactModal();
window.showStatusModal = () => adminDashboard.showStatusModal();
window.uploadWork = () => adminDashboard.uploadWork();
window.sendCustomerMessage = () => adminDashboard.sendCustomerMessage();
window.updateOrderStatus = () => adminDashboard.updateOrderStatus();
window.deleteOrder = () => adminDashboard.deleteOrder();
window.archiveOrder = () => adminDashboard.archiveOrder();
window.resetDatabase = () => adminDashboard.resetDatabase();

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.adminDashboard = new AdminDashboard();
});
