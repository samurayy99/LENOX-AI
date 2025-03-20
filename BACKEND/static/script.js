$(document).ready(function() {
    // Theme-Wechsel
    $('#theme').change(function() {
        const theme = $(this).val();
        $('body').removeClass('cyberpunk dark light').addClass(theme);
    });
    
    // Settings-Panel ein-/ausblenden
    $('.settings-toggle').click(function() {
        $('.settings-content').toggleClass('active');
    });
    
    // Chat löschen
    $('#clear-chat').click(function() {
        $('#chat').empty();
    });
    
    // Dropdown-Link-Funktionalität
    $('.dropdown-content a').click(function(e) {
        e.preventDefault();
        const query = $(this).text();
        $('#query').val(query);
        $('#sendButton').click();
    });

    // Sende-Button
    $('#sendButton').click(async () => {
        await submitQuery();
    });

    // Enter-Taste zum Senden
    $('#query').keydown(async (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            if (!e.shiftKey) {
                await submitQuery();
            } else {
                let content = $('#query').val();
                $('#query').val(content + '\n');
            }
        }
    });

    async function submitQuery() {
        const queryInput = $('#query');
        const query = queryInput.val().trim();
        if (!query) return;

        appendMessage(query, 'user-message');
        queryInput.val('');
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
            if (!data || typeof data !== 'object' || !('type' in data)) {
                throw new Error('Invalid response structure');
            }

            switch (data.type) {
                case 'visualization':
                    console.log("Handling visualization response");
                    handleVisualResponse(data);
                    break;
                case 'text':
                    console.log("Handling text response");
                    if (typeof data.content === 'string') {
                        let cleanContent = data.content.replace(/^content=/, '').replace(/\\n/g, '\n');
                        cleanContent = marked.parse(cleanContent);
                        appendMessage(convertUrlsToLinks(cleanContent), 'bot-message');
                    } else {
                        throw new Error('Invalid text response structure');
                    }
                    break;
                case 'document_response':
                    console.log("Handling document response");
                    if (Array.isArray(data.content)) {
                        data.content.forEach(doc => {
                            let content = `**Filename:** ${doc.metadata.filename}<br>**Content:** ${doc.page_content}`;
                            content = marked.parse(content);
                            appendMessage(content, 'bot-message');
                        });
                    } else {
                        throw new Error('Invalid document_response structure');
                    }
                    break;
                case 'chart_analysis':
                    console.log("Handling chart analysis response");
                    if (typeof data.content === 'object') {
                        let content = `Chart Analysis: ${JSON.stringify(data.content, null, 2)}`;
                        content = marked.parse(content);
                        appendMessage(content, 'bot-message');
                    } else {
                        throw new Error('Invalid chart_analysis structure');
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

    function handleVisualResponse(response) {
        console.log("Handling visual response:", response);
        
        // Erstelle eine neue Nachrichtencontainer
        const messageContent = response.content || "Here's a visualization";
        appendMessage(messageContent, 'bot-message');
        
        // Bild anzeigen, wenn vorhanden
        if (response.image) {
            const imgElement = $('<img>')
                .attr('src', response.image)
                .attr('alt', 'Visualization')
                .css('max-width', '100%');
                
            $('#chat').append($('<div>').addClass('message bot-message').append(imgElement));
        }
        
        // Zum Ende des Chats scrollen
        const chatContainer = document.getElementById('chat');
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    function convertUrlsToLinks(text) {
        const urlRegex = /(\b(https?|ftp|file):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/ig;
        return text.replace(urlRegex, url => {
            // Prüfe, ob die URL bereits in einem <a>-Tag ist
            if (text.includes(`<a href="${url}`)) {
                return url;
            }
            return `<a href="${url}" target="_blank">${url}</a>`;
        });
    }

    function appendMessage(message, className) {
        const messageElement = $('<div>').addClass('message ' + className);
        
        if (typeof message === 'string') {
            if (className === 'user-message') {
                messageElement.text(message);
            } else {
                messageElement.html(message);
            }
        } else {
            // Falls message kein String ist (z.B. HTML Element)
            messageElement.append(message);
        }
        
        $('#chat').append(messageElement);
        
        // Zum Ende des Chats scrollen
        const chatContainer = document.getElementById('chat');
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    function showLoadingIndicator(isLoading) {
        $('#loadingIndicator').css('display', isLoading ? 'block' : 'none');
    }
});