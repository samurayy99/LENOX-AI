// Chat Interface
document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chatMessages');
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    const clearButton = document.getElementById('clearButton');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const tokenAnalysisContainer = document.getElementById('tokenAnalysisContainer');

    // Regex patterns for token recognition
    const solanaAddressRegex = /[1-9A-HJ-NP-Za-km-z]{32,44}(?!\w)/g;
    const tokenSymbolRegex = /\$([A-Z0-9]{2,10})\b|\b([A-Z0-9]{2,10})\b/g;

    // Preprocess user message to detect token addresses and symbols
    function preprocessUserMessage(message) {
        // Check for Solana address
        const addressMatches = message.match(solanaAddressRegex);
        if (addressMatches && addressMatches.length > 0) {
            return `/analyze_token ${addressMatches[0]}`;
        }
        
        // Check for token symbol
        const symbolMatches = message.match(tokenSymbolRegex);
        if (symbolMatches && symbolMatches.length > 0) {
            const symbol = symbolMatches[0].replace('$', '');
            return `/analyze_token ${symbol}`;
        }
        
        return message;
    }

    // Format token analysis results
    function formatTokenAnalysis(tokenData) {
        if (!tokenData) return '';

        const {
            basicInfo,
            marketData,
            liquidityAnalysis,
            tradingActivity,
            riskAssessment,
            investmentOutlook
        } = tokenData;

        return `
            <div class="token-analysis">
                <div class="token-header">
                    <h3>${basicInfo.name} (${basicInfo.symbol})</h3>
                    <span class="token-address">${basicInfo.address}</span>
                </div>
                
                <div class="token-section">
                    <h4>Market Data</h4>
                    <div class="token-grid">
                        <div class="token-item">
                            <span class="label">Price</span>
                            <span class="value">${marketData.price}</span>
                        </div>
                        <div class="token-item">
                            <span class="label">Market Cap</span>
                            <span class="value">${marketData.marketCap}</span>
                        </div>
                        <div class="token-item">
                            <span class="label">24h Change</span>
                            <span class="value ${marketData.priceChange.includes('-') ? 'negative' : 'positive'}">
                                ${marketData.priceChange}
                            </span>
                        </div>
                    </div>
                </div>

                <div class="token-section">
                    <h4>Liquidity Analysis</h4>
                    <div class="token-grid">
                        <div class="token-item">
                            <span class="label">Total Liquidity</span>
                            <span class="value">${liquidityAnalysis.totalLiquidity}</span>
                        </div>
                        <div class="token-item">
                            <span class="label">Trading Pairs</span>
                            <span class="value">${liquidityAnalysis.tradingPairs}</span>
                        </div>
                    </div>
                    <div class="liquidity-bars">
                        ${liquidityAnalysis.pairLiquidity}
                    </div>
                </div>

                <div class="token-section">
                    <h4>Trading Activity</h4>
                    <div class="token-grid">
                        <div class="token-item">
                            <span class="label">24h Volume</span>
                            <span class="value">${tradingActivity.volume24h}</span>
                        </div>
                        <div class="token-item">
                            <span class="label">Unique Traders</span>
                            <span class="value">${tradingActivity.uniqueTraders}</span>
                        </div>
                    </div>
                    <div class="recent-swaps">
                        ${tradingActivity.recentSwaps}
                    </div>
                </div>

                <div class="token-section">
                    <h4>Risk Assessment</h4>
                    <div class="risk-level ${riskAssessment.level.toLowerCase()}">
                        ${riskAssessment.level}
                    </div>
                    <div class="risk-factors">
                        ${riskAssessment.factors}
                    </div>
                </div>

                <div class="token-section">
                    <h4>Investment Outlook</h4>
                    <div class="outlook">
                        ${investmentOutlook}
                    </div>
                </div>
            </div>
        `;
    }

    // Add message to chat
    function addMessage(message, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;
        
        // Check if the message contains token analysis data
        try {
            const tokenData = JSON.parse(message);
            if (tokenData.basicInfo) {
                messageDiv.innerHTML = formatTokenAnalysis(tokenData);
            } else {
                messageDiv.textContent = message;
            }
        } catch (e) {
            messageDiv.textContent = message;
        }
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Send message to backend
    async function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) return;

        // Add user message to chat
        addMessage(message, true);
        messageInput.value = '';

        // Show loading indicator
        loadingIndicator.style.display = 'block';

        try {
            // Preprocess message to detect token addresses/symbols
            const processedMessage = preprocessUserMessage(message);

            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: processedMessage }),
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();
            addMessage(data.response);
        } catch (error) {
            console.error('Error:', error);
            addMessage('Sorry, there was an error processing your request.');
        } finally {
            loadingIndicator.style.display = 'none';
        }
    }

    // Clear chat history
    function clearChat() {
        chatMessages.innerHTML = '';
        tokenAnalysisContainer.innerHTML = '';
    }

    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    clearButton.addEventListener('click', clearChat);
}); 