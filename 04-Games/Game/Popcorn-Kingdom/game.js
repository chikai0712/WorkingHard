// 🎮 遊戲主邏輯

class PopcornKingdomGame {
    constructor() {
        // 初始化管理器
        this.resourceManager = new ResourceManager();
        this.buildingManager = new BuildingManager(this.resourceManager);
        this.characterManager = new CharacterManager();
        this.animationManager = new AnimationManager();
        this.audioManager = new AudioManager();
        this.uiManager = new UIManager(this);
        
        // 連接建築管理器和角色管理器
        this.buildingManager.setCharacterManager(this.characterManager);
        
        // 遊戲狀態
        this.running = false;
        this.lastTime = 0;
        
        // 訂單系統
        this.currentOrder = null;
        this.orderTimer = 0;
        this.orderInterval = 60; // 60秒出現一次訂單
        
        // 載入進度
        this.load();
        
        // 等待 DOM 完全載入後設定角色位置
        setTimeout(() => {
            this.characterManager.positionCharacters();
        }, 100);
        
        // 開始遊戲
        this.start();
    }
    
    start() {
        this.running = true;
        this.lastTime = performance.now();
        this.gameLoop();
        console.log('🎮 爆米花王國已啟動！');
    }
    
    gameLoop() {
        if (!this.running) return;
        
        const currentTime = performance.now();
        const deltaTime = (currentTime - this.lastTime) / 1000; // 轉換為秒
        this.lastTime = currentTime;
        
        // 更新遊戲邏輯
        this.update(deltaTime);
        
        // 繼續循環
        requestAnimationFrame(() => this.gameLoop());
    }
    
    update(deltaTime) {
        // 更新資源（被動收入）
        this.resourceManager.update(deltaTime);
        
        // 更新建築
        const events = this.buildingManager.update(deltaTime);
        
        // 處理建築事件
        events.forEach(event => this.handleBuildingEvent(event));
        
        // 更新角色
        this.characterManager.update(deltaTime);
        
        // 更新動畫
        this.animationManager.update(deltaTime);
        
        // 更新UI進度條
        this.uiManager.updateProgress();
        
        // 更新訂單系統
        this.updateOrderSystem(deltaTime);
    }
    
    handleBuildingEvent(event) {
        const buildingElement = document.getElementById(this.getBuildingElementId(event.building));
        
        switch (event.type) {
            case 'produce':
                // 玉米田生產玉米
                this.audioManager.playSound(event.isGood ? 'produce' : 'bad');
                this.animationManager.flashBuilding(buildingElement);
                break;
                
            case 'needDelivery':
                // 需要角色運送
                this.handleDelivery(event);
                break;
                
            case 'sell':
                // 市場賣玉米（運送完成後）
                if (event.isGood) {
                    this.audioManager.playSound('sell');
                    this.animationManager.animateGoldGain(buildingElement, event.price);
                } else {
                    this.audioManager.playSound('bad');
                    this.animationManager.animateGoldGain(buildingElement, event.price);
                    buildingElement.classList.add('shake');
                    setTimeout(() => buildingElement.classList.remove('shake'), 500);
                }
                break;
                
            case 'cook':
                // 烤爐烤爆米花（運送完成後）
                if (event.success) {
                    this.audioManager.playSound('cook');
                    this.animationManager.flashBuilding(buildingElement);
                } else {
                    this.audioManager.playSound('bad');
                    buildingElement.classList.add('shake');
                    setTimeout(() => buildingElement.classList.remove('shake'), 500);
                }
                break;
                
            case 'deliver':
                // 外送站送爆米花（運送完成後）
                this.audioManager.playSound('deliver');
                this.animationManager.animateGoldGain(buildingElement, event.price);
                
                // 檢查訂單
                this.checkOrder();
                break;
        }
    }
    
    handleDelivery(event) {
        const fromBuilding = document.getElementById(this.getBuildingElementId(event.from));
        const toBuilding = document.getElementById(this.getBuildingElementId(event.building));
        
        if (!fromBuilding || !toBuilding) {
            console.error('❌ 建築元素不存在:', event.from, event.building);
            return;
        }
        
        // 決定使用哪個角色
        let characterId;
        let itemEmoji;
        
        if (event.building === 'market') {
            characterId = 'kuromi';
            itemEmoji = '🌽';
        } else if (event.building === 'oven') {
            characterId = 'pompompurin';
            itemEmoji = '🌽';
        } else if (event.building === 'delivery') {
            characterId = 'mymelody';
            itemEmoji = '🍿';
        }
        
        if (!characterId) {
            console.error('❌ 無法決定角色:', event.building);
            return;
        }
        
        console.log(`📦 觸發運送: ${characterId} 運送 ${itemEmoji} 從 ${event.from} 到 ${event.building}`);
        
        // 創建運送任務
        this.characterManager.createDeliveryTask(
            characterId,
            fromBuilding,
            toBuilding,
            { emoji: itemEmoji, type: event.item },
            (item) => {
                // 運送完成回調
                console.log(`✅ 運送完成: ${characterId} 送達 ${item.emoji}`);
                this.onDeliveryComplete(event.building, item);
            }
        );
    }
    
    onDeliveryComplete(buildingId, item) {
        const building = this.buildingManager.buildings[buildingId];
        const buildingElement = document.getElementById(this.getBuildingElementId(buildingId));
        
        // 消耗資源
        let result;
        if (item.type === 'corn') {
            result = this.resourceManager.useCorn();
        } else if (item.type === 'popcorn') {
            result = this.resourceManager.usePopcorn();
        }
        
        // 處理建築的運送完成邏輯
        if (building.onDeliveryComplete) {
            const event = building.onDeliveryComplete(result, this.resourceManager);
            if (event) {
                this.handleBuildingEvent({ building: buildingId, ...event });
            }
        }
    }
    
    getBuildingElementId(buildingKey) {
        const ids = {
            cornField: 'corn-field',
            market: 'market',
            oven: 'oven',
            delivery: 'delivery'
        };
        return ids[buildingKey] || buildingKey;
    }
    
    // 訂單系統
    updateOrderSystem(deltaTime) {
        // 檢查外送站是否解鎖
        if (!this.buildingManager.buildings.delivery.unlocked) return;
        
        this.orderTimer += deltaTime;
        
        // 生成新訂單
        if (!this.currentOrder && this.orderTimer >= this.orderInterval) {
            this.generateOrder();
            this.orderTimer = 0;
        }
        
        // 更新訂單倒數
        if (this.currentOrder) {
            this.currentOrder.timeLeft -= deltaTime;
            
            if (this.currentOrder.timeLeft <= 0) {
                // 訂單超時
                this.audioManager.playFailure();
                this.uiManager.showNotification('訂單超時！', '⏰');
                this.currentOrder = null;
            }
        }
    }
    
    generateOrder() {
        const orders = [
            { amount: 3, reward: 30, timeLimit: 90 },
            { amount: 5, reward: 60, timeLimit: 90 },
            { amount: 10, reward: 150, timeLimit: 120 }
        ];
        
        const order = orders[Math.floor(Math.random() * orders.length)];
        this.currentOrder = {
            ...order,
            timeLeft: order.timeLimit,
            completed: 0
        };
        
        this.audioManager.playSuccess();
        this.uiManager.showOrderNotification(this.currentOrder);
    }
    
    checkOrder() {
        if (!this.currentOrder) return;
        
        this.currentOrder.completed++;
        
        if (this.currentOrder.completed >= this.currentOrder.amount) {
            // 訂單完成
            this.resourceManager.addGold(this.currentOrder.reward);
            this.audioManager.playSuccess();
            this.uiManager.showNotification(`訂單完成！獲得 ${this.currentOrder.reward} 金幣`, '🎉');
            
            // 動畫效果
            const delivery = document.getElementById('delivery');
            this.animationManager.glowBuilding(delivery, 2000);
            
            this.currentOrder = null;
        }
    }
    
    // 儲存遊戲
    save() {
        this.resourceManager.save();
        this.buildingManager.save();
        
        const gameData = {
            orderTimer: this.orderTimer,
            currentOrder: this.currentOrder
        };
        localStorage.setItem('popcornKingdom_game', JSON.stringify(gameData));
        
        console.log('💾 遊戲已儲存');
    }
    
    // 載入遊戲
    load() {
        const loaded1 = this.resourceManager.load();
        const loaded2 = this.buildingManager.load();
        
        const gameData = localStorage.getItem('popcornKingdom_game');
        if (gameData) {
            const data = JSON.parse(gameData);
            this.orderTimer = data.orderTimer || 0;
            this.currentOrder = data.currentOrder || null;
        }
        
        if (loaded1 || loaded2) {
            console.log('📂 進度已載入');
            this.uiManager.showNotification('歡迎回來！', '👋');
        } else {
            console.log('🆕 開始新遊戲');
            this.uiManager.showNotification('歡迎來到爆米花王國！', '🏰');
        }
    }
    
    // 重置遊戲
    reset() {
        this.resourceManager.reset();
        this.buildingManager.reset();
        this.characterManager.reset();
        this.currentOrder = null;
        this.orderTimer = 0;
        
        localStorage.removeItem('popcornKingdom_resources');
        localStorage.removeItem('popcornKingdom_buildings');
        localStorage.removeItem('popcornKingdom_game');
        
        console.log('🔄 遊戲已重置');
    }
}

// 當頁面載入完成後啟動遊戲
window.addEventListener('DOMContentLoaded', () => {
    window.game = new PopcornKingdomGame();
});

// 定期自動儲存（每30秒）
setInterval(() => {
    if (window.game) {
        window.game.save();
    }
}, 30000);

// 頁面關閉前儲存
window.addEventListener('beforeunload', () => {
    if (window.game) {
        window.game.save();
    }
});

