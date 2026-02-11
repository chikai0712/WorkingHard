// 🎨 UI 控制系統

class UIManager {
    constructor(game) {
        this.game = game;
        this.currentModal = null;
        this.currentSlot = null;
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // 建築點擊事件
        document.querySelectorAll('.building[data-building]').forEach(element => {
            element.addEventListener('click', (e) => {
                const buildingId = element.dataset.building;
                this.handleBuildingClick(buildingId);
            });
        });
        
        // 建設槽位點擊事件
        document.querySelectorAll('.construction-slot').forEach(element => {
            element.addEventListener('click', (e) => {
                const slotIndex = parseInt(element.dataset.slot);
                this.handleSlotClick(slotIndex);
            });
        });
        
        // 控制按鈕
        document.getElementById('save-btn').addEventListener('click', () => {
            this.game.save();
            this.showNotification('遊戲已儲存！', '💾');
        });
        
        document.getElementById('reset-btn').addEventListener('click', () => {
            if (confirm('確定要重置遊戲嗎？所有進度將會消失！')) {
                this.game.reset();
                this.showNotification('遊戲已重置！', '🔄');
            }
        });
        
        document.getElementById('sound-btn').addEventListener('click', () => {
            this.game.audioManager.toggleMute();
            const btn = document.getElementById('sound-btn');
            btn.textContent = this.game.audioManager.muted ? '🔇 音效' : '🔊 音效';
        });
        
        // 升級彈窗
        document.getElementById('modal-close').addEventListener('click', () => {
            this.closeModal('upgrade-modal');
        });
        
        document.getElementById('upgrade-btn').addEventListener('click', () => {
            this.handleUpgrade();
        });
        
        // 建設彈窗
        document.getElementById('build-modal-close').addEventListener('click', () => {
            this.closeModal('build-modal');
        });
        
        document.querySelectorAll('.build-option').forEach(element => {
            element.addEventListener('click', (e) => {
                const buildType = element.dataset.build;
                this.handleBuild(buildType);
            });
        });
        
        // 點擊彈窗外部關閉
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal(modal.id);
                }
            });
        });
    }
    
    // 處理建築點擊
    handleBuildingClick(buildingId) {
        const building = this.game.buildingManager.buildings[buildingId];
        
        if (!building.unlocked) {
            // 顯示解鎖彈窗
            this.showUnlockModal(buildingId, building);
        } else {
            // 顯示升級彈窗
            this.showUpgradeModal(buildingId, building);
        }
    }
    
    // 顯示解鎖彈窗
    showUnlockModal(buildingId, building) {
        const modal = document.getElementById('upgrade-modal');
        
        document.getElementById('modal-title').textContent = building.name;
        document.getElementById('modal-icon').textContent = building.icon;
        
        // 隱藏當前等級資訊
        document.querySelector('.modal-info').style.display = 'none';
        
        // 顯示解鎖資訊
        const upgradeSection = document.querySelector('.modal-upgrade');
        upgradeSection.querySelector('h3').textContent = '解鎖建築';
        document.getElementById('modal-cost').textContent = building.unlockCost;
        document.getElementById('modal-next-effect').textContent = `${building.speeds[0]}秒/個`;
        
        const upgradeBtn = document.getElementById('upgrade-btn');
        upgradeBtn.textContent = '🔓 解鎖';
        upgradeBtn.disabled = this.game.resourceManager.resources.gold < building.unlockCost;
        upgradeBtn.dataset.action = 'unlock';
        upgradeBtn.dataset.building = buildingId;
        
        this.openModal('upgrade-modal');
    }
    
    // 顯示升級彈窗
    showUpgradeModal(buildingId, building) {
        const modal = document.getElementById('upgrade-modal');
        
        document.getElementById('modal-title').textContent = building.name;
        document.getElementById('modal-icon').textContent = building.icon;
        
        // 顯示當前等級資訊
        const infoSection = document.querySelector('.modal-info');
        infoSection.style.display = 'block';
        document.getElementById('modal-current-level').textContent = building.level;
        document.getElementById('modal-current-effect').textContent = `${building.getSpeed()}秒/個`;
        
        // 顯示升級資訊
        const upgradeSection = document.querySelector('.modal-upgrade');
        const upgradeBtn = document.getElementById('upgrade-btn');
        
        if (building.canUpgrade()) {
            upgradeSection.style.display = 'block';
            upgradeSection.querySelector('h3').textContent = `升級到 Lv.${building.level + 1}`;
            document.getElementById('modal-cost').textContent = building.getUpgradeCost();
            document.getElementById('modal-next-effect').textContent = `${building.getNextSpeed()}秒/個`;
            
            upgradeBtn.textContent = '⬆️ 升級';
            upgradeBtn.disabled = this.game.resourceManager.resources.gold < building.getUpgradeCost();
            upgradeBtn.dataset.action = 'upgrade';
            upgradeBtn.dataset.building = buildingId;
        } else {
            upgradeSection.style.display = 'none';
        }
        
        this.openModal('upgrade-modal');
    }
    
    // 處理升級/解鎖
    handleUpgrade() {
        const btn = document.getElementById('upgrade-btn');
        const action = btn.dataset.action;
        const buildingId = btn.dataset.building;
        
        let success = false;
        
        if (action === 'unlock') {
            success = this.game.buildingManager.unlockBuilding(buildingId);
            if (success) {
                this.game.audioManager.playSound('unlock');
                this.showNotification('建築已解鎖！', '🔓');
            }
        } else if (action === 'upgrade') {
            success = this.game.buildingManager.upgradeBuilding(buildingId);
            if (success) {
                this.game.audioManager.playSound('upgrade');
                this.showNotification('升級成功！', '⬆️');
            }
        }
        
        if (success) {
            this.closeModal('upgrade-modal');
            this.game.buildingManager.updateUI();
        } else {
            this.showNotification('金幣不足！', '❌');
            this.game.audioManager.playSound('error');
        }
    }
    
    // 處理槽位點擊
    handleSlotClick(slotIndex) {
        const slot = this.game.buildingManager.constructionSlots[slotIndex];
        
        if (slot === null) {
            // 空槽位，顯示建設選單
            this.currentSlot = slotIndex;
            this.openModal('build-modal');
        } else {
            // 已建設，顯示資訊
            this.showNotification(`${slot.name}：${this.getConstructionEffect(slot)}`, slot.icon);
        }
    }
    
    // 獲取建設效果描述
    getConstructionEffect(construction) {
        if (construction.income) {
            return `每秒 +${construction.income} 金幣`;
        } else if (construction.effect === 'satisfaction') {
            return `滿意度 +${construction.value}%`;
        } else if (construction.effect === 'quality') {
            return `品質 +${construction.value * 100}%`;
        } else if (construction.effect === 'income') {
            return `收益 +${construction.value * 100}%`;
        }
        return '';
    }
    
    // 處理建設
    handleBuild(buildType) {
        const construction = this.game.buildingManager.constructionTypes[buildType];
        
        if (this.game.resourceManager.resources.gold < construction.cost) {
            this.showNotification('金幣不足！', '❌');
            this.game.audioManager.playSound('error');
            return;
        }
        
        const success = this.game.buildingManager.buildConstruction(this.currentSlot, buildType);
        
        if (success) {
            this.game.audioManager.playSound('build');
            this.showNotification(`${construction.name} 建造完成！`, construction.icon);
            this.closeModal('build-modal');
            this.game.buildingManager.updateUI();
        }
    }
    
    // 打開彈窗
    openModal(modalId) {
        const modal = document.getElementById(modalId);
        modal.classList.remove('hidden');
        this.currentModal = modalId;
    }
    
    // 關閉彈窗
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        modal.classList.add('hidden');
        this.currentModal = null;
    }
    
    // 顯示通知
    showNotification(text, icon = '📢') {
        // 創建通知元素
        const notification = document.createElement('div');
        notification.className = 'floating-notification';
        notification.innerHTML = `
            <span style="font-size: 24px; margin-right: 10px;">${icon}</span>
            <span style="font-size: 16px; font-weight: bold;">${text}</span>
        `;
        
        // 樣式
        notification.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            background: white;
            padding: 15px 25px;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            z-index: 9999;
            display: flex;
            align-items: center;
            animation: slideInRight 0.3s ease, fadeOut 0.3s ease 2.7s;
        `;
        
        document.body.appendChild(notification);
        
        // 3秒後移除
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
    
    // 顯示訂單通知
    showOrderNotification(order) {
        const notification = document.getElementById('order-notification');
        document.getElementById('order-text').textContent = `需要 ${order.amount} 個爆米花`;
        document.getElementById('order-reward').textContent = `獎勵：💰 ${order.reward}`;
        
        notification.classList.remove('hidden');
        
        // 更新倒數計時
        let timeLeft = order.timeLimit;
        const timerElement = document.getElementById('order-timer');
        
        const countdown = setInterval(() => {
            timeLeft--;
            timerElement.textContent = `${timeLeft}s`;
            
            if (timeLeft <= 0 || !this.game.currentOrder) {
                clearInterval(countdown);
                notification.classList.add('hidden');
            }
        }, 1000);
    }
    
    // 更新進度條
    updateProgress() {
        for (const key in this.game.buildingManager.buildings) {
            const building = this.game.buildingManager.buildings[key];
            if (building.unlocked) {
                const progressElement = document.getElementById(`${this.getBuildingPrefix(key)}-progress`);
                if (progressElement) {
                    progressElement.style.width = building.progress + '%';
                }
            }
        }
    }
    
    getBuildingPrefix(buildingId) {
        const prefixes = {
            cornField: 'cornfield',
            market: 'market',
            oven: 'oven',
            delivery: 'delivery'
        };
        return prefixes[buildingId] || buildingId;
    }
}

