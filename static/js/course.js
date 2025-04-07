document.addEventListener('DOMContentLoaded', function() {
    // Set up chapter navigation
    setupChapterNavigation();
    
    // Handle test button clicks
    setupTestButtons();
    
    // Set up chatbot if it exists
    setupChatbot();
});

function setupChapterNavigation() {
    const chapterItems = document.querySelectorAll('.chapter-item');
    if (chapterItems.length === 0) return; // Prevent errors if no elements exist

    chapterItems.forEach(item => {
        item.addEventListener('click', function() {
            if (!this.classList.contains('disabled')) {
                const courseName = this.getAttribute('data-course');
                const chapterId = this.getAttribute('data-chapter');
                window.location.href = `/chapter/${courseName}/${chapterId}`;
            }
        });
    });
}

function setupTestButtons() {
    const testButtons = document.querySelectorAll('.btn-take-test');
    if (testButtons.length === 0) return; // Prevent errors if no buttons exist

    testButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            // Let the regular link handle the navigation with the correct route
        });
    });
}

function setupChatbot() {
    // Check if chatbot elements exist
    const chatbotIcon = document.getElementById('chatbotIcon');
    const chatbotCard = document.getElementById('chatbotCard');
    const chatContainer = document.getElementById('chatContainer');
    const chatInput = document.getElementById('chatInput');
    const sendChatBtn = document.getElementById('sendChatBtn');
    const chatMessages = document.getElementById('chatMessages');
    const closeChatBtn = document.getElementById('closeChatBtn');
    
    if (!chatbotIcon || !chatbotCard || !chatContainer || !chatInput || !sendChatBtn || !chatMessages) {
        return; // Chatbot not available on this page
    }
    
    // Get course and chapter information from URL
    const pathParts = window.location.pathname.split('/');
    const courseName = pathParts[2]; // /chapter/{course_name}/{chapter_id}
    const chapterId = pathParts[3];
    
    // Function to toggle chatbot visibility
    function toggleChatbot() {
        chatbotCard.classList.toggle('show');
        if (chatbotCard.classList.contains('show')) {
            // Focus input when opened
            setTimeout(() => {
                chatInput.focus();
                scrollChatToBottom();
            }, 300);
        }
    }
    
    // Function to close the chatbot
    function closeChatbot() {
        chatbotCard.classList.remove('show');
    }
    
    // Function to send message to chatbot
    function sendMessage() {
        const message = chatInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        addMessageToChat('user', message);
        
        // Clear input
        chatInput.value = '';
        
        // Call API with fetch
        fetch(window.location.origin + '/api/chatbot', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                course_name: courseName,
                chapter_id: chapterId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                addMessageToChat('bot', 'Sorry, there was an error processing your question.');
            } else {
                addMessageToChat('bot', formatResponseText(data.response));
            }
            // Scroll to bottom
            scrollChatToBottom();
        })
        .catch(error => {
            console.error('Error:', error);
            addMessageToChat('bot', 'Sorry, there was a technical issue. Please try again.');
            scrollChatToBottom();
        });
    }
    
    // Function to format response text with code blocks
    function formatResponseText(text) {
        // Check if the text contains triple backticks for code blocks
        if (text.includes('```')) {
            // We'll process the text to handle markdown-style code blocks
            return text.replace(/```([a-z]*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
        }
        return text;
    }
    
    // Function to add a message to the chat
    function addMessageToChat(sender, text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Check if text contains HTML (from formatted code blocks)
        if (text.includes('<pre>')) {
            contentDiv.innerHTML = text;
        } else {
            const paragraph = document.createElement('p');
            paragraph.textContent = text;
            contentDiv.appendChild(paragraph);
        }
        
        messageDiv.appendChild(contentDiv);
        chatMessages.appendChild(messageDiv);
        
        scrollChatToBottom();
    }
    
    // Function to scroll chat to bottom
    function scrollChatToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Event listeners
    chatbotIcon.addEventListener('click', toggleChatbot);
    closeChatBtn.addEventListener('click', closeChatbot);
    sendChatBtn.addEventListener('click', sendMessage);
    
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Close chatbot when clicking outside
    document.addEventListener('click', function(e) {
        if (chatbotCard.classList.contains('show') && 
            !chatbotCard.contains(e.target) && 
            e.target !== chatbotIcon) {
            closeChatbot();
        }
    });
    
    // Initial scroll
    scrollChatToBottom();
}
