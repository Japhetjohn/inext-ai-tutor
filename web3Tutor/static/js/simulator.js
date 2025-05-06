
let balance = 10000;
let portfolio = {};
let tradeHistory = [];
let chart;

function initializeSimulator() {
    updateBalance();
    createChart();
    setInterval(updatePrices, 5000);
}

function createChart() {
    const ctx = document.getElementById('priceChart').getContext('2d');
    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array(10).fill(''),
            datasets: [{
                label: 'Price',
                data: Array(10).fill(0),
                borderColor: '#3498db',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: false
                }
            }
        }
    });
}

function updatePrices() {
    const currentPrice = chart.data.datasets[0].data[chart.data.datasets[0].data.length - 1] || 50000;
    const newPrice = currentPrice * (1 + (Math.random() - 0.5) * 0.02);
    
    chart.data.datasets[0].data.shift();
    chart.data.datasets[0].data.push(newPrice);
    chart.update();
}

function executeTrade(type) {
    const amount = parseFloat(document.getElementById('tradeAmount').value);
    const pair = document.getElementById('tradingPair').value;
    const currentPrice = chart.data.datasets[0].data[chart.data.datasets[0].data.length - 1];
    
    if (!amount || amount <= 0) {
        showNotification('Please enter a valid amount', 'error');
        return;
    }
    
    const total = amount * currentPrice;
    
    if (type === 'buy') {
        if (total > balance) {
            showNotification('Insufficient funds', 'error');
            return;
        }
        balance -= total;
        portfolio[pair] = (portfolio[pair] || 0) + amount;
    } else {
        if (!portfolio[pair] || portfolio[pair] < amount) {
            showNotification('Insufficient crypto balance', 'error');
            return;
        }
        balance += total;
        portfolio[pair] -= amount;
    }
    
    tradeHistory.unshift({
        type,
        pair,
        amount,
        price: currentPrice,
        timestamp: new Date().toLocaleString()
    });
    
    updateBalance();
    updatePortfolio();
    updateTradeHistory();
    showNotification(`${type.toUpperCase()} order executed successfully`, 'success');
}

function updateBalance() {
    document.getElementById('accountBalance').textContent = balance.toFixed(2);
}

function updatePortfolio() {
    const portfolioList = document.getElementById('portfolioList');
    portfolioList.innerHTML = Object.entries(portfolio)
        .map(([pair, amount]) => `<div class="portfolio-item">
            <span>${pair}</span>
            <span>${amount.toFixed(8)}</span>
        </div>`)
        .join('');
}

function updateTradeHistory() {
    const historyList = document.getElementById('tradeHistoryList');
    historyList.innerHTML = tradeHistory
        .map(trade => `<div class="trade-item ${trade.type}">
            <span>${trade.timestamp}</span>
            <span>${trade.type.toUpperCase()} ${trade.amount} ${trade.pair}</span>
            <span>$${trade.price.toFixed(2)}</span>
        </div>`)
        .join('');
}

function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
}

document.addEventListener('DOMContentLoaded', initializeSimulator);
