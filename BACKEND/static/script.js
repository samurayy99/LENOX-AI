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
    event.preventDefault(); // Prevent the default form submission

    const fileInput = document.getElementById('fileUpload');
    const formData = new FormData();

    for (const file of fileInput.files) {
        formData.append('file', file);
    }

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Error uploading file:', data.error);
            appendMessage(`Error uploading file: ${data.error}`, 'error-message');
        } else {
            console.log('File uploaded successfully:', data.message);
            appendMessage(`File uploaded successfully: ${data.message}`, 'bot-message');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        appendMessage('An error occurred while uploading the file.', 'error-message');
    });
});



function appendMessage(message, className, shouldIncludeAudio = false) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('chat-message', className);

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

    if (shouldIncludeAudio && className === 'bot-message') {
        const button = document.createElement('button');
        button.textContent = 'Play';
        button.classList.add('play-button'); // Add a class to the play button for styling
        button.onclick = () => fetchAudio(message);
        messageDiv.appendChild(button);
    }

    if (className === 'bot-message') {
        addFeedbackButtons(messageDiv, message); // Add feedback buttons only to bot messages
    }

    chatMessages.appendChild(messageDiv);
    scrollToLatestMessage();
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

function fetchAudio(text) {
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
        const audio = new Audio(url);
        audio.play();
    }).catch(error => {
        console.error('Error fetching or playing audio:', error);
        appendMessage('Failed to play audio.', 'error-message');
    });
}



function handleVisualResponse(data) {
    const visualizationContainer = appendVisualizationPlaceholder();
    if (data.content && visualizationContainer) {
        try {
            console.log('Visualization data:', data.content.image);
            const imgElement = document.createElement('img');
            imgElement.src = `data:image/png;base64,${data.content.image}`;
            visualizationContainer.appendChild(imgElement);

            // Append the textual response
            appendMessage(data.content.text, 'bot-message');
        } catch (e) {
            console.error('Error rendering visualization:', e);
            appendMessage('An error occurred while rendering the visualization.', 'error-message');
        }
    } else {
        appendMessage('Visualization content is not available or container missing.', 'error-message');
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
                // No need to parse content as JSON, it's already an object
                appendMessage(data.content.message, 'bot-message');
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
    thumbsUp.onclick = () => sendFeedback(messageContent, 'positive');
    feedbackButtons.appendChild(thumbsUp);

    const thumbsDown = document.createElement('button');
    thumbsDown.className = 'thumbs-down';
    thumbsDown.onclick = () => sendFeedback(messageContent, 'negative');
    feedbackButtons.appendChild(thumbsDown);

    messageElement.appendChild(feedbackButtons);
}

function sendFeedback(query, feedback) {
    fetch('/feedback', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query, feedback }),
    })
    .then(response => response.json())
    .then(data => {
        console.log('Feedback sent:', data);
    })
    .catch((error) => {
        console.error('Error sending feedback:', error);
    });
}