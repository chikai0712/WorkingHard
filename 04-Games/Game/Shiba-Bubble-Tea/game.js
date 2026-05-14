// 遊戲狀態
const gameState = {
    currentLevel: 1,
    totalCoins: 0,
    drinksMade: 0,
    perfectCount: 0,
    currentStage: 'idle',
    currentOrder: null,
    shakeCount: 0,
    pourLevel: 0,
    bobaCount: 0,
    sealProgress: 0,
    isPerfect: false
};

// 遊戲配置
const config = {
    stages: ['shake', 'pour', 'boba', 'seal', 'complete'],
    shakeRequired: 10,
    pourTarget: 70, // 70% 高度
    pourTolerance: 5, // ±5% 容錯
    bobaRequired: 8,
    customers: ['🐶', '🐱', '🐰', '🐻', '🦊', '🐼', '🐨', '🐯'],
    orders: [
        { name: '經典珍奶', emoji: '🧋' },
        { name: '黑糖珍奶', emoji: '🧋' },
        { name: '抹茶珍奶', emoji: '🍵' },
        { name: '草莓珍奶', emoji: '🍓' }
    ],
    rewards: {
        perfect: 50,
        good: 30,
        normal: 20
    }
};

// DOM 元素
const elements = {
    // 頂部
    currentLevel: document.getElementById('current-level'),
    totalCoins: document.getElementById('total-coins'),
    
    // 顧客
    customer: document.getElementById('customer'),
    orderDisplay: document.getElementById('order-display'),
    
    // 步驟指示
    stepText: document.getElementById('step-text'),
    progressBar: document.getElementById('progress-bar'),
    
    // 各階段
    shakeStage: document.getElementById('shake-stage'),
    pourStage: document.getElementById('pour-stage'),
    bobaStage: document.getElementById('boba-stage'),
    sealStage: document.getElementById('seal-stage'),
    completeStage: document.getElementById('complete-stage'),
    
    // 互動元素
    shaker: document.getElementById('shaker'),
    shakeCount: document.getElementById('shake-count'),
    cupLiquid: document.getElementById('cup-liquid'),
    bobaArea: document.getElementById('boba-area'),
    bobaCount: document.getElementById('boba-count'),
    cupWithTea: document.getElementById('cup-with-tea'),
    sealFilm: document.getElementById('seal-film'),
    sealBar: document.getElementById('seal-bar'),
    cupFinal: document.getElementById('cup-final'),
    
    // 完成
    rating: document.getElementById('rating'),
    coinsEarned: document.getElementById('coins-earned'),
    nextButton: document.getElementById('next-button'),
    
    // 按鈕
    startButton: document.getElementById('start-button'),
    
    // 統計
    drinksMade: document.getElementById('drinks-made'),
    perfectCount: document.getElementById('perfect-count'),
    
    // 教學
    tutorialOverlay: document.getElementById('tutorial-overlay'),
    startTutorial: document.getElementById('start-tutorial')
};

// 初始化遊戲
function initGame() {
    console.log('遊戲初始化中...');
    
    // 確保開始按鈕顯示
    if (elements.startButton) {
        elements.startButton.classList.remove('hidden');
        console.log('開始按鈕已顯示');
    }
    
    // 確保教學提示顯示
    if (elements.tutorialOverlay) {
        elements.tutorialOverlay.classList.remove('hidden');
        console.log('教學提示已顯示');
    }
    
    setupEventListeners();
    updateUI();
    console.log('遊戲初始化完成！');
}

// 設置事件監聽器
function setupEventListeners() {
    // 教學按鈕
    elements.startTutorial.addEventListener('click', () => {
        elements.tutorialOverlay.classList.add('hidden');
    });
    
    // 開始按鈕
    elements.startButton.addEventListener('click', startMaking);
    
    // 下一位顧客按鈕
    elements.nextButton.addEventListener('click', nextCustomer);
    
    // 搖茶 - 拖曳
    let isDragging = false;
    let lastX = 0;
    let shakeVelocity = 0;
    
    elements.shaker.addEventListener('mousedown', (e) => {
        isDragging = true;
        lastX = e.clientX;
    });
    
    elements.shaker.addEventListener('touchstart', (e) => {
        isDragging = true;
        lastX = e.touches[0].clientX;
    });
    
    document.addEventListener('mousemove', (e) => {
        if (isDragging && gameState.currentStage === 'shake') {
            const deltaX = e.clientX - lastX;
            shakeVelocity = Math.abs(deltaX);
            
            if (shakeVelocity > 10) {
                shake();
                elements.shaker.style.transform = `translateX(${deltaX}px) rotate(${deltaX * 0.5}deg)`;
            }
            
            lastX = e.clientX;
        }
    });
    
    document.addEventListener('touchmove', (e) => {
        if (isDragging && gameState.currentStage === 'shake') {
            const deltaX = e.touches[0].clientX - lastX;
            shakeVelocity = Math.abs(deltaX);
            
            if (shakeVelocity > 10) {
                shake();
                elements.shaker.style.transform = `translateX(${deltaX}px) rotate(${deltaX * 0.5}deg)`;
            }
            
            lastX = e.touches[0].clientX;
        }
    });
    
    document.addEventListener('mouseup', () => {
        isDragging = false;
        if (elements.shaker) {
            elements.shaker.style.transform = 'translateX(0) rotate(0)';
        }
    });
    
    document.addEventListener('touchend', () => {
        isDragging = false;
        if (elements.shaker) {
            elements.shaker.style.transform = 'translateX(0) rotate(0)';
        }
    });
    
    // 倒茶 - 長按
    let isPouring = false;
    let pourInterval;
    
    elements.pourStage.addEventListener('mousedown', () => {
        if (gameState.currentStage === 'pour') {
            isPouring = true;
            startPouring();
        }
    });
    
    elements.pourStage.addEventListener('touchstart', (e) => {
        e.preventDefault();
        if (gameState.currentStage === 'pour') {
            isPouring = true;
            startPouring();
        }
    });
    
    document.addEventListener('mouseup', () => {
        if (isPouring) {
            isPouring = false;
            stopPouring();
        }
    });
    
    document.addEventListener('touchend', () => {
        if (isPouring) {
            isPouring = false;
            stopPouring();
        }
    });
    
    function startPouring() {
        pourInterval = setInterval(() => {
            if (gameState.pourLevel < 100) {
                gameState.pourLevel += 1;
                elements.cupLiquid.style.height = `${gameState.pourLevel}%`;
            } else {
                stopPouring();
            }
        }, 30);
    }
    
    function stopPouring() {
        clearInterval(pourInterval);
        if (gameState.pourLevel >= config.pourTarget - config.pourTolerance) {
            setTimeout(() => {
                nextStage();
            }, 500);
        }
    }
    
    // 加珍珠 - 點擊
    elements.cupWithTea.addEventListener('click', () => {
        if (gameState.currentStage === 'boba' && gameState.bobaCount < config.bobaRequired) {
            addBoba();
        }
    });
    
    // 封膜 - 拖曳
    let isSealing = false;
    let sealStartX = 0;
    
    elements.cupFinal.addEventListener('mousedown', (e) => {
        if (gameState.currentStage === 'seal') {
            isSealing = true;
            sealStartX = e.clientX;
        }
    });
    
    elements.cupFinal.addEventListener('touchstart', (e) => {
        if (gameState.currentStage === 'seal') {
            isSealing = true;
            sealStartX = e.touches[0].clientX;
        }
    });
    
    document.addEventListener('mousemove', (e) => {
        if (isSealing && gameState.currentStage === 'seal') {
            const deltaX = e.clientX - sealStartX;
            const progress = Math.min(100, Math.max(0, (deltaX / 200) * 100));
            gameState.sealProgress = progress;
            elements.sealFilm.style.width = `${progress}%`;
            elements.sealBar.style.width = `${progress}%`;
            
            if (progress >= 100) {
                isSealing = false;
                setTimeout(() => {
                    nextStage();
                }, 300);
            }
        }
    });
    
    document.addEventListener('touchmove', (e) => {
        if (isSealing && gameState.currentStage === 'seal') {
            const deltaX = e.touches[0].clientX - sealStartX;
            const progress = Math.min(100, Math.max(0, (deltaX / 200) * 100));
            gameState.sealProgress = progress;
            elements.sealFilm.style.width = `${progress}%`;
            elements.sealBar.style.width = `${progress}%`;
            
            if (progress >= 100) {
                isSealing = false;
                setTimeout(() => {
                    nextStage();
                }, 300);
            }
        }
    });
    
    document.addEventListener('mouseup', () => {
        isSealing = false;
    });
    
    document.addEventListener('touchend', () => {
        isSealing = false;
    });
}

// 開始製作
function startMaking() {
    elements.startButton.classList.add('hidden');
    spawnCustomer();
    setTimeout(() => {
        startStage('shake');
    }, 1000);
}

// 生成顧客
function spawnCustomer() {
    const customer = config.customers[Math.floor(Math.random() * config.customers.length)];
    const order = config.orders[Math.floor(Math.random() * config.orders.length)];
    
    gameState.currentOrder = order;
    
    elements.customer.querySelector('.customer-avatar').textContent = customer;
    elements.orderDisplay.textContent = `我要一杯${order.name}！${order.emoji}`;
    elements.customer.classList.remove('hidden');
}

// 開始階段
function startStage(stage) {
    gameState.currentStage = stage;
    
    // 隱藏所有階段
    elements.shakeStage.classList.add('hidden');
    elements.pourStage.classList.add('hidden');
    elements.bobaStage.classList.add('hidden');
    elements.sealStage.classList.add('hidden');
    elements.completeStage.classList.add('hidden');
    
    // 顯示當前階段
    switch(stage) {
        case 'shake':
            elements.stepText.textContent = '步驟 1/4：搖茶';
            elements.progressBar.style.width = '25%';
            elements.shakeStage.classList.remove('hidden');
            gameState.shakeCount = 0;
            elements.shakeCount.textContent = '0';
            break;
        case 'pour':
            elements.stepText.textContent = '步驟 2/4：倒茶';
            elements.progressBar.style.width = '50%';
            elements.pourStage.classList.remove('hidden');
            gameState.pourLevel = 0;
            elements.cupLiquid.style.height = '0%';
            break;
        case 'boba':
            elements.stepText.textContent = '步驟 3/4：加珍珠';
            elements.progressBar.style.width = '75%';
            elements.bobaStage.classList.remove('hidden');
            gameState.bobaCount = 0;
            elements.bobaCount.textContent = '0';
            elements.bobaArea.innerHTML = '';
            break;
        case 'seal':
            elements.stepText.textContent = '步驟 4/4：封膜';
            elements.progressBar.style.width = '100%';
            elements.sealStage.classList.remove('hidden');
            gameState.sealProgress = 0;
            elements.sealFilm.style.width = '0%';
            elements.sealBar.style.width = '0%';
            break;
        case 'complete':
            elements.stepText.textContent = '完成！';
            elements.completeStage.classList.remove('hidden');
            calculateReward();
            break;
    }
}

// 搖茶
function shake() {
    gameState.shakeCount++;
    elements.shakeCount.textContent = gameState.shakeCount;
    
    // 添加震動效果
    elements.shaker.style.animation = 'none';
    setTimeout(() => {
        elements.shaker.style.animation = '';
    }, 10);
    
    if (gameState.shakeCount >= config.shakeRequired) {
        setTimeout(() => {
            nextStage();
        }, 500);
    }
}

// 加珍珠
function addBoba() {
    gameState.bobaCount++;
    elements.bobaCount.textContent = gameState.bobaCount;
    
    const boba = document.createElement('div');
    boba.className = 'boba';
    elements.bobaArea.appendChild(boba);
    
    if (gameState.bobaCount >= config.bobaRequired) {
        setTimeout(() => {
            nextStage();
        }, 500);
    }
}

// 下一階段
function nextStage() {
    const currentIndex = config.stages.indexOf(gameState.currentStage);
    if (currentIndex < config.stages.length - 1) {
        startStage(config.stages[currentIndex + 1]);
    }
}

// 計算獎勵
function calculateReward() {
    let rating = '';
    let coins = 0;
    
    // 判斷完美度
    const isPerfectShake = gameState.shakeCount === config.shakeRequired;
    const isPerfectPour = Math.abs(gameState.pourLevel - config.pourTarget) <= config.pourTolerance;
    const isPerfectBoba = gameState.bobaCount === config.bobaRequired;
    const isPerfectSeal = gameState.sealProgress === 100;
    
    const perfectSteps = [isPerfectShake, isPerfectPour, isPerfectBoba, isPerfectSeal].filter(Boolean).length;
    
    if (perfectSteps === 4) {
        rating = '⭐⭐⭐ 完美！';
        coins = config.rewards.perfect;
        gameState.perfectCount++;
        gameState.isPerfect = true;
    } else if (perfectSteps >= 2) {
        rating = '⭐⭐ 很好！';
        coins = config.rewards.good;
    } else {
        rating = '⭐ 不錯！';
        coins = config.rewards.normal;
    }
    
    gameState.totalCoins += coins;
    gameState.drinksMade++;
    
    elements.rating.textContent = rating;
    elements.coinsEarned.textContent = coins;
    
    updateUI();
}

// 下一位顧客
function nextCustomer() {
    // 隱藏顧客
    elements.customer.classList.add('hidden');
    
    // 重置狀態
    gameState.currentStage = 'idle';
    gameState.shakeCount = 0;
    gameState.pourLevel = 0;
    gameState.bobaCount = 0;
    gameState.sealProgress = 0;
    gameState.isPerfect = false;
    
    // 隱藏完成階段
    elements.completeStage.classList.add('hidden');
    
    // 顯示開始按鈕
    elements.startButton.classList.remove('hidden');
    elements.stepText.textContent = '點擊開始製作';
    elements.progressBar.style.width = '0%';
}

// 更新 UI
function updateUI() {
    elements.currentLevel.textContent = gameState.currentLevel;
    elements.totalCoins.textContent = gameState.totalCoins;
    elements.drinksMade.textContent = gameState.drinksMade;
    elements.perfectCount.textContent = gameState.perfectCount;
}

// 啟動遊戲
initGame();

