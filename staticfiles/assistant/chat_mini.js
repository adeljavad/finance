// متغیرهای سراسری
let chatHistory = [];
let currentSessionId = "session_" + Math.random().toString(36).substr(2, 9);
let layoutManager, responsiveManager;
let currentChats = [];

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    console.log('Chat system initializing...');
    initializeChat();
});

function initializeChat() {
    // تنظیم marked
    if (typeof marked !== 'undefined') {
        marked.setOptions({
            breaks: true,
            gfm: true,
            highlight: function(code, lang) {
                if (lang && typeof hljs !== 'undefined' && hljs.getLanguage(lang)) {
                    try {
                        return hljs.highlight(code, { language: lang }).value;
                    } catch (err) {
                        console.error('Highlight error:', err);
                    }
                }
                return code;
            }
        });
    }

    // راه‌اندازی مدیران
    layoutManager = new LayoutManager();
    responsiveManager = new ResponsiveManager();

    // بارگذاری داده‌ها
    loadChatHistory();
    loadSystemInfo();
    setInterval(loadSystemInfo, 30000);

    // Event Listeners
    const sendButton = document.getElementById('sendButton');
    const messageInput = document.getElementById('messageInput');
    
    if (sendButton) sendButton.addEventListener('click', sendMessage);
    if (messageInput) {
        messageInput.addEventListener('keypress', handleKeyPress);
        messageInput.addEventListener('input', handleInputChange);
    }

    // تنظیم اولیه layout
    setTimeout(() => {
        layoutManager.adjustLayout();
        responsiveManager.adjustLayout();
    }, 100);
}

// کلاس مدیریت لایوت
class LayoutManager {
    constructor() {
        this.leftSidebarVisible = false;
        this.rightSidebarVisible = false;
        this.isCollapsed = localStorage.getItem('rightSidebarCollapsed') === 'true';
    }

    toggleLeftSidebar() {
        this.leftSidebarVisible = !this.leftSidebarVisible;
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebarOverlay');
        
        if (this.leftSidebarVisible) {
            sidebar.classList.add('active');
            overlay.classList.add('active');
            document.body.classList.add('sidebar-open');
            if (this.rightSidebarVisible) this.toggleRightSidebar();
        } else {
            sidebar.classList.remove('active');
            overlay.classList.remove('active');
            document.body.classList.remove('sidebar-open');
        }
        
        this.adjustLayout();
    }

    toggleRightSidebar() {
        this.rightSidebarVisible = !this.rightSidebarVisible;
        const sidebar = document.getElementById('rightSidebar');
        const overlay = document.getElementById('rightSidebarOverlay');
        
        if (this.rightSidebarVisible) {
            sidebar.classList.add('active');
            overlay.classList.add('active');
            document.body.classList.add('sidebar-open');
            if (this.leftSidebarVisible) this.toggleLeftSidebar();
        } else {
            sidebar.classList.remove('active');
            overlay.classList.remove('active');
            document.body.classList.remove('sidebar-open');
        }
        
        this.adjustLayout();
    }

    adjustLayout() {
        this.adjustMainContentMargin();
        this.adjustInputAreaPosition();
        this.adjustChatHeight();
        this.handleMobileOverlay();
    }

    adjustMainContentMargin() {
        const mainContent = document.querySelector('.main-content');
        const rightSidebar = document.getElementById('rightSidebar');
        const leftSidebar = document.getElementById('sidebar');
        
        let marginLeft = 0, marginRight = 0;
        
        if (rightSidebar && rightSidebar.classList.contains('active')) {
            marginLeft = rightSidebar.classList.contains('collapsed') ? 60 : 320;
        }
        
        if (leftSidebar && leftSidebar.classList.contains('active')) {
            marginRight = 320;
        }
        
        mainContent.style.marginLeft = `${marginLeft}px`;
        mainContent.style.marginRight = `${marginRight}px`;
    }

    adjustInputAreaPosition() {
        const chatInputArea = document.querySelector('.chat-input-area');
        const rightSidebar = document.getElementById('rightSidebar');
        
        if (window.innerWidth > 768 && rightSidebar && rightSidebar.classList.contains('active')) {
            chatInputArea.style.left = rightSidebar.classList.contains('collapsed') ? '60px' : '320px';
        } else {
            chatInputArea.style.left = '0';
        }
    }

    adjustChatHeight() {
        const chatArea = document.querySelector('.main-chat-area');
        if (!chatArea) return;
        
        const viewportHeight = window.innerHeight;
        const inputAreaHeight = document.querySelector('.chat-input-area')?.offsetHeight || 100;
        const availableHeight = viewportHeight - inputAreaHeight - 20;
        
        chatArea.style.height = `${Math.max(availableHeight, 350)}px`;
        
        // اسکرول به آخرین پیام
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            setTimeout(() => {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }, 100);
        }
    }

    handleMobileOverlay() {
        if (window.innerWidth > 768) return;
        
        const overlays = document.querySelectorAll('.sidebar-overlay');
        overlays.forEach(overlay => {
            if (overlay.classList.contains('active')) {
                overlay.style.pointerEvents = 'auto';
                overlay.onclick = () => {
                    if (this.leftSidebarVisible) this.toggleLeftSidebar();
                    if (this.rightSidebarVisible) this.toggleRightSidebar();
                };
            }
        });
    }
}

// کلاس مدیریت ریسپانسیو
class ResponsiveManager {
    constructor() {
        this.currentBreakpoint = this.getBreakpoint();
        window.addEventListener('resize', () => this.adjustLayout());
        window.addEventListener('orientationchange', () => setTimeout(() => this.adjustLayout(), 100));
    }

    getBreakpoint() {
        const width = window.innerWidth;
        if (width < 576) return 'xs';
        if (width < 768) return 'sm';
        if (width < 992) return 'md';
        return 'lg';
    }

    adjustLayout() {
        const newBreakpoint = this.getBreakpoint();
        if (newBreakpoint !== this.currentBreakpoint) {
            this.currentBreakpoint = newBreakpoint;
            console.log(`Breakpoint: ${newBreakpoint}`);
        }
        
        if (layoutManager) layoutManager.adjustLayout();
    }
}

// توابع سایدبار
function toggleSidebar() {
    layoutManager.toggleLeftSidebar();
}

function toggleRightSidebar() {
    layoutManager.toggleRightSidebar();
}

function toggleSidebarCollapse() {
    const rightSidebar = document.getElementById('rightSidebar');
    const collapseBtn = document.getElementById('collapseSidebarBtn');
    const btnIcon = collapseBtn.querySelector('i');
    
    rightSidebar.classList.toggle('collapsed');
    const isCollapsed = rightSidebar.classList.contains('collapsed');
    
    localStorage.setItem('rightSidebarCollapsed', isCollapsed);
    btnIcon.className = isCollapsed ? 'fas fa-chevron-right' : 'fas fa-chevron-left';
    collapseBtn.title = isCollapsed ? 'بزرگ کردن' : 'کوچک کردن';
    
    layoutManager.adjustLayout();
    showNotification(isCollapsed ? 'سایدبار کوچک شد' : 'سایدبار بزرگ شد', 'info');
}

// توابع پانل
function togglePanel(panelId) {
    const panel = document.getElementById(panelId);
    const content = panel.querySelector('.panel-content');
    const btn = panel.querySelector('.collapse-btn i');
    
    if (panel.classList.contains('collapsed')) {
        panel.classList.remove('collapsed');
        content.style.maxHeight = content.scrollHeight + 'px';
        btn.className = 'fas fa-minus';
    } else {
        panel.classList.add('collapsed');
        content.style.maxHeight = '0';
        btn.className = 'fas fa-plus';
    }
    
    layoutManager.adjustLayout();
}

// توابع چت
function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

function handleInputChange(event) {
    const sendButton = document.getElementById('sendButton');
    const message = event.target.value.trim();
    
    sendButton.disabled = message.length === 0;
    sendButton.className = message.length > 0 ? 'btn btn-primary btn-lg flex-grow-1' : 'btn btn-secondary btn-lg flex-grow-1';
}

function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    
    if (!message) {
        showNotification('لطفاً پیامی وارد کنید', 'warning');
        return;
    }

    addMessageToChat(message, 'user');
    messageInput.value = '';
    handleInputChange({ target: messageInput });

    const sendButton = document.getElementById('sendButton');
    sendButton.disabled = true;
    sendButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> درحال پردازش';

    showTypingIndicator();

    fetch('/assistant/api/chat_django/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ message: message, session_id: currentSessionId })
    })
    .then(response => response.json())
    .then(data => {
        hideTypingIndicator();
        if (data.success) {
            addMessageToChat(data.response, 'bot');
            saveChatToHistory(message, data.response);
        } else {
            addMessageToChat('❌ ' + (data.error || 'خطا در پردازش'), 'bot');
        }
        
        sendButton.disabled = false;
        sendButton.innerHTML = '<i class="fas fa-paper-plane ml-2"></i> ارسال';
        
        layoutManager.adjustLayout();
    })
    .catch(error => {
        console.error('Error:', error);
        hideTypingIndicator();
        addMessageToChat('❌ خطا در ارتباط با سرور', 'bot');
        sendButton.disabled = false;
        sendButton.innerHTML = '<i class="fas fa-paper-plane ml-2"></i> ارسال';
    });
}

function addMessageToChat(message, sender) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `fade-in ${sender === 'user' ? 'message-user' : 'message-bot'} p-3 mb-3`;
    
    if (sender === 'user') {
        messageDiv.innerHTML = `
            <div class="d-flex align-items-start gap-3 justify-content-end">
                <div class="flex-grow-1 text-start">
                    <p class="text-white mb-2">${escapeHtml(message)}</p>
                    <small class="text-white-50">${getCurrentTime()}</small>
                </div>
                <div class="bg-gradient-user rounded-2 p-2">
                    <i class="fas fa-user text-white"></i>
                </div>
            </div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="d-flex align-items-start gap-3">
                <div class="bg-gradient-bot rounded-2 p-2">
                    <i class="fas fa-robot text-white"></i>
                </div>
                <div class="flex-grow-1">
                    <h6 class="mb-1 fw-bold">دستیار مالی</h6>
                    <div class="text-dark">${formatBotMessage(message)}</div>
                    <small class="text-muted">${getCurrentTime()}</small>
                </div>
            </div>
        `;
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// توابع utility
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    const bgClass = type === 'error' ? 'alert-danger' : type === 'warning' ? 'alert-warning' : type === 'success' ? 'alert-success' : 'alert-info';
    
    notification.className = `alert ${bgClass} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; left: 20px; right: 20px; z-index: 1060; max-width: 400px; margin: 0 auto;';
    notification.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas fa-${type === 'error' ? 'exclamation-triangle' : type === 'warning' ? 'exclamation-circle' : type === 'success' ? 'check-circle' : 'info-circle'} ml-2"></i>
            <span class="flex-grow-1">${message}</span>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 5000);
}

function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getCurrentTime() {
    return new Date().toLocaleTimeString('fa-IR', { hour: '2-digit', minute: '2-digit' });
}

function formatBotMessage(message) {
    try {
        let html = typeof marked !== 'undefined' ? marked.parse(message) : escapeHtml(message).replace(/\n/g, '<br>');
        return html;
    } catch (e) {
        return escapeHtml(message).replace(/\n/g, '<br>');
    }
}

function showTypingIndicator() {
    const chatMessages = document.getElementById('chatMessages');
    const typingDiv = document.createElement('div');
    typingDiv.id = 'typingIndicator';
    typingDiv.className = 'message-bot p-3 fade-in';
    typingDiv.innerHTML = `
        <div class="d-flex align-items-start gap-3">
            <div class="bg-gradient-bot rounded-2 p-2">
                <i class="fas fa-robot text-white"></i>
            </div>
            <div class="flex-grow-1">
                <div class="typing-animation">
                    <span></span><span></span><span></span>
                </div>
            </div>
        </div>
    `;
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function hideTypingIndicator() {
    document.getElementById('typingIndicator')?.remove();
}

// توابع دیگر (مختصر شده برای خوانایی)
function openFileUpload() {
    if (!layoutManager.rightSidebarVisible) layoutManager.toggleRightSidebar();
    setTimeout(() => togglePanel('uploadPanel'), 300);
    showNotification('پانل آپلود باز شد', 'info');
}

function clearChat() {
    document.getElementById('chatMessages').innerHTML = '';
    chatHistory = [];
    showNotification('چت پاک شد', 'info');
}

function loadSystemInfo() {
    fetch('/assistant/api/system-info/')
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                const statusEl = document.getElementById('systemStatus');
                const docs = data.rag_info?.total_documents || 0;
                if (statusEl) statusEl.textContent = `آنلاین - ${docs} سند فعال`;
            }
        })
        .catch(console.error);
}

// توابع ابزارها
function analyzeBalanceSheet() { setInputMessage("تحلیل کامل ترازنامه را انجام بده"); }
function generateFinancialReport() { setInputMessage("یک گزارش مالی جامع تهیه کن"); }
function calculateFinancialRatios() { setInputMessage("نسبت‌های مالی مهم را محاسبه کن"); }
function analyzeCashFlow() { setInputMessage("جریان نقدینگی را تحلیل کن"); }
function setInputMessage(msg) {
    const input = document.getElementById('messageInput');
    input.value = msg;
    handleInputChange({ target: input });
    input.focus();
}

// اضافه کردن به scope جهانی
window.toggleSidebar = toggleSidebar;
window.toggleRightSidebar = toggleRightSidebar;
window.toggleSidebarCollapse = toggleSidebarCollapse;
window.togglePanel = togglePanel;
window.sendMessage = sendMessage;
window.openFileUpload = openFileUpload;
window.clearChat = clearChat;
window.analyzeBalanceSheet = analyzeBalanceSheet;
window.generateFinancialReport = generateFinancialReport;
window.calculateFinancialRatios = calculateFinancialRatios;
window.analyzeCashFlow = analyzeCashFlow;