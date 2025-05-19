const canvas = document.getElementById('crash-canvas');
const ctx = canvas.getContext('2d');
const multiplierDisplay = document.getElementById('multiplier');
const betButton = document.getElementById('bet-button');
const cashoutButton = document.getElementById('cashout-button');
const depositButton = document.getElementById('deposit-button');
const withdrawButton = document.getElementById('withdraw-button');
const giftList = document.getElementById('gift-list');
const verifyButton = document.getElementById('verify-button');
const serverSeedDisplay = document.getElementById('server-seed');
const nonceDisplay = document.getElementById('nonce');

// Telegram Web App
const tg = window.Telegram.WebApp;
tg.expand();

// Инициализация
let gifts = [];
let currentMultiplier = 1.0;
let crashPoint = 0;
let gameActive = false;
let planeX = 50;
let planeY = canvas.height - 50;
let serverSeed = 'server_seed_' + Math.random().toString(36).substring(2);
let nonce = 0;
let marketPrices = {
    'Easter Egg': 600,
    'Jelly Bunny': 300
};

// Анимация самолета
function drawPlane() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (gameActive) {
        ctx.fillStyle = 'red';
        ctx.fillRect(planeX, planeY, 20, 10); // Самолет
        planeX += 2;
        planeY -= 1;
        if (currentMultiplier >= crashPoint) {
            ctx.fillStyle = 'orange';
            ctx.fillRect(planeX - 20, planeY - 20, 40, 40); // Взрыв
            gameActive = false;
            betButton.disabled = false;
            cashoutButton.disabled = true;
            tg.showAlert('Краш на ' + crashPoint.toFixed(2) + 'x! Ты проиграл.');
        }
    }
    requestAnimationFrame(drawPlane);
}

// Provably Fair
function generateCrashPoint() {
    const clientSeed = document.getElementById('client-seed').value;
    const combined = serverSeed + clientSeed + nonce;
    const hash = sha256(combined);
    const result = parseInt(hash.substr(0, 8), 16) / 0xffffffff;
    nonce++;
    return Math.max(1, Math.floor(100 / (result * 100)) / 100); // RTP ~95%
}

// SHA-256 (упрощенная реализация)
function sha256(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash;
    }
    return Math.abs(hash).toString(16).padStart(64, '0');
}

// Таймер для коэффициента
function updateMultiplier() {
    if (gameActive) {
        currentMultiplier += 0.05;
        multiplierDisplay.textContent = currentMultiplier.toFixed(2) + 'x';
        if (currentMultiplier >= crashPoint) {
            gameActive = false;
            betButton.disabled = false;
            cashoutButton.disabled = true;
        }
    }
    setTimeout(updateMultiplier, 100);
}

// Парсинг цен (имитация)
function updateMarketPrices() {
    marketPrices['Easter Egg'] = Math.floor(600 + Math.random() * 100);
    marketPrices['Jelly Bunny'] = Math.floor(300 + Math.random() * 50);
    console.log('Обновлены цены:', marketPrices);
}
setInterval(updateMarketPrices, 10 * 60 * 1000); // Каждые 10 минут

// Депозит
depositButton.addEventListener('click', () => {
    const name = document.getElementById('gift-name').value;
    const price = parseInt(document.getElementById('gift-price').value);
    if (name && price > 0) {
        gifts.push({ name, price: marketPrices[name] || price });
        updateInventory();
        tg.sendData(JSON.stringify({ action: 'deposit', name, price }));
        document.getElementById('gift-name').value = '';
        document.getElementById('gift-price').value = '';
    } else {
        tg.showAlert('Введите название и цену подарка!');
    }
});

// Обновление инвентаря
function updateInventory() {
    giftList.innerHTML = '';
    gifts.forEach(gift => {
        const li = document.createElement('li');
        li.textContent = `${-detect-language
language: Russian
confidence: 0.99
---
gift.name}: ${gift.price} Stars`;
        giftList.appendChild(li);
    });
}

// Ставка
betButton.addEventListener('click', () => {
    if (gifts.length === 0) {
        tg.showAlert('Нет подарков для ставки!');
        return;
    }
    const gift = gifts.shift(); // Берем первый подарок
    crashPoint = generateCrashPoint();
    currentMultiplier = 1.0;
    gameActive = true;
    betButton.disabled = true;
    cashoutButton.disabled = false;
    planeX = 50;
    planeY = canvas.height - 50;
    serverSeedDisplay.textContent = serverSeed;
    nonceDisplay.textContent = nonce;
    updateInventory();
    tg.sendData(JSON.stringify({ action: 'bet', name: gift.name, price: gift.price }));
});

// Кэшаут
cashoutButton.addEventListener('click', () => {
    if (!gameActive) return;
    gameActive = false;
    betButton.disabled = false;
    cashoutButton.disabled = true;
    const winValue = Math.floor(gifts[0]?.price * currentMultiplier || 100);
    gifts.push({ name: `Win_${gifts[0]?.name || 'Gift'}`, price: winValue });
    updateInventory();
    tg.showAlert(`Кэшаут на ${currentMultiplier.toFixed(2)}x! Выигрыш: ${winValue} Stars`);
    tg.sendData(JSON.stringify({ action: 'cashout', value: winValue }));
});

// Вывод
withdrawButton.addEventListener('click', () => {
    const name = document.getElementById('withdraw-name').value;
    const price = parseInt(document.getElementById('withdraw-price').value);
    const totalValue = gifts.reduce((sum, gift) => sum + gift.price, 0);
    if (totalValue < price) {
        tg.showAlert('Недостаточно баланса!');
        return;
    }
    gifts = gifts.filter(gift => gift.price <= totalValue - price);
    updateInventory();
    tg.sendData(JSON.stringify({ action: 'withdraw', name, price }));
    tg.showAlert(`Подарок '${name}' (${price} Stars) отправлен!`);
});

// Проверка Provably Fair
verifyButton.addEventListener('click', () => {
    const clientSeed = document.getElementById('client-seed').value;
    const combined = serverSeed + clientSeed + (nonce - 1);
    const hash = sha256(combined);
    const result = parseInt(hash.substr(0, 8), 16) / 0xffffffff;
    const verifiedCrash = Math.max(1, Math.floor(100 / (result * 100)) / 100);
    tg.showAlert(`Проверено! Краш-поинт: ${verifiedCrash.toFixed(2)}x`);
});

// Старт
drawPlane();
updateMultiplier();
updateMarketPrices();