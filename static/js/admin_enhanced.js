// Enhanced Admin Dashboard JavaScript with full functionality
class AdminDashboard {
    constructor() {
        this.currentOrderId = null;
        this.currentCustomerId = null;
        this.orders = [];
        this.customers = [];
        this.payments = [];
        this.stats = {};
        this.isLoading = false;
        this.currentSection = 'dashboard';
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadInitialData();
        this.startAutoRefresh();
        this.initializeDirhamFont();
    }
    
    initializeDirhamFont() {
        // Add the new UAE Dirham symbol font
        const style = document.createElement('style');
        style.textContent = `
            @font-face {
                font-family: 'UAESymbol';
                src: url('data:font/woff2;base64,') format('woff2');
            }
            .dirham-symbol {
                font-family: 'UAESymbol', sans-serif;
                font-weight: bold;
            }
        `;
        document.head.appendChild(style);
    }
    
    setupEventListeners() {
        // Sidebar navigation
        document.addEventListener('click', (e) => {
            if (e.target.matches('.nav-link') || e.target.closest('.nav-link')) {
                e.preventDefault();
                const navLink = e.target.matches('.nav-link') ? e.target : e.target.closest('.nav-link');
                const section = navLink.dataset.section;
                if (section) {
                    this.showSection(section);
                    this.setActiveNavItem(navLink);
                }
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
        
        // Refresh button
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshCurrentSection();
            });
        }
        
        // Search functionality
        const orderSearch = document.getElementById('orderSearch');
        if (orderSearch) {
            orderSearch.addEventListener('input', (e) => {
                this.searchOrders(e.target.value);
            });
        }
        
        const customerSearch = document.getElementById('customerSearch');
        if (customerSearch) {
            customerSearch.addEventListener('input', (e) => {
                this.searchCustomers(e.target.value);
            });
        }
        
        // Status filter
        const statusFilter = document.getElementById('statusFilter');
        if (statusFilter) {
            statusFilter.addEventListener('change', (e) => {
                this.filterOrdersByStatus(e.target.value);
            });
        }
        
        // Modal close buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('.modal-close') || e.target.closest('.modal-close')) {
                this.closeAllModals();
            }
            
            if (e.target.matches('.modal') && e.target.classList.contains('active')) {
                this.closeAllModals();
            }
        });
        
        // Quick action buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('[onclick]')) {
                e.preventDefault();
                const action = e.target.getAttribute('onclick');
                if (action.includes('showSection')) {
                    const section = action.match(/showSection\\('([^']+)'\\)/)?.[1];
                    if (section) this.showSection(section);
                }
            }
        });
        
        // Restore sidebar state
        const sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
        if (sidebarCollapsed && sidebar) {
            sidebar.classList.add('collapsed');
        }
    }
    
    async loadInitialData() {
        this.showLoading(true);
        
        try {
            await Promise.all([
                this.loadStats(),
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
    
    async loadStats() {
        try {
            const response = await api.get('/dashboard/stats');
            this.stats = response;
            this.updateStatsDisplay();
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }
    
    async loadOrders() {
        try {
            const response = await api.get('/orders');
            this.orders = Array.isArray(response) ? response : (response || []);
            this.renderOrdersTable();
            this.updatePendingOrdersBadge();
        } catch (error) {
            console.error('Error loading orders:', error);
            this.orders = [];
        }
    }
    
    async loadCustomers() {
        try {
            const response = await api.get('/customers');
            this.customers = Array.isArray(response) ? response : (response || []);
            this.renderCustomersTable();
        } catch (error) {
            console.error('Error loading customers:', error);
            this.customers = [];
        }
    }
    
    async loadPayments() {
        try {
            const response = await api.get('/payments');
            this.payments = Array.isArray(response) ? response : (response || []);
            this.renderPaymentsTable();
        } catch (error) {
            console.error('Error loading payments:', error);
            this.payments = [];
        }
    }
    
    async loadRecentActivity() {
        try {
            const response = await api.get('/dashboard/activity');
            const activities = Array.isArray(response) ? response : (response || []);
            this.renderRecentActivity(activities);
        } catch (error) {
            console.error('Error loading activity:', error);
            this.renderRecentActivity([]);
        }
    }
    
    showSection(sectionName) {
        // Hide all sections
        const sections = document.querySelectorAll('.content-section');
        sections.forEach(section => {
            section.classList.remove('active');
        });
        
        // Show target section
        const targetSection = document.getElementById(sectionName + 'Section');
        if (targetSection) {
            targetSection.classList.add('active');
            this.currentSection = sectionName;
            
            // Update page title
            const pageTitle = document.getElementById('pageTitle');
            if (pageTitle) {
                pageTitle.textContent = sectionName.charAt(0).toUpperCase() + sectionName.slice(1);
            }
            
            // Load section-specific data
            this.loadSectionData(sectionName);
        } else {
            console.error(`Section ${sectionName}Section not found`);
            this.showToast('Section not found', 'error');
        }
    }
    
    async loadSectionData(sectionName) {
        switch (sectionName) {
            case 'dashboard':
                await this.loadStats();
                await this.loadRecentActivity();
                break;
            case 'orders':
                await this.loadOrders();
                break;
            case 'customers':
                await this.loadCustomers();
                break;
            case 'payments':
                await this.loadPayments();
                break;
            case 'analytics':
                await this.loadAnalytics();
                break;
            case 'settings':
                await this.loadSettings();
                break;
        }
    }
    
    setActiveNavItem(activeLink) {
        // Remove active class from all nav items
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Add active class to parent nav item
        const navItem = activeLink.closest('.nav-item');
        if (navItem) {
            navItem.classList.add('active');
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
        if (elements.totalRevenue) {
            elements.totalRevenue.innerHTML = this.formatCurrency(this.stats.total_revenue || 0, this.stats.currency || 'AED');
        }
    }
    
    formatCurrency(amount, currency = 'AED') {
        if (currency === 'AED') {
            return `<span class="dirham-symbol">ê</span> ${amount.toLocaleString('en-AE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        } else if (currency === 'USD') {
            return `$${amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        } else {
            return `${currency} ${amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
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
                    <div class="text-muted small">${order.user?.email || 'N/A'}</div>
                </td>
                <td>
                    <div class="font-weight-bold">${order.service_type}</div>
                    <div class="text-muted small">${order.subject}</div>
                </td>
                <td>
                    <div class="font-weight-bold">${this.formatCurrency(order.total_price, order.currency)}</div>
                </td>
                <td>
                    <span class="badge badge-${this.getPaymentStatusColor(order.payment_status)}">
                        ${order.payment_status}
                    </span>
                </td>
                <td>
                    <span class="badge badge-${this.getStatusColor(order.status)}">
                        ${order.status}
                    </span>
                </td>
                <td>${this.formatDate(order.created_at)}</td>
                <td>
                    <div class="btn-group">
                        <button class="btn btn-sm btn-primary" onclick="dashboard.viewOrder(${order.id})">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-sm btn-success" onclick="dashboard.showUploadModal(${order.id})">
                            <i class="fas fa-upload"></i>
                        </button>
                        <button class="btn btn-sm btn-info" onclick="dashboard.showContactModal(${order.id})">
                            <i class="fas fa-envelope"></i>
                        </button>
                        <button class="btn btn-sm btn-warning" onclick="dashboard.showStatusModal(${order.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }
    
    renderCustomersTable() {
        const tbody = document.getElementById('customersTableBody');
        if (!tbody) return;
        
        if (this.customers.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center">No customers found</td></tr>';
            return;
        }
        
        tbody.innerHTML = this.customers.map(customer => `
            <tr>
                <td>
                    <div class="font-weight-bold">${customer.full_name}</div>
                    <div class="text-muted small">ID: ${customer.id}</div>
                </td>
                <td>
                    <div>${customer.email}</div>
                    <div class="text-muted small">${customer.phone || 'N/A'}</div>
                </td>
                <td>${customer.country || 'N/A'}</td>
                <td>${customer.total_orders}</td>
                <td>${this.formatCurrency(customer.total_spent)}</td>
                <td>
                    <span class="badge badge-${customer.status === 'active' ? 'success' : 'secondary'}">
                        ${customer.status}
                    </span>
                </td>
                <td>
                    <div class="btn-group">
                        <button class="btn btn-sm btn-primary" onclick="dashboard.viewCustomer(${customer.id})">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-sm btn-info" onclick="dashboard.contactCustomer(${customer.id})">
                            <i class="fas fa-envelope"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }
    
    renderPaymentsTable() {
        const tbody = document.getElementById('paymentsTableBody');
        if (!tbody) return;
        
        if (this.payments.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">No payments found</td></tr>';
            return;
        }
        
        tbody.innerHTML = this.payments.map(payment => `
            <tr>
                <td>
                    <div class="font-weight-bold">#${payment.id}</div>
                    <div class="text-muted small">${payment.transaction_id}</div>
                </td>
                <td>
                    <div class="font-weight-bold">Order #${payment.order_id}</div>
                    <div class="text-muted small">${payment.customer}</div>
                </td>
                <td>${this.formatCurrency(payment.amount, payment.currency)}</td>
                <td>${payment.payment_method}</td>
                <td>
                    <span class="badge badge-${this.getPaymentStatusColor(payment.status)}">
                        ${payment.status}
                    </span>
                </td>
                <td>${this.formatDate(payment.created_at)}</td>
            </tr>
        `).join('');
    }
    
    renderRecentActivity(activities) {
        const container = document.getElementById('recentActivity');
        if (!container) return;
        
        if (activities.length === 0) {
            container.innerHTML = '<div class="text-center text-muted">No recent activity</div>';
            return;
        }
        
        container.innerHTML = activities.map(activity => `
            <div class="activity-item">
                <div class="activity-icon">
                    <i class="fas fa-shopping-cart"></i>
                </div>
                <div class="activity-content">
                    <div class="activity-title">${activity.title}</div>
                    <div class="activity-description">${activity.description}</div>
                    <div class="activity-time">${this.formatDate(activity.created_at)}</div>
                </div>
                ${activity.amount ? `<div class="activity-amount">${activity.amount}</div>` : ''}
            </div>
        `).join('');
    }
    
    async loadAnalytics() {
        try {
            const [revenueData, orderData] = await Promise.all([
                api.get('/analytics/revenue'),
                api.get('/analytics/orders')
            ]);
            
            this.renderRevenueChart(revenueData);
            this.renderOrdersChart(orderData);
        } catch (error) {
            console.error('Error loading analytics:', error);
        }
    }
    
    renderRevenueChart(data) {
        const ctx = document.getElementById('revenueChart');
        if (!ctx) return;
        
        // Simple chart implementation (you can replace with Chart.js)
        const chartContainer = ctx.parentElement;
        chartContainer.innerHTML = `
            <div class="chart-placeholder">
                <h4>Revenue Analytics</h4>
                <p>Total Revenue: ${this.formatCurrency(data.total, data.currency)}</p>
                <div class="chart-bars">
                    ${data.data.map((value, index) => `
                        <div class="chart-bar" style="height: ${(value / Math.max(...data.data)) * 100}%">
                            <span class="chart-label">${data.labels[index]}</span>
                            <span class="chart-value">${this.formatCurrency(value, data.currency)}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    renderOrdersChart(data) {
        const ctx = document.getElementById('ordersChart');
        if (!ctx) return;
        
        const chartContainer = ctx.parentElement;
        chartContainer.innerHTML = `
            <div class="chart-placeholder">
                <h4>Orders by Status</h4>
                <div class="status-stats">
                    ${Object.entries(data.status_distribution).map(([status, count]) => `
                        <div class="status-stat">
                            <span class="badge badge-${this.getStatusColor(status)}">${status}</span>
                            <span class="count">${count}</span>
                        </div>
                    `).join('')}
                </div>
                <h4>Orders by Service Type</h4>
                <div class="service-stats">
                    ${Object.entries(data.service_distribution).map(([service, count]) => `
                        <div class="service-stat">
                            <span class="service-name">${service}</span>
                            <span class="count">${count}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    async loadSettings() {
        try {
            const settings = await api.get('/settings');
            this.renderSettingsForm(settings);
        } catch (error) {
            console.error('Error loading settings:', error);
        }
    }
    
    renderSettingsForm(settings) {
        const container = document.getElementById('settingsForm');
        if (!container) return;
        
        container.innerHTML = `
            <form id="settingsUpdateForm">
                <div class="form-group">
                    <label for="currency">Default Currency</label>
                    <select id="currency" name="currency" class="form-control">
                        <option value="AED" ${settings.currency === 'AED' ? 'selected' : ''}>UAE Dirham (AED)</option>
                        <option value="USD" ${settings.currency === 'USD' ? 'selected' : ''}>US Dollar (USD)</option>
                        <option value="SAR" ${settings.currency === 'SAR' ? 'selected' : ''}>Saudi Riyal (SAR)</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="timezone">Timezone</label>
                    <select id="timezone" name="timezone" class="form-control">
                        <option value="Asia/Dubai" ${settings.timezone === 'Asia/Dubai' ? 'selected' : ''}>Asia/Dubai</option>
                        <option value="UTC" ${settings.timezone === 'UTC' ? 'selected' : ''}>UTC</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="language">Default Language</label>
                    <select id="language" name="language" class="form-control">
                        <option value="en" ${settings.language === 'en' ? 'selected' : ''}>English</option>
                        <option value="ar" ${settings.language === 'ar' ? 'selected' : ''}>Arabic</option>
                    </select>
                </div>
                <div class="form-group">
                    <div class="form-check">
                        <input type="checkbox" id="notifications_enabled" name="notifications_enabled" class="form-check-input" ${settings.notifications_enabled ? 'checked' : ''}>
                        <label for="notifications_enabled" class="form-check-label">Enable Notifications</label>
                    </div>
                </div>
                <div class="form-group">
                    <label for="auto_archive_days">Auto Archive Orders (days)</label>
                    <input type="number" id="auto_archive_days" name="auto_archive_days" class="form-control" value="${settings.auto_archive_days}">
                </div>
                <button type="submit" class="btn btn-primary">Save Settings</button>
            </form>
        `;
        
        // Add form submit handler
        document.getElementById('settingsUpdateForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.updateSettings(new FormData(e.target));
        });
    }
    
    // Modal functions
    async viewOrder(orderId) {
        try {
            const order = await api.get(`/orders/${orderId}`);
            this.showOrderModal(order);
        } catch (error) {
            console.error('Error loading order:', error);
            this.showToast('Error loading order details', 'error');
        }
    }
    
    showOrderModal(order) {
        const modal = document.getElementById('orderModal');
        const content = document.getElementById('orderModalContent');
        
        if (!modal || !content) return;
        
        content.innerHTML = `
            <div class="order-details">
                <h4>Order #${order.order_number}</h4>
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>Customer:</strong> ${order.user?.full_name || 'N/A'}</p>
                        <p><strong>Email:</strong> ${order.user?.email || 'N/A'}</p>
                        <p><strong>Service:</strong> ${order.service_type}</p>
                        <p><strong>Subject:</strong> ${order.subject}</p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>Amount:</strong> ${this.formatCurrency(order.total_price, order.currency)}</p>
                        <p><strong>Status:</strong> <span class="badge badge-${this.getStatusColor(order.status)}">${order.status}</span></p>
                        <p><strong>Payment:</strong> <span class="badge badge-${this.getPaymentStatusColor(order.payment_status)}">${order.payment_status}</span></p>
                        <p><strong>Deadline:</strong> ${order.deadline ? this.formatDate(order.deadline) : 'N/A'}</p>
                    </div>
                </div>
                <div class="mt-3">
                    <h5>Requirements</h5>
                    <p>${order.requirements || 'No requirements specified'}</p>
                </div>
                ${order.requirement_files && order.requirement_files.length > 0 ? `
                    <div class="mt-3">
                        <h5>Requirement Files</h5>
                        <ul class="list-unstyled">
                            ${order.requirement_files.map(file => `
                                <li><a href="${file.url}" target="_blank">${file.name}</a></li>
                            `).join('')}
                        </ul>
                    </div>
                ` : ''}
                ${order.delivered_files && order.delivered_files.length > 0 ? `
                    <div class="mt-3">
                        <h5>Delivered Files</h5>
                        <ul class="list-unstyled">
                            ${order.delivered_files.map(file => `
                                <li><a href="${file.url}" target="_blank">${file.name}</a></li>
                            `).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;
        
        this.currentOrderId = order.id;
        modal.classList.add('active');
    }
    
    showUploadModal(orderId) {
        this.currentOrderId = orderId;
        const modal = document.getElementById('uploadModal');
        if (modal) {
            modal.classList.add('active');
        }
    }
    
    showContactModal(orderId) {
        this.currentOrderId = orderId;
        const modal = document.getElementById('contactModal');
        if (modal) {
            modal.classList.add('active');
        }
    }
    
    showStatusModal(orderId) {
        this.currentOrderId = orderId;
        const modal = document.getElementById('statusModal');
        if (modal) {
            modal.classList.add('active');
        }
    }
    
    closeAllModals() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.remove('active');
        });
    }
    
    // Utility functions
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
    
    getStatusColor(status) {
        const colors = {
            'pending': 'warning',
            'paid': 'info',
            'in_progress': 'primary',
            'delivered': 'success',
            'completed': 'success',
            'cancelled': 'danger',
            'archived': 'secondary'
        };
        return colors[status] || 'secondary';
    }
    
    getPaymentStatusColor(status) {
        const colors = {
            'pending': 'warning',
            'confirmed': 'success',
            'failed': 'danger',
            'refunded': 'info'
        };
        return colors[status] || 'secondary';
    }
    
    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.style.display = show ? 'flex' : 'none';
        }
        this.isLoading = show;
    }
    
    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        if (!container) return;
        
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'times' : 'info'}-circle"></i>
                <span>${message}</span>
            </div>
            <button class="toast-close">&times;</button>
        `;
        
        container.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            toast.remove();
        }, 5000);
        
        // Close button
        toast.querySelector('.toast-close').addEventListener('click', () => {
            toast.remove();
        });
    }
    
    updatePendingOrdersBadge() {
        const badge = document.getElementById('pendingOrdersBadge');
        if (badge) {
            const pendingCount = this.orders.filter(order => order.status === 'pending').length;
            badge.textContent = pendingCount;
        }
    }
    
    searchOrders(query) {
        const filteredOrders = this.orders.filter(order => 
            order.order_number.toLowerCase().includes(query.toLowerCase()) ||
            order.subject.toLowerCase().includes(query.toLowerCase()) ||
            order.user?.full_name?.toLowerCase().includes(query.toLowerCase()) ||
            order.user?.email?.toLowerCase().includes(query.toLowerCase())
        );
        
        this.renderFilteredOrders(filteredOrders);
    }
    
    searchCustomers(query) {
        const filteredCustomers = this.customers.filter(customer => 
            customer.full_name.toLowerCase().includes(query.toLowerCase()) ||
            customer.email.toLowerCase().includes(query.toLowerCase()) ||
            customer.phone?.toLowerCase().includes(query.toLowerCase())
        );
        
        this.renderFilteredCustomers(filteredCustomers);
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
    
    renderFilteredCustomers(customers) {
        const originalCustomers = this.customers;
        this.customers = customers;
        this.renderCustomersTable();
        this.customers = originalCustomers;
    }
    
    refreshCurrentSection() {
        this.loadSectionData(this.currentSection);
        this.showToast('Data refreshed', 'success');
    }
    
    startAutoRefresh() {
        setInterval(() => {
            if (!this.isLoading && this.currentSection === 'dashboard') {
                this.loadStats();
            }
        }, 30000); // Refresh every 30 seconds
    }
    
    async updateSettings(formData) {
        try {
            await api.put('/settings', formData);
            this.showToast('Settings updated successfully', 'success');
        } catch (error) {
            console.error('Error updating settings:', error);
            this.showToast('Error updating settings', 'error');
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new AdminDashboard();
});

// Global functions for onclick handlers
function showSection(section) {
    if (window.dashboard) {
        window.dashboard.showSection(section);
    }
}

function exportData() {
    // Implement data export functionality
    console.log('Export data functionality');
}

function showResetModal() {
    const modal = document.getElementById('resetModal');
    if (modal) {
        modal.classList.add('active');
    }
}

function resetDatabase() {
    const confirmation = document.getElementById('resetConfirmation').value;
    if (confirmation === 'RESET_ALL_DATA') {
        // Implement database reset
        console.log('Reset database functionality');
    } else {
        alert('Please type "RESET_ALL_DATA" to confirm');
    }
}
