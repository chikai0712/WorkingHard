// 遊戲狀態
const gameState = {
    money: 50,
    level: 1,
    experience: 0,
    experienceToNextLevel: 100,
    hasRegister: false,
    staffCount: 0,
    ovenLevel: 1,
    decorationLevel: 0,
    customers: [],
    pizzasServed: 0,
    customerSpawnRate: 3000,
    lastCustomerSpawn: 0,
    gameStarted: false
};

// 遊戲配置
const config = {
    prices: {
        register: 50,
        staff: 100,
        oven: 150,
        decoration: 200
    },
    customerTypes: [
        { icon: '🐱', pizzas: 1, payment: 10 },
        { icon: '🐶', pizzas: 2, payment: 20 },
        { icon: '🐰', pizzas: 3, payment: 30 },
        { icon: '🐻', pizzas: 4, payment: 40 },
        { icon: '🦊', pizzas: 2, payment: 25 }
    ],
    baseServiceTime: 2000,
    experiencePerPizza: 10
};

// DOM 元素
const elements = {
    moneyAmount: document.getElementById('money-amount'),
    levelText: document.getElementById('level-text'),
    levelProgress: document.getElementById('level-progress'),
    queueArea: document.getElementById('queue-area'),
    staffArea: document.getElementById('staff-area'),
    cashRegister: document.getElementById('cash-register'),
    shopButton: document.getElementById('shop-button'),
    shopPanel: document.getElementById('shop-panel'),
    closeShop: document.getElementById('close-shop'),
    notification: document.getElementById('notification')
};

// 初始化遊戲
function initGame() {
    updateUI();
    setupEventListeners();
    startGameLoop();
    
    // 添加初始等待顧客（即使沒有收銀台也顯示）
    setTimeout(() => {
        spawnWaitingCustomer();
    }, 500);
    
    setTimeout(() => {
        spawnWaitingCustomer();
    }, 1000);
    
    showNotification('歡迎來到貓咪披薩店！🐱🍕');
    
    // 顯示提示
    setTimeout(() => {
        if (!gameState.hasRegister) {
            showNotification('點擊收銀台開始營業！');
        }
    }, 3000);
}

// 設置事件監聽器
function setupEventListeners() {
    elements.shopButton.addEventListener('click', openShop);
    elements.closeShop.addEventListener('click', closeShop);
    elements.cashRegister.addEventListener('click', buyRegister);

    // 商店購買按鈕
    document.querySelectorAll('.buy-button').forEach(button => {
        button.addEventListener('click', (e) => {
            const item = e.target.closest('.shop-item').dataset.item;
            const cost = parseInt(e.target.dataset.cost);
            buyItem(item, cost);
        });
    });
}

// 遊戲主循環
function startGameLoop() {
    setInterval(() => {
        const now = Date.now();
        
        // 生成顧客
        if (gameState.hasRegister && now - gameState.lastCustomerSpawn > gameState.customerSpawnRate) {
            spawnCustomer();
            gameState.lastCustomerSpawn = now;
        }

        // 自動服務顧客
        if (gameState.staffCount > 0 && gameState.customers.length > 0) {
            serveCustomers();
        }
    }, 100);
}

// 生成顧客
function spawnCustomer() {
    if (gameState.customers.length >= 5) return;

    const customerType = config.customerTypes[Math.floor(Math.random() * config.customerTypes.length)];
    const customer = {
        id: Date.now(),
        ...customerType,
        element: null
    };

    gameState.customers.push(customer);
    renderCustomer(customer);
}

// 生成等待中的顧客（遊戲開始時）
function spawnWaitingCustomer() {
    if (gameState.customers.length >= 3) return;

    const customerType = config.customerTypes[Math.floor(Math.random() * config.customerTypes.length)];
    const customer = {
        id: Date.now() + Math.random(),
        ...customerType,
        element: null,
        waiting: true
    };

    gameState.customers.push(customer);
    renderCustomer(customer);
}

// 渲染顧客
function renderCustomer(customer) {
    const customerEl = document.createElement('div');
    customerEl.className = 'customer';
    customerEl.dataset.customerId = customer.id;
    
    // 如果是等待中的顧客，添加特殊樣式
    if (customer.waiting) {
        customerEl.style.opacity = '0.7';
        customerEl.style.filter = 'grayscale(0.3)';
    }
    
    customerEl.innerHTML = `
        <div class="customer-icon">${customer.icon}</div>
        <div class="customer-order">
            <span class="order-icon">🍕</span>
            <span class="order-count">${customer.pizzas}</span>
        </div>
        <div class="customer-payment">💵 ${customer.payment}</div>
    `;

    customerEl.addEventListener('click', () => {
        if (customer.waiting) {
            showNotification('需要先購買收銀台！💵 50');
            // 讓收銀台閃爍提示
            elements.cashRegister.style.animation = 'shake 0.5s ease';
            setTimeout(() => {
                elements.cashRegister.style.animation = '';
            }, 500);
            return;
        }
        if (!gameState.hasRegister) {
            showNotification('需要先購買收銀台！');
            return;
        }
        serveCustomer(customer);
    });

    customer.element = customerEl;
    elements.queueArea.appendChild(customerEl);
}

// 服務顧客
function serveCustomer(customer) {
    if (customer.beingServed) return;
    
    const serviceTime = config.baseServiceTime / gameState.ovenLevel;
    customer.beingServed = true;
    
    // 添加服務動畫
    customer.element.style.transform = 'scale(1.1)';
    customer.element.style.filter = 'brightness(1.2)';
    customer.element.style.opacity = '1';

    setTimeout(() => {
        // 獲得金錢和經驗
        gameState.money += customer.payment;
        gameState.experience += customer.pizzas * config.experiencePerPizza;
        gameState.pizzasServed += customer.pizzas;

        // 移除顧客
        customer.element.style.animation = 'slideOut 0.5s ease';
        setTimeout(() => {
            customer.element.remove();
            gameState.customers = gameState.customers.filter(c => c.id !== customer.id);
        }, 500);

        // 顯示獲得金錢動畫
        showFloatingText(`+💵${customer.payment}`, customer.element);

        // 檢查升級
        checkLevelUp();
        updateUI();
    }, serviceTime);
}

// 自動服務顧客（員工）
function serveCustomers() {
    const customer = gameState.customers[0];
    if (customer && !customer.beingServed) {
        customer.beingServed = true;
        serveCustomer(customer);
    }
}

// 檢查升級
function checkLevelUp() {
    while (gameState.experience >= gameState.experienceToNextLevel) {
        gameState.level++;
        gameState.experience -= gameState.experienceToNextLevel;
        gameState.experienceToNextLevel = Math.floor(gameState.experienceToNextLevel * 1.5);
        
        // 升級獎勵
        gameState.money += 50;
        gameState.customerSpawnRate = Math.max(1000, gameState.customerSpawnRate - 200);
        
        showNotification(`🎉 升級到 Level ${gameState.level}！`);
    }
}

// 購買收銀台
function buyRegister() {
    if (gameState.hasRegister) {
        showNotification('已經有收銀台了！');
        return;
    }

    if (gameState.money >= config.prices.register) {
        gameState.money -= config.prices.register;
        gameState.hasRegister = true;
        gameState.gameStarted = true;
        elements.cashRegister.classList.remove('locked');
        elements.cashRegister.style.background = 'linear-gradient(135deg, #6BCF7F 0%, #5AB86E 100%)';
        
        // 移除等待標記，讓顧客可以被服務
        gameState.customers.forEach(customer => {
            customer.waiting = false;
        });
        
        showNotification('購買收銀台成功！開始營業！');
        updateUI();
    } else {
        const needed = config.prices.register - gameState.money;
        showNotification(`金錢不足！還需要 💵 ${needed}`);
    }
}

// 購買物品
function buyItem(item, cost) {
    if (gameState.money < cost) {
        showNotification('金錢不足！');
        return;
    }

    switch(item) {
        case 'register':
            buyRegister();
            closeShop();
            break;
        case 'staff':
            gameState.money -= cost;
            gameState.staffCount++;
            addStaff();
            showNotification('雇用貓咪員工成功！');
            config.prices.staff = Math.floor(config.prices.staff * 1.5);
            break;
        case 'oven':
            gameState.money -= cost;
            gameState.ovenLevel++;
            showNotification(`烤箱升級到 Level ${gameState.ovenLevel}！`);
            config.prices.oven = Math.floor(config.prices.oven * 1.5);
            break;
        case 'decoration':
            gameState.money -= cost;
            gameState.decorationLevel++;
            gameState.customerSpawnRate = Math.max(500, gameState.customerSpawnRate - 300);
            showNotification('店面裝飾升級！吸引更多顧客！');
            config.prices.decoration = Math.floor(config.prices.decoration * 1.5);
            break;
    }

    updateUI();
    updateShopPrices();
}

// 添加員工
function addStaff() {
    const staffEl = document.createElement('div');
    staffEl.className = 'cat-staff';
    staffEl.innerHTML = `
        <div class="cat-icon">🐱</div>
        <div class="cat-status">工作中</div>
    `;
    elements.staffArea.appendChild(staffEl);
}

// 更新商店價格
function updateShopPrices() {
    document.querySelectorAll('.buy-button').forEach(button => {
        const item = button.closest('.shop-item').dataset.item;
        const cost = config.prices[item];
        button.innerHTML = `<span>💵 ${cost}</span>`;
        button.dataset.cost = cost;
        
        // 更新按鈕狀態
        if (gameState.money < cost) {
            button.disabled = true;
        } else {
            button.disabled = false;
        }
    });
}

// 打開商店
function openShop() {
    elements.shopPanel.classList.remove('hidden');
    updateShopPrices();
}

// 關閉商店
function closeShop() {
    elements.shopPanel.classList.add('hidden');
}

// 顯示通知
function showNotification(message) {
    elements.notification.textContent = message;
    elements.notification.classList.remove('hidden');
    
    setTimeout(() => {
        elements.notification.classList.add('hidden');
    }, 2000);
}

// 顯示浮動文字
function showFloatingText(text, element) {
    const floatingText = document.createElement('div');
    floatingText.textContent = text;
    floatingText.style.cssText = `
        position: absolute;
        top: ${element.offsetTop}px;
        left: ${element.offsetLeft + element.offsetWidth / 2}px;
        font-size: 24px;
        font-weight: 700;
        color: #6BCF7F;
        pointer-events: none;
        z-index: 1000;
        animation: floatUp 1s ease-out forwards;
    `;
    
    document.getElementById('game-area').appendChild(floatingText);
    
    setTimeout(() => {
        floatingText.remove();
    }, 1000);
}

// 添加浮動動畫
const style = document.createElement('style');
style.textContent = `
    @keyframes floatUp {
        0% {
            opacity: 1;
            transform: translateY(0);
        }
        100% {
            opacity: 0;
            transform: translateY(-50px);
        }
    }
    
    @keyframes slideOut {
        0% {
            opacity: 1;
            transform: translateX(0) scale(1);
        }
        100% {
            opacity: 0;
            transform: translateX(100px) scale(0.5);
        }
    }
    
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-10px); }
        75% { transform: translateX(10px); }
    }
`;
document.head.appendChild(style);

// 更新 UI
function updateUI() {
    elements.moneyAmount.textContent = gameState.money;
    elements.levelText.textContent = `LEVEL ${gameState.level}`;
    
    const progressPercent = (gameState.experience / gameState.experienceToNextLevel) * 100;
    elements.levelProgress.style.width = `${progressPercent}%`;
}

// 啟動遊戲
initGame();

