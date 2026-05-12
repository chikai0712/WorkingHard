// 🏗️ 建築系統

class Building {
    constructor(id, name, icon, type) {
        this.id = id;
        this.name = name;
        this.icon = icon;
        this.type = type;  // 'production', 'processing', 'selling', 'delivery'
        this.level = 1;
        this.unlocked = false;
        this.working = false;
        this.progress = 0;
        this.timer = 0;
    }
    
    getSpeed() {
        // 返回當前等級的速度（秒）
        return this.speeds[this.level - 1];
    }
    
    getUpgradeCost() {
        // 返回升級到下一等級的成本
        return this.upgradeCosts[this.level - 1] || null;
    }
    
    getNextSpeed() {
        // 返回下一等級的速度
        return this.speeds[this.level] || null;
    }
    
    canUpgrade() {
        return this.level < this.maxLevel;
    }
    
    upgrade() {
        if (this.canUpgrade()) {
            this.level++;
            return true;
        }
        return false;
    }
}

// 玉米田
class CornField extends Building {
    constructor() {
        super('cornField', '玉米田', '🌾', 'production');
        this.maxLevel = 4;
        this.speeds = [5, 3, 2, 1];  // 秒/個
        this.upgradeCosts = [50, 150, 500];
        this.storageBonus = [10, 10, 10];  // 每次升級增加的儲存
        this.unlocked = true;
    }
    
    work(deltaTime, resourceManager) {
        if (!this.unlocked) return;
        
        this.timer += deltaTime;
        const speed = this.getSpeed();
        this.progress = (this.timer / speed) * 100;
        
        if (this.timer >= speed) {
            this.timer = 0;
            this.progress = 0;
            
            // 生產玉米
            const result = resourceManager.addCorn();
            if (result.success) {
                return { type: 'produce', item: 'corn', isGood: result.isGood };
            }
        }
        return null;
    }
}

// 市場
class Market extends Building {
    constructor() {
        super('market', '市場', '🏪', 'selling');
        this.maxLevel = 4;
        this.speeds = [3, 2, 1, 0.5];  // 秒/個
        this.upgradeCosts = [100, 300, 1000];
        this.unlocked = true;
    }
    
    work(deltaTime, resourceManager) {
        if (!this.unlocked) return;
        if (resourceManager.resources.corn === 0) {
            this.timer = 0;
            this.progress = 0;
            return null;
        }
        
        this.timer += deltaTime;
        const speed = this.getSpeed();
        this.progress = (this.timer / speed) * 100;
        
        if (this.timer >= speed) {
            this.timer = 0;
            this.progress = 0;
            
            // 需要角色運送
            return { type: 'needDelivery', from: 'cornField', to: 'market', item: 'corn' };
        }
        return null;
    }
    
    // 處理運送完成
    onDeliveryComplete(result, resourceManager) {
        if (result.success) {
            if (result.isGood) {
                // 好玉米
                const basePrice = 10;
                const finalPrice = Math.floor(basePrice * resourceManager.bonuses.satisfactionMultiplier);
                resourceManager.addGold(finalPrice);
                resourceManager.adjustSatisfaction(1);
                return { type: 'sell', item: 'corn', isGood: true, price: finalPrice };
            } else {
                // 壞玉米
                resourceManager.addGold(-5);
                resourceManager.adjustSatisfaction(-10);
                return { type: 'sell', item: 'corn', isGood: false, price: -5 };
            }
        }
        return null;
    }
}

// 烤爐
class Oven extends Building {
    constructor() {
        super('oven', '烤爐', '🔥', 'processing');
        this.maxLevel = 4;
        this.speeds = [5, 3, 2, 1];  // 秒/個
        this.upgradeCosts = [200, 500, 1500];
        this.unlockCost = 100;
        this.unlocked = false;
    }
    
    work(deltaTime, resourceManager) {
        if (!this.unlocked) return;
        if (resourceManager.resources.corn === 0) {
            this.timer = 0;
            this.progress = 0;
            return null;
        }
        if (resourceManager.resources.popcorn >= resourceManager.resources.popcornMax) {
            this.timer = 0;
            this.progress = 0;
            return null;
        }
        
        this.timer += deltaTime;
        const speed = this.getSpeed();
        this.progress = (this.timer / speed) * 100;
        
        if (this.timer >= speed) {
            this.timer = 0;
            this.progress = 0;
            
            // 需要角色運送
            return { type: 'needDelivery', from: 'cornField', to: 'oven', item: 'corn' };
        }
        return null;
    }
    
    // 處理運送完成
    onDeliveryComplete(result, resourceManager) {
        if (result.success) {
            if (result.isGood) {
                // 好玉米 → 爆米花
                resourceManager.addPopcorn();
                return { type: 'cook', item: 'popcorn', success: true };
            } else {
                // 壞玉米 → 燒焦
                return { type: 'cook', item: 'popcorn', success: false };
            }
        }
        return null;
    }
}

// 外送站
class Delivery extends Building {
    constructor() {
        super('delivery', '外送站', '🚚', 'delivery');
        this.maxLevel = 4;
        this.speeds = [3, 2, 1, 0.5];  // 秒/個
        this.upgradeCosts = [400, 1000, 3000];
        this.unlockCost = 200;
        this.unlocked = false;
        this.incomeBonus = [0, 0, 0, 0.5];  // Lv4 收益+50%
    }
    
    work(deltaTime, resourceManager) {
        if (!this.unlocked) return;
        if (resourceManager.resources.popcorn === 0) {
            this.timer = 0;
            this.progress = 0;
            return null;
        }
        
        this.timer += deltaTime;
        const speed = this.getSpeed();
        this.progress = (this.timer / speed) * 100;
        
        if (this.timer >= speed) {
            this.timer = 0;
            this.progress = 0;
            
            // 需要角色運送
            return { type: 'needDelivery', from: 'oven', to: 'delivery', item: 'popcorn' };
        }
        return null;
    }
    
    // 處理運送完成
    onDeliveryComplete(result, resourceManager) {
        if (result.success) {
            const basePrice = 50;
            const bonus = 1 + this.incomeBonus[this.level - 1];
            const finalPrice = Math.floor(basePrice * bonus);
            resourceManager.addGold(finalPrice);
            return { type: 'deliver', item: 'popcorn', price: finalPrice };
        }
        return null;
    }
}

// 建築管理器
class BuildingManager {
    constructor(resourceManager) {
        this.resourceManager = resourceManager;
        this.buildings = {
            cornField: new CornField(),
            market: new Market(),
            oven: new Oven(),
            delivery: new Delivery()
        };
        
        // 建設槽位
        this.constructionSlots = [null, null, null, null, null];
        
        // 建設類型定義
        this.constructionTypes = {
            house1: { name: '小屋', icon: '🏠', cost: 100, income: 1 },
            house2: { name: '房子', icon: '🏡', cost: 500, income: 5 },
            house3: { name: '豪宅', icon: '🏰', cost: 2000, income: 20 },
            flower1: { name: '小花', icon: '🌸', cost: 50, effect: 'satisfaction', value: 5 },
            flower2: { name: '大花', icon: '🌺', cost: 200, effect: 'satisfaction', value: 10 },
            tree: { name: '大樹', icon: '🌳', cost: 1000, effect: 'quality', value: 0.1 },
            fountain: { name: '噴泉', icon: '⛲', cost: 5000, effect: 'income', value: 0.2 }
        };
        
        // 角色管理器引用（稍後設定）
        this.characterManager = null;
    }
    
    // 設定角色管理器
    setCharacterManager(characterManager) {
        this.characterManager = characterManager;
    }
    
    // 解鎖建築
    unlockBuilding(buildingId) {
        const building = this.buildings[buildingId];
        if (!building || building.unlocked) return false;
        
        if (this.resourceManager.spendGold(building.unlockCost)) {
            building.unlocked = true;
            
            // 烤爐解鎖時增加爆米花儲存
            if (buildingId === 'oven') {
                this.resourceManager.upgradePopcornStorage(10);
            }
            
            return true;
        }
        return false;
    }
    
    // 升級建築
    upgradeBuilding(buildingId) {
        const building = this.buildings[buildingId];
        if (!building || !building.unlocked || !building.canUpgrade()) return false;
        
        const cost = building.getUpgradeCost();
        if (this.resourceManager.spendGold(cost)) {
            building.upgrade();
            
            // 玉米田升級增加儲存
            if (buildingId === 'cornField') {
                this.resourceManager.upgradeCornStorage(10);
            }
            
            return true;
        }
        return false;
    }
    
    // 建造建設
    buildConstruction(slotIndex, constructionType) {
        if (slotIndex < 0 || slotIndex >= this.constructionSlots.length) return false;
        if (this.constructionSlots[slotIndex] !== null) return false;
        
        const construction = this.constructionTypes[constructionType];
        if (!construction) return false;
        
        if (this.resourceManager.spendGold(construction.cost)) {
            this.constructionSlots[slotIndex] = {
                type: constructionType,
                ...construction
            };
            
            // 應用效果
            if (construction.income) {
                this.resourceManager.addPassiveIncome(construction.income);
            } else if (construction.effect === 'satisfaction') {
                this.resourceManager.adjustSatisfaction(construction.value);
            } else if (construction.effect === 'quality') {
                this.resourceManager.addQualityBonus(construction.value);
            } else if (construction.effect === 'income') {
                this.resourceManager.addIncomeBonus(construction.value);
            }
            
            return true;
        }
        return false;
    }
    
    // 更新所有建築
    update(deltaTime) {
        const events = [];
        
        for (const key in this.buildings) {
            const building = this.buildings[key];
            const event = building.work(deltaTime, this.resourceManager);
            if (event) {
                events.push({ building: key, ...event });
            }
        }
        
        return events;
    }
    
    // 更新UI
    updateUI() {
        // 更新玉米田
        this.updateBuildingUI('cornField', 'cornfield');
        
        // 更新市場
        this.updateBuildingUI('market', 'market');
        
        // 更新烤爐
        this.updateBuildingUI('oven', 'oven');
        
        // 更新外送站
        this.updateBuildingUI('delivery', 'delivery');
        
        // 更新建設槽位
        this.updateConstructionUI();
    }
    
    updateBuildingUI(buildingId, elementPrefix) {
        const building = this.buildings[buildingId];
        const element = document.getElementById(elementPrefix);
        
        if (!building.unlocked) {
            element.classList.add('locked');
            element.classList.remove('unlocked');
        } else {
            element.classList.remove('locked');
            element.classList.add('unlocked');
            
            // 更新等級
            document.getElementById(`${elementPrefix}-level`).textContent = building.level;
            
            // 更新速度
            const speedElement = document.getElementById(`${elementPrefix}-speed`);
            if (speedElement) {
                speedElement.textContent = building.getSpeed();
            }
            
            // 更新進度條
            const progressElement = document.getElementById(`${elementPrefix}-progress`);
            if (progressElement) {
                progressElement.style.width = building.progress + '%';
            }
        }
    }
    
    updateConstructionUI() {
        this.constructionSlots.forEach((slot, index) => {
            const element = document.querySelector(`.construction-slot[data-slot="${index}"]`);
            if (slot) {
                element.classList.remove('empty');
                element.classList.add('built');
                element.querySelector('.slot-icon').textContent = slot.icon;
                element.querySelector('.slot-label').textContent = slot.name;
            }
        });
    }
    
    // 儲存進度
    save() {
        const saveData = {
            buildings: {},
            constructionSlots: this.constructionSlots
        };
        
        for (const key in this.buildings) {
            const building = this.buildings[key];
            saveData.buildings[key] = {
                level: building.level,
                unlocked: building.unlocked
            };
        }
        
        localStorage.setItem('popcornKingdom_buildings', JSON.stringify(saveData));
    }
    
    // 載入進度
    load() {
        const saveData = localStorage.getItem('popcornKingdom_buildings');
        if (saveData) {
            const data = JSON.parse(saveData);
            
            for (const key in data.buildings) {
                if (this.buildings[key]) {
                    this.buildings[key].level = data.buildings[key].level;
                    this.buildings[key].unlocked = data.buildings[key].unlocked;
                }
            }
            
            this.constructionSlots = data.constructionSlots;
            
            // 重新計算被動收入和加成
            this.constructionSlots.forEach(slot => {
                if (slot) {
                    const construction = this.constructionTypes[slot.type];
                    if (construction.income) {
                        this.resourceManager.addPassiveIncome(construction.income);
                    } else if (construction.effect === 'quality') {
                        this.resourceManager.addQualityBonus(construction.value);
                    } else if (construction.effect === 'income') {
                        this.resourceManager.addIncomeBonus(construction.value);
                    }
                }
            });
            
            this.updateUI();
            return true;
        }
        return false;
    }
    
    // 重置
    reset() {
        this.buildings = {
            cornField: new CornField(),
            market: new Market(),
            oven: new Oven(),
            delivery: new Delivery()
        };
        this.constructionSlots = [null, null, null, null, null];
        this.updateUI();
    }
}

