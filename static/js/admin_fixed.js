// Fixed Admin Dashboard JavaScript - Keep the beautiful UI, just make tabs work
class AdminDashboard {
    constructor() {
        this.currentOrderId = null;
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
    }
    
    setupEventListeners() {
        // Sidebar navigation - Fix tab switching
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
        const sidebar = document.getElementById('sidebar');
        
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => {
                sidebar.classList.toggle('collapsed');
            });
        }
        
        // Refresh button
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshCurrentSection();
            });
        }
        
        // Modal close functionality
        document.addEventListener('click', (e) => {
            if (e.target.matches('.modal-close') || e.target.closest('.modal-close')) {
                this.closeAllModals();
            }
        });
        
        // Quick action buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('[onclick]')) {
                e.preventDefault();
                const action = e.target.getAttribute('onclick');
                if (action && action.includes('showSection')) {
                    const section = action.match(/showSection\\('([^']+)'\\)/)?.[1];
                    if (section) this.showSection(section);
                }
            }
        });
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
        } catch (error) {
            console.error('Error loading customers:', error);
            this.customers = [];
        }
    }
    
    async loadPayments() {
        try {
            const response = await api.get('/payments');
            this.payments = Array.isArray(response) ? response : (response || []);
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
        // Hide all content sections
        const sections = document.querySelectorAll('.content-section');
        sections.forEach(section => {
            section.style.display = 'none';
        });
        
        // Show the target section
        let targetSection = document.getElementById(sectionName + 'Section');
        
        if (targetSection) {
            // Update existing section content
            if (sectionName === 'customers') {
                targetSection.innerHTML = this.createCustomersSection();
            } else if (sectionName === 'payments') {
                targetSection.innerHTML = this.createPaymentsSection();
            } else if (sectionName === 'analytics') {
                targetSection.innerHTML = this.createAnalyticsSection();
            } else if (sectionName === 'settings') {
                targetSection.innerHTML = this.createSettingsSection();
            }
            
            targetSection.style.display = 'block';
            this.currentSection = sectionName;
            
            // Update page title if exists
            const pageTitle = document.getElementById('pageTitle');
            if (pageTitle) {
                pageTitle.textContent = sectionName.charAt(0).toUpperCase() + sectionName.slice(1);
            }
            
            // Load section-specific data
            this.loadSectionData(sectionName);
        }
    }
    
    createSectionContent(sectionName) {
        // Find the main content area
        const mainContent = document.querySelector('.main-content') || document.querySelector('.content');
        if (!mainContent) return null;
        
        // Create section content dynamically
        let sectionHTML = '';
        
        switch (sectionName) {
            case 'orders':
                sectionHTML = this.createOrdersSection();
                break;
            case 'customers':
                sectionHTML = this.createCustomersSection();
                break;
            case 'payments':
                sectionHTML = this.createPaymentsSection();
                break;
            case 'analytics':
                sectionHTML = this.createAnalyticsSection();
                break;
            case 'settings':
                sectionHTML = this.createSettingsSection();
                break;
            default:
                sectionHTML = `<div class="section-placeholder">
                    <h2>${sectionName.charAt(0).toUpperCase() + sectionName.slice(1)}</h2>
                    <p>This section is under development.</p>
                </div>`;
        }
        
        // Create or update the section
        let section = document.getElementById(sectionName + 'Section');
        if (!section) {
            section = document.createElement('div');
            section.id = sectionName + 'Section';
            section.className = 'content-section';
            section.style.display = 'none';
            mainContent.appendChild(section);
        }
        
        section.innerHTML = sectionHTML;
        return section;
    }
    
    createOrdersSection() {
        return `
            <div class="section-header">
                <h2>Orders Management</h2>
                <div class="section-actions">
                    <input type="text" id="orderSearch" placeholder="Search orders..." class="form-control">
                    <select id="statusFilter" class="form-control">
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
                <table class="table">
                    <thead>
                        <tr>
                            <th>Order #</th>
                            <th>Customer</th>
                            <th>Service</th>
                            <th>Amount</th>
                            <th>Payment</th>
                            <th>Status</th>
                            <th>Date</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="ordersTableBody">
                        <tr><td colspan="8" class="text-center">Loading orders...</td></tr>
                    </tbody>
                </table>
            </div>
        `;
    }
    
    createCustomersSection() {
        return `
            <div class="section-header">
                <h2><i class="fas fa-users"></i> Customers Management</h2>
                <div class="section-actions">
                    <div class="search-box">
                        <i class="fas fa-search"></i>
                        <input type="text" id="customerSearch" placeholder="Search customers..." class="form-control">
                    </div>
                    <button class="btn btn-primary">
                        <i class="fas fa-plus"></i> Add Customer
                    </button>
                </div>
            </div>
            
            <div class="stats-row mb-4">
                <div class="stat-card">
                    <div class="stat-icon bg-primary">
                        <i class="fas fa-users"></i>
                    </div>
                    <div class="stat-content">
                        <h3>8</h3>
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
                        <h3>7</h3>
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
                        <h3>3.2</h3>
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
                        <tr>
                            <td>
                                <div class="customer-info">
                                    <div class="customer-avatar">JD</div>
                                    <div class="customer-details">
                                        <strong>John Doe</strong>
                                        <small>Customer since Oct 2024</small>
                                    </div>
                                </div>
                            </td>
                            <td>john@example.com</td>
                            <td>+971 50 123 4567</td>
                            <td><span class="badge badge-info">3 orders</span></td>
                            <td><strong><span class="uae-dirham">د.إ</span> 850.00</strong></td>
                            <td><span class="badge badge-success">Active</span></td>
                            <td>
                                <button class="btn btn-sm btn-primary" onclick="dashboard.viewCustomer(1)">
                                    <i class="fas fa-eye"></i> View
                                </button>
                                <button class="btn btn-sm btn-success" onclick="dashboard.contactCustomer(1)">
                                    <i class="fas fa-comment"></i> Contact
                                </button>
                            </td>
                        </tr>
                        <tr>
                            <td>
                                <div class="customer-info">
                                    <div class="customer-avatar">JS</div>
                                    <div class="customer-details">
                                        <strong>Jane Smith</strong>
                                        <small>Customer since Oct 2024</small>
                                    </div>
                                </div>
                            </td>
                            <td>jane@example.com</td>
                            <td>+971 55 987 6543</td>
                            <td><span class="badge badge-info">1 order</span></td>
                            <td><strong><span class="uae-dirham">د.إ</span> 300.00</strong></td>
                            <td><span class="badge badge-success">Active</span></td>
                            <td>
                                <button class="btn btn-sm btn-primary" onclick="dashboard.viewCustomer(2)">
                                    <i class="fas fa-eye"></i> View
                                </button>
                                <button class="btn btn-sm btn-success" onclick="dashboard.contactCustomer(2)">
                                    <i class="fas fa-comment"></i> Contact
                                </button>
                            </td>
                        </tr>
                        <tr>
                            <td>
                                <div class="customer-info">
                                    <div class="customer-avatar">AA</div>
                                    <div class="customer-details">
                                        <strong>Ahmed Ali</strong>
                                        <small>Customer since Oct 2024</small>
                                    </div>
                                </div>
                            </td>
                            <td>ahmed@example.com</td>
                            <td>+971 56 456 7890</td>
                            <td><span class="badge badge-info">2 orders</span></td>
                            <td><strong><span class="uae-dirham">د.إ</span> 1,350.00</strong></td>
                            <td><span class="badge badge-success">Active</span></td>
                            <td>
                                <button class="btn btn-sm btn-primary" onclick="dashboard.viewCustomer(3)">
                                    <i class="fas fa-eye"></i> View
                                </button>
                                <button class="btn btn-sm btn-success" onclick="dashboard.contactCustomer(3)">
                                    <i class="fas fa-comment"></i> Contact
                                </button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        `;
    }
    
    createPaymentsSection() {
        return `
            <div class="section-header">
                <h2><i class="fas fa-credit-card"></i> Payments Management</h2>
                <div class="section-actions">
                    <div class="search-box">
                        <i class="fas fa-search"></i>
                        <input type="text" placeholder="Search payments..." class="form-control">
                    </div>
                    <select class="form-select">
                        <option value="">All Status</option>
                        <option value="confirmed">Confirmed</option>
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
                        <h3><span class="uae-dirham">د.إ</span> 2,500.00</h3>
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
                        <h3>15</h3>
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
                        <h3>2</h3>
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
                        <tr>
                            <td>
                                <strong>#PAY-001</strong>
                                <small class="text-muted d-block">Stripe Transaction</small>
                            </td>
                            <td>
                                <a href="#" class="text-primary">ORD-001</a>
                                <small class="text-muted d-block">Assignment Help</small>
                            </td>
                            <td>
                                <div class="customer-info">
                                    <div class="customer-avatar">JD</div>
                                    <div class="customer-details">
                                        <strong>John Doe</strong>
                                        <small>john@example.com</small>
                                    </div>
                                </div>
                            </td>
                            <td>
                                <strong><span class="uae-dirham">د.إ</span> 150.00</strong>
                                <small class="text-muted d-block">AED</small>
                            </td>
                            <td>
                                <span class="badge badge-info">
                                    <i class="fab fa-stripe"></i> Stripe
                                </span>
                            </td>
                            <td><span class="badge badge-success">Confirmed</span></td>
                            <td>
                                <strong>Oct 4, 2024</strong>
                                <small class="text-muted d-block">2:30 PM</small>
                            </td>
                            <td>
                                <button class="btn btn-sm btn-primary">
                                    <i class="fas fa-eye"></i> View
                                </button>
                                <button class="btn btn-sm btn-secondary">
                                    <i class="fas fa-receipt"></i> Receipt
                                </button>
                            </td>
                        </tr>
                        <tr>
                            <td>
                                <strong>#PAY-002</strong>
                                <small class="text-muted d-block">Stripe Transaction</small>
                            </td>
                            <td>
                                <a href="#" class="text-primary">ORD-002</a>
                                <small class="text-muted d-block">Project Report</small>
                            </td>
                            <td>
                                <div class="customer-info">
                                    <div class="customer-avatar">JS</div>
                                    <div class="customer-details">
                                        <strong>Jane Smith</strong>
                                        <small>jane@example.com</small>
                                    </div>
                                </div>
                            </td>
                            <td>
                                <strong><span class="uae-dirham">د.إ</span> 300.00</strong>
                                <small class="text-muted d-block">AED</small>
                            </td>
                            <td>
                                <span class="badge badge-info">
                                    <i class="fab fa-stripe"></i> Stripe
                                </span>
                            </td>
                            <td><span class="badge badge-warning">Pending</span></td>
                            <td>
                                <strong>Oct 4, 2024</strong>
                                <small class="text-muted d-block">1:15 PM</small>
                            </td>
                            <td>
                                <button class="btn btn-sm btn-primary">
                                    <i class="fas fa-eye"></i> View
                                </button>
                                <button class="btn btn-sm btn-warning">
                                    <i class="fas fa-sync"></i> Retry
                                </button>
                            </td>
                        </tr>
                        <tr>
                            <td>
                                <strong>#PAY-003</strong>
                                <small class="text-muted d-block">Stripe Transaction</small>
                            </td>
                            <td>
                                <a href="#" class="text-primary">ORD-003</a>
                                <small class="text-muted d-block">Thesis Writing</small>
                            </td>
                            <td>
                                <div class="customer-info">
                                    <div class="customer-avatar">AA</div>
                                    <div class="customer-details">
                                        <strong>Ahmed Ali</strong>
                                        <small>ahmed@example.com</small>
                                    </div>
                                </div>
                            </td>
                            <td>
                                <strong><span class="uae-dirham">د.إ</span> 2,050.00</strong>
                                <small class="text-muted d-block">AED</small>
                            </td>
                            <td>
                                <span class="badge badge-info">
                                    <i class="fab fa-stripe"></i> Stripe
                                </span>
                            </td>
                            <td><span class="badge badge-success">Confirmed</span></td>
                            <td>
                                <strong>Oct 3, 2024</strong>
                                <small class="text-muted d-block">4:45 PM</small>
                            </td>
                            <td>
                                <button class="btn btn-sm btn-primary">
                                    <i class="fas fa-eye"></i> View
                                </button>
                                <button class="btn btn-sm btn-secondary">
                                    <i class="fas fa-receipt"></i> Receipt
                                </button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        `;
    }
    
    createAnalyticsSection() {
        return `
            <div class="section-header">
                <h2>Analytics & Reports</h2>
            </div>
            <div class="analytics-grid">
                <div class="stats-row">
                    <div class="stat-card">
                        <div class="stat-icon">
                            <i class="fas fa-chart-line"></i>
                        </div>
                        <div class="stat-content">
                            <div class="stat-number"><span class="uae-dirham">د.إ</span> 2,500.00</div>
                            <div class="stat-label">Monthly Revenue</div>
                            <div class="stat-change positive">
                                <i class="fas fa-arrow-up"></i>
                                <span>+23%</span>
                            </div>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon">
                            <i class="fas fa-shopping-cart"></i>
                        </div>
                        <div class="stat-content">
                            <div class="stat-number">25</div>
                            <div class="stat-label">Total Orders</div>
                            <div class="stat-change positive">
                                <i class="fas fa-arrow-up"></i>
                                <span>+12%</span>
                            </div>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon">
                            <i class="fas fa-users"></i>
                        </div>
                        <div class="stat-content">
                            <div class="stat-number">8</div>
                            <div class="stat-label">Active Customers</div>
                            <div class="stat-change positive">
                                <i class="fas fa-arrow-up"></i>
                                <span>+18%</span>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="chart-container">
                    <h3>Revenue Trends</h3>
                    <div class="chart-placeholder">
                        <p>📊 Revenue analytics chart will be implemented here</p>
                        <p>Monthly revenue: <span class="uae-dirham">د.إ</span> 2,500.00</p>
                        <p>Growth rate: +23% from last month</p>
                    </div>
                </div>
                <div class="chart-container">
                    <h3>Order Analytics</h3>
                    <div class="chart-placeholder">
                        <p>📈 Order analytics chart will be implemented here</p>
                        <p>Total orders: 25</p>
                        <p>Completed: 2 | In Progress: 7 | Pending: 5</p>
                    </div>
                </div>
            </div>
        `;
    }
    
    createSettingsSection() {
        return `
            <div class="section-header">
                <h2>System Settings</h2>
            </div>
            <div class="settings-form">
                <form id="settingsForm">
                    <div class="form-group">
                        <label for="currency">Default Currency</label>
                        <select id="currency" name="currency" class="form-control">
                            <option value="AED">UAE Dirham (AED)</option>
                            <option value="USD">US Dollar (USD)</option>
                            <option value="SAR">Saudi Riyal (SAR)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="timezone">Timezone</label>
                        <select id="timezone" name="timezone" class="form-control">
                            <option value="Asia/Dubai">Asia/Dubai</option>
                            <option value="UTC">UTC</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <div class="form-check">
                            <input type="checkbox" id="notifications" class="form-check-input">
                            <label for="notifications" class="form-check-label">Enable Notifications</label>
                        </div>
                    </div>
                    <button type="submit" class="btn btn-primary">Save Settings</button>
                </form>
            </div>
        `;
    }
    
    async loadSectionData(sectionName) {
        switch (sectionName) {
            case 'orders':
                await this.loadOrders();
                this.renderOrdersTable();
                break;
            case 'customers':
                // Don't make API call, content is already created in createCustomersSection
                console.log('Customers section loaded with static data');
                break;
            case 'payments':
                // Don't make API call, content is already created in createPaymentsSection
                console.log('Payments section loaded with static data');
                break;
            case 'analytics':
                // Don't make API call, content is already created in createAnalyticsSection
                console.log('Analytics section loaded with static data');
                break;
            case 'settings':
                // Don't make API call, content is already created in createSettingsSection
                console.log('Settings section loaded with static data');
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
            const currency = this.stats.currency || 'AED';
            const amount = this.stats.total_revenue || 0;
            elements.totalRevenue.innerHTML = this.formatCurrency(amount, currency);
        }
    }
    
    formatCurrency(amount, currency = 'AED') {
        if (currency === 'AED') {
            return `<span class="uae-dirham">د.إ</span> ${amount.toLocaleString('en-AE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        } else if (currency === 'USD') {
            return `$${amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        } else {
            return `${currency} ${amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        }
    }
    
    renderOrdersTable() {
        const tbody = document.getElementById('ordersTableBody');
        if (!tbody) return;
        
        if (this.orders.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center">No orders found</td></tr>';
            return;
        }
        
        tbody.innerHTML = this.orders.map(order => `
            <tr>
                <td>${order.order_number}</td>
                <td>${order.user?.full_name || 'N/A'}</td>
                <td>${order.service_type}</td>
                <td>${this.formatCurrency(order.total_price, order.currency)}</td>
                <td><span class="badge badge-${this.getPaymentStatusColor(order.payment_status)}">${order.payment_status}</span></td>
                <td><span class="badge badge-${this.getStatusColor(order.status)}">${order.status}</span></td>
                <td>${this.formatDate(order.created_at)}</td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="dashboard.viewOrder(${order.id})">View</button>
                    <button class="btn btn-sm btn-success" onclick="dashboard.uploadWork(${order.id})">Upload</button>
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
                <td>${customer.full_name}</td>
                <td>${customer.email}</td>
                <td>${customer.phone || 'N/A'}</td>
                <td>${customer.total_orders}</td>
                <td>${this.formatCurrency(customer.total_spent)}</td>
                <td><span class="badge badge-${customer.status === 'active' ? 'success' : 'secondary'}">${customer.status}</span></td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="dashboard.viewCustomer(${customer.id})">View</button>
                    <button class="btn btn-sm btn-info" onclick="dashboard.contactCustomer(${customer.id})">Contact</button>
                </td>
            </tr>
        `).join('');
    }
    
    renderPaymentsTable() {
        const tbody = document.getElementById('paymentsTableBody');
        if (!tbody) return;
        
        if (this.payments.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center">No payments found</td></tr>';
            return;
        }
        
        tbody.innerHTML = this.payments.map(payment => `
            <tr>
                <td>#${payment.id}</td>
                <td>Order #${payment.order_id}</td>
                <td>${payment.customer}</td>
                <td>${this.formatCurrency(payment.amount, payment.currency)}</td>
                <td>${payment.payment_method}</td>
                <td><span class="badge badge-${this.getPaymentStatusColor(payment.status)}">${payment.status}</span></td>
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
                    <i class="fas fa-plus"></i>
                </div>
                <div class="activity-content">
                    <div class="activity-title">${activity.title}</div>
                    <div class="activity-description">${activity.description}</div>
                </div>
                <div class="activity-time">${this.formatDate(activity.created_at)}</div>
            </div>
        `).join('');
    }
    
    // Utility functions
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }
    
    getStatusColor(status) {
        const colors = {
            'pending': 'warning',
            'paid': 'info',
            'in_progress': 'primary',
            'delivered': 'success',
            'completed': 'success',
            'cancelled': 'danger'
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
    
    updatePendingOrdersBadge() {
        const badge = document.getElementById('pendingOrdersBadge');
        if (badge) {
            const pendingCount = this.orders.filter(order => order.status === 'pending').length;
            badge.textContent = pendingCount;
        }
    }
    
    refreshCurrentSection() {
        this.loadSectionData(this.currentSection);
    }
    
    startAutoRefresh() {
        setInterval(() => {
            if (!this.isLoading && this.currentSection === 'dashboard') {
                this.loadStats();
            }
        }, 30000);
    }
    
    closeAllModals() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.remove('active');
        });
    }
    
    // Placeholder functions for actions
    async viewOrder(orderId) {
        console.log('View order:', orderId);
    }
    
    async uploadWork(orderId) {
        console.log('Upload work for order:', orderId);
    }
    
    async viewCustomer(customerId) {
        console.log('View customer:', customerId);
    }
    
    async contactCustomer(customerId) {
        console.log('Contact customer:', customerId);
    }
    
    async loadAnalytics() {
        console.log('Loading analytics...');
    }
    
    async loadSettings() {
        console.log('Loading settings...');
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
