/**
 * Live Admin Panel JavaScript - Connected to Real Database
 */

class LiveAdminDashboard {
    constructor() {
        this.API_BASE = window.location.origin;
        this.currentSection = 'dashboard';
        this.currentOrderId = null;
        this.refreshInterval = null;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadDashboard();
        this.startAutoRefresh();
    }
    
    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const section = item.getAttribute('data-section');
                this.showSection(section);
            });
        });
        
        // Refresh button
        document.getElementById('refreshBtn')?.addEventListener('click', () => {
            this.refreshCurrentSection();
        });
        
        // Search functionality
        document.addEventListener('input', (e) => {
            if (e.target.matches('[data-search]')) {
                this.handleSearch(e.target);
            }
        });
        
        // Filter functionality
        document.addEventListener('change', (e) => {
            if (e.target.matches('[data-filter]')) {
                this.handleFilter(e.target);
            }
        });
    }
    
    async apiCall(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.API_BASE}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'API call failed');
            }
            
            return data.data;
        } catch (error) {
            console.error('API Error:', error);
            this.showToast('Error: ' + error.message, 'error');
            throw error;
        }
    }
    
    async loadDashboard() {
        try {
            this.showLoading(true);
            
            // Load all dashboard data
            const [statsResponse, activityResponse] = await Promise.all([
                this.apiCall('/api/stats'),
                this.apiCall('/api/recent-activity')
            ]);
            
            // Handle the response structure properly
            const stats = statsResponse.data || statsResponse;
            const recentActivity = activityResponse.data || activityResponse;
            
            this.updateDashboardStats(stats);
            this.updateRecentActivity(recentActivity);
            
        } catch (error) {
            console.error('Failed to load dashboard:', error);
            // Show fallback data if API fails
            this.updateDashboardStats({
                total_orders: 0,
                pending_orders: 0,
                in_progress_orders: 0,
                completed_orders: 0,
                total_revenue: 0,
                growth: { orders: 0, pending: 0, in_progress: 0, completed: 0, revenue: 0 }
            });
            this.updateRecentActivity([]);
        } finally {
            this.showLoading(false);
        }
    }
    
    updateDashboardStats(stats) {
        // Update stat cards
        document.getElementById('totalOrders').textContent = stats.total_orders;
        document.getElementById('pendingOrders').textContent = stats.pending_orders;
        document.getElementById('inProgressOrders').textContent = stats.in_progress_orders;
        document.getElementById('completedOrders').textContent = stats.completed_orders;
        
        // Update revenue with proper currency
        const revenueElement = document.getElementById('totalRevenue');
        if (revenueElement) {
            revenueElement.innerHTML = `<span class="uae-dirham">د.إ</span> ${this.formatNumber(stats.total_revenue)}`;
        }
        
        // Update growth indicators
        this.updateGrowthIndicator('ordersGrowth', stats.growth.orders);
        this.updateGrowthIndicator('pendingGrowth', stats.growth.pending);
        this.updateGrowthIndicator('progressGrowth', stats.growth.in_progress);
        this.updateGrowthIndicator('completedGrowth', stats.growth.completed);
        this.updateGrowthIndicator('revenueGrowth', stats.growth.revenue);
        
        // Update sidebar badges
        document.querySelector('[data-section="orders"] .badge').textContent = stats.pending_orders;
    }
    
    updateGrowthIndicator(elementId, growth) {
        const element = document.getElementById(elementId);
        if (element) {
            const isPositive = growth >= 0;
            element.innerHTML = `
                <i class="fas fa-arrow-${isPositive ? 'up' : 'down'}"></i> 
                ${isPositive ? '+' : ''}${growth}%
            `;
            element.className = `stat-change ${isPositive ? 'positive' : 'negative'}`;
        }
    }
    
    updateRecentActivity(activities) {
        const container = document.getElementById('recentActivity');
        if (!container) return;
        
        if (activities.length === 0) {
            container.innerHTML = '<p class="text-muted">No recent activity</p>';
            return;
        }
        
        container.innerHTML = activities.map(activity => `
            <div class="activity-item">
                <div class="activity-icon">
                    <i class="fas fa-plus"></i>
                </div>
                <div class="activity-content">
                    <h4>${activity.title}</h4>
                    <p>${activity.description}</p>
                    <small>${this.formatDate(activity.date)}</small>
                </div>
            </div>
        `).join('');
    }
    
    async showSection(section) {
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        
        const targetNav = document.querySelector(`[data-section="${section}"]`);
        if (targetNav) {
            targetNav.classList.add('active');
        }
        
        // Hide all existing sections first
        document.querySelectorAll('.content-section').forEach(sec => {
            sec.style.display = 'none';
        });
        
        // Update content
        this.currentSection = section;
        const contentArea = document.getElementById('contentArea');
        
        try {
            this.showLoading(true);
            
            switch (section) {
                case 'dashboard':
                    // Show dashboard section
                    const dashboardSection = document.getElementById('dashboardSection');
                    if (dashboardSection) {
                        dashboardSection.style.display = 'block';
                    }
                    await this.loadDashboard();
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
                    this.loadAnalytics();
                    break;
                case 'settings':
                    this.loadSettings();
                    break;
            }
        } catch (error) {
            console.error(`Failed to load ${section}:`, error);
            if (contentArea) {
                contentArea.innerHTML = `<div class="error-message">Failed to load ${section}. Please try again.</div>`;
            }
        } finally {
            this.showLoading(false);
        }
    }
    
    async loadOrders() {
        try {
            const response = await this.apiCall('/api/orders/live');
            const orders = response.data || response;
            this.renderOrdersSection(orders);
        } catch (error) {
            console.error('Failed to load orders:', error);
            this.renderOrdersSection([]);
        }
    }
    
    renderOrdersSection(orders) {
        const contentArea = document.getElementById('contentArea');
        contentArea.innerHTML = `
            <div class="section-header">
                <h2><i class="fas fa-shopping-cart"></i> Orders Management</h2>
                <div class="section-actions">
                    <div class="search-box">
                        <i class="fas fa-search"></i>
                        <input type="text" data-search="orders" placeholder="Search orders..." class="form-control">
                    </div>
                    <select data-filter="orders-status" class="form-select">
                        <option value="">All Status</option>
                        <option value="pending">Pending</option>
                        <option value="paid">Paid</option>
                        <option value="in_progress">In Progress</option>
                        <option value="delivered">Delivered</option>
                        <option value="completed">Completed</option>
                    </select>
                </div>
            </div>
            
            <div class="table-container">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th><i class="fas fa-hashtag"></i> Order #</th>
                            <th><i class="fas fa-user"></i> Customer</th>
                            <th><i class="fas fa-cog"></i> Service</th>
                            <th><i class="fas fa-money-bill-wave"></i> Amount</th>
                            <th><i class="fas fa-credit-card"></i> Payment</th>
                            <th><i class="fas fa-circle"></i> Status</th>
                            <th><i class="fas fa-calendar"></i> Date</th>
                            <th><i class="fas fa-cogs"></i> Actions</th>
                        </tr>
                    </thead>
                    <tbody id="ordersTableBody">
                        ${this.renderOrdersTable(orders)}
                    </tbody>
                </table>
            </div>
        `;
    }
    
    renderOrdersTable(orders) {
        if (orders.length === 0) {
            return '<tr><td colspan="8" class="text-center text-muted">No orders found</td></tr>';
        }
        
        return orders.map(order => `
            <tr>
                <td>
                    <strong>${order.order_number}</strong>
                    <small class="text-muted d-block">${order.subject}</small>
                </td>
                <td>
                    <div class="customer-info">
                        <div class="customer-avatar">${this.getInitials(order.customer_name)}</div>
                        <div class="customer-details">
                            <strong>${order.customer_name}</strong>
                            <small>${order.customer_email}</small>
                        </div>
                    </div>
                </td>
                <td>
                    <span class="badge badge-info">${order.service_type}</span>
                </td>
                <td>
                    <strong><span class="uae-dirham">د.إ</span> ${this.formatNumber(order.total_price)}</strong>
                    <small class="text-muted d-block">${order.currency}</small>
                </td>
                <td>${this.getPaymentStatusBadge(order.payment_status)}</td>
                <td>${this.getOrderStatusBadge(order.status)}</td>
                <td>
                    <strong>${this.formatDate(order.created_at)}</strong>
                    ${order.deadline ? `<small class="text-muted d-block">Due: ${this.formatDate(order.deadline)}</small>` : ''}
                </td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="liveAdmin.viewOrder(${order.id})">
                        <i class="fas fa-eye"></i> View
                    </button>
                    <button class="btn btn-sm btn-success" onclick="liveAdmin.manageOrder(${order.id})">
                        <i class="fas fa-cog"></i> Manage
                    </button>
                </td>
            </tr>
        `).join('');
    }
    
    async loadCustomers() {
        try {
            const response = await this.apiCall('/api/customers');
            const customers = response.data || response;
            this.renderCustomersSection(customers);
        } catch (error) {
            console.error('Failed to load customers:', error);
            this.renderCustomersSection([]);
        }
    }
    
    renderCustomersSection(customers) {
        const contentArea = document.getElementById('contentArea');
        
        // Calculate stats
        const totalCustomers = customers.length;
        const activeCustomers = customers.filter(c => c.is_active).length;
        const avgOrders = totalCustomers > 0 ? (customers.reduce((sum, c) => sum + c.total_orders, 0) / totalCustomers).toFixed(1) : 0;
        
        contentArea.innerHTML = `
            <div class="section-header">
                <h2><i class="fas fa-users"></i> Customers Management</h2>
                <div class="section-actions">
                    <div class="search-box">
                        <i class="fas fa-search"></i>
                        <input type="text" data-search="customers" placeholder="Search customers..." class="form-control">
                    </div>
                </div>
            </div>
            
            <div class="stats-row mb-4">
                <div class="stat-card">
                    <div class="stat-icon bg-primary">
                        <i class="fas fa-users"></i>
                    </div>
                    <div class="stat-content">
                        <h3>${totalCustomers}</h3>
                        <p>Total Customers</p>
                        <span class="stat-change positive">
                            <i class="fas fa-arrow-up"></i> +18%
                        </span>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon bg-success">
                        <i class="fas fa-user-check"></i>
                    </div>
                    <div class="stat-content">
                        <h3>${activeCustomers}</h3>
                        <p>Active Customers</p>
                        <span class="stat-change positive">
                            <i class="fas fa-arrow-up"></i> +12%
                        </span>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon bg-info">
                        <i class="fas fa-shopping-cart"></i>
                    </div>
                    <div class="stat-content">
                        <h3>${avgOrders}</h3>
                        <p>Avg Orders/Customer</p>
                        <span class="stat-change positive">
                            <i class="fas fa-arrow-up"></i> +8%
                        </span>
                    </div>
                </div>
            </div>
            
            <div class="table-container">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th><i class="fas fa-user"></i> Customer</th>
                            <th><i class="fas fa-envelope"></i> Email</th>
                            <th><i class="fas fa-phone"></i> Phone</th>
                            <th><i class="fas fa-shopping-bag"></i> Orders</th>
                            <th><i class="fas fa-money-bill-wave"></i> Total Spent</th>
                            <th><i class="fas fa-circle"></i> Status</th>
                            <th><i class="fas fa-cogs"></i> Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${this.renderCustomersTable(customers)}
                    </tbody>
                </table>
            </div>
        `;
    }
    
    renderCustomersTable(customers) {
        if (customers.length === 0) {
            return '<tr><td colspan="7" class="text-center text-muted">No customers found</td></tr>';
        }
        
        return customers.map(customer => `
            <tr>
                <td>
                    <div class="customer-info">
                        <div class="customer-avatar">${this.getInitials(customer.full_name)}</div>
                        <div class="customer-details">
                            <strong>${customer.full_name}</strong>
                            <small>Customer since ${this.formatDate(customer.created_at)}</small>
                        </div>
                    </div>
                </td>
                <td>${customer.email}</td>
                <td>${customer.phone}</td>
                <td><span class="badge badge-info">${customer.total_orders} orders</span></td>
                <td><strong><span class="uae-dirham">د.إ</span> ${this.formatNumber(customer.total_spent)}</strong></td>
                <td><span class="badge badge-success">Active</span></td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="liveAdmin.viewCustomer(${customer.id})">
                        <i class="fas fa-eye"></i> View
                    </button>
                    <button class="btn btn-sm btn-success" onclick="liveAdmin.contactCustomer(${customer.id})">
                        <i class="fas fa-comment"></i> Contact
                    </button>
                </td>
            </tr>
        `).join('');
    }
    
    async loadPayments() {
        try {
            const response = await this.apiCall('/api/payments');
            const payments = response.data || response;
            this.renderPaymentsSection(payments);
        } catch (error) {
            console.error('Failed to load payments:', error);
            this.renderPaymentsSection([]);
        }
    }
    
    renderPaymentsSection(payments) {
        const contentArea = document.getElementById('contentArea');
        
        // Calculate stats
        const totalRevenue = payments.filter(p => p.status === 'succeeded').reduce((sum, p) => sum + p.amount, 0);
        const totalPayments = payments.length;
        const pendingPayments = payments.filter(p => p.status === 'pending').length;
        
        contentArea.innerHTML = `
            <div class="section-header">
                <h2><i class="fas fa-credit-card"></i> Payments Management</h2>
                <div class="section-actions">
                    <div class="search-box">
                        <i class="fas fa-search"></i>
                        <input type="text" data-search="payments" placeholder="Search payments..." class="form-control">
                    </div>
                    <select data-filter="payments-status" class="form-select">
                        <option value="">All Status</option>
                        <option value="succeeded">Confirmed</option>
                        <option value="pending">Pending</option>
                        <option value="failed">Failed</option>
                        <option value="refunded">Refunded</option>
                    </select>
                </div>
            </div>
            
            <div class="stats-row mb-4">
                <div class="stat-card">
                    <div class="stat-icon bg-success">
                        <i class="fas fa-check-circle"></i>
                    </div>
                    <div class="stat-content">
                        <h3><span class="uae-dirham">د.إ</span> ${this.formatNumber(totalRevenue)}</h3>
                        <p>Total Revenue</p>
                        <span class="stat-change positive">
                            <i class="fas fa-arrow-up"></i> +23%
                        </span>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon bg-primary">
                        <i class="fas fa-credit-card"></i>
                    </div>
                    <div class="stat-content">
                        <h3>${totalPayments}</h3>
                        <p>Total Payments</p>
                        <span class="stat-change positive">
                            <i class="fas fa-arrow-up"></i> +15%
                        </span>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon bg-warning">
                        <i class="fas fa-clock"></i>
                    </div>
                    <div class="stat-content">
                        <h3>${pendingPayments}</h3>
                        <p>Pending Payments</p>
                        <span class="stat-change neutral">
                            <i class="fas fa-minus"></i> 0%
                        </span>
                    </div>
                </div>
            </div>
            
            <div class="table-container">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th><i class="fas fa-hashtag"></i> Payment ID</th>
                            <th><i class="fas fa-shopping-bag"></i> Order</th>
                            <th><i class="fas fa-user"></i> Customer</th>
                            <th><i class="fas fa-money-bill-wave"></i> Amount</th>
                            <th><i class="fas fa-credit-card"></i> Method</th>
                            <th><i class="fas fa-circle"></i> Status</th>
                            <th><i class="fas fa-calendar"></i> Date</th>
                            <th><i class="fas fa-cogs"></i> Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${this.renderPaymentsTable(payments)}
                    </tbody>
                </table>
            </div>
        `;
    }
    
    renderPaymentsTable(payments) {
        if (payments.length === 0) {
            return '<tr><td colspan="8" class="text-center text-muted">No payments found</td></tr>';
        }
        
        return payments.map(payment => `
            <tr>
                <td>
                    <strong>${payment.payment_id}</strong>
                    <small class="text-muted d-block">${payment.method} Transaction</small>
                </td>
                <td>
                    <a href="#" class="text-primary">${payment.order_number}</a>
                    <small class="text-muted d-block">${payment.order_service}</small>
                </td>
                <td>
                    <div class="customer-info">
                        <div class="customer-avatar">${this.getInitials(payment.customer_name)}</div>
                        <div class="customer-details">
                            <strong>${payment.customer_name}</strong>
                            <small>${payment.customer_email}</small>
                        </div>
                    </div>
                </td>
                <td>
                    <strong><span class="uae-dirham">د.إ</span> ${this.formatNumber(payment.amount)}</strong>
                    <small class="text-muted d-block">${payment.currency}</small>
                </td>
                <td>
                    <span class="badge badge-info">
                        <i class="fab fa-stripe"></i> ${payment.method}
                    </span>
                </td>
                <td>${this.getPaymentStatusBadge(payment.status)}</td>
                <td>
                    <strong>${this.formatDate(payment.created_at)}</strong>
                </td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="liveAdmin.viewPayment(${payment.id})">
                        <i class="fas fa-eye"></i> View
                    </button>
                    ${payment.receipt_url ? `
                        <a href="${payment.receipt_url}" target="_blank" class="btn btn-sm btn-secondary">
                            <i class="fas fa-receipt"></i> Receipt
                        </a>
                    ` : ''}
                </td>
            </tr>
        `).join('');
    }
    
    // Order Management Functions
    
    async viewOrder(orderId) {
        try {
            const orders = await this.apiCall(`/api/orders?limit=1&offset=0`);
            const order = orders.find(o => o.id === orderId);
            
            if (!order) {
                this.showToast('Order not found', 'error');
                return;
            }
            
            this.showOrderModal(order);
        } catch (error) {
            console.error('Failed to load order:', error);
        }
    }
    
    showOrderModal(order) {
        const modal = document.getElementById('orderModal');
        const modalContent = document.getElementById('modalContent');
        
        modalContent.innerHTML = `
            <div class="modal-header">
                <h3>Order Details - ${order.order_number}</h3>
                <button onclick="liveAdmin.closeModal()" class="btn-close">&times;</button>
            </div>
            <div class="modal-body">
                <div class="order-details">
                    <div class="detail-row">
                        <strong>Customer:</strong> ${order.customer_name}
                    </div>
                    <div class="detail-row">
                        <strong>Service:</strong> ${order.service_type}
                    </div>
                    <div class="detail-row">
                        <strong>Subject:</strong> ${order.subject}
                    </div>
                    <div class="detail-row">
                        <strong>Amount:</strong> <span class="uae-dirham">د.إ</span> ${this.formatNumber(order.total_price)}
                    </div>
                    <div class="detail-row">
                        <strong>Status:</strong> ${this.getOrderStatusBadge(order.status)}
                    </div>
                    <div class="detail-row">
                        <strong>Payment:</strong> ${this.getPaymentStatusBadge(order.payment_status)}
                    </div>
                    <div class="detail-row">
                        <strong>Created:</strong> ${this.formatDate(order.created_at)}
                    </div>
                    ${order.deadline ? `
                        <div class="detail-row">
                            <strong>Deadline:</strong> ${this.formatDate(order.deadline)}
                        </div>
                    ` : ''}
                </div>
                
                <div class="modal-actions">
                    <button class="btn btn-primary" onclick="liveAdmin.manageOrder(${order.id})">
                        <i class="fas fa-cog"></i> Manage Order
                    </button>
                    <button class="btn btn-success" onclick="liveAdmin.uploadWork(${order.id})">
                        <i class="fas fa-upload"></i> Upload Work
                    </button>
                    <button class="btn btn-info" onclick="liveAdmin.contactCustomer(${order.id})">
                        <i class="fas fa-comment"></i> Contact Customer
                    </button>
                </div>
            </div>
        `;
        
        modal.classList.remove('hidden');
    }
    
    async manageOrder(orderId) {
        this.currentOrderId = orderId;
        
        const modal = document.getElementById('orderModal');
        const modalContent = document.getElementById('modalContent');
        
        modalContent.innerHTML = `
            <div class="modal-header">
                <h3>Manage Order</h3>
                <button onclick="liveAdmin.closeModal()" class="btn-close">&times;</button>
            </div>
            <div class="modal-body">
                <form id="manageOrderForm">
                    <div class="form-group">
                        <label>Order Status</label>
                        <select name="status" class="form-control">
                            <option value="pending">Pending</option>
                            <option value="paid">Paid</option>
                            <option value="in_progress">In Progress</option>
                            <option value="delivered">Delivered</option>
                            <option value="completed">Completed</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label>Payment Status</label>
                        <select name="payment_status" class="form-control">
                            <option value="waiting">Waiting</option>
                            <option value="confirmed">Confirmed</option>
                            <option value="failed">Failed</option>
                        </select>
                    </div>
                    
                    <div class="form-actions">
                        <button type="button" class="btn btn-primary" onclick="liveAdmin.updateOrderStatus()">
                            <i class="fas fa-save"></i> Update Order
                        </button>
                        <button type="button" class="btn btn-warning" onclick="liveAdmin.archiveOrder(${orderId})">
                            <i class="fas fa-archive"></i> Archive
                        </button>
                        <button type="button" class="btn btn-danger" onclick="liveAdmin.deleteOrder(${orderId})">
                            <i class="fas fa-trash"></i> Delete
                        </button>
                    </div>
                </form>
            </div>
        `;
        
        modal.classList.remove('hidden');
    }
    
    async updateOrderStatus() {
        try {
            const form = document.getElementById('manageOrderForm');
            const formData = new FormData(form);
            
            // Update order status
            await this.apiCall(`/api/orders/${this.currentOrderId}/status`, {
                method: 'PUT',
                body: formData
            });
            
            // Update payment status
            await this.apiCall(`/api/orders/${this.currentOrderId}/payment-status`, {
                method: 'PUT',
                body: formData
            });
            
            this.showToast('Order updated successfully', 'success');
            this.closeModal();
            this.refreshCurrentSection();
        } catch (error) {
            console.error('Failed to update order:', error);
        }
    }
    
    async uploadWork(orderId) {
        this.currentOrderId = orderId;
        
        const modal = document.getElementById('orderModal');
        const modalContent = document.getElementById('modalContent');
        
        modalContent.innerHTML = `
            <div class="modal-header">
                <h3>Upload Work Files</h3>
                <button onclick="liveAdmin.closeModal()" class="btn-close">&times;</button>
            </div>
            <div class="modal-body">
                <form id="uploadWorkForm" enctype="multipart/form-data">
                    <div class="upload-area">
                        <input type="file" id="workFile" name="file" multiple class="file-input">
                        <div class="upload-placeholder">
                            <i class="fas fa-cloud-upload-alt"></i>
                            <p>Drag & drop files here or click to browse</p>
                        </div>
                    </div>
                    
                    <div class="form-actions">
                        <button type="button" class="btn btn-success" onclick="liveAdmin.submitWorkUpload()">
                            <i class="fas fa-upload"></i> Upload Files
                        </button>
                    </div>
                </form>
            </div>
        `;
        
        modal.classList.remove('hidden');
    }
    
    async submitWorkUpload() {
        try {
            const fileInput = document.getElementById('workFile');
            if (fileInput.files.length === 0) {
                this.showToast('Please select a file', 'warning');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            
            await this.apiCall(`/api/orders/${this.currentOrderId}/upload`, {
                method: 'POST',
                body: formData,
                headers: {} // Remove Content-Type to let browser set it for FormData
            });
            
            this.showToast('File uploaded successfully', 'success');
            this.closeModal();
            this.refreshCurrentSection();
        } catch (error) {
            console.error('Failed to upload file:', error);
        }
    }
    
    async contactCustomer(orderId) {
        this.currentOrderId = orderId;
        
        const modal = document.getElementById('orderModal');
        const modalContent = document.getElementById('modalContent');
        
        modalContent.innerHTML = `
            <div class="modal-header">
                <h3>Contact Customer</h3>
                <button onclick="liveAdmin.closeModal()" class="btn-close">&times;</button>
            </div>
            <div class="modal-body">
                <form id="contactForm">
                    <div class="form-group">
                        <label>Message Type</label>
                        <select name="message_type" class="form-control">
                            <option value="info">Information</option>
                            <option value="update">Status Update</option>
                            <option value="request">Request</option>
                            <option value="delivery">Delivery Notification</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label>Message</label>
                        <textarea name="message" class="form-control" rows="4" placeholder="Write your message here..."></textarea>
                    </div>
                    
                    <div class="form-actions">
                        <button type="button" class="btn btn-success" onclick="liveAdmin.sendCustomerMessage()">
                            <i class="fas fa-paper-plane"></i> Send Message
                        </button>
                    </div>
                </form>
            </div>
        `;
        
        modal.classList.remove('hidden');
    }
    
    async sendCustomerMessage() {
        try {
            const form = document.getElementById('contactForm');
            const formData = new FormData(form);
            
            await this.apiCall(`/api/orders/${this.currentOrderId}/contact`, {
                method: 'POST',
                body: formData
            });
            
            this.showToast('Message sent successfully', 'success');
            this.closeModal();
        } catch (error) {
            console.error('Failed to send message:', error);
        }
    }
    
    async deleteOrder(orderId) {
        if (!confirm('Are you sure you want to delete this order? This action cannot be undone.')) {
            return;
        }
        
        try {
            await this.apiCall(`/api/orders/${orderId}`, {
                method: 'DELETE'
            });
            
            this.showToast('Order deleted successfully', 'success');
            this.closeModal();
            this.refreshCurrentSection();
        } catch (error) {
            console.error('Failed to delete order:', error);
        }
    }
    
    async archiveOrder(orderId) {
        if (!confirm('Are you sure you want to archive this order?')) {
            return;
        }
        
        try {
            await this.apiCall(`/api/orders/${orderId}/archive`, {
                method: 'POST'
            });
            
            this.showToast('Order archived successfully', 'success');
            this.closeModal();
            this.refreshCurrentSection();
        } catch (error) {
            console.error('Failed to archive order:', error);
        }
    }
    
    // Utility Functions
    
    closeModal() {
        document.getElementById('orderModal').classList.add('hidden');
    }
    
    formatNumber(num) {
        return new Intl.NumberFormat('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(num);
    }
    
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }
    
    getInitials(name) {
        return name.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2);
    }
    
    getOrderStatusBadge(status) {
        const statusMap = {
            'pending': { class: 'badge-warning', text: 'Pending' },
            'paid': { class: 'badge-info', text: 'Paid' },
            'in_progress': { class: 'badge-primary', text: 'In Progress' },
            'delivered': { class: 'badge-success', text: 'Delivered' },
            'completed': { class: 'badge-success', text: 'Completed' },
            'archived': { class: 'badge-secondary', text: 'Archived' }
        };
        
        const statusInfo = statusMap[status] || { class: 'badge-secondary', text: status };
        return `<span class="badge ${statusInfo.class}">${statusInfo.text}</span>`;
    }
    
    getPaymentStatusBadge(status) {
        const statusMap = {
            'waiting': { class: 'badge-warning', text: 'Waiting' },
            'confirmed': { class: 'badge-success', text: 'Confirmed' },
            'succeeded': { class: 'badge-success', text: 'Confirmed' },
            'failed': { class: 'badge-danger', text: 'Failed' },
            'pending': { class: 'badge-warning', text: 'Pending' }
        };
        
        const statusInfo = statusMap[status] || { class: 'badge-secondary', text: status };
        return `<span class="badge ${statusInfo.class}">${statusInfo.text}</span>`;
    }
    
    showToast(message, type = 'info') {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'times' : 'info'}"></i>
            <span>${message}</span>
        `;
        
        document.body.appendChild(toast);
        
        // Show toast
        setTimeout(() => toast.classList.add('show'), 100);
        
        // Hide toast
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => document.body.removeChild(toast), 300);
        }, 3000);
    }
    
    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        if (show) {
            overlay.classList.remove('hidden');
        } else {
            overlay.classList.add('hidden');
        }
    }
    
    refreshCurrentSection() {
        this.showSection(this.currentSection);
    }
    
    startAutoRefresh() {
        // Refresh every 30 seconds
        this.refreshInterval = setInterval(() => {
            if (this.currentSection === 'dashboard') {
                this.loadDashboard();
            }
        }, 30000);
    }
    
    loadAnalytics() {
        const contentArea = document.getElementById('contentArea');
        contentArea.innerHTML = `
            <div class="section-header">
                <h2><i class="fas fa-chart-bar"></i> Analytics Dashboard</h2>
            </div>
            
            <div class="analytics-grid">
                <div class="chart-container">
                    <h3>Revenue Trends</h3>
                    <div class="chart-placeholder">
                        <p>📊 Revenue analytics chart will be implemented here</p>
                        <p>Monthly revenue: <span class="uae-dirham">د.إ</span> 2,500.00</p>
                        <p>Growth rate: +23% from last month</p>
                    </div>
                </div>
                
                <div class="chart-container">
                    <h3>Order Statistics</h3>
                    <div class="chart-placeholder">
                        <p>📈 Order statistics chart will be implemented here</p>
                        <p>Total orders this month: 25</p>
                        <p>Completion rate: 85%</p>
                    </div>
                </div>
            </div>
        `;
    }
    
    loadSettings() {
        const contentArea = document.getElementById('contentArea');
        contentArea.innerHTML = `
            <div class="section-header">
                <h2><i class="fas fa-cog"></i> System Settings</h2>
            </div>
            
            <div class="settings-container">
                <div class="settings-section">
                    <h3>Database Management</h3>
                    <div class="danger-zone">
                        <h4>DANGER: Reset Database</h4>
                        <p><strong>Warning!</strong> This will permanently delete ALL data including orders, users, and payments. This action cannot be undone!</p>
                        
                        <div class="form-group">
                            <label>Type "RESET_ALL_DATA" to confirm:</label>
                            <input type="text" id="resetConfirmation" class="form-control" placeholder="RESET_ALL_DATA">
                        </div>
                        
                        <button class="btn btn-danger" onclick="liveAdmin.resetDatabase()">
                            <i class="fas fa-exclamation-triangle"></i> Reset Database
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    async resetDatabase() {
        const confirmation = document.getElementById('resetConfirmation').value;
        
        if (confirmation !== 'RESET_ALL_DATA') {
            this.showToast('Please type "RESET_ALL_DATA" to confirm', 'error');
            return;
        }
        
        if (!confirm('Are you absolutely sure? This will delete ALL data permanently!')) {
            return;
        }
        
        try {
            const formData = new FormData();
            formData.append('confirmation', confirmation);
            
            await this.apiCall('/api/admin/reset-database', {
                method: 'POST',
                body: formData
            });
            
            this.showToast('Database reset successfully', 'success');
            this.loadDashboard();
        } catch (error) {
            console.error('Failed to reset database:', error);
        }
    }
    
    handleSearch(input) {
        const searchTerm = input.value.toLowerCase();
        const section = input.getAttribute('data-search');
        
        // Implement search functionality based on section
        // This would filter the current table data
        console.log(`Searching ${section} for: ${searchTerm}`);
    }
    
    handleFilter(select) {
        const filterValue = select.value;
        const section = select.getAttribute('data-filter');
        
        // Implement filter functionality based on section
        // This would reload data with filter applied
        console.log(`Filtering ${section} by: ${filterValue}`);
    }
}

// Initialize the live admin dashboard
let liveAdmin;
window.addEventListener('DOMContentLoaded', () => {
    liveAdmin = new LiveAdminDashboard();
});
