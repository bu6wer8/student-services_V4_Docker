// API Communication Module

class ApiClient {
    constructor(baseURL = '/api') {
        this.baseURL = baseURL;
        this.defaultHeaders = {
            'Content-Type': 'application/json',
        };
        this.interceptors = {
            request: [],
            response: []
        };
        
        this.setupAxiosDefaults();
    }
    
    setupAxiosDefaults() {
        if (typeof axios !== 'undefined') {
            // Set default base URL
            axios.defaults.baseURL = this.baseURL;
            
            // Request interceptor
            axios.interceptors.request.use(
                (config) => {
                    // Add auth token if available
                    const token = this.getAuthToken();
                    if (token) {
                        config.headers.Authorization = `Bearer ${token}`;
                    }
                    
                    // Add admin token for admin endpoints
                    if (config.url.includes('/admin/')) {
                        const adminToken = this.getAdminToken();
                        if (adminToken) {
                            config.headers['X-Admin-Token'] = adminToken;
                        }
                    }
                    
                    // Run custom request interceptors
                    this.interceptors.request.forEach(interceptor => {
                        config = interceptor(config);
                    });
                    
                    return config;
                },
                (error) => {
                    return Promise.reject(error);
                }
            );
            
            // Response interceptor
            axios.interceptors.response.use(
                (response) => {
                    // Run custom response interceptors
                    this.interceptors.response.forEach(interceptor => {
                        response = interceptor(response);
                    });
                    
                    return response;
                },
                (error) => {
                    this.handleResponseError(error);
                    return Promise.reject(error);
                }
            );
        }
    }
    
    // Authentication methods
    getAuthToken() {
        return localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
    }
    
    setAuthToken(token, remember = false) {
        if (remember) {
            localStorage.setItem('auth_token', token);
        } else {
            sessionStorage.setItem('auth_token', token);
        }
    }
    
    removeAuthToken() {
        localStorage.removeItem('auth_token');
        sessionStorage.removeItem('auth_token');
    }
    
    getAdminToken() {
        return localStorage.getItem('admin_token') || 'admin-secret-token'; // Default for development
    }
    
    setAdminToken(token) {
        localStorage.setItem('admin_token', token);
    }
    
    // HTTP Methods
    async get(url, config = {}) {
        try {
            const response = await axios.get(url, config);
            return this.handleResponse(response);
        } catch (error) {
            throw this.handleError(error);
        }
    }
    
    async post(url, data = {}, config = {}) {
        try {
            const response = await axios.post(url, data, config);
            return this.handleResponse(response);
        } catch (error) {
            throw this.handleError(error);
        }
    }
    
    async put(url, data = {}, config = {}) {
        try {
            const response = await axios.put(url, data, config);
            return this.handleResponse(response);
        } catch (error) {
            throw this.handleError(error);
        }
    }
    
    async patch(url, data = {}, config = {}) {
        try {
            const response = await axios.patch(url, data, config);
            return this.handleResponse(response);
        } catch (error) {
            throw this.handleError(error);
        }
    }
    
    async delete(url, config = {}) {
        try {
            const response = await axios.delete(url, config);
            return this.handleResponse(response);
        } catch (error) {
            throw this.handleError(error);
        }
    }
    
    // File upload method
    async uploadFile(url, file, onProgress = null) {
        const formData = new FormData();
        formData.append('file', file);
        
        const config = {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
            onUploadProgress: (progressEvent) => {
                if (onProgress) {
                    const percentCompleted = Math.round(
                        (progressEvent.loaded * 100) / progressEvent.total
                    );
                    onProgress(percentCompleted);
                }
            }
        };
        
        return this.post(url, formData, config);
    }
    
    // Multiple file upload
    async uploadFiles(url, files, onProgress = null) {
        const formData = new FormData();
        Array.from(files).forEach((file, index) => {
            formData.append(`files`, file);
        });
        
        const config = {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
            onUploadProgress: (progressEvent) => {
                if (onProgress) {
                    const percentCompleted = Math.round(
                        (progressEvent.loaded * 100) / progressEvent.total
                    );
                    onProgress(percentCompleted);
                }
            }
        };
        
        return this.post(url, formData, config);
    }
    
    // Response handlers
    handleResponse(response) {
        if (response.data && response.data.success === false) {
            throw new Error(response.data.message || 'API request failed');
        }
        // Return the data portion if it exists, otherwise return the full response data
        return response.data && response.data.data ? response.data.data : response.data;
    }
    
    handleError(error) {
        const errorInfo = {
            message: 'An error occurred',
            status: null,
            data: null
        };
        
        if (error.response) {
            // Server responded with error status
            errorInfo.status = error.response.status;
            errorInfo.data = error.response.data;
            errorInfo.message = error.response.data?.message || `HTTP ${error.response.status}`;
        } else if (error.request) {
            // Request was made but no response received
            errorInfo.message = 'Network error - please check your connection';
        } else {
            // Something else happened
            errorInfo.message = error.message;
        }
        
        return errorInfo;
    }
    
    handleResponseError(error) {
        if (error.response) {
            switch (error.response.status) {
                case 401:
                    this.handleUnauthorized();
                    break;
                case 403:
                    this.handleForbidden();
                    break;
                case 404:
                    this.handleNotFound();
                    break;
                case 500:
                    this.handleServerError();
                    break;
                default:
                    this.handleGenericError(error);
            }
        }
    }
    
    handleUnauthorized() {
        console.warn('Unauthorized access - redirecting to login');
        this.removeAuthToken();
        // Could redirect to login page here
    }
    
    handleForbidden() {
        console.warn('Access forbidden');
        if (window.uiComponents) {
            window.uiComponents.showToast('Access denied', 'error');
        }
    }
    
    handleNotFound() {
        console.warn('Resource not found');
        if (window.uiComponents) {
            window.uiComponents.showToast('Resource not found', 'error');
        }
    }
    
    handleServerError() {
        console.error('Server error');
        if (window.uiComponents) {
            window.uiComponents.showToast('Server error - please try again later', 'error');
        }
    }
    
    handleGenericError(error) {
        console.error('API Error:', error);
        if (window.uiComponents) {
            const message = error.response?.data?.message || 'An error occurred';
            window.uiComponents.showToast(message, 'error');
        }
    }
    
    // Interceptor methods
    addRequestInterceptor(interceptor) {
        this.interceptors.request.push(interceptor);
    }
    
    addResponseInterceptor(interceptor) {
        this.interceptors.response.push(interceptor);
    }
    
    // Utility methods
    buildQueryString(params) {
        const searchParams = new URLSearchParams();
        Object.keys(params).forEach(key => {
            if (params[key] !== null && params[key] !== undefined) {
                searchParams.append(key, params[key]);
            }
        });
        return searchParams.toString();
    }
    
    async downloadFile(url, filename) {
        try {
            const response = await axios.get(url, {
                responseType: 'blob'
            });
            
            const blob = new Blob([response.data]);
            const downloadUrl = window.URL.createObjectURL(blob);
            
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            window.URL.revokeObjectURL(downloadUrl);
        } catch (error) {
            throw this.handleError(error);
        }
    }
    
    // Connection status
    async checkConnection() {
        try {
            await this.get('/health');
            return true;
        } catch (error) {
            return false;
        }
    }
    
    // Retry mechanism
    async retryRequest(requestFn, maxRetries = 3, delay = 1000) {
        let lastError;
        
        for (let i = 0; i < maxRetries; i++) {
            try {
                return await requestFn();
            } catch (error) {
                lastError = error;
                if (i < maxRetries - 1) {
                    await this.delay(delay * Math.pow(2, i)); // Exponential backoff
                }
            }
        }
        
        throw lastError;
    }
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// API Endpoints
class AdminAPI extends ApiClient {
    constructor() {
        super('/api');
    }
    
    // Dashboard endpoints
    async getDashboardStats() {
        return this.get('/dashboard/stats');
    }
    
    async getRecentActivity() {
        return this.get('/dashboard/activity');
    }
    
    // Order endpoints
    async getOrders(params = {}) {
        const queryString = this.buildQueryString(params);
        return this.get(`/orders${queryString ? '?' + queryString : ''}`);
    }
    
    async getOrder(orderId) {
        return this.get(`/orders/${orderId}`);
    }
    
    async updateOrderStatus(orderId, data) {
        return this.put(`/orders/${orderId}/status`, data);
    }
    
    async deleteOrder(orderId) {
        return this.delete(`/orders/${orderId}`);
    }
    
    async archiveOrder(orderId) {
        return this.put(`/orders/${orderId}/archive`);
    }
    
    async uploadWorkFiles(orderId, files, onProgress) {
        return this.uploadFiles(`/orders/${orderId}/upload`, files, onProgress);
    }
    
    async contactCustomer(orderId, data) {
        return this.post(`/orders/${orderId}/contact`, data);
    }
    
    async notifyCustomer(orderId, data) {
        return this.post(`/orders/${orderId}/notify`, data);
    }
    
    // Payment endpoints
    async confirmPayment(paymentId) {
        return this.post(`/payments/${paymentId}/confirm`);
    }
    
    async checkPaymentStatus(orderId) {
        return this.get(`/payments/check/${orderId}`);
    }
    
    async createRefund(paymentId, data) {
        return this.post(`/payments/${paymentId}/refund`, data);
    }
    
    // Customer endpoints
    async getCustomers(params = {}) {
        const queryString = this.buildQueryString(params);
        return this.get(`/customers${queryString ? '?' + queryString : ''}`);
    }
    
    async getCustomer(customerId) {
        return this.get(`/customers/${customerId}`);
    }
    
    async updateCustomer(customerId, data) {
        return this.put(`/customers/${customerId}`, data);
    }
    
    // Admin endpoints
    async resetDatabase() {
        return this.post('/admin/reset-database');
    }
    
    async exportData(type = 'orders') {
        return this.get(`/admin/export/${type}`);
    }
    
    async getSystemSettings() {
        return this.get('/admin/settings');
    }
    
    async updateSystemSettings(data) {
        return this.put('/admin/settings', data);
    }
    
    async getAdminLogs(params = {}) {
        const queryString = this.buildQueryString(params);
        return this.get(`/admin/logs${queryString ? '?' + queryString : ''}`);
    }
    
    // Analytics endpoints
    async getAnalytics(period = '30d') {
        return this.get(`/analytics?period=${period}`);
    }
    
    async getRevenueStats(period = '30d') {
        return this.get(`/analytics/revenue?period=${period}`);
    }
    
    async getOrderStats(period = '30d') {
        return this.get(`/analytics/orders?period=${period}`);
    }
    
    async getCustomerStats(period = '30d') {
        return this.get(`/analytics/customers?period=${period}`);
    }
    
    // File management endpoints
    async uploadFile(file, onProgress) {
        return this.uploadFile('/files/upload', file, onProgress);
    }
    
    async deleteFile(fileId) {
        return this.delete(`/files/${fileId}`);
    }
    
    async getFileInfo(fileId) {
        return this.get(`/files/${fileId}/info`);
    }
    
    // Notification endpoints
    async sendBroadcast(data) {
        return this.post('/notifications/broadcast', data);
    }
    
    async getNotificationHistory(params = {}) {
        const queryString = this.buildQueryString(params);
        return this.get(`/notifications/history${queryString ? '?' + queryString : ''}`);
    }
    
    // Webhook endpoints
    async getWebhookLogs(params = {}) {
        const queryString = this.buildQueryString(params);
        return this.get(`/webhooks/logs${queryString ? '?' + queryString : ''}`);
    }
    
    async retryWebhook(webhookId) {
        return this.post(`/webhooks/${webhookId}/retry`);
    }
}

// Connection monitor
class ConnectionMonitor {
    constructor(api) {
        this.api = api;
        this.isOnline = navigator.onLine;
        this.checkInterval = null;
        this.statusElement = null;
        
        this.init();
    }
    
    init() {
        this.statusElement = document.getElementById('connectionStatus');
        this.updateStatus();
        this.startMonitoring();
        
        // Listen for online/offline events
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.updateStatus();
        });
        
        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.updateStatus();
        });
    }
    
    startMonitoring() {
        this.checkInterval = setInterval(async () => {
            if (this.isOnline) {
                try {
                    const isConnected = await this.api.checkConnection();
                    if (!isConnected && this.isOnline) {
                        this.isOnline = false;
                        this.updateStatus();
                    }
                } catch (error) {
                    if (this.isOnline) {
                        this.isOnline = false;
                        this.updateStatus();
                    }
                }
            }
        }, 30000); // Check every 30 seconds
    }
    
    updateStatus() {
        if (this.statusElement) {
            if (this.isOnline) {
                this.statusElement.className = 'connection-status';
                this.statusElement.innerHTML = '<i class="fas fa-circle"></i><span>Connected</span>';
            } else {
                this.statusElement.className = 'connection-status error';
                this.statusElement.innerHTML = '<i class="fas fa-circle"></i><span>Disconnected</span>';
            }
        }
    }
    
    destroy() {
        if (this.checkInterval) {
            clearInterval(this.checkInterval);
        }
    }
}

// Initialize API client
document.addEventListener('DOMContentLoaded', () => {
    window.api = new AdminAPI();
    window.connectionMonitor = new ConnectionMonitor(window.api);
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ApiClient, AdminAPI, ConnectionMonitor };
}
