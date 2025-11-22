document.addEventListener('DOMContentLoaded', function () {
    // عناصر DOM
    const chatForm = document.getElementById('chat-form');
    const chatBox = document.getElementById('chat-box');
    const messageInput = document.getElementById('message');
    const currentModelElement = document.getElementById('currentModel');
    const csrftoken = getCookie('csrftoken');

    // توابع کمکی
    function getCookie(name) {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                return decodeURIComponent(cookie.substring(name.length + 1));
            }
        }
        return null;
    }

    function addMessage(content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add(type === 'user' ? 'chatbot-user-message' : 'chatbot-bot-response');
    
        if(type === 'bot') {
            messageDiv.innerHTML = `
                <div class="message-content">${content}</div>
                <button class="copy-btn">
                    <i class="fas fa-copy">کپی</i>
                </button>
            `;
        } else {
            messageDiv.textContent = content;
        }
    
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    
        // اضافه کردن قابلیت کپی
        if(type === 'bot') {
            const copyBtn = messageDiv.querySelector('.copy-btn');
            copyBtn.addEventListener('click', () => {
                copyToClipboard(content);
                sendToServer(content); // اختیاری - برای ارسال به سرور
            });
        }
    }
    
    // تابع کپی به کلیپ‌برد
    function copyToClipboard(text) {
        navigator.clipboard.writeText(text)
            .then(() => showToast('متن با موفقیت کپی شد!', 'success'))
            .catch(err => showToast('خطا در کپی کردن متن', 'danger'));
    }
    
    // تابع ارسال به سرور (اختیاری)
    async function sendToServer(text) {
        try {
            const response = await fetch('/save_to_sql/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify({text: text})
            });
            
            const data = await response.json();
            if(!response.ok) throw new Error(data.message);
        } catch (error) {
            console.error('خطا در ارسال به سرور:', error);
        }
    }
    
    // function addMessage(content, type) {
    //     const messageDiv = document.createElement('div');
    //     messageDiv.classList.add(type === 'user' ? 'chatbot-user-message' : 'chatbot-bot-response');
    //     // messageDiv.className = `flex ${isUser ? 'justify-end' : 'justify-start'}`;
    //     // messageDiv.innerHTML = `
    //     //     <div class="${isUser ? 'bg-indigo-600 text-white' : 'bg-white'} 
    //     //                 p-3 rounded-lg max-w-xs md:max-w-md lg:max-w-lg 
    //     //                 shadow-md animate__animated animate__fadeInUp">
    //     //         ${content}
    //     //     </div>
    //     // `;

    //     if (type === 'error') {
    //         messageDiv.classList.add('error-message');
    //     }

    //     messageDiv.textContent = content;
    //     chatBox.appendChild(messageDiv);
    //     chatBox.scrollTop = chatBox.scrollHeight;
    // }
// نمونه کد برای نمایش پیام با انیمیشن
// function addMessage(content, isUser) {
//     const chatContainer = document.getElementById('chat-container');
//     const messageDiv = document.createElement('div');
    
//     messageDiv.className = `flex ${isUser ? 'justify-end' : 'justify-start'}`;
//     messageDiv.innerHTML = `
//         <div class="${isUser ? 'bg-indigo-600 text-white' : 'bg-white'} 
//                      p-3 rounded-lg max-w-xs md:max-w-md lg:max-w-lg 
//                      shadow-md animate__animated animate__fadeInUp">
//             ${content}
//         </div>
//     `;
    
//     chatContainer.appendChild(messageDiv);
//     chatContainer.scrollTop = chatContainer.scrollHeight;
// }




    function showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        document.body.appendChild(toast);
        new bootstrap.Toast(toast).show();
        
        setTimeout(() => toast.remove(), 5000);
    }

    // مدیریت انتخاب مدل
    document.addEventListener('click', async function(e) {
        if (e.target.closest('.model-choice')) {
            e.preventDefault();
            const button = e.target.closest('.model-choice');
            const modelId = button.dataset.modelId;
            const modelName = button.dataset.modelName;
            
            // ذخیره مقدار قبلی برای حالت خطا
            currentModelElement.dataset.previousValue = currentModelElement.textContent;
            currentModelElement.textContent = modelName;
            
            try {
                const response = await fetch('/select_model/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-CSRFToken': csrftoken
                    },
                    body: `model_id=${modelId}`
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    showToast(`مدل ${modelName} با موفقیت انتخاب شد`);
                } else {
                    throw new Error(data.message || 'خطا در انتخاب مدل');
                }
            } catch (error) {
                console.error('خطا در انتخاب مدل:', error);
                showToast('خطا در تغییر مدل', 'danger');
                currentModelElement.textContent = currentModelElement.dataset.previousValue;
            }
        }
    });

    // مدیریت ارسال پیام
    if (chatForm) {
        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const message = messageInput.value.trim();
            if (!message) return;

            addMessage(message, 'user');
            messageInput.value = '';
            
            try {
                // ساخت URLSearchParams برای ارسال داده
                const params = new URLSearchParams();
                params.append('message', message);
                
                const response = await fetch("/send_message/", {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-CSRFToken': csrftoken,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: params
                });

                if (!response.ok) {
                    throw new Error(`خطای سرور: ${response.status}`);
                }

                const data = await response.json();
                console.log('Response data:', data); // دیباگ پاسخ سرور

                if (data.status === 'success') {
                    addMessage(data.answer, 'bot');
                } else {
                    throw new Error(data.message || 'پاسخی دریافت نشد');
                }
            } catch (error) {
                console.error('خطا در ارسال پیام:', error);
                addMessage(`خطا: ${error.message}`, 'error');
            }
        });
    }

    // مدیریت فشردن Enter (بدون Shift)
    messageInput?.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm?.dispatchEvent(new Event('submit'));
        }
    });



// نمایش اسپینر هنگام پردازش
document.getElementById('chat-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const userInput = document.getElementById('user-input');
    const message = userInput.value.trim();
    
    if (message) {
        addMessage(message, true);
        userInput.value = '';
        
        // نمایش اسپینر
        document.getElementById('loading-spinner').classList.remove('hidden');
        
        // شبیه‌سازی تاخیر پردازش
        setTimeout(async () => {
            try {
                // در اینجا با مدل چت ارتباط برقرار می‌کنید
                const response = "این پاسخ مدل است";
                
                // مخفی کردن اسپینر
                document.getElementById('loading-spinner').classList.add('hidden');
                
                // نمایش پاسخ با تایپینگ متنی
                simulateTyping(response);
            } catch (error) {
                console.error(error);
                document.getElementById('loading-spinner').classList.add('hidden');
                addMessage("خطا در پردازش درخواست", false);
            }
        }, 1000);
    }
});

// شبیه‌سازی تایپینگ متنی
function simulateTyping(text) {
    const chatContainer = document.getElementById('chat-container');
    const typingDiv = document.createElement('div');
    
    typingDiv.className = 'flex justify-start';
    typingDiv.innerHTML = `
        <div class="bg-white p-3 rounded-lg max-w-xs md:max-w-md lg:max-w-lg shadow-md">
            <div class="flex space-x-1">
                <div class="w-2 h-2 rounded-full bg-gray-400 animate-bounce"></div>
                <div class="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style="animation-delay: 0.2s"></div>
                <div class="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style="animation-delay: 0.4s"></div>
            </div>
        </div>
    `;
    
    chatContainer.appendChild(typingDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    // حذف انیمیشن تایپینگ و نمایش پیام کامل
    setTimeout(() => {
        typingDiv.remove();
        addMessage(text, false);
    }, 1500);
}

});

function toggleTheme() {
    const body = document.body;
    const isDark = body.getAttribute('data-theme') === 'dark';
    body.setAttribute('data-theme', isDark ? 'light' : 'dark');
    localStorage.setItem('theme', isDark ? 'light' : 'dark');
  }
  
  // بازیابی تم از localStorage
  function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.body.setAttribute('data-theme', savedTheme);
  }
  
  // فراخوانی هنگام لود صفحه
  window.addEventListener('load', loadTheme);