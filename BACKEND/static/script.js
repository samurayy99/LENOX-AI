document.getElementById('startRecording').addEventListener('click', function () {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
            let audioChunks = [];
            mediaRecorder.ondataavailable = function (event) {
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = async function () {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                const formData = new FormData();
                formData.append('file', audioBlob, 'recording.webm');

                try {
                    const response = await fetch('/transcribe', {
                        method: 'POST',
                        body: formData,
                    });
                    if (response.ok) {
                        const data = await response.json();
                        document.getElementById('query').value = data.transcription;
                    } else {
                        console.error('Failed to transcribe audio:', await response.text());
                    }
                    audioChunks = [];
                } catch (error) {
                    console.error('Error:', error);
                }
            };

            document.getElementById('stopRecording').addEventListener('click', function () {
                mediaRecorder.stop();
                stream.getTracks().forEach(track => track.stop());
                document.getElementById('stopRecording').disabled = true;
            });

            document.getElementById('stopRecording').disabled = false;
            mediaRecorder.start();
        })
        .catch(error => console.error('Permission denied or microphone not available:', error));
});

document.getElementById('startRecording').disabled = false;

document.getElementById('sendButton').addEventListener('click', async () => {
    await submitQuery();
});

document.getElementById('query').addEventListener('keydown', async (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        if (!e.shiftKey) {
            await submitQuery();
        } else {
            let content = document.getElementById('query').value;
            document.getElementById('query').value = content + '\n';
        }
    }
});


async function submitQuery() {
    const queryInput = document.getElementById('query');
    const query = queryInput.value.trim();
    if (!query) return;

    appendMessage(query, 'user-message');
    queryInput.value = '';
    showLoadingIndicator(true);

    try {
        const response = await fetch('/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });

        if (!response.ok) {
            console.error('Error fetching response:', response.statusText);
            appendMessage(`An error occurred: ${response.statusText}`, 'error-message');
        } else {
            const data = await response.json();
            processResponseData(data);
        }
    } catch (error) {
        console.error('Error processing response:', error);
        appendMessage('An error occurred while processing the response.', 'error-message');
    }
    showLoadingIndicator(false);
}



function processResponseData(data) {
    console.log("Received data from server:", data);
    try {
        switch (data.type) {
            case 'visualization':
                // Ensure content is parsed correctly
                const content = JSON.parse(data.content.replace(/'/g, '"'));
                appendMessage(content.message, 'bot-message');
                break;
            case 'text':
                if (typeof data.content === 'string') {
                    appendMessage(convertUrlsToLinks(data.content), 'bot-message', true);
                } else if (typeof data.content === 'object' && 'response' in data.content) {
                    appendMessage(convertUrlsToLinks(data.content.response), 'bot-message', true);
                } else {
                    throw new Error('Invalid text response structure.');
                }
                break;
            case 'document_response':
                if (Array.isArray(data.content)) {
                    data.content.forEach(doc => {
                        appendMessage(`**Filename:** ${doc.metadata.filename}<br>**Content:** ${doc.page_content}`, 'bot-message');
                    });
                } else {
                    throw new Error('Invalid document_response structure.');
                }
                break;
            case 'error':
                console.error('Error response received:', data.content);
                appendMessage(data.content, 'error-message');
                break;
            default:
                console.error('Unexpected response type:', data.type);
                appendMessage('Received unexpected type of data from the server.', 'error-message');
                break;
        }
    } catch (error) {
        console.error('Error processing response:', error);
        appendMessage(`Error processing response: ${error.message}`, 'error-message');
    }
}


document.getElementById('uploadForm').addEventListener('submit', function (event) {
    event.preventDefault();

    const fileInput = document.getElementById('fileUpload');
    const file = fileInput.files[0];
    if (!file) {
        appendMessage('No file selected.', 'error-message');
        return;
    }

    showLoadingIndicator(true);

    const reader = new FileReader();
    reader.onload = function(e) {
        const fileContent = e.target.result;
        
        // Display the uploaded image
        const imgElement = document.createElement('img');
        imgElement.src = fileContent;
        imgElement.style.maxWidth = '100%';
        imgElement.style.height = 'auto';
        appendMessage('Uploaded Chart:', 'bot-message');
        appendMessage(imgElement.outerHTML, 'bot-message');

        // Send only the base64 part to the server
        const base64Content = fileContent.split(',')[1];
        
        fetch('/upload', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ file_content: base64Content })
        })
        .then(response => response.json())
        .then(data => {
            showLoadingIndicator(false);
            if (data.error) {
                console.error('Error uploading file:', data.error);
                appendMessage(`Error uploading file: ${data.error}`, 'error-message');
            } else {
                console.log('File uploaded successfully:', data.message);
                appendMessage(`File uploaded successfully: ${data.message}`, 'bot-message');
                
                if (data.analysis) {
                    appendMessage(`Chart Analysis: ${data.analysis}`, 'bot-message');
                }
            }
        })
        .catch(error => {
            showLoadingIndicator(false);
            console.error('Error:', error);
            appendMessage('An error occurred while uploading the file.', 'error-message');
        });
    };
    reader.readAsDataURL(file);
});


let currentAudio = null;
let currentPlayButton = null;

function appendMessage(message, className, shouldIncludeAudio = false) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('chat-message', className);

    if (typeof message === 'string') {
        // Convert URLs to links
        message = convertUrlsToLinks(message);

        // Convert newlines to <br> tags
        message = message.replace(/\n/g, '<br>');

        // Convert markdown-style lists to HTML lists
        message = message.replace(/(\*\*Response:\*\*)\n/g, '$1<br><ul>');
        message = message.replace(/- (.+)/g, '<li>$1</li>');
        message = message.replace(/<\/li>\n/g, '</li>');
        message = message.replace(/<\/li><br>/g, '</li>');
        message = message.replace(/<\/ul><br>/g, '</ul>');
        message = message.replace(/<\/ul>/g, '</ul><br>');

        messageDiv.innerHTML = message;
    } else {
        // If message is not a string (e.g., HTML for image), use innerHTML directly
        messageDiv.innerHTML = message;
    }

    if (shouldIncludeAudio && className === 'bot-message') {
        const button = document.createElement('button');
        button.textContent = 'Play';
        button.classList.add('play-button');
        button.onclick = () => {
            if (currentAudio) {
                currentAudio.pause();
                currentAudio.currentTime = 0;
                currentAudio = null;
                currentPlayButton.textContent = 'Play';
                currentPlayButton.disabled = false;
                if (currentPlayButton !== button) {
                    button.textContent = 'Playing...';
                    button.disabled = true;
                    fetchAudio(message, button);
                }
            } else {
                button.textContent = 'Playing...';
                button.disabled = true;
                fetchAudio(message, button);
            }
            currentPlayButton = button;
        };
        messageDiv.appendChild(button);
    }

    if (className === 'bot-message') {
        addFeedbackButtons(messageDiv, message); // Add feedback buttons only to bot messages
    }

    chatMessages.appendChild(messageDiv);
    scrollToLatestMessage();
}

function fetchAudio(text, button) {
    const data = { input: text, voice: "alloy" };

    fetch('/synthesize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    }).then(response => {
        if (!response.ok) throw new Error(`Failed to fetch audio with status: ${response.status}`);
        return response.blob();
    }).then(blob => {
        const url = URL.createObjectURL(blob);
        currentAudio = new Audio(url);
        currentAudio.play();

        currentAudio.onended = () => {
            URL.revokeObjectURL(url);
            currentAudio = null;
            if (button) {
                button.textContent = 'Play';
                button.disabled = false;
            }
        };
    }).catch(error => {
        console.error('Error fetching or playing audio:', error);
        appendMessage('Failed to play audio.', 'error-message');
        currentAudio = null;
        if (button) {
            button.textContent = 'Play';
            button.disabled = false;
        }
    });
}


function scrollToLatestMessage() {
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

document.querySelectorAll('.dropdown-content a').forEach(item => {
    item.addEventListener('click', function (e) {
        e.preventDefault();
        const predefinedQuery = this.innerText;
        document.getElementById('query').value = predefinedQuery;
        document.getElementById('query').focus();
    });
});

function handleAudioResponse(response) {
    response.blob().then(blob => {
        const audioType = blob.type;
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        audio.oncanplaythrough = () => audio.play();
        audio.onerror = () => {
            console.error('Error playing audio:', audio.error);
            appendMessage('Error playing audio.', 'error-message');
        };
        appendMessage('Playing response...', 'bot-message');
    }).catch(error => {
        console.error('Error processing audio blob:', error);
        appendMessage('Error processing audio.', 'error-message');
    });
}



function handleVisualResponse(content) {
    console.log("Handling visual response:", content);
    if (content && content.status === 'success') {
        appendMessage(content.message, 'bot-message');
    } else {
        console.error('Unexpected visualization content:', content);
        appendMessage('An error occurred while processing the visualization response.', 'error-message');
    }
}

function appendVisualizationPlaceholder() {
    const chatMessages = document.getElementById('chat-messages');
    const visualizationPlaceholder = document.createElement('div');
    visualizationPlaceholder.classList.add('visualization-placeholder', 'bot-message');
    chatMessages.appendChild(visualizationPlaceholder);
    return visualizationPlaceholder;
}



function processResponseData(data) {
    console.log("Received data from server:", data);
    try {
        switch (data.type) {
            case 'visualization':
                if (data.content && typeof data.content === 'object') {
                    handleVisualResponse(data.content);
                } else if (typeof data.content === 'string') {
                    handleVisualResponse(JSON.parse(data.content));
                } else {
                    throw new Error('Invalid visualization content structure.');
                }
                break;
            case 'text':
                if (typeof data.content === 'string') {
                    appendMessage(convertUrlsToLinks(data.content), 'bot-message', true);
                } else if (typeof data.content === 'object' && 'response' in data.content) {
                    appendMessage(convertUrlsToLinks(data.content.response), 'bot-message', true);
                } else {
                    throw new Error('Invalid text response structure.');
                }
                break;
            case 'document_response':
                if (Array.isArray(data.content)) {
                    data.content.forEach(doc => {
                        appendMessage(`**Filename:** ${doc.metadata.filename}<br>**Content:** ${doc.page_content}`, 'bot-message');
                    });
                } else {
                    throw new Error('Invalid document_response structure.');
                }
                break;
            case 'chart_analysis':
                if (typeof data.response === 'object') {
                    appendMessage(`Chart Analysis: ${JSON.stringify(data.response, null, 2)}`, 'bot-message');
                } else {
                    throw new Error('Invalid chart_analysis structure.');
                }
                break;
            case 'error':
                console.error('Error response received:', data.content);
                appendMessage(data.content, 'error-message');
                break;
            default:
                throw new Error(`Unexpected response type: ${data.type}`);
        }
    } catch (error) {
        console.error('Error processing response:', error);
        appendMessage(`Error processing response: ${error.message}`, 'error-message');
    }
}


function handleVisualResponse(content) {
    console.log("Handling visual response:", content);
    if (content && content.status === 'success') {
        appendMessage(content.message, 'bot-message');
    } else {
        console.error('Unexpected visualization content:', content);
        appendMessage('An error occurred while processing the visualization response.', 'error-message');
    }
}


function convertUrlsToLinks(text) {
    const urlRegex = /(\b(https?|ftp|file):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/ig;
    return text.replace(urlRegex, url => {
        // Check if the URL is already wrapped in an <a> tag
        if (text.includes(`<a href="${url}`)) {
            return url;
        }
        return `<a href="${url}" target="_blank">${url}</a>`;
    });
}

function scrollToLatestMessage() {
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showLoadingIndicator(isLoading) {
    const loadingIndicator = document.getElementById('loadingIndicator');
    loadingIndicator.style.display = isLoading ? 'block' : 'none';
}


function addFeedbackButtons(messageElement, messageContent) {
    const feedbackButtons = document.createElement('div');
    feedbackButtons.className = 'feedback-buttons';

    const thumbsUp = document.createElement('button');
    thumbsUp.className = 'thumbs-up';
    thumbsUp.onclick = () => handleFeedback(thumbsUp, messageContent, 'positive');
    feedbackButtons.appendChild(thumbsUp);

    const thumbsDown = document.createElement('button');
    thumbsDown.className = 'thumbs-down';
    thumbsDown.onclick = () => handleFeedback(thumbsDown, messageContent, 'negative');
    feedbackButtons.appendChild(thumbsDown);

    messageElement.appendChild(feedbackButtons);
}


function handleFeedback(button, messageContent, feedbackType) {
    // Disable both buttons and add selected class
    const buttons = button.parentElement.querySelectorAll('button');
    buttons.forEach(btn => {
        btn.disabled = true;
        btn.classList.add('disabled');
        if (btn === button) {
            btn.classList.add('selected');
        }
    });

    // Create and append thank you message
    const feedbackMessage = document.createElement('div');
    feedbackMessage.className = 'feedback-message';
    feedbackMessage.textContent = 'Thank you for your feedback!';
    button.parentElement.appendChild(feedbackMessage);

    // Send feedback
    sendFeedback(messageContent, feedbackType)
        .then(response => {
            console.log('Feedback sent:', response);
        })
        .catch(error => {
            console.error('Error sending feedback:', error);
            // Remove selected class and re-enable buttons if there's an error
            buttons.forEach(btn => {
                btn.disabled = false;
                btn.classList.remove('disabled', 'selected');
            });
            feedbackMessage.textContent = 'Error sending feedback. Please try again.';
        });
}


function sendFeedback(query, feedback) {
    return fetch('/feedback', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query, feedback }),
    })
    .then(response => response.json());
}


