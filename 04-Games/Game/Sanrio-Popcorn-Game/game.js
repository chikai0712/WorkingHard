// ===================================
// 三麗鷗爆米花大遊行 - 遊戲邏輯
// ===================================

class PopcornGame {
    constructor() {
        // 遊戲狀態
        this.score = 0;
        this.level = 1;
        this.feverMeter = 0;
        this.currentStage = 1;
        this.isPlaying = false;
        this.isFeverTime = false;
        
        // 生產線狀態
        this.collectedCorns = 0;      // 階段1收集的玉米數
        this.heatedPopcorns = 0;       // 階段2加熱好的爆米花數
        this.packagedPopcorns = 0;     // 階段3包裝好的爆米花數
        
        // 階段實例
        this.stages = {
            1: new CinnamorollStage(this),
            2: new KuromiStage(this),
            3: new PompompurinStage(this),
            4: new MyMelodyStage(this)
        };
        
        // DOM 元素
        this.elements = {
            startScreen: document.getElementById('start-screen'),
            gameOverScreen: document.getElementById('game-over-screen'),
            gameContainer: document.getElementById('game-container'),
            scoreDisplay: document.getElementById('score'),
            levelDisplay: document.getElementById('level'),
            feverFill: document.getElementById('fever-fill'),
            feverPercent: document.getElementById('fever-percent'),
            feverOverlay: document.getElementById('fever-overlay'),
            gameMessage: document.getElementById('game-message'),
            finalScoreValue: document.getElementById('final-score-value')
        };
        
        this.init();
    }
    
    init() {
        console.log('🎮 遊戲初始化...');
        
        // 綁定事件
        document.getElementById('start-btn').addEventListener('click', () => this.startGame());
        document.getElementById('restart-btn').addEventListener('click', () => this.restartGame());
        
        // 音效控制按鈕
        const muteBtn = document.getElementById('mute-btn');
        if (muteBtn) {
            muteBtn.addEventListener('click', () => {
                const isMuted = audioManager.toggleMute();
                muteBtn.textContent = isMuted ? '🔇' : '🔊';
                muteBtn.classList.toggle('muted', isMuted);
            });
        }
        
        // 階段切換按鈕
        document.querySelectorAll('.stage-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const stage = parseInt(btn.dataset.stage);
                this.switchStage(stage);
            });
        });
        
        // 鍵盤快捷鍵
        document.addEventListener('keydown', (e) => this.handleKeyPress(e));
        
        console.log('✅ 遊戲初始化完成');
    }
    
    startGame() {
        console.log('🎮 開始遊戲');
        this.elements.startScreen.classList.add('hidden');
        this.isPlaying = true;
        this.score = 0;
        this.level = 1;
        this.feverMeter = 0;
        this.currentStage = 1;
        
        // 重置生產線狀態
        this.collectedCorns = 0;
        this.heatedPopcorns = 0;
        this.packagedPopcorns = 0;
        
        this.updateUI();
        this.switchStage(1);
        
        // 啟動第一個階段
        this.stages[1].start();
        
        // 播放背景音樂
        audioManager.playBGM();
    }
    
    switchStage(stageNum) {
        if (!this.isPlaying) return;
        
        console.log(`🔄 切換到階段 ${stageNum}`);
        
        // 停止當前階段
        if (this.stages[this.currentStage]) {
            this.stages[this.currentStage].stop();
        }
        
        // 隱藏所有階段
        document.querySelectorAll('.stage').forEach(stage => {
            stage.classList.remove('active');
        });
        
        // 顯示新階段
        document.getElementById(`stage${stageNum}`).classList.add('active');
        
        // 更新按鈕狀態
        document.querySelectorAll('.stage-btn').forEach(btn => {
            btn.classList.remove('active');
            if (parseInt(btn.dataset.stage) === stageNum) {
                btn.classList.add('active');
            }
        });
        
        this.currentStage = stageNum;
        
        // 啟動新階段
        if (this.stages[stageNum]) {
            this.stages[stageNum].start();
        }
    }
    
    handleKeyPress(e) {
        if (!this.isPlaying) return;
        
        // 數字鍵 1-4 切換階段
        if (e.key >= '1' && e.key <= '4') {
            this.switchStage(parseInt(e.key));
        }
        
        // 傳遞按鍵給當前階段
        if (this.stages[this.currentStage]) {
            this.stages[this.currentStage].handleKeyPress(e);
        }
    }
    
    addScore(points) {
        const multiplier = this.isFeverTime ? 3 : 1;
        this.score += points * multiplier;
        this.updateUI();
        
        // 顯示得分動畫
        if (points > 0) {
            this.showMessage(`+${points * multiplier}`, 'success');
            
            // 添加特效
            const rect = this.elements.scoreDisplay.getBoundingClientRect();
            effectsManager.createStars(rect.left + rect.width / 2, rect.top + rect.height / 2, 5);
        }
    }
    
    addFeverMeter(amount) {
        this.feverMeter = Math.min(100, this.feverMeter + amount);
        this.updateUI();
        
        // 檢查是否觸發 Fever Time
        if (this.feverMeter >= 100 && !this.isFeverTime) {
            this.startFeverTime();
        }
    }
    
    startFeverTime() {
        console.log('🌟 Fever Time 開始！');
        this.isFeverTime = true;
        this.feverMeter = 0;
        
        // 顯示 Fever 特效
        this.elements.feverOverlay.classList.remove('hidden');
        this.showMessage('🌟 FEVER TIME! 🌟', 'fever');
        
        // 播放音效
        audioManager.playSound('feverStart');
        
        // 創建特效
        effectsManager.createFeverEffect();
        
        // 通知所有階段
        Object.values(this.stages).forEach(stage => {
            if (stage.onFeverStart) stage.onFeverStart();
        });
        
        // 15 秒後結束
        setTimeout(() => this.endFeverTime(), 15000);
    }
    
    endFeverTime() {
        console.log('⭐ Fever Time 結束');
        this.isFeverTime = false;
        this.elements.feverOverlay.classList.add('hidden');
        
        // 通知所有階段
        Object.values(this.stages).forEach(stage => {
            if (stage.onFeverEnd) stage.onFeverEnd();
        });
    }
    
    showMessage(text, type = 'info') {
        const msg = this.elements.gameMessage;
        msg.textContent = text;
        msg.className = `show ${type}`;
        
        setTimeout(() => {
            msg.classList.remove('show');
        }, 1000);
    }
    
    updateUI() {
        this.elements.scoreDisplay.textContent = this.score;
        this.elements.levelDisplay.textContent = this.level;
        this.elements.feverFill.style.width = `${this.feverMeter}%`;
        this.elements.feverPercent.textContent = `${Math.floor(this.feverMeter)}%`;
    }
    
    gameOver() {
        console.log('🎮 遊戲結束');
        this.isPlaying = false;
        
        // 停止所有階段
        Object.values(this.stages).forEach(stage => stage.stop());
        
        // 顯示結束畫面
        this.elements.finalScoreValue.textContent = this.score;
        this.elements.gameOverScreen.classList.remove('hidden');
    }
    
    restartGame() {
        this.elements.gameOverScreen.classList.add('hidden');
        this.startGame();
    }
}

// ===================================
// 階段 1: 大耳狗 - 原料接取
// ===================================
class CinnamorollStage {
    constructor(game) {
        this.game = game;
        this.isActive = false;
        this.basketX = 400; // 籃子 X 座標
        this.corns = [];
        this.cornCount = 0;
        this.spawnInterval = null;
        this.updateInterval = null;
        
        // DOM 元素
        this.character = document.getElementById('cinnamoroll');
        this.dropZone = document.getElementById('corn-drop-zone');
        this.cornCounter = document.getElementById('corn-count');
        
        // 綁定滑鼠移動
        document.addEventListener('mousemove', (e) => this.handleMouseMove(e));
    }
    
    start() {
        console.log('🐶 大耳狗階段開始');
        this.isActive = true;
        this.cornCount = 0;
        this.updateUI();
        
        // 開始生成玉米
        this.spawnInterval = setInterval(() => this.spawnCorn(), 1500);
        
        // 開始更新
        this.updateInterval = setInterval(() => this.update(), 50);
    }
    
    stop() {
        console.log('🐶 大耳狗階段停止');
        this.isActive = false;
        clearInterval(this.spawnInterval);
        clearInterval(this.updateInterval);
        
        // 清除所有玉米
        this.corns.forEach(corn => corn.element.remove());
        this.corns = [];
    }
    
    spawnCorn() {
        if (!this.isActive) return;
        
        const rand = Math.random() * 100;
        let type, emoji;
        
        if (rand < 70) {
            type = 'good';
            emoji = '🌽';
        } else if (rand < 90) {
            type = 'golden';
            emoji = '⭐';
        } else if (rand < 98) {
            type = 'bad';
            emoji = '🥀';
        } else {
            type = 'rock';
            emoji = '🪨';
        }
        
        const corn = {
            x: Math.random() * 700 + 50,
            y: -50,
            type: type,
            element: this.createCornElement(emoji, type)
        };
        
        this.corns.push(corn);
        this.dropZone.appendChild(corn.element);
    }
    
    createCornElement(emoji, type) {
        const el = document.createElement('div');
        el.className = `corn ${type}`;
        el.textContent = emoji;
        el.style.left = '0px';
        el.style.animationDuration = '3s';
        return el;
    }
    
    update() {
        if (!this.isActive) return;
        
        // 更新玉米位置並檢查碰撞
        this.corns = this.corns.filter(corn => {
            corn.y += 5;
            corn.element.style.top = `${corn.y}px`;
            corn.element.style.left = `${corn.x}px`;
            
            // 檢查碰撞
            if (this.checkCollision(corn)) {
                this.collectCorn(corn);
                corn.element.remove();
                return false;
            }
            
            // 移除超出畫面的玉米
            if (corn.y > 350) {
                corn.element.remove();
                return false;
            }
            
            return true;
        });
    }
    
    checkCollision(corn) {
        const basketLeft = this.basketX - 40;
        const basketRight = this.basketX + 40;
        const basketTop = 280;
        
        return corn.x > basketLeft && 
               corn.x < basketRight && 
               corn.y > basketTop && 
               corn.y < basketTop + 50;
    }
    
    collectCorn(corn) {
        switch (corn.type) {
            case 'good':
                this.cornCount++;
                this.game.addScore(10);
                this.game.addFeverMeter(5);
                audioManager.playSound('cornCatch');
                break;
            case 'golden':
                this.cornCount++;
                this.game.addScore(30);
                this.game.addFeverMeter(15);
                this.game.showMessage('⭐ 金色玉米！', 'success');
                audioManager.playSound('goldenCorn');
                break;
            case 'bad':
                this.game.addScore(-5);
                this.game.showMessage('💥 壞玉米！', 'warning');
                audioManager.playSound('badCorn');
                break;
            case 'rock':
                this.game.addScore(-10);
                this.game.showMessage('🪨 石頭！', 'danger');
                audioManager.playSound('badCorn');
                break;
        }
        
        this.updateUI();
        
        // 收集滿 3 個玉米 → 進入階段 2
        if (this.cornCount >= 3) {
            this.game.showMessage('✅ 玉米收集完成！送去加熱', 'success');
            this.game.collectedCorns += 3;
            this.cornCount = 0;
            this.game.addFeverMeter(10);
            this.updateUI();
            
            // 自動切換到階段 2
            setTimeout(() => {
                this.game.switchStage(2);
            }, 1000);
        }
    }
    
    handleMouseMove(e) {
        if (!this.isActive) return;
        
        const rect = this.dropZone.getBoundingClientRect();
        this.basketX = Math.max(50, Math.min(750, e.clientX - rect.left));
        this.character.style.left = `${this.basketX}px`;
    }
    
    handleKeyPress(e) {
        if (!this.isActive) return;
        
        if (e.key === 'ArrowLeft') {
            this.basketX = Math.max(50, this.basketX - 20);
            this.character.style.left = `${this.basketX}px`;
        } else if (e.key === 'ArrowRight') {
            this.basketX = Math.min(750, this.basketX + 20);
            this.character.style.left = `${this.basketX}px`;
        }
    }
    
    updateUI() {
        this.cornCounter.textContent = this.cornCount;
    }
    
    onFeverStart() {
        // Fever Time 效果：自動吸引玉米
        console.log('🐶 大耳狗 Fever 效果啟動');
    }
    
    onFeverEnd() {
        console.log('🐶 大耳狗 Fever 效果結束');
    }
}

// ===================================
// 階段 2: 庫洛米 - 魔法加熱
// ===================================
class KuromiStage {
    constructor(game) {
        this.game = game;
        this.isActive = false;
        this.temperature = 0;
        this.targetMin = 60;
        this.targetMax = 80;
        this.coolingInterval = null;
        
        // DOM 元素
        this.tempFill = document.getElementById('temp-fill');
        this.tempValue = document.getElementById('temp-value');
        this.stageContent = document.querySelector('#stage2 .stage-content');
        
        // 綁定點擊事件
        this.stageContent.addEventListener('click', () => this.heat());
    }
    
    start() {
        console.log('😈 庫洛米階段開始');
        this.isActive = true;
        this.temperature = 0;
        this.updateUI();
        
        // 開始自動降溫
        this.coolingInterval = setInterval(() => this.cool(), 100);
    }
    
    stop() {
        console.log('😈 庫洛米階段停止');
        this.isActive = false;
        clearInterval(this.coolingInterval);
    }
    
    heat() {
        if (!this.isActive) return;
        
        this.temperature = Math.min(100, this.temperature + 5);
        this.updateUI();
        
        // 檢查是否在黃金區間
        if (this.temperature >= this.targetMin && this.temperature <= this.targetMax) {
            // 在黃金區間
            if (this.temperature === this.targetMax) {
                this.explode();
            }
        } else if (this.temperature > 90) {
            // 燒焦
            this.game.showMessage('🔥 燒焦了！', 'danger');
            this.temperature = 0;
        }
    }
    
    cool() {
        if (!this.isActive) return;
        
        this.temperature = Math.max(0, this.temperature - 2);
        this.updateUI();
    }
    
    explode() {
        console.log('💥 完美爆發！');
        this.game.addScore(50);
        this.game.addFeverMeter(20);
        this.game.showMessage('💥 完美爆米花！送去包裝', 'perfect');
        audioManager.playSound('explode');
        
        // 產生爆米花
        this.game.heatedPopcorns += 3;
        this.temperature = 0;
        this.updateUI();
        
        // 自動切換到階段 3
        setTimeout(() => {
            this.game.switchStage(3);
        }, 1000);
    }
    
    handleKeyPress(e) {
        if (!this.isActive) return;
        
        if (e.key === ' ') {
            e.preventDefault();
            this.heat();
        }
    }
    
    updateUI() {
        this.tempFill.style.width = `${this.temperature}%`;
        this.tempValue.textContent = Math.floor(this.temperature);
        
        // 根據溫度改變顏色
        if (this.temperature >= this.targetMin && this.temperature <= this.targetMax) {
            this.tempFill.style.background = 'rgba(255, 215, 0, 0.8)';
        } else if (this.temperature > 90) {
            this.tempFill.style.background = 'rgba(255, 0, 0, 0.8)';
        } else {
            this.tempFill.style.background = 'rgba(255, 255, 255, 0.5)';
        }
    }
    
    onFeverStart() {
        console.log('😈 庫洛米 Fever 效果啟動');
        // Fever Time：自動維持完美溫度
    }
    
    onFeverEnd() {
        console.log('😈 庫洛米 Fever 效果結束');
    }
}

// ===================================
// 階段 3: 布丁狗 - 精準包裝
// ===================================
class PompompurinStage {
    constructor(game) {
        this.game = game;
        this.isActive = false;
        this.combo = 0;
        this.popcorns = [];
        this.spawnInterval = null;
        this.updateInterval = null;
        
        // DOM 元素
        this.flightZone = document.getElementById('popcorn-flight-zone');
        this.comboDisplay = document.getElementById('combo-count');
        this.timingFeedback = document.getElementById('timing-feedback');
        this.stageContent = document.querySelector('#stage3 .stage-content');
        
        // 綁定點擊事件
        this.stageContent.addEventListener('click', () => this.tryPackage());
    }
    
    start() {
        console.log('🐶 布丁狗階段開始');
        this.isActive = true;
        this.combo = 0;
        this.updateUI();
        
        // 開始生成爆米花
        this.spawnInterval = setInterval(() => this.spawnPopcorn(), 2000);
        
        // 開始更新
        this.updateInterval = setInterval(() => this.update(), 50);
    }
    
    stop() {
        console.log('🐶 布丁狗階段停止');
        this.isActive = false;
        clearInterval(this.spawnInterval);
        clearInterval(this.updateInterval);
        
        // 清除所有爆米花
        this.popcorns.forEach(p => p.element.remove());
        this.popcorns = [];
    }
    
    spawnPopcorn() {
        if (!this.isActive) return;
        
        const popcorn = {
            x: -50,
            y: 50,
            speed: 3 + Math.random() * 2,
            element: this.createPopcornElement()
        };
        
        this.popcorns.push(popcorn);
        this.flightZone.appendChild(popcorn.element);
    }
    
    createPopcornElement() {
        const el = document.createElement('div');
        el.className = 'flying-popcorn';
        el.textContent = '🍿';
        return el;
    }
    
    update() {
        if (!this.isActive) return;
        
        this.popcorns = this.popcorns.filter(popcorn => {
            popcorn.x += popcorn.speed;
            popcorn.element.style.left = `${popcorn.x}px`;
            
            // 移除超出畫面的爆米花
            if (popcorn.x > 850) {
                popcorn.element.remove();
                this.combo = 0;
                this.updateUI();
                return false;
            }
            
            return true;
        });
    }
    
    tryPackage() {
        if (!this.isActive || this.popcorns.length === 0) return;
        
        // 找到最接近目標的爆米花
        const target = this.popcorns.find(p => {
            const distance = Math.abs(p.x - 400);
            return distance < 100;
        });
        
        if (target) {
            const distance = Math.abs(target.x - 400);
            let timing, points, text;
            
            if (distance < 20) {
                timing = 'perfect';
                points = 20;
                text = 'Perfect!';
                audioManager.playSound('perfect');
            } else if (distance < 50) {
                timing = 'great';
                points = 15;
                text = 'Great!';
                audioManager.playSound('great');
            } else {
                timing = 'good';
                points = 10;
                text = 'Good!';
                audioManager.playSound('good');
            }
            
            this.combo++;
            const comboBonus = Math.floor(this.combo / 5) * 0.1;
            const finalPoints = Math.floor(points * (1 + comboBonus));
            
            this.game.addScore(finalPoints);
            this.game.addFeverMeter(5);
            this.showTiming(text, timing);
            
            // 包裝成功，傳遞到階段 4
            this.game.packagedPopcorns++;
            
            // 移除爆米花
            target.element.remove();
            this.popcorns = this.popcorns.filter(p => p !== target);
            
            this.updateUI();
            
            // 如果包裝了 3 個，自動切換到階段 4
            if (this.game.packagedPopcorns >= 3) {
                setTimeout(() => {
                    this.game.showMessage('📦 爆米花包裝完成！送去裝箱', 'success');
                    setTimeout(() => {
                        this.game.switchStage(4);
                    }, 1000);
                }, 500);
            }
        } else {
            this.showTiming('Miss!', 'miss');
            audioManager.playSound('miss');
            this.combo = 0;
            this.updateUI();
        }
    }
    
    showTiming(text, type) {
        this.timingFeedback.textContent = text;
        this.timingFeedback.className = `show ${type}`;
        
        setTimeout(() => {
            this.timingFeedback.classList.remove('show');
        }, 500);
    }
    
    handleKeyPress(e) {
        if (!this.isActive) return;
        
        if (e.key === ' ') {
            e.preventDefault();
            this.tryPackage();
        }
    }
    
    updateUI() {
        this.comboDisplay.textContent = this.combo;
    }
    
    onFeverStart() {
        console.log('🐶 布丁狗 Fever 效果啟動');
        // Fever Time：所有判定都是 Perfect
    }
    
    onFeverEnd() {
        console.log('🐶 布丁狗 Fever 效果結束');
    }
}

// ===================================
// 階段 4: 美樂蒂 - 裝箱送餐
// ===================================
class MyMelodyStage {
    constructor(game) {
        this.game = game;
        this.isActive = false;
        this.readyPopcorns = [];
        this.boxCount = 0;
        this.customers = [];
        
        // DOM 元素
        this.readyZone = document.getElementById('popcorn-ready-zone');
        this.boxZone = document.getElementById('box-zone');
        this.customerQueue = document.getElementById('customer-queue');
    }
    
    start() {
        console.log('🐰 美樂蒂階段開始');
        this.isActive = true;
        this.boxCount = 0;
        
        // 生成待裝爆米花（使用從階段 3 傳來的數量）
        this.generateReadyPopcorns();
        
        // 生成客人
        this.spawnCustomer();
    }
    
    stop() {
        console.log('🐰 美樂蒂階段停止');
        this.isActive = false;
        
        // 清除所有元素
        this.readyZone.innerHTML = '';
        this.customerQueue.innerHTML = '';
        this.readyPopcorns = [];
        this.customers = [];
    }
    
    generateReadyPopcorns() {
        this.readyZone.innerHTML = '';
        
        // 使用從階段 3 傳來的包裝好的爆米花數量
        const popcornCount = this.game.packagedPopcorns || 0;
        
        // 如果沒有爆米花，顯示提示
        if (popcornCount === 0) {
            const hint = document.createElement('div');
            hint.className = 'empty-hint';
            hint.innerHTML = '📦 還沒有包裝好的爆米花<br>請先完成前面的階段！';
            hint.style.cssText = `
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                font-size: 24px;
                color: rgba(255, 255, 255, 0.8);
                text-align: center;
                line-height: 1.5;
            `;
            this.readyZone.appendChild(hint);
            return;
        }
        
        for (let i = 0; i < popcornCount; i++) {
            const popcorn = document.createElement('div');
            popcorn.className = 'ready-popcorn';
            popcorn.textContent = '🍿';
            popcorn.draggable = true;
            
            popcorn.addEventListener('dragstart', (e) => {
                e.dataTransfer.effectAllowed = 'move';
                popcorn.classList.add('dragging');
            });
            
            popcorn.addEventListener('dragend', () => {
                popcorn.classList.remove('dragging');
            });
            
            this.readyZone.appendChild(popcorn);
        }
        
        // 設置拖放目標
        this.boxZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
        });
        
        this.boxZone.addEventListener('drop', (e) => {
            e.preventDefault();
            this.addToBox();
        });
    }
    
    addToBox() {
        // 檢查是否還有爆米花
        const popcorns = this.readyZone.querySelectorAll('.ready-popcorn');
        if (popcorns.length === 0) {
            this.game.showMessage('❌ 沒有爆米花了！', 'warning');
            return;
        }
        
        if (this.boxCount < 6) {
            this.boxCount++;
            this.updateBoxUI();
            this.game.addScore(5);
            audioManager.playSound('good');
            
            // 移除一個爆米花
            popcorns[0].remove();
            this.game.packagedPopcorns--;
            
            if (this.boxCount === 6) {
                audioManager.playSound('boxFull');
                this.serveCustomer();
            }
        }
    }
    
    serveCustomer() {
        if (this.customers.length > 0) {
            const customer = this.customers.shift();
            customer.element.remove();
            
            this.game.addScore(100);
            this.game.addFeverMeter(15);
            this.game.showMessage('✅ 客人滿意！', 'success');
            audioManager.playSound('customerHappy');
            
            this.boxCount = 0;
            this.updateBoxUI();
            
            // 如果還有爆米花，繼續服務
            if (this.game.packagedPopcorns > 0) {
                setTimeout(() => this.spawnCustomer(), 2000);
            } else {
                // 沒有爆米花了，回到階段 1
                setTimeout(() => {
                    this.game.showMessage('🔄 需要更多爆米花！', 'info');
                    setTimeout(() => {
                        this.game.switchStage(1);
                    }, 1000);
                }, 2000);
            }
        }
    }
    
    spawnCustomer() {
        if (!this.isActive) return;
        
        const customerData = [
            { name: 'Hello Kitty', emoji: '😺', patience: 30 },
            { name: 'Keroppi', emoji: '🐸', patience: 20 },
            { name: 'Bad Badtz-Maru', emoji: '🐧', patience: 15 }
        ];
        
        const data = customerData[Math.floor(Math.random() * customerData.length)];
        
        const customerEl = document.createElement('div');
        customerEl.className = 'customer';
        customerEl.innerHTML = `
            <div class="customer-sprite">${data.emoji}</div>
            <div class="customer-name">${data.name}</div>
            <div class="patience-bar">
                <div class="patience-fill" style="width: 100%"></div>
            </div>
            <div class="order-count">需要: 6個</div>
        `;
        
        this.customerQueue.appendChild(customerEl);
        
        const customer = {
            element: customerEl,
            patience: data.patience,
            maxPatience: data.patience
        };
        
        this.customers.push(customer);
        
        // 開始耐心倒數
        this.startPatienceCountdown(customer);
    }
    
    startPatienceCountdown(customer) {
        const interval = setInterval(() => {
            if (!this.isActive || !this.customers.includes(customer)) {
                clearInterval(interval);
                return;
            }
            
            customer.patience -= 0.1;
            const patienceFill = customer.element.querySelector('.patience-fill');
            const percent = (customer.patience / customer.maxPatience) * 100;
            patienceFill.style.width = `${percent}%`;
            
            if (customer.patience <= 0) {
                clearInterval(interval);
                this.customerLeave(customer);
            }
        }, 100);
    }
    
    customerLeave(customer) {
        this.game.showMessage('😢 客人生氣離開了', 'danger');
        customer.element.remove();
        this.customers = this.customers.filter(c => c !== customer);
        
        // 生成新客人
        setTimeout(() => this.spawnCustomer(), 2000);
    }
    
    updateBoxUI() {
        const boxCountEl = this.boxZone.querySelector('.box-count');
        if (boxCountEl) {
            boxCountEl.textContent = `${this.boxCount}/6`;
        }
    }
    
    handleKeyPress(e) {
        // 美樂蒂階段主要使用拖曳操作
    }
    
    onFeverStart() {
        console.log('🐰 美樂蒂 Fever 效果啟動');
        // Fever Time：客人耐心凍結
    }
    
    onFeverEnd() {
        console.log('🐰 美樂蒂 Fever 效果結束');
    }
}

// ===================================
// 初始化遊戲
// ===================================
window.addEventListener('DOMContentLoaded', () => {
    console.log('🎮 載入三麗鷗爆米花大遊行...');
    const game = new PopcornGame();
    console.log('✅ 遊戲載入完成！');
});

