document.getElementById('chat-form').addEventListener('submit', function(event) {
    event.preventDefault();
    const message = document.getElementById('message').value;

    // استفاده از متغیر sendMessageUrl
    fetch(sendMessageUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: `message=${message}`
    })
    .then(response => response.json())
    .then(data => {
        const chatBox = document.getElementById('chat-box');
        chatBox.innerHTML += `<div class="user-message">${message}</div>`;
        chatBox.innerHTML += `<div class="bot-response">${data.response}</div>`;
        document.getElementById('message').value = '';
        chatBox.scrollTop = chatBox.scrollHeight;
    })
    .catch(error => console.error('Error:', error));
});
