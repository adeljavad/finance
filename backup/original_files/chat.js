// متغیرهای سراسری
let chatHistory = [];
let isDarkTheme = false;
let currentSessionId = "session_" + Math.random().toString(36).substr(2, 9);
let layoutManager;
let responsiveManager;
let currentChats = [];
let panelsVisible = false;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Chat interface loaded');
    initializeChat();
});

function initializeChat() {
    // پیکربندی marked برای رندر Markdown
    if (typeof marked !== 'undefined') {
        marked.setOptions({
            breaks: true,
            gfm: true,
            langPrefix: 'language-',
            highlight: function(code, lang) {
                if (lang && typeof hljs !== 'undefined' && hljs.getLanguage(lang)) {
                    try {
                        return hljs.highlight(code, { language: lang }).value;
                    } catch (err) {
                        console.error('Error highlighting code:', err);
                    }
                }
                return code;
            }
        });
    } else {
        console.warn('Marked.js not loaded');
    }

    // راه‌اندازی مدیر لایوت
    layoutManager = new LayoutManager();
    
    // راه‌اندازی مدیر ریسپانسیو
    responsiveManager = new ResponsiveManager();
    
    // مدیریت سایدبار
    setupMobileSidebar();
    
    // بارگذاری تاریخچه چت
    loadChatHistory();
    
    // بارگذاری اطلاعات سیستم
    loadSystemInfo();
    setInterval(loadSystemInfo, 30000);
    
    // بارگذاری وضعیت collapsed سایدبار
    loadSidebarCollapseState();

    // راه‌اندازی سیستم drag برای سایدبار
    setupSidebarDrag();

    // بارگذاری ترجیح‌های کاربر
    loadUserPreferences();

    // راه‌اندازی سیستم مخفی/نمایش پانل‌ها
    setupPanelVisibility();

    // اضافه کردن event listener
    const sendButton = document.getElementById('sendButton');
    const messageInput = document.getElementById('messageInput');
    
    if (sendButton) {
        sendButton.addEventListener('click', sendMessage);
    }
    
    if (messageInput) {
        messageInput.addEventListener('keypress', handleKeyPress);
        messageInput.addEventListener('input', handleInputChange);
    }

    // تنظیم ارتفاع اولیه
    setTimeout(() => {
        responsiveManager.adjustLayout();
        layoutManager.adjustChatHeight();
    }, 100);

    console.log('Chat initialized successfully');
}

// کلاس مدیریت لایوت و سایدبار
class LayoutManager {
    constructor() {
        this.leftSidebarVisible = false;
        this.rightSidebarVisible = false;
        this.isRightSidebarCollapsed = localStorage.getItem('rightSidebarCollapsed') === 'true';
        this.init();
    }

    init() {
        this.adjustLayout();
        console.log('Layout Manager initialized');
    }

    toggleLeftSidebar() {
        this.leftSidebarVisible = !this.leftSidebarVisible;
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebarOverlay');
        const mainContent = document.querySelector('.main-content');
        
        if (this.leftSidebarVisible) {
            sidebar.classList.add('active');
            overlay.classList.add('active');
            document.body.classList.add('sidebar-open');
            // بستن سایدبار راست اگر باز است
            if (this.rightSidebarVisible) {
                this.toggleRightSidebar();
            }
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
            // بستن سایدبار چپ اگر باز است
            if (this.leftSidebarVisible) {
                this.toggleLeftSidebar();
            }
        } else {
            sidebar.classList.remove('active');
            overlay.classList.remove('active');
            document.body.classList.remove('sidebar-open');
        }
        
        this.adjustLayout();
    }

    adjustLayout() {
        const rightSidebar = document.getElementById('rightSidebar');
        const chatInputArea = document.querySelector('.chat-input-area');
        const viewportWidth = window.innerWidth;
        
        // تنظیم margin برای محتوای اصلی
        this.adjustMainContentMargin();
        
        // تنظیم position برای input area
        this.adjustInputAreaPosition();
        
        // تنظیم ارتفاع چت
        this.adjustChatHeight();
        
        // در موبایل، overlay را قابل کلیک کن
        if (viewportWidth <= 768) {
            const overlays = document.querySelectorAll('.sidebar-overlay');
            overlays.forEach(overlay => {
                if (overlay.classList.contains('active')) {
                    overlay.style.pointerEvents = 'auto';
                    overlay.addEventListener('click', () => {
                        if (this.leftSidebarVisible) this.toggleLeftSidebar();
                        if (this.rightSidebarVisible) this.toggleRightSidebar();
                    }, { once: true });
                }
            });
        }
    }

    adjustMainContentMargin() {
        const mainContent = document.querySelector('.main-content');
        const rightSidebar = document.getElementById('rightSidebar');
        const leftSidebar = document.getElementById('sidebar');
        
        let marginLeft = 0;
        let marginRight = 0;
        
        if (rightSidebar && rightSidebar.classList.contains('active')) {
            if (rightSidebar.classList.contains('collapsed')) {
                marginLeft = 60;
            } else {
                marginLeft = 320;
            }
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
        
        if (window.innerWidth > 768) {
            if (rightSidebar && rightSidebar.classList.contains('active')) {
                if (rightSidebar.classList.contains('collapsed')) {
                    chatInputArea.style.left = '60px';
                } else {
                    chatInputArea.style.left = '320px';
                }
            } else {
                chatInputArea.style.left = '0';
            }
        } else {
            chatInputArea.style.left = '0';
        }
    }

    adjustChatHeight() {
        const chatArea = document.querySelector('.main-chat-area');
        if (!chatArea) return;
        
        const viewportHeight = window.innerHeight;
        const inputAreaHeight = document.querySelector('.chat-input-area')?.offsetHeight || 100;
        const headerHeight = document.querySelector('.compact-header')?.offsetHeight || 0;
        
        const availableHeight = viewportHeight - inputAreaHeight - headerHeight - 20;
        chatArea.style.height = `${Math.max(availableHeight, 350)}px`;
        
        // اسکرول به آخرین پیام
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            setTimeout(() => {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }, 100);
        }
    }
}

// کلاس مدیریت ریسپانسیو
class ResponsiveManager {
    constructor() {
        this.currentBreakpoint = this.getBreakpoint();
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.adjustLayout();
    }

    getBreakpoint() {
        const width = window.innerWidth;
        if (width < 576) return 'xs';
        if (width < 768) return 'sm';
        if (width < 992) return 'md';
        if (width < 1200) return 'lg';
        if (width < 1400) return 'xl';
        return 'xxl';
    }

    adjustLayout() {
        const breakpoint = this.getBreakpoint();
        
        if (breakpoint !== this.currentBreakpoint) {
            this.currentBreakpoint = breakpoint;
            this.handleBreakpointChange(breakpoint);
        }

        this.adjustChatHeight();
        this.adjustInputLayout();
    }

    handleBreakpointChange(breakpoint) {
        console.log(`Breakpoint changed to: ${breakpoint}`);
        
        switch(breakpoint) {
            case 'xs':
            case 'sm':
                this.handleMobileLayout();
                break;
            case 'md':
                this.handleTabletLayout();
                break;
            case 'lg':
            case 'xl':
            case 'xxl':
                this.handleDesktopLayout();
                break;
        }
    }

    handleMobileLayout() {
        this.adjustChatHeight();
        this.updateButtonLayout();
    }

    handleTabletLayout() {
        this.adjustChatHeight();
        this.updateButtonLayout();
    }

    handleDesktopLayout() {
        this.adjustChatHeight();
        this.updateButtonLayout();
    }

    adjustChatHeight() {
        const chatArea = document.querySelector('.main-chat-area');
        if (!chatArea) return;

        const breakpoint = this.currentBreakpoint;
        let baseHeight;

        switch(breakpoint) {
            case 'xs':
                baseHeight = window.innerHeight - 150;
                break;
            case 'sm':
                baseHeight = window.innerHeight - 180;
                break;
            case 'md':
                baseHeight = window.innerHeight - 220;
                break;
            case 'lg':
                baseHeight = window.innerHeight - 280;
                break;
            default:
                baseHeight = window.innerHeight - 320;
        }

        chatArea.style.height = `${Math.max(baseHeight, 300)}px`;
    }

    adjustInputLayout() {
        const inputArea = document.querySelector('.chat-input-area');
        const messageInput = document.getElementById('messageInput');
        
        if (inputArea && messageInput) {
            const breakpoint = this.currentBreakpoint;
            
            if (breakpoint === 'xs' || breakpoint === 'sm') {
                messageInput.placeholder = "سوال خود را تایپ کنید...";
            } else {
                messageInput.placeholder = "سوال مالی خود را اینجا تایپ کنید... (برای مثال: تحلیل مالی شرکت با دارایی ۲۰۰ میلیارد)";
            }
        }
    }

    updateButtonLayout() {
        const buttons = document.querySelectorAll('.tool-btn, .header-btn');
        const breakpoint = this.currentBreakpoint;
        
        buttons.forEach(btn => {
            if (breakpoint === 'xs' || breakpoint === 'sm') {
                btn.style.fontSize = '12px';
                btn.style.padding = '8px 12px';
            } else {
                btn.style.fontSize = '';
                btn.style.padding = '';
            }
        });
    }

    setupEventListeners() {
        window.addEventListener('resize', () => {
            this.adjustLayout();
        });

        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                this.adjustLayout();
            }, 100);
        });
    }
}

// مدیریت سایدبار
function setupMobileSidebar() {
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    const mainContent = document.querySelector('.main-content');

    if (sidebar && sidebarOverlay && mainContent) {
        sidebarOverlay.addEventListener('click', () => {
            layoutManager.toggleSidebar();
        });

        // بستن سایدبار با کلید ESC
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                if (layoutManager.sidebarVisible) {
                    layoutManager.toggleSidebar();
                }
            }
        });
    }
}

function toggleSidebar() {
    if (layoutManager) {
        layoutManager.toggleLeftSidebar();
    }
}

function toggleRightSidebar() {
    if (layoutManager) {
        layoutManager.toggleRightSidebar();
    }
}

// تابع برای کوچک کردن/بزرگ کردن سایدبار راست
function toggleSidebarCollapse() {
    const rightSidebar = document.getElementById('rightSidebar');
    const collapseBtn = document.getElementById('collapseSidebarBtn');
    const btnIcon = collapseBtn.querySelector('i');
    
    if (!rightSidebar || !collapseBtn) return;
    
    rightSidebar.classList.toggle('collapsed');
    const isCollapsed = rightSidebar.classList.contains('collapsed');
    
    // ذخیره وضعیت
    localStorage.setItem('rightSidebarCollapsed', isCollapsed);
    
    // تغییر آیکون
    btnIcon.className = isCollapsed ? 'fas fa-chevron-left' : 'fas fa-chevron-right';
    collapseBtn.title = isCollapsed ? 'بزرگ کردن' : 'کوچک کردن';
    
    // نمایش/پنهان کردن متن در دکمه‌ها
    document.querySelectorAll('.tool-btn span').forEach(span => {
        span.style.transition = 'opacity 0.3s';
        span.style.opacity = isCollapsed ? '0' : '1';
    });
    
    // تنظیم layout
    if (layoutManager) {
        layoutManager.adjustLayout();
        showNotification(isCollapsed ? 'سایدبار راست کوچک شد' : 'سایدبار راست بزرگ شد', 'info');
    }
}

// تابع برای کوچک کردن/بزرگ کردن سایدبار چپ
function toggleLeftSidebarCollapse() {
    const leftSidebar = document.getElementById('sidebar');
    const collapseBtn = document.getElementById('collapseLeftSidebarBtn');
    const btnIcon = collapseBtn.querySelector('i');
    
    if (!leftSidebar || !collapseBtn) return;
    
    leftSidebar.classList.toggle('collapsed');
    const isCollapsed = leftSidebar.classList.contains('collapsed');
    
    // ذخیره وضعیت
    localStorage.setItem('leftSidebarCollapsed', isCollapsed);
    
    // تغییر آیکون
    btnIcon.className = isCollapsed ? 'fas fa-chevron-left' : 'fas fa-chevron-right';
    collapseBtn.title = isCollapsed ? 'بزرگ کردن' : 'کوچک کردن';
    
    // تنظیم layout
    if (layoutManager) {
        layoutManager.adjustLayout();
        showNotification(isCollapsed ? 'سایدبار چپ کوچک شد' : 'سایدبار چپ بزرگ شد', 'info');
    }
}

// بارگذاری وضعیت collapsed از localStorage
function loadSidebarCollapseState() {
    // سایدبار راست
    const rightSidebar = document.getElementById('rightSidebar');
    const collapseBtn = document.getElementById('collapseSidebarBtn');
    
    if (rightSidebar && collapseBtn) {
        const isCollapsed = localStorage.getItem('rightSidebarCollapsed') === 'true';
        const btnIcon = collapseBtn.querySelector('i');
        
        if (isCollapsed) {
            rightSidebar.classList.add('collapsed');
            if (btnIcon) {
                btnIcon.className = 'fas fa-chevron-right';
                collapseBtn.title = 'بزرگ کردن';
            }
        } else {
            rightSidebar.classList.remove('collapsed');
            if (btnIcon) {
                btnIcon.className = 'fas fa-chevron-left';
                collapseBtn.title = 'کوچک کردن';
            }
        }
    }
    
    // سایدبار چپ
    const leftSidebar = document.getElementById('sidebar');
    const collapseLeftBtn = document.getElementById('collapseLeftSidebarBtn');
    
    if (leftSidebar && collapseLeftBtn) {
        const isCollapsed = localStorage.getItem('leftSidebarCollapsed') === 'true';
        const btnIcon = collapseLeftBtn.querySelector('i');
        
        if (isCollapsed) {
            leftSidebar.classList.add('collapsed');
            if (btnIcon) {
                btnIcon.className = 'fas fa-chevron-left';
                collapseLeftBtn.title = 'بزرگ کردن';
            }
        } else {
            leftSidebar.classList.remove('collapsed');
            if (btnIcon) {
                btnIcon.className = 'fas fa-chevron-right';
                collapseLeftBtn.title = 'کوچک کردن';
            }
        }
    }
}

// مدیریت پانل‌ها
function toggleAllPanels() {
    const panelsContainer = document.querySelector('.collapsible-panels');
    const toggleBtn = document.getElementById('panelsToggleBtn');
    
    panelsVisible = !panelsVisible;
    
    if (panelsVisible) {
        panelsContainer.style.display = 'block';
        toggleBtn.innerHTML = '<i class="fas fa-times"></i> مخفی کردن پانل‌ها';
    } else {
        panelsContainer.style.display = 'none';
        toggleBtn.innerHTML = '<i class="fas fa-bars"></i> نمایش پانل‌ها';
    }
    
    if (layoutManager) {
        layoutManager.adjustChatHeight();
    }
}

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
    
    if (layoutManager) {
        layoutManager.adjustChatHeight();
    }
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
    
    if (sendButton) {
        if (message.length > 0) {
            sendButton.disabled = false;
            sendButton.classList.remove('btn-secondary');
            sendButton.classList.add('btn-primary');
        } else {
            sendButton.disabled = true;
            sendButton.classList.remove('btn-primary');
            sendButton.classList.add('btn-secondary');
        }
    }
}

function sendMessage() {
    console.log('sendMessage called');
    
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    
    if (!message) {
        showNotification('لطفاً پیامی وارد کنید', 'warning');
        return;
    }

    // اضافه کردن پیام کاربر به چت
    addMessageToChat(message, 'user');
    messageInput.value = '';

    // به‌روزرسانی وضعیت دکمه
    const sendButton = document.getElementById('sendButton');
    sendButton.disabled = true;
    sendButton.classList.remove('btn-primary');
    sendButton.classList.add('btn-secondary');
    sendButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span class="hidden sm:inline"> درحال پردازش</span>';

    // نمایش تایپینگ
    showTypingIndicator();

    // ارسال درخواست به سرور با session_id
    fetch('/assistant/api/chat_django/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ 
            message: message,
            session_id: currentSessionId
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        console.log('Response received:', data);
        hideTypingIndicator();
        
        if (data.success) {
            addMessageToChat(data.response, 'bot');
            saveChatToHistory(message, data.response);
        } else {
            addMessageToChat('❌ ' + (data.error || 'خطا در پردازش'), 'bot');
        }
    })
    .catch(error => {
        console.error('Fetch error:', error);
        hideTypingIndicator();
        addMessageToChat('❌ خطا در ارتباط با سرور. لطفاً اتصال اینترنت را بررسی کنید.', 'bot');
    })
    .finally(() => {
        // فعال کردن دکمه ارسال
        const sendButton = document.getElementById('sendButton');
        sendButton.disabled = false;
        sendButton.classList.remove('btn-secondary');
        sendButton.classList.add('btn-primary');
        sendButton.innerHTML = '<i class="fas fa-paper-plane"></i><span class="hidden sm:inline"> ارسال پیام</span>';
        
        // تنظیم مجدد لایوت
        if (layoutManager) {
            setTimeout(() => layoutManager.adjustChatHeight(), 100);
        }
        if (responsiveManager) {
            responsiveManager.adjustLayout();
        }
    });
}

function addMessageToChat(message, sender) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) {
        console.error('chatMessages element not found');
        return;
    }

    const messageDiv = document.createElement('div');
    
    messageDiv.className = `fade-in ${sender === 'user' ? 'message-user' : 'message-bot'} p-3 p-md-4 mb-3`;
    
    if (sender === 'user') {
        messageDiv.innerHTML = `
            <div class="d-flex align-items-start gap-3 justify-content-end">
                <div class="flex-grow-1 text-start">
                    <p class="text-white mb-2 leading-relaxed whitespace-pre-wrap">${escapeHtml(message)}</p>
                    <p class="text-white-70 text-xs mt-2 text-start">${getCurrentTime()}</p>
                </div>
                <div class="bg-gradient-user rounded-2 p-2 flex-shrink-0">
                    <i class="fas fa-user text-white"></i>
                </div>
            </div>
        `;
    } else {
        const formattedMessage = formatBotMessage(message);
        messageDiv.innerHTML = `
            <div class="d-flex align-items-start gap-3">
                <div class="bg-gradient-bot rounded-2 p-2 flex-shrink-0">
                    <i class="fas fa-robot text-white"></i>
                </div>
                <div class="flex-grow-1">
                    <div class="d-flex align-items-center gap-2 mb-2">
                        <h6 class="mb-0 fw-bold">دستیار مالی</h6>
                        <span class="badge bg-primary">پاسخ هوشمند</span>
                    </div>
                    <div class="text-dark leading-relaxed overflow-hidden">${formattedMessage}</div>
                    <p class="text-muted text-xs mt-2 text-start">${getCurrentTime()}</p>
                </div>
            </div>
        `;
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // هایلایت کدها بعد از اضافه شدن به DOM
    if (sender === 'bot' && typeof hljs !== 'undefined') {
        setTimeout(() => {
            document.querySelectorAll('pre code').forEach((block) => {
                hljs.highlightElement(block);
            });
        }, 100);
    }
    
    // ذخیره در تاریخچه
    chatHistory.push({ sender, message, timestamp: new Date().toISOString() });
    
    // تنظیم ارتفاع چت
    if (layoutManager) {
        setTimeout(() => layoutManager.adjustChatHeight(), 50);
    }
}

// مدیریت تاریخچه چت
function saveChatToHistory(question, answer) {
    const chatItem = {
        id: 'chat_' + Date.now(),
        question: question,
        answer: answer,
        timestamp: new Date().toISOString(),
        date: new Date().toLocaleDateString('fa-IR')
    };
    
    currentChats.unshift(chatItem);
    updateChatHistorySidebar();
    saveChatsToLocalStorage();
}

function loadChatHistory() {
    const savedChats = localStorage.getItem('financialAssistantChats');
    if (savedChats) {
        try {
            currentChats = JSON.parse(savedChats);
            updateChatHistorySidebar();
        } catch (error) {
            console.error('Error loading chat history:', error);
            currentChats = [];
        }
    }
}

function saveChatsToLocalStorage() {
    try {
        localStorage.setItem('financialAssistantChats', JSON.stringify(currentChats.slice(0, 50)));
    } catch (error) {
        console.error('Error saving chat history:', error);
        // اگر localStorage پر شده، قدیمی‌ترین چت‌ها رو پاک کن
        if (error.name === 'QuotaExceededError') {
            currentChats = currentChats.slice(0, 25);
            localStorage.setItem('financialAssistantChats', JSON.stringify(currentChats));
        }
    }
}

function updateChatHistorySidebar() {
    const historyContainer = document.getElementById('chatHistoryContainer');
    if (!historyContainer) return;

    if (currentChats.length === 0) {
        historyContainer.innerHTML = `
            <div class="text-center text-muted py-5">
                <i class="fas fa-history fa-3x mb-3 opacity-50"></i>
                <p class="mb-2">تاریخچه‌ای وجود ندارد</p>
                <small class="text-muted">چت‌های شما اینجا نمایش داده می‌شوند</small>
            </div>
        `;
        return;
    }

    let groupedChats = {};
    currentChats.forEach(chat => {
        if (!groupedChats[chat.date]) {
            groupedChats[chat.date] = [];
        }
        groupedChats[chat.date].push(chat);
    });

    let html = '';
    Object.keys(groupedChats).forEach(date => {
        html += `<div class="history-date">${date}</div>`;
        groupedChats[date].forEach(chat => {
            const shortQuestion = chat.question.length > 30 ? 
                chat.question.substring(0, 30) + '...' : chat.question;
            const shortAnswer = chat.answer.length > 50 ? 
                chat.answer.substring(0, 50) + '...' : chat.answer;
            
            html += `
                <div class="chat-history-item" onclick="loadChat('${chat.id}')" data-chat-id="${chat.id}">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <strong class="text-dark">${escapeHtml(shortQuestion)}</strong>
                        <small class="text-muted">${new Date(chat.timestamp).toLocaleTimeString('fa-IR')}</small>
                    </div>
                    <p class="text-muted small mb-0">${escapeHtml(shortAnswer)}</p>
                </div>
            `;
        });
    });

    historyContainer.innerHTML = html;
}

function loadChat(chatId) {
    const chat = currentChats.find(c => c.id === chatId);
    if (!chat) {
        showNotification('چت مورد نظر یافت نشد', 'error');
        return;
    }

    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;

    // پاک کردن چت فعلی
    chatMessages.innerHTML = '';

    // اضافه کردن پیام بارگذاری
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message-bot p-4 fade-in';
    loadingDiv.innerHTML = `
        <div class="d-flex align-items-start gap-3">
            <div class="bg-gradient-bot rounded-2 p-2 flex-shrink-0">
                <i class="fas fa-robot text-white"></i>
            </div>
            <div class="flex-grow-1">
                <div class="d-flex align-items-center gap-2 mb-2">
                    <h6 class="mb-0 fw-bold">دستیار مالی</h6>
                    <span class="badge bg-success">بارگذاری شده</span>
                </div>
                <div class="text-muted">
                    <p class="mb-0">مکالمه بارگذاری شد - ${new Date(chat.timestamp).toLocaleString('fa-IR')}</p>
                </div>
            </div>
        </div>
    `;
    chatMessages.appendChild(loadingDiv);

    // اضافه کردن پیام‌های چت با تاخیر برای اثر بصری
    setTimeout(() => {
        addMessageToChat(chat.question, 'user');
        setTimeout(() => {
            addMessageToChat(chat.answer, 'bot');
        }, 500);
    }, 1000);

    // بستن سایدبار در موبایل
    if (window.innerWidth < 768) {
        toggleSidebar();
    }

    // هایلایت آیتم فعال
    document.querySelectorAll('.chat-history-item').forEach(item => {
        item.classList.remove('active');
        if (item.getAttribute('data-chat-id') === chatId) {
            item.classList.add('active');
        }
    });

    showNotification('چت بارگذاری شد', 'success');
}

function clearChatHistory() {
    if (confirm('آیا از پاک کردن تمام تاریخچه چت اطمینان دارید؟ این عمل قابل بازگشت نیست.')) {
        currentChats = [];
        localStorage.removeItem('financialAssistantChats');
        updateChatHistorySidebar();
        showNotification('تاریخچه چت پاک شد', 'success');
    }
}

function clearChat() {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;

    chatMessages.innerHTML = `
        <div class="message-bot p-4 fade-in">
            <div class="d-flex align-items-start gap-3">
                <div class="bg-gradient-bot rounded-2 p-2 flex-shrink-0">
                    <i class="fas fa-robot text-white"></i>
                </div>
                <div class="flex-grow-1">
                    <div class="d-flex align-items-center gap-2 mb-2">
                        <h6 class="mb-0 fw-bold">دستیار مالی</h6>
                        <span class="badge bg-success">آماده خدمات</span>
                    </div>
                    <div class="text-muted">
                        <p class="mb-2">سلام! 👋 من آماده پاسخگویی به سوالات مالی شما هستم.</p>
                        <p class="mb-0">می‌توانید سوال خود را تایپ کنید یا از ابزارهای تحلیل سریع استفاده نمایید.</p>
                    </div>
                </div>
            </div>
        </div>
    `;
    chatHistory = [];
    
    showNotification('چت فعلی پاک شد', 'info');
}

// توابع ابزارهای تحلیل سریع
function analyzeBalanceSheet() {
    setInputMessage("تحلیل کامل ترازنامه و صورت‌های مالی را انجام بده");
}

function generateFinancialReport() {
    setInputMessage("یک گزارش مالی جامع تهیه کن");
}

function calculateFinancialRatios() {
    setInputMessage("نسبت‌های مالی مهم را محاسبه و تحلیل کن");
}

function analyzeCashFlow() {
    setInputMessage("جریان نقدینگی و وضعیت نقدی را تحلیل کن");
}

function setInputMessage(message) {
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.value = message;
        messageInput.focus();
        
        // به‌روزرسانی وضعیت دکمه
        const sendButton = document.getElementById('sendButton');
        if (sendButton) {
            sendButton.disabled = false;
            sendButton.classList.remove('btn-secondary');
            sendButton.classList.add('btn-primary');
        }
        
        showNotification('پیام در کادر متن قرار داده شد', 'info');
    }
}

        // تابع برای حالت تمام‌صفحه
        function toggleFullscreen() {
            const chatContainer = document.querySelector('.main-chat-area');
            if (chatContainer) {
                chatContainer.classList.toggle('chat-fullscreen');
                
                if (chatContainer.classList.contains('chat-fullscreen')) {
                    showNotification('حالت تمام‌صفحه فعال شد', 'info');
                    // در حالت تمام‌صفحه، پانل‌ها را مخفی کن
                    if (panelsVisible) {
                        toggleAllPanels();
                    }
                } else {
                    showNotification('حالت معمولی فعال شد', 'info');
                }
                
                if (layoutManager) {
                    layoutManager.adjustChatHeight();
                }
                if (responsiveManager) {
                    responsiveManager.adjustLayout();
                }
            }
        }

        // تابع برای باز کردن آپلود فایل
        function openFileUpload() {
            // اول سایدبار راست را باز کن
            if (layoutManager && !layoutManager.rightSidebarVisible) {
                layoutManager.toggleRightSidebar();
            }
            
            // پانل آپلود را باز کن
            const uploadPanel = document.getElementById('uploadPanel');
            if (uploadPanel && uploadPanel.classList.contains('collapsed')) {
                togglePanel('uploadPanel');
            }
            
            // focus روی پانل آپلود
            setTimeout(() => {
                const uploadPanelContent = uploadPanel?.querySelector('.panel-content');
                if (uploadPanelContent) {
                    uploadPanelContent.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }, 300);
            
            showNotification('پانل آپلود فایل باز شد', 'info');
        }

// تابع برای ریفرش لایوت
function refreshLayout() {
    if (responsiveManager) {
        responsiveManager.adjustLayout();
    }
    if (layoutManager) {
        layoutManager.adjustChatHeight();
    }
}

// سایر توابع utility
function formatBotMessage(message) {
    try {
        let htmlContent = message;
        
        if (typeof marked !== 'undefined') {
            htmlContent = marked.parse(message);
        } else {
            htmlContent = escapeHtml(message).replace(/\n/g, '<br>');
        }
        
        htmlContent = enhanceFinancialContent(htmlContent);
        htmlContent = addCustomStyles(htmlContent);
        
        return htmlContent;
        
    } catch (error) {
        console.error('Error formatting message:', error);
        return `<div class="markdown-content">${escapeHtml(message).replace(/\n/g, '<br>')}</div>`;
    }
}

function enhanceFinancialContent(html) {
    // هایلایت اعداد و ارقام مالی
    html = html.replace(/(\d[\d,\.]*)\s*(ریال|تومان|میلیون|میلیارد|هزار)/g, 
        '<span class="financial-number">$1 $2</span>');
    
    // هایلایت کلمات کلیدی مالی
    const financialKeywords = [
        'مالیات', 'درآمد', 'سود', 'زیان', 'دارایی', 'بدهی', 'سرمایه', 
        'ترازنامه', 'صورت مالی', 'نقدینگی', 'نسبت', 'تحلیل', 'گزارش',
        'نقدی', 'سودآوری', 'بازدهی', 'گردش', 'وجه', 'عملیاتی'
    ];
    
    financialKeywords.forEach(keyword => {
        const regex = new RegExp(`(${keyword})`, 'gi');
        html = html.replace(regex, '<span class="keyword-highlight">$1</span>');
    });
    
    // جایگزینی ایموجی با آیکون‌های Font Awesome
    html = html.replace(/✅|✔️/g, '<i class="fas fa-check-circle text-success ml-1"></i>');
    html = html.replace(/⚠️|❌/g, '<i class="fas fa-exclamation-triangle text-warning ml-1"></i>');
    html = html.replace(/📊|📈/g, '<i class="fas fa-chart-line text-primary ml-1"></i>');
    html = html.replace(/💡/g, '<i class="fas fa-lightbulb text-warning ml-1"></i>');
    html = html.replace(/🔧/g, '<i class="fas fa-tools text-secondary ml-1"></i>');
    html = html.replace(/📚/g, '<i class="fas fa-book text-purple ml-1"></i>');
    html = html.replace(/📋/g, '<i class="fas fa-file-alt text-success ml-1"></i>');
    html = html.replace(/💧/g, '<i class="fas fa-tint text-info ml-1"></i>');
    html = html.replace(/🎯/g, '<i class="fas fa-bullseye text-danger ml-1"></i>');
    
    return html;
}

function addCustomStyles(html) {
    // اضافه کردن استایل‌های ریسپانسیو به جداول
    html = html.replace(/<table>/g, '<div class="table-responsive"><table class="table table-bordered table-hover">');
    html = html.replace(/<\/table>/g, '</table></div>');
    
    // اضافه کردن استایل به blockquote
    html = html.replace(/<blockquote>/g, '<blockquote class="blockquote bg-light p-3 rounded border-start border-primary border-4">');
    
    return html;
}

function showTypingIndicator() {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;

    const typingDiv = document.createElement('div');
    typingDiv.id = 'typingIndicator';
    typingDiv.className = 'message-bot p-4 fade-in';
    typingDiv.innerHTML = `
        <div class="d-flex align-items-start gap-3">
            <div class="bg-gradient-bot rounded-2 p-2 flex-shrink-0">
                <i class="fas fa-robot text-white"></i>
            </div>
            <div class="flex-grow-1">
                <div class="d-flex align-items-center gap-2 mb-2">
                    <h6 class="mb-0 fw-bold">دستیار مالی</h6>
                    <span class="badge bg-secondary">درحال تایپ...</span>
                </div>
                <div class="typing-animation">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        </div>
    `;
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// توابع قبلی که تغییر نکرده‌اند
function quickAction(action) {
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.value = action;
        sendMessage();
    }
}

function uploadFile() {
    const fileInput = document.getElementById('fileUpload');
    const file = fileInput.files[0];
    const uploadStatus = document.getElementById('uploadStatus');
    
    if (!file) return;

    const allowedExtensions = ['.xlsx', '.xls', '.csv'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedExtensions.includes(fileExtension)) {
        uploadStatus.innerHTML = `
            <div class="alert alert-danger d-flex align-items-center">
                <i class="fas fa-times-circle ml-2"></i>
                <span>فرمت فایل مجاز نیست. فقط فایل‌های Excel و CSV قابل قبول هستند.</span>
            </div>
        `;
        return;
    }

    if (file.size > 10 * 1024 * 1024) {
        uploadStatus.innerHTML = `
            <div class="alert alert-danger d-flex align-items-center">
                <i class="fas fa-times-circle ml-2"></i>
                <span>حجم فایل نباید بیشتر از ۱۰ مگابایت باشد.</span>
            </div>
        `;
        return;
    }

    uploadStatus.innerHTML = `
        <div class="alert alert-info d-flex align-items-center">
            <i class="fas fa-spinner fa-spin ml-2"></i>
            <span>در حال بررسی و آپلود "${file.name}" ...</span>
        </div>
    `;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', file.name);
    formData.append('file_type', 'accounting_document');

    fetch('/assistant/api/upload/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken()
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            uploadStatus.innerHTML = `
                <div class="alert alert-success">
                    <div class="d-flex align-items-center">
                        <i class="fas fa-check-circle ml-2"></i>
                        <div>
                            <strong>فایل با موفقیت آپلود شد</strong>
                            <div class="mt-1">${data.message}</div>
                            ${data.file_size ? `<small>حجم: ${(data.file_size / 1024).toFixed(2)} KB</small>` : ''}
                        </div>
                    </div>
                </div>
            `;
            showNotification('سند حسابداری با موفقیت افزوده شد', 'success');
            
            setTimeout(() => {
                showNotification('می‌توانید از سیستم تحلیل خودکار اسناد استفاده کنید', 'info');
            }, 2000);
            
        } else {
            uploadStatus.innerHTML = `
                <div class="alert alert-danger">
                    <div class="d-flex align-items-center">
                        <i class="fas fa-times-circle ml-2"></i>
                        <div>
                            <strong>خطا در آپلود فایل</strong>
                            <div class="mt-1">${data.error}</div>
                        </div>
                    </div>
                </div>
            `;
        }
    })
    .catch(error => {
        console.error('Upload error:', error);
        uploadStatus.innerHTML = `
            <div class="alert alert-danger d-flex align-items-center">
                <i class="fas fa-times-circle ml-2"></i>
                <span>خطا در ارتباط با سرور. لطفاً مجدداً تلاش کنید.</span>
            </div>
        `;
    })
    .finally(() => {
        fileInput.value = '';
    });
}

function toggleTheme() {
    isDarkTheme = !isDarkTheme;
    document.body.classList.toggle('dark-theme');
    showNotification(isDarkTheme ? 'تم تیره فعال شد' : 'تم روشن فعال شد', 'info');
}

function showSystemInfo() {
    const modal = document.getElementById('systemInfoModal');
    const content = document.getElementById('systemInfoContent');
    
    if (!modal || !content) return;

    content.innerHTML = `
        <div class="space-y-4">
            <div class="d-flex justify-content-between align-items-center p-3 bg-light rounded">
                <span class="font-semibold">وضعیت سیستم:</span>
                <span class="badge bg-success">فعال</span>
            </div>
            <div class="row text-center">
                <div class="col-6">
                    <div class="p-3 bg-light rounded">
                        <i class="fas fa-database text-primary fs-4 mb-2"></i>
                        <div class="fs-5 fw-bold" id="infoDocuments">0</div>
                        <div class="text-muted small">اسناد</div>
                    </div>
                </div>
                <div class="col-6">
                    <div class="p-3 bg-light rounded">
                        <i class="fas fa-tools text-success fs-4 mb-2"></i>
                        <div class="fs-5 fw-bold">6</div>
                        <div class="text-muted small">ابزار فعال</div>
                    </div>
                </div>
            </div>
            <div class="p-3 bg-info bg-opacity-10 rounded">
                <p class="text-info mb-0 small">
                    <i class="fas fa-info-circle ml-1"></i>
                    سیستم آماده پاسخگویی به سوالات مالی و حسابداری است.
                </p>
            </div>
        </div>
    `;
    
    const modalInstance = new bootstrap.Modal(modal);
    modalInstance.show();
    
    loadSystemInfo();
}

function closeSystemInfo() {
    const modal = document.getElementById('systemInfoModal');
    if (modal) {
        const modalInstance = bootstrap.Modal.getInstance(modal);
        modalInstance.hide();
    }
}

function showSampleData() {
    const messageInput = document.getElementById('messageInput');
    if (!messageInput) return;

    const sampleData = `شرکت نمونه نوآوران
ترازنامه سال ۱۴۰۲
دارایی‌های جاری: ۱۵۰,۰۰۰,۰۰۰,۰۰۰ ریال
دارایی‌های ثابت: ۲۰۰,۰۰۰,۰۰۰,۰۰۰ ریال  
بدهی‌های جاری: ۸۰,۰۰۰,۰۰۰,۰۰۰ ریال
بدهی‌های بلندمدت: ۶۰,۰۰۰,۰۰۰,۰۰۰ ریال
سرمایه: ۲۱۰,۰۰0,۰۰۰,۰۰۰ ریال

صورت سود و زیان
درآمد عملیاتی: ۳۰۰,۰۰۰,۰۰۰,۰۰۰ ریال
هزینه‌های عملیاتی: ۲۲۰,۰۰۰,۰۰۰,۰۰۰ ریال
سود عملیاتی: ۸۰,۰۰۰,۰۰۰,۰۰۰ ریال
سود خالص: ۶۵,۰۰۰,۰۰۰,۰۰۰ ریال`;
    
    messageInput.value = 'تحلیل این داده مالی:\n' + sampleData;
    
    // به‌روزرسانی وضعیت دکمه
    const sendButton = document.getElementById('sendButton');
    if (sendButton) {
        sendButton.disabled = false;
        sendButton.classList.remove('btn-secondary');
        sendButton.classList.add('btn-primary');
    }
    
    showNotification('داده نمونه بارگذاری شد. برای تحلیل ارسال کنید.', 'info');
}

function loadSystemInfo() {
    fetch('/assistant/api/system-info/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const statusElement = document.getElementById('systemStatus');
                const documentsCount = data.rag_info?.total_documents || 0;
                if (statusElement) {
                    statusElement.textContent = `آنلاین - ${documentsCount} سند فعال`;
                }
                
                const infoDocuments = document.getElementById('infoDocuments');
                if (infoDocuments) {
                    infoDocuments.textContent = documentsCount;
                }
            }
        })
        .catch(error => {
            console.error('Error loading system info:', error);
        });
}

function showNotification(message, type = 'info') {
    // ایجاد عنصر اطلاع‌رسانی
    const notification = document.createElement('div');
    const bgColor = type === 'error' ? 'alert-danger' : 
                   type === 'warning' ? 'alert-warning' : 
                   type === 'success' ? 'alert-success' : 'alert-info';
    
    notification.className = `alert ${bgColor} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; left: 20px; right: 20px; z-index: 1060; max-width: 400px; margin: 0 auto;';
    notification.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas fa-${type === 'error' ? 'exclamation-triangle' : type === 'warning' ? 'exclamation-circle' : type === 'success' ? 'check-circle' : 'info-circle'} ml-2"></i>
            <span class="flex-grow-1">${message}</span>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // حذف خودکار پس از 5 ثانیه
    setTimeout(() => {
        if (document.body.contains(notification)) {
            notification.remove();
        }
    }, 5000);
}

function getCsrfToken() {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    return csrfToken ? csrfToken.value : '';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getCurrentTime() {
    const now = new Date();
    return now.toLocaleTimeString('fa-IR', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: false 
    });
}

// توابع مربوط به تمپلیت
function showTemplateInfo() {
    const modal = new bootstrap.Modal(document.getElementById('templateInfoModal'));
    modal.show();
}

function closeTemplateInfo() {
    const modal = bootstrap.Modal.getInstance(document.getElementById('templateInfoModal'));
    if (modal) {
        modal.hide();
    }
}

function downloadTemplate() {
    const templateData = `شماره سند,تاریخ سند,بدهکار,بستانکار,توضیحات,معین
15,1404/01/24,0,2000000000,"بابت واگذار به غیر چک شماره 385640",5
15,1404/01/24,0,500000000,"بابت واگذار به غیر چک شماره 757431",5
15,1404/01/24,0,200000000,"بابت واگذار به غیر چک شماره 948939",5
16,1404/01/25,1500000000,0,"دریافت وجه از صندوق",1
16,1404/01/25,0,1500000000,"واریز به بانک",2`;

    const blob = new Blob([templateData], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', 'تمپلیت_اسناد_حسابداری.csv');
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showNotification('تمپلیت با موفقیت دانلود شد', 'success');
}

// اضافه کردن توابع به scope جهانی
window.toggleFullscreen = toggleFullscreen;
window.analyzeBalanceSheet = analyzeBalanceSheet;
window.generateFinancialReport = generateFinancialReport;
window.calculateFinancialRatios = calculateFinancialRatios;
window.analyzeCashFlow = analyzeCashFlow;
window.toggleSidebar = toggleSidebar;
window.toggleRightSidebar = toggleRightSidebar;
window.toggleSidebarCollapse = toggleSidebarCollapse;
window.toggleLeftSidebarCollapse = toggleLeftSidebarCollapse;
window.loadChat = loadChat;
window.clearChatHistory = clearChatHistory;
window.refreshLayout = refreshLayout;
window.toggleAllPanels = toggleAllPanels;
window.togglePanel = togglePanel;
window.openFileUpload = openFileUpload;

// توابع قبلی در scope جهانی
window.handleKeyPress = handleKeyPress;
window.sendMessage = sendMessage;
window.quickAction = quickAction;
window.uploadFile = uploadFile;
window.clearChat = clearChat;
window.toggleTheme = toggleTheme;
window.showSystemInfo = showSystemInfo;
window.closeSystemInfo = closeSystemInfo;
window.showSampleData = showSampleData;
window.showTemplateInfo = showTemplateInfo;
window.closeTemplateInfo = closeTemplateInfo;
window.downloadTemplate = downloadTemplate;

// ========== توابع جدید برای فاز ۳: ویژگی‌های پیشرفته ==========

// 1. قابلیت drag برای تنظیم عرض سایدبار
function setupSidebarDrag() {
    const rightSidebar = document.getElementById('rightSidebar');
    if (!rightSidebar) return;

    // ایجاد handle برای drag
    const resizeHandle = document.createElement('div');
    resizeHandle.className = 'sidebar-resize-handle';
    resizeHandle.title = 'کشیدن برای تغییر عرض سایدبار';
    rightSidebar.appendChild(resizeHandle);

    let isResizing = false;
    let startX, startWidth;

    function startResize(e) {
        isResizing = true;
        startX = e.clientX || e.touches[0].clientX;
        startWidth = rightSidebar.offsetWidth;
        resizeHandle.classList.add('resizing');
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';

        e.preventDefault();
    }

    function doResize(e) {
        if (!isResizing) return;
        
        const currentX = e.clientX || e.touches[0].clientX;
        const deltaX = currentX - startX;
        
        // در RTL سایدبار راست در سمت چپ است، پس deltaX مثبت یعنی عرض بیشتر
        let newWidth = startWidth + deltaX;
        
        // محدودیت‌های عرض
        newWidth = Math.max(280, Math.min(500, newWidth));
        
        // اعمال عرض جدید
        rightSidebar.style.width = `${newWidth}px`;
        
        // به‌روزرسانی layout
        if (layoutManager) {
            layoutManager.adjustLayout();
        }
        
        e.preventDefault();
    }

    function stopResize() {
        if (!isResizing) return;
        
        isResizing = false;
        resizeHandle.classList.remove('resizing');
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        
        // ذخیره عرض ترجیحی
        const preferredWidth = rightSidebar.offsetWidth;
        localStorage.setItem('sidebarPreferredWidth', preferredWidth);
        
        showNotification(`عرض سایدبار تنظیم شد: ${preferredWidth}px`, 'info');
    }

    // اضافه کردن event listeners
    resizeHandle.addEventListener('mousedown', startResize);
    resizeHandle.addEventListener('touchstart', startResize);
    
    document.addEventListener('mousemove', doResize);
    document.addEventListener('touchmove', doResize);
    
    document.addEventListener('mouseup', stopResize);
    document.addEventListener('touchend', stopResize);
    
    // بارگذاری عرض ترجیحی ذخیره شده
    const savedWidth = localStorage.getItem('sidebarPreferredWidth');
    if (savedWidth && !rightSidebar.classList.contains('collapsed')) {
        rightSidebar.style.width = `${savedWidth}px`;
        if (layoutManager) {
            setTimeout(() => layoutManager.adjustLayout(), 100);
        }
    }
}

// 2. سیستم ذخیره ترجیح‌های کاربر
function loadUserPreferences() {
    // بارگذاری وضعیت پانل‌ها
    const panelStates = JSON.parse(localStorage.getItem('panelStates') || '{}');
    Object.keys(panelStates).forEach(panelId => {
        const panel = document.getElementById(panelId);
        if (panel) {
            if (panelStates[panelId] === 'collapsed') {
                panel.classList.add('collapsed');
                const content = panel.querySelector('.panel-content');
                const btn = panel.querySelector('.collapse-btn i');
                if (content) content.style.maxHeight = '0';
                if (btn) btn.className = 'fas fa-plus';
            } else {
                panel.classList.remove('collapsed');
                const content = panel.querySelector('.panel-content');
                const btn = panel.querySelector('.collapse-btn i');
                if (content) content.style.maxHeight = content.scrollHeight + 'px';
                if (btn) btn.className = 'fas fa-minus';
            }
        }
    });

    // بارگذاری تم
    const savedTheme = localStorage.getItem('preferredTheme');
    if (savedTheme === 'dark') {
        isDarkTheme = true;
        document.body.classList.add('dark-theme');
    }

    // بارگذاری تنظیمات دیگر
    const preferences = JSON.parse(localStorage.getItem('userPreferences') || '{}');
    
    // نمایش badge ترجیح‌ها
    updatePreferenceBadge();
}

function savePanelState(panelId, isCollapsed) {
    const panelStates = JSON.parse(localStorage.getItem('panelStates') || '{}');
    panelStates[panelId] = isCollapsed ? 'collapsed' : 'expanded';
    localStorage.setItem('panelStates', JSON.stringify(panelStates));
}

function saveUserPreference(key, value) {
    const preferences = JSON.parse(localStorage.getItem('userPreferences') || '{}');
    preferences[key] = value;
    localStorage.setItem('userPreferences', JSON.stringify(preferences));
    updatePreferenceBadge();
}

function updatePreferenceBadge() {
    const preferences = JSON.parse(localStorage.getItem('userPreferences') || '{}');
    const panelStates = JSON.parse(localStorage.getItem('panelStates') || '{}');
    
    const totalPreferences = Object.keys(preferences).length + Object.keys(panelStates).length;
    
    const badge = document.getElementById('preferenceBadge') || createPreferenceBadge();
    badge.textContent = `${totalPreferences} ترجیح ذخیره شده`;
}

function createPreferenceBadge() {
    const badge = document.createElement('span');
    badge.id = 'preferenceBadge';
    badge.className = 'preference-badge';
    badge.innerHTML = '<i class="fas fa-cog"></i> 0 ترجیح ذخیره شده';
    
    const statusPanel = document.querySelector('#statusPanel .panel-content');
    if (statusPanel) {
        const existingBadge = statusPanel.querySelector('.preference-badge');
        if (existingBadge) existingBadge.remove();
        statusPanel.appendChild(badge);
    }
    
    return badge;
}

// 3. نمایش وضعیت واقعی سیستم
function updateRealSystemStatus() {
    fetch('/assistant/api/system-status/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateSystemStatusIndicator(data);
            }
        })
        .catch(error => {
            console.error('Error fetching system status:', error);
            setSystemStatusOffline();
        });
}

function updateSystemStatusIndicator(data) {
    const indicator = document.getElementById('systemStatusIndicator') || createSystemStatusIndicator();
    
    if (data.status === 'online') {
        indicator.className = 'system-status-indicator online';
        indicator.innerHTML = `<i class="fas fa-check-circle"></i> آنلاین`;
        
        // نمایش اطلاعات اضافی
        if (data.memory_usage) {
            const memoryPercent = Math.round((data.memory_usage.used / data.memory_usage.total) * 100);
            indicator.title = `استفاده از RAM: ${memoryPercent}% | CPU: ${data.cpu_usage || 'N/A'}%`;
        }
    } else if (data.status === 'offline') {
        indicator.className = 'system-status-indicator offline';
        indicator.innerHTML = `<i class="fas fa-times-circle"></i> آفلاین`;
    } else {
        indicator.className = 'system-status-indicator loading';
        indicator.innerHTML = `<i class="fas fa-spinner fa-spin"></i> در حال بارگذاری`;
    }
}

function createSystemStatusIndicator() {
    const indicator = document.createElement('span');
    indicator.id = 'systemStatusIndicator';
    indicator.className = 'system-status-indicator loading';
    indicator.innerHTML = `<i class="fas fa-spinner fa-spin"></i> در حال بارگذاری`;
    
    const statusElement = document.getElementById('systemStatus');
    if (statusElement) {
        statusElement.parentNode.insertBefore(indicator, statusElement.nextSibling);
    }
    
    return indicator;
}

function setSystemStatusOffline() {
    const indicator = document.getElementById('systemStatusIndicator');
    if (indicator) {
        indicator.className = 'system-status-indicator offline';
        indicator.innerHTML = `<i class="fas fa-times-circle"></i> آفلاین`;
    }
}

// 4. قابلیت مخفی/نمایش انتخابی پانل‌ها
function setupPanelVisibility() {
    const panels = document.querySelectorAll('.panel');
    panels.forEach(panel => {
        const panelId = panel.id;
        const header = panel.querySelector('.panel-header');
        
        // ایجاد دکمه مخفی/نمایش
        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'panel-visibility-toggle';
        toggleBtn.innerHTML = '<i class="fas fa-eye"></i>';
        toggleBtn.title = 'مخفی/نمایش پانل';
        toggleBtn.onclick = (e) => {
            e.stopPropagation();
            togglePanelVisibility(panelId);
        };
        
        header.appendChild(toggleBtn);
        
        // بارگذاری وضعیت ذخیره شده
        const isHidden = localStorage.getItem(`panel_${panelId}_hidden`) === 'true';
        if (isHidden) {
            panel.style.display = 'none';
            toggleBtn.classList.add('hidden');
        }
    });
}

function togglePanelVisibility(panelId) {
    const panel = document.getElementById(panelId);
    const toggleBtn = panel.querySelector('.panel-visibility-toggle');
    
    if (panel.style.display === 'none') {
        panel.style.display = 'block';
        toggleBtn.classList.remove('hidden');
        localStorage.setItem(`panel_${panelId}_hidden`, 'false');
        showNotification(`پانل "${getPanelTitle(panelId)}" نمایش داده شد`, 'success');
    } else {
        panel.style.display = 'none';
        toggleBtn.classList.add('hidden');
        localStorage.setItem(`panel_${panelId}_hidden`, 'true');
        showNotification(`پانل "${getPanelTitle(panelId)}" مخفی شد`, 'info');
    }
    
    if (layoutManager) {
        layoutManager.adjustChatHeight();
    }
}

function getPanelTitle(panelId) {
    const panel = document.getElementById(panelId);
    if (!panel) return panelId;
    
    const header = panel.querySelector('.panel-header h3');
    if (header) {
        return header.textContent.trim();
    }
    return panelId;
}

// اضافه کردن توابع جدید به scope جهانی
window.setupSidebarDrag = setupSidebarDrag;
window.loadUserPreferences = loadUserPreferences;
window.setupPanelVisibility = setupPanelVisibility;
window.togglePanelVisibility = togglePanelVisibility;
window.saveUserPreference = saveUserPreference;

// اضافه کردن event listener برای لود کامل صفحه
window.addEventListener('load', function() {
    // تنظیم نهایی لایوت پس از لود کامل
    setTimeout(() => {
        if (responsiveManager) responsiveManager.adjustLayout();
        if (layoutManager) layoutManager.adjustChatHeight();
        
        // به‌روزرسانی وضعیت سیستم
        updateRealSystemStatus();
        setInterval(updateRealSystemStatus, 60000); // هر 1 دقیقه
        
        // راه‌اندازی پانل‌های سایدبار جدید
        setupSidebarPanels();
        
        // راه‌اندازی دکمه‌های سایدبار موبایل
        setupMobileSidebarButtons();
    }, 500);
});

// ========== توابع جدید برای سایدبار طراحی جدید ==========

// راه‌اندازی پانل‌های سایدبار جدید
function setupSidebarPanels() {
    const panelHeaders = document.querySelectorAll('.sidebar-panel .panel-header');
    
    panelHeaders.forEach(header => {
        // اضافه کردن event listener برای کلیک
        header.addEventListener('click', function(e) {
            // اگر روی آیکون کلیک شده، event را متوقف نکن
            if (e.target.closest('.panel-toggle-icon')) {
                return;
            }
            toggleSidebarPanel(this);
        });
        
        // اضافه کردن event listener برای آیکون
        const toggleIcon = header.querySelector('.panel-toggle-icon');
        if (toggleIcon) {
            toggleIcon.addEventListener('click', function(e) {
                e.stopPropagation();
                toggleSidebarPanel(header);
            });
        }
        
        // بارگذاری وضعیت ذخیره شده
        const panel = header.closest('.sidebar-panel');
        const panelId = header.getAttribute('data-panel');
        if (panelId) {
            const isCollapsed = localStorage.getItem(`sidebarPanel_${panelId}_collapsed`) === 'true';
            if (isCollapsed) {
                panel.classList.add('collapsed');
                const content = panel.querySelector('.panel-content');
                const icon = header.querySelector('.panel-toggle-icon');
                if (content) content.style.maxHeight = '0';
                if (icon) icon.className = 'fas fa-chevron-down panel-toggle-icon';
            }
        }
    });
}

// تابع برای toggle کردن پانل‌های سایدبار
function toggleSidebarPanel(header) {
    const panel = header.closest('.sidebar-panel');
    const content = panel.querySelector('.panel-content');
    const icon = header.querySelector('.panel-toggle-icon');
    const panelId = header.getAttribute('data-panel');
    
    if (panel.classList.contains('collapsed')) {
        // باز کردن پانل
        panel.classList.remove('collapsed');
        content.style.maxHeight = content.scrollHeight + 'px';
        icon.className = 'fas fa-chevron-up panel-toggle-icon';
        
        // ذخیره وضعیت
        if (panelId) {
            localStorage.setItem(`sidebarPanel_${panelId}_collapsed`, 'false');
        }
    } else {
        // بستن پانل
        panel.classList.add('collapsed');
        content.style.maxHeight = '0';
        icon.className = 'fas fa-chevron-down panel-toggle-icon';
        
        // ذخیره وضعیت
        if (panelId) {
            localStorage.setItem(`sidebarPanel_${panelId}_collapsed`, 'true');
        }
    }
    
    // تنظیم مجدد layout
    if (layoutManager) {
        setTimeout(() => layoutManager.adjustChatHeight(), 100);
    }
}

// تابع برای کنترل پانل‌ها (بستن همه به جز یکی) - از اسکریپت کاربر
function togglePanelExclusive(header) {
    const panelContent = header.nextElementSibling;
    const toggleIcon = header.querySelector('.panel-toggle-icon');
    const panelId = header.getAttribute('data-panel');
    
    // بستن همه پانل‌ها به جز این یکی
    document.querySelectorAll('.sidebar-panel .panel-content').forEach(content => {
        if (content !== panelContent) {
            content.style.maxHeight = '0';
            content.previousElementSibling.querySelector('.panel-toggle-icon').className = 'fas fa-chevron-down panel-toggle-icon';
            // علامت‌گذاری به عنوان collapsed
            content.closest('.sidebar-panel').classList.add('collapsed');
        }
    });
    
    // تغییر وضعیت این پانل
    const isExpanded = panelContent.style.maxHeight && panelContent.style.maxHeight !== '0';
    
    if (isExpanded) {
        panelContent.style.maxHeight = '0';
        toggleIcon.className = 'fas fa-chevron-down panel-toggle-icon';
        panelContent.closest('.sidebar-panel').classList.add('collapsed');
    } else {
        panelContent.style.maxHeight = panelContent.scrollHeight + 'px';
        toggleIcon.className = 'fas fa-chevron-up panel-toggle-icon';
        panelContent.closest('.sidebar-panel').classList.remove('collapsed');
    }
    
    // ذخیره وضعیت
    if (panelId) {
        localStorage.setItem(`sidebarPanel_${panelId}_collapsed`, isExpanded ? 'true' : 'false');
    }
    
    // تنظیم مجدد layout
    if (layoutManager) {
        setTimeout(() => layoutManager.adjustChatHeight(), 100);
    }
}

// راه‌اندازی دکمه‌های سایدبار موبایل
function setupMobileSidebarButtons() {
    const openSidebarBtn = document.getElementById('openSidebarBtn');
    const closeSidebarBtn = document.getElementById('closeSidebarBtn');
    const mainSidebarOverlay = document.getElementById('mainSidebarOverlay');
    
    if (openSidebarBtn) {
        openSidebarBtn.addEventListener('click', function() {
            if (layoutManager) {
                layoutManager.toggleRightSidebar();
            }
        });
    }
    
    if (closeSidebarBtn) {
        closeSidebarBtn.addEventListener('click', function() {
            if (layoutManager) {
                layoutManager.toggleRightSidebar();
            }
        });
    }
    
    if (mainSidebarOverlay) {
        mainSidebarOverlay.addEventListener('click', function() {
            if (layoutManager && layoutManager.rightSidebarVisible) {
                layoutManager.toggleRightSidebar();
            }
        });
    }
}

// تابع برای باز کردن همه پانل‌های سایدبار
function expandAllSidebarPanels() {
    const panels = document.querySelectorAll('.sidebar-panel');
    panels.forEach(panel => {
        panel.classList.remove('collapsed');
        const content = panel.querySelector('.panel-content');
        const icon = panel.querySelector('.panel-toggle-icon');
        if (content) content.style.maxHeight = content.scrollHeight + 'px';
        if (icon) icon.className = 'fas fa-chevron-up panel-toggle-icon';
        
        // ذخیره وضعیت
        const panelId = panel.querySelector('.panel-header')?.getAttribute('data-panel');
        if (panelId) {
            localStorage.setItem(`sidebarPanel_${panelId}_collapsed`, 'false');
        }
    });
    
    showNotification('همه پانل‌ها باز شدند', 'info');
}

// تابع برای بستن همه پانل‌های سایدبار
function collapseAllSidebarPanels() {
    const panels = document.querySelectorAll('.sidebar-panel');
    panels.forEach(panel => {
        panel.classList.add('collapsed');
        const content = panel.querySelector('.panel-content');
        const icon = panel.querySelector('.panel-toggle-icon');
        if (content) content.style.maxHeight = '0';
        if (icon) icon.className = 'fas fa-chevron-down panel-toggle-icon';
        
        // ذخیره وضعیت
        const panelId = panel.querySelector('.panel-header')?.getAttribute('data-panel');
        if (panelId) {
            localStorage.setItem(`sidebarPanel_${panelId}_collapsed`, 'true');
        }
    });
    
    showNotification('همه پانل‌ها بسته شدند', 'info');
}

// اضافه کردن توابع جدید به scope جهانی
window.setupSidebarPanels = setupSidebarPanels;
window.toggleSidebarPanel = toggleSidebarPanel;
window.expandAllSidebarPanels = expandAllSidebarPanels;
window.collapseAllSidebarPanels = collapseAllSidebarPanels;
window.setupMobileSidebarButtons = setupMobileSidebarButtons;
window.togglePanelExclusive = togglePanelExclusive;

// ========== event listener اضافی از اسکریپت کاربر ==========

// event listener برای fileUpload (اضافه به سیستم موجود)
document.addEventListener('DOMContentLoaded', function() {
    const fileUpload = document.getElementById('fileUpload');
    if (fileUpload) {
        fileUpload.addEventListener('change', function(e) {
            if (this.files.length > 0) {
                const fileName = this.files[0].name;
                showNotification(`فایل "${fileName}" انتخاب شد. برای آپلود روی دکمه آپلود کلیک کنید.`, 'info');
            }
        });
    }
    
    // event listener برای تغییر اندازه صفحه (اضافه به سیستم موجود)
    window.addEventListener('resize', function() {
        const sidebar = document.getElementById('rightSidebar');
        const sidebarOverlay = document.getElementById('sidebarOverlay');
        
        if (window.innerWidth > 991 && sidebar && sidebar.classList.contains('active')) {
            sidebar.classList.remove('active');
            if (sidebarOverlay) sidebarOverlay.classList.remove('active');
        }
    });
});
