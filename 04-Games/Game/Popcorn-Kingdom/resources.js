// 🎮 資源管理系統

class ResourceManager {
    constructor() {
        this.resources = {
            gold: 100,           // 金幣
            corn: 0,             // 玉米數量
            cornMax: 10,         // 玉米最大儲存
            popcorn: 0,          // 爆米花數量
            popcornMax: 10,      // 爆米花最大儲存
            satisfaction: 100    // 客戶滿意度 (0-100)
        };
        
        // 品質機率
        this.cornQuality = {
            good: 0.70,    // 好玉米機率
            bad: 0.30      // 壞玉米機率
        };
        
        // 收益加成
        this.bonuses = {
            satisfactionMultiplier: 1.0,  // 滿意度影響價格
            qualityBonus: 0,               // 品質提升
            incomeBonus: 0                 // 收益加成
        };
        
        // 被動收入
        this.passiveIncome = 0;  // 每秒金幣
    }
    
    // 增加金幣
    addGold(amount) {
        const bonus = 1 + this.bonuses.incomeBonus;
        const finalAmount = Math.floor(amount * bonus);
        this.resources.gold += finalAmount;
        this.updateUI();
        return finalAmount;
    }
    
    // 扣除金幣
    spendGold(amount) {
        if (this.resources.gold >= amount) {
            this.resources.gold -= amount;
            this.updateUI();
            return true;
        }
        return false;
    }
    
    // 增加玉米
    addCorn(isGood = true) {
        if (this.resources.corn < this.resources.cornMax) {
            this.resources.corn++;
            this.updateUI();
            return { success: true, isGood };
        }
        return { success: false, isGood };
    }
    
    // 消耗玉米
    useCorn() {
        if (this.resources.corn > 0) {
            this.resources.corn--;
            this.updateUI();
            
            // 根據品質機率決定是好玉米還是壞玉米
            const quality = this.cornQuality.good + this.bonuses.qualityBonus;
            const isGood = Math.random() < quality;
            return { success: true, isGood };
        }
        return { success: false, isGood: false };
    }
    
    // 增加爆米花
    addPopcorn() {
        if (this.resources.popcorn < this.resources.popcornMax) {
            this.resources.popcorn++;
            this.updateUI();
            return true;
        }
        return false;
    }
    
    // 消耗爆米花
    usePopcorn() {
        if (this.resources.popcorn > 0) {
            this.resources.popcorn--;
            this.updateUI();
            return true;
        }
        return false;
    }
    
    // 調整滿意度
    adjustSatisfaction(amount) {
        this.resources.satisfaction = Math.max(0, Math.min(100, this.resources.satisfaction + amount));
        
        // 根據滿意度調整價格倍數
        if (this.resources.satisfaction >= 80) {
            this.bonuses.satisfactionMultiplier = 1.0;
        } else if (this.resources.satisfaction >= 50) {
            this.bonuses.satisfactionMultiplier = 0.8;
        } else {
            this.bonuses.satisfactionMultiplier = 0.5;
        }
        
        this.updateUI();
    }
    
    // 升級玉米儲存上限
    upgradeCornStorage(amount) {
        this.resources.cornMax += amount;
        this.updateUI();
    }
    
    // 升級爆米花儲存上限
    upgradePopcornStorage(amount) {
        this.resources.popcornMax += amount;
        this.updateUI();
    }
    
    // 增加品質加成
    addQualityBonus(amount) {
        this.bonuses.qualityBonus += amount;
        this.cornQuality.good = Math.min(0.95, 0.70 + this.bonuses.qualityBonus);
        this.cornQuality.bad = 1 - this.cornQuality.good;
    }
    
    // 增加收益加成
    addIncomeBonus(amount) {
        this.bonuses.incomeBonus += amount;
    }
    
    // 增加被動收入
    addPassiveIncome(amount) {
        this.passiveIncome += amount;
    }
    
    // 每秒更新（被動收入）
    update(deltaTime) {
        if (this.passiveIncome > 0) {
            this.addGold(this.passiveIncome * deltaTime);
        }
        
        // 滿意度自然恢復（每秒+0.1%）
        if (this.resources.satisfaction < 100) {
            this.adjustSatisfaction(0.1 * deltaTime);
        }
    }
    
    // 更新UI
    updateUI() {
        document.getElementById('gold-value').textContent = Math.floor(this.resources.gold);
        document.getElementById('corn-value').textContent = this.resources.corn;
        document.getElementById('corn-max').textContent = `/${this.resources.cornMax}`;
        document.getElementById('popcorn-value').textContent = this.resources.popcorn;
        document.getElementById('popcorn-max').textContent = `/${this.resources.popcornMax}`;
        document.getElementById('satisfaction-value').textContent = Math.floor(this.resources.satisfaction);
        
        // 更新滿意度圖示
        const satIcon = document.querySelector('#resource-bar .resource-item:nth-child(4) .resource-icon');
        if (this.resources.satisfaction >= 80) {
            satIcon.textContent = '😊';
        } else if (this.resources.satisfaction >= 50) {
            satIcon.textContent = '😐';
        } else {
            satIcon.textContent = '😠';
        }
    }
    
    // 儲存進度
    save() {
        const saveData = {
            resources: this.resources,
            bonuses: this.bonuses,
            passiveIncome: this.passiveIncome,
            cornQuality: this.cornQuality
        };
        localStorage.setItem('popcornKingdom_resources', JSON.stringify(saveData));
    }
    
    // 載入進度
    load() {
        const saveData = localStorage.getItem('popcornKingdom_resources');
        if (saveData) {
            const data = JSON.parse(saveData);
            this.resources = data.resources;
            this.bonuses = data.bonuses;
            this.passiveIncome = data.passiveIncome;
            this.cornQuality = data.cornQuality;
            this.updateUI();
            return true;
        }
        return false;
    }
    
    // 重置
    reset() {
        this.resources = {
            gold: 100,
            corn: 0,
            cornMax: 10,
            popcorn: 0,
            popcornMax: 10,
            satisfaction: 100
        };
        this.cornQuality = {
            good: 0.70,
            bad: 0.30
        };
        this.bonuses = {
            satisfactionMultiplier: 1.0,
            qualityBonus: 0,
            incomeBonus: 0
        };
        this.passiveIncome = 0;
        this.updateUI();
    }
}

