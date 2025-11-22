$(document).ready(function() {
    $('#chat-form').on('submit', function(event) {
        event.preventDefault(); // جلوگیری از ارسال فرم به‌صورت پیش‌فرض
        
        const message = $('#message').val();
        $('#chat-box').append('<div class="chatbot-user-message">' + message + '</div>'); // نمایش پیام کاربر
        
        $.ajax({
            type: 'POST',
            url: $(this).attr('action'),
            data: $(this).serialize(),
            success: function(response) {
                if (response.status === 'success') {
                    $('#chat-box').append('<div class="chatbot-bot-response">' + response.answer + '</div>'); // نمایش پاسخ بات
                } else {
                    alert('خطا: ' + response.message);
                }
            },
            error: function(xhr, status, error) {
                alert('خطا در ارسال پیام: ' + error);
            }
        });
    
        $('#message').val(''); // پاک کردن جعبه متن
    });
    });
    
    