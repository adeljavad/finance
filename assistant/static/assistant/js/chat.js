// Financial Assistant Chat System - Improved Version
// حل مشکلات Redis + Session Management

class FinancialAssistant {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.userId = null;
        this.chatHistory = [];
        this.isProcessing = false;
        this.dataManager = new DataManager(this);
        this.retryAttempts = 3;
        this.retryDelay = 1000; // 1 second
        
        this.init();
    }
    
    generateSessionId() {
        // تولید sessionId منحصر به فرد
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    async init() {
        console.log('🚀 Initializing Financial Assistant...');
        
        // بارگذاری session از localStorage
        const savedSession = localStorage.getItem('finance_assistant_session');
        if (savedSession) {
            try {
                const sessionData = JSON.parse(savedSession);
                this.sessionId = sessionData.sessionId || this.sessionId;
                this.userId = sessionData.userId;
                this.chatHistory = sessionData.chatHistory || [];
                console.log('📂 Loaded saved session:', this.sessionId);
            } catch (e) {
                console.warn('⚠️ Error loading saved session:', e);
            }
        }
        
        // ایجاد userId منحصر به فرد
        this.userId = this.userId || this.generateUserId();
        
        // ذخیره session
        this.saveSession();
        
        // بارگذاری UI
        this.loadChatHistory();
        this.updateUploadStatus();
        
        // تست اتصال سیستم
        await this.testSystemConnection();
        
        console.log('✅ Financial Assistant initialized');
    }
    
    generateUserId() {
        // تولید userId منحصر به فرد برای این session
        let userId = localStorage.getItem('finance_assistant_user_id');
        if (!userId) {
            userId = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('finance_assistant_user_id', userId);
        }
        return userId;
    }
    
    saveSession() {
        const sessionData = {
            sessionId: this.sessionId,
            userId: this.userId,
            chatHistory: this.chatHistory,
            timestamp: Date.now()
        };
        
        localStorage.setItem('finance_assistant_session', JSON.stringify(sessionData));
        console.log('💾 Session saved:', this.sessionId);
    }
    
    async testSystemConnection() {
        try {
            console.log('🔧 Testing system connection...');
            const response = await this.makeRequest('/api/system-info/', 'GET');
            
            if (response.success) {
                console.log('✅ System connection successful');
                this.updateSystemStatus('online', response);
            } else {
                console.warn('⚠️ System connection warning:', response);
                this.updateSystemStatus('warning', response);
            }
        } catch (error) {
            console.error('❌ System connection failed:', error);
            this.updateSystemStatus('offline', { error: error.message });
        }
    }
    
    updateSystemStatus(status, info = {}) {
        const statusElement = document.getElementById('system-status');
        if (!statusElement) return;
        
        let statusText = '';
        let statusClass = '';
        
        switch (status) {
            case 'online':
                statusText = '🟢 سیستم آنلاین';
                statusClass = 'status-online';
                break;
            case 'warning':
                statusText = '🟡 هشدار سیستم';
                statusClass = 'status-warning';
                break;
            case 'offline':
                statusText = '🔴 سیستم آفلاین';
                statusClass = 'status-offline';
                break;
        }
        
        statusElement.innerHTML = `
            <span class="${statusClass}">${statusText}</span>
            <button onclick="assistant.showSystemInfo()" class="btn-info">ℹ️ جزئیات</button>
        `;
    }
    
    async showSystemInfo() {
        try {
            const response = await this.makeRequest('/api/system-info/', 'GET');
            
            let infoHtml = '<h3>🔧 اطلاعات سیستم</h3>';
            
            if (response.success) {
                infoHtml += '<div class="system-info">';
                
                // Components status
                if (response.components) {
                    infoHtml += '<h4>وضعیت اجزای سیستم:</h4>';
                    for (const [name, info] of Object.entries(response.components)) {
                        const status = info.status === 'active' || info.status === 'available' ? '✅' : '❌';
                        infoHtml += `<p>${status} ${name}: ${JSON.stringify(info)}</p>`;
                    }
                }
                
                infoHtml += '</div>';
            } else {
                infoHtml += `<p>خطا در دریافت اطلاعات: ${response.error}</p>`;
            }
            
            this.showModal('system-info-modal', infoHtml);
            
        } catch (error) {
            console.error('Error showing system info:', error);
            this.showNotification('خطا در دریافت اطلاعات سیستم', 'error');
        }
    }
    
    async sendMessage(message) {
        if (this.isProcessing) {
            console.log('⚠️ Message processing already in progress');
            return;
        }
        
        if (!message.trim()) {
            console.log('⚠️ Empty message');
            return;
        }
        
        this.isProcessing = true;
        this.showTypingIndicator();
        
        try {
            console.log('💬 Sending message:', message);
            
            // اضافه کردن پیام به تاریخچه
            this.addMessageToHistory('user', message);
            this.displayMessage('user', message);
            
            // ارسال به سرور با retry logic
            const response = await this.sendMessageWithRetry(message);
            
            // پنهان کردن typing indicator
            this.hideTypingIndicator();
            
            if (response.success) {
                console.log('✅ Message processed successfully:', response);
                
                // نمایش پاسخ دستیار
                this.addMessageToHistory('assistant', response.response);
                this.displayMessage('assistant', response.response);
                
                // آپدیت status اطلاعات
                this.updateUploadStatus();
                
                // نمایش tools used اگر موجود باشد
                if (response.tools_used && response.tools_used.length > 0) {
                    this.showNotification(`ابزارهای استفاده شده: ${response.tools_used.join(', ')}`, 'info');
                }
                
            } else {
                console.error('❌ Message processing failed:', response);
                this.showNotification(`خطا: ${response.error}`, 'error');
                
                // نمایش پاسخ خطا
                this.addMessageToHistory('assistant', `متأسفانه خطایی رخ داد: ${response.error}`);
                this.displayMessage('assistant', `متأسفانه خطایی رخ داد: ${response.error}`);
            }
            
            // ذخیره session
            this.saveSession();
            
        } catch (error) {
            console.error('❌ Error sending message:', error);
            this.hideTypingIndicator();
            
            this.showNotification('خطا در ارسال پیام', 'error');
            this.addMessageToHistory('assistant', 'متأسفانه خطایی در ارتباط با سرور رخ داد. لطفاً دوباره تلاش کنید.');
            this.displayMessage('assistant', 'متأسفانه خطایی در ارتباط با سرور رخ داد. لطفاً دوباره تلاش کنید.');
        } finally {
            this.isProcessing = false;
        }
    }
    
    async sendMessageWithRetry(message, attempt = 1) {
        try {
            const requestData = {
                user_message: message,
                session_id: this.sessionId,
                user_id: this.userId
            };
            
            return await this.makeRequest('/api/chat/', 'POST', requestData);
            
        } catch (error) {
            console.error(`❌ Attempt ${attempt} failed:`, error);
            
            if (attempt < this.retryAttempts) {
                console.log(`🔄 Retrying in ${this.retryDelay}ms...`);
                await this.delay(this.retryDelay);
                return this.sendMessageWithRetry(message, attempt + 1);
            } else {
                throw error;
            }
        }
    }
    
    async makeRequest(url, method = 'GET', data = null) {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        };
        
        if (data && method === 'POST') {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(url, options);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    }
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    addMessageToHistory(role, content) {
        this.chatHistory.push({
            role: role,
            content: content,
            timestamp: Date.now()
        });
        
        // محدود کردن تاریخچه به ۵۰ پیام آخر
        if (this.chatHistory.length > 50) {
            this.chatHistory = this.chatHistory.slice(-50);
        }
    }
    
    loadChatHistory() {
        const chatContainer = document.getElementById('chat-messages');
        if (!chatContainer) return;
        
        chatContainer.innerHTML = '';
        
        this.chatHistory.forEach(message => {
            this.displayMessage(message.role, message.content, false);
        });
        
        // اسکرول به پایین
        this.scrollToBottom();
    }
    
    displayMessage(role, content, animate = true) {
        const chatContainer = document.getElementById('chat-messages');
        if (!chatContainer) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message message-${role}`;
        
        if (animate) {
            messageDiv.style.opacity = '0';
            messageDiv.style.transform = 'translateY(20px)';
        }
        
        const avatar = role === 'user' ? '👤' : '🤖';
        const senderName = role === 'user' ? 'شما' : 'دستیار مالی';
        
        messageDiv.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <div class="message-header">
                    <span class="message-sender">${senderName}</span>
                    <span class="message-time">${this.formatTime(new Date())}</span>
                </div>
                <div class="message-text">${this.formatMessage(content)}</div>
            </div>
        `;
        
        chatContainer.appendChild(messageDiv);
        
        if (animate) {
            // انیمیشن ورود
            setTimeout(() => {
                messageDiv.style.transition = 'all 0.3s ease';
                messageDiv.style.opacity = '1';
                messageDiv.style.transform = 'translateY(0)';
            }, 50);
        }
        
        this.scrollToBottom();
    }
    
    formatMessage(content) {
        // تبدیل محتوا به HTML safe
        return content
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>');
    }
    
    formatTime(date) {
        return date.toLocaleTimeString('fa-IR', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }
    
    showTypingIndicator() {
        const chatContainer = document.getElementById('chat-messages');
        if (!chatContainer) return;
        
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.className = 'message message-assistant';
        typingDiv.innerHTML = `
            <div class="message-avatar">🤖</div>
            <div class="message-content">
                <div class="message-header">
                    <span class="message-sender">دستیار مالی</span>
                </div>
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        
        chatContainer.appendChild(typingDiv);
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    scrollToBottom() {
        const chatContainer = document.getElementById('chat-messages');
        if (chatContainer) {
            setTimeout(() => {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }, 100);
        }
    }
    
    updateUploadStatus() {
        // آپدیت status فایل‌های آپلود شده
        this.dataManager.checkUserDataStatus().then(data => {
            const statusElement = document.getElementById('upload-status');
            if (statusElement) {
                if (data.has_data) {
                    statusElement.innerHTML = `
                        <div class="upload-status success">
                            📁 <strong>${data.total_files}</strong> فایل آپلود شده
                            <br>📊 <strong>${data.total_records}</strong> رکورد موجود
                            <br>💾 ${data.storage_type}
                        </div>
                    `;
                } else {
                    statusElement.innerHTML = `
                        <div class="upload-status empty">
                            📂 هیچ فایلی آپلود نشده است
                            <br><small>برای تحلیل داده‌ها، فایل اکسل آپلود کنید</small>
                        </div>
                    `;
                }
            }
        }).catch(error => {
            console.error('Error updating upload status:', error);
        });
    }
    
    showNotification(message, type = 'info') {
        // نمایش notification
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // انیمیشن ورود
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
        
        // حذف خودکار بعد از 5 ثانیه
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 5000);
    }
    
    showModal(modalId, content) {
        let modal = document.getElementById(modalId);
        if (!modal) {
            modal = document.createElement('div');
            modal.id = modalId;
            modal.className = 'modal';
            document.body.appendChild(modal);
        }
        
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>جزئیات</h3>
                    <button onclick="this.closest('.modal').style.display='none'" class="modal-close">×</button>
                </div>
                <div class="modal-body">
                    ${content}
                </div>
            </div>
        `;
        
        modal.style.display = 'block';
        
        // بستن با کلیک روی بک‌گراند
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });
    }
    
    clearChat() {
        if (confirm('آیا مطمئن هستید که می‌خواهید تاریخچه چت را پاک کنید؟')) {
            this.chatHistory = [];
            this.saveSession();
            
            const chatContainer = document.getElementById('chat-messages');
            if (chatContainer) {
                chatContainer.innerHTML = '';
            }
            
            // پاک کردن در سرور
            this.makeRequest('/api/clear-chat/', 'POST', {
                session_id: this.sessionId
            }).then(response => {
                if (response.success) {
                    this.showNotification('تاریخچه چت پاک شد', 'success');
                }
            }).catch(error => {
                console.error('Error clearing chat:', error);
            });
        }
    }
    
    newSession() {
        if (confirm('آیا می‌خواهید جلسه جدیدی شروع کنید؟')) {
            this.sessionId = this.generateSessionId();
            this.chatHistory = [];
            this.saveSession();
            
            const chatContainer = document.getElementById('chat-messages');
            if (chatContainer) {
                chatContainer.innerHTML = '';
            }
            
            this.showNotification('جلسه جدید ایجاد شد', 'success');
        }
    }
    
    debugSession() {
        const debugInfo = {
            sessionId: this.sessionId,
            userId: this.userId,
            chatHistory: this.chatHistory.length,
            timestamp: new Date().toISOString()
        };
        
        let debugHtml = '<h3>🔍 اطلاعات دیباگ</h3>';
        debugHtml += '<div class="debug-info">';
        
        for (const [key, value] of Object.entries(debugInfo)) {
            debugHtml += `<p><strong>${key}:</strong> ${JSON.stringify(value)}</p>`;
        }
        
        debugHtml += '</div>';
        
        debugHtml += '<button onclick="assistant.showServerDebug()" class="btn-primary">🔧 دیباگ سرور</button>';
        
        this.showModal('debug-modal', debugHtml);
    }
    
    async showServerDebug() {
        try {
            const response = await this.makeRequest('/debug/', 'GET', {
                user_id: this.userId
            });
            
            let debugHtml = '<h3>🔧 دیباگ سرور</h3>';
            
            if (response.success) {
                debugHtml += '<div class="server-debug">';
                debugHtml += '<h4>وضعیت سیستم:</h4>';
                debugHtml += `<pre>${JSON.stringify(response.system_status, null, 2)}</pre>`;
                
                debugHtml += '<h4>داده‌های کاربر:</h4>';
                debugHtml += `<pre>${JSON.stringify(response.user_data, null, 2)}</pre>`;
                debugHtml += '</div>';
            } else {
                debugHtml += `<p>خطا: ${response.error}</p>`;
            }
            
            const debugModal = document.getElementById('debug-modal');
            if (debugModal) {
                const modalBody = debugModal.querySelector('.modal-body');
                modalBody.innerHTML = debugHtml;
            }
            
        } catch (error) {
            console.error('Error in server debug:', error);
            this.showNotification('خطا در دیباگ سرور', 'error');
        }
    }
}

// Data Manager Class
class DataManager {
    constructor(assistant) {
        this.assistant = assistant;
    }
    
    async checkUserDataStatus() {
        try {
            const response = await this.assistant.makeRequest('/api/session-info/', 'GET', {
                session_id: this.assistant.sessionId
            });
            
            if (response.success) {
                return {
                    has_data: response.has_data,
                    total_files: response.uploaded_files ? response.uploaded_files.length : 0,
                    total_records: response.dataframes ? Object.keys(response.dataframes).length : 0,
                    storage_type: 'Active'
                };
            }
            
            return {
                has_data: false,
                total_files: 0,
                total_records: 0,
                storage_type: 'Unknown'
            };
            
        } catch (error) {
            console.error('Error checking user data status:', error);
            return {
                has_data: false,
                total_files: 0,
                total_records: 0,
                storage_type: 'Error'
            };
        }
    }
    
    async uploadFile(file) {
        if (!file) {
            throw new Error('فایل انتخاب نشده است');
        }
        
        // بررسی نوع فایل
        const allowedTypes = ['.xlsx', '.xls', '.csv'];
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        
        if (!allowedTypes.includes(fileExtension)) {
            throw new Error('فرمت فایل پشتیبانی نمی‌شود. فقط Excel و CSV مجاز هستند.');
        }
        
        // بررسی اندازه فایل (حداکثر 50MB)
        if (file.size > 50 * 1024 * 1024) {
            throw new Error('فایل بسیار بزرگ است. حداکثر اندازه 50 مگابایت است.');
        }
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('user_id', this.assistant.userId);
        formData.append('session_id', this.assistant.sessionId);
        
        // نمایش progress
        this.showUploadProgress();
        
        try {
            const response = await fetch('/api/upload/', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            this.hideUploadProgress();
            
            if (result.success) {
                this.assistant.showNotification(`فایل ${file.name} با موفقیت آپلود شد`, 'success');
                this.assistant.updateUploadStatus();
                return result;
            } else {
                throw new Error(result.error || 'خطا در آپلود فایل');
            }
            
        } catch (error) {
            this.hideUploadProgress();
            console.error('Upload error:', error);
            this.assistant.showNotification(`خطا در آپلود: ${error.message}`, 'error');
            throw error;
        }
    }
    
    showUploadProgress() {
        const progressBar = document.getElementById('upload-progress');
        if (progressBar) {
            progressBar.style.display = 'block';
            progressBar.innerHTML = `
                <div class="progress-bar">
                    <div class="progress-fill" style="width: 100%"></div>
                </div>
                <p>در حال پردازش فایل...</p>
            `;
        }
    }
    
    hideUploadProgress() {
        const progressBar = document.getElementById('upload-progress');
        if (progressBar) {
            progressBar.style.display = 'none';
        }
    }
}

// Initialize Assistant
let assistant;

document.addEventListener('DOMContentLoaded', function() {
    console.log('📱 DOM loaded, initializing assistant...');
    assistant = new FinancialAssistant();
    
    // Event Listeners
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const fileInput = document.getElementById('file-input');
    const clearChatButton = document.getElementById('clear-chat');
    const newSessionButton = document.getElementById('new-session');
    const debugButton = document.getElementById('debug-session');
    
    // Send message
    if (sendButton && messageInput) {
        sendButton.addEventListener('click', function() {
            const message = messageInput.value.trim();
            if (message) {
                assistant.sendMessage(message);
                messageInput.value = '';
                sendButton.disabled = true;
            }
        });
        
        // Send on Enter (without Shift)
        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey && !e.ctrlKey && !e.metaKey) {
                e.preventDefault();
                const message = messageInput.value.trim();
                if (message) {
                    assistant.sendMessage(message);
                    messageInput.value = '';
                    sendButton.disabled = true;
                }
            }
        });
    }
    
    // File upload - handle click on upload area (already handled in HTML inline JS)
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const file = fileInput.files[0];
            if (file) {
                assistant.dataManager.uploadFile(file);
                fileInput.value = ''; // Reset input
            }
        });
    }
    
    // Clear chat
    if (clearChatButton) {
        clearChatButton.addEventListener('click', function() {
            assistant.clearChat();
        });
    }
    
    // New session
    if (newSessionButton) {
        newSessionButton.addEventListener('click', function() {
            assistant.newSession();
        });
    }
    
    // Debug
    if (debugButton) {
        debugButton.addEventListener('click', function() {
            assistant.debugSession();
        });
    }
    
    console.log('✅ Event listeners attached');
});
