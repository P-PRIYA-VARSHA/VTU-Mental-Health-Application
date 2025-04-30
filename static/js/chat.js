document.addEventListener("DOMContentLoaded", function() {
    const chatBox = document.getElementById("chat-box");
    const chatInput = document.getElementById("chat-input");
    const sendBtn = document.getElementById("send-btn");
    const speakBtn = document.getElementById("speak-btn"); // Added for speech recognition

    // Function to append messages to the chat box
    function appendMessage(sender, message) {
        const messageElement = document.createElement("div");
        messageElement.innerHTML = `<strong>${sender}:</strong> ${message}`;
        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // Function to send messages to the backend
    function sendMessage(message) {
        if (message.trim() === "") return;
        appendMessage("You", message);
        
        // Send the message to the backend
        fetch("/chatbot", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ message: message })
        })
        .then(response => response.json())
        .then(data => {
            appendMessage("Bot", data.response);
        })
        .catch(error => {
            console.error("Error:", error);
            appendMessage("Bot", "An error occurred. Please try again later.");
        });
    }

    // Handle send button click (for text input)
    sendBtn.addEventListener("click", function() {
        const userMessage = chatInput.value.trim();
        if (userMessage === "") return;
        sendMessage(userMessage);
        chatInput.value = "";
    });

    // Allow sending message with the Enter key
    chatInput.addEventListener("keyup", function(event) {
        if (event.key === "Enter") {
            sendBtn.click();
        }
    });

    // Speech Recognition Integration
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        alert("Your browser does not support speech recognition. Try using Chrome or Edge.");
    } else {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;   // single result per click
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        // Handle the result from speech recognition
        recognition.onresult = function(event) {
    let transcript = event.results[0][0].transcript;
    // Remove common punctuation characters and trim whitespace
    transcript = transcript.replace(/[.,\/#!$%\^&\*;:{}=\-_`~()]/g, "").trim();
    appendMessage("You (spoken)", transcript);
    sendMessage(transcript);
};

        recognition.onerror = function(event) {
            console.error("Speech recognition error", event.error);
            appendMessage("Bot", "There was an error with speech recognition. Please try again.");
        };

        // Start speech recognition when the speak button is clicked
        speakBtn.addEventListener("click", function() {
            recognition.start();
        });
    }
});
