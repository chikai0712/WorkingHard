// 🎭 三麗鷗角色系統

class Character {
    constructor(id, name, emoji, speed = 100) {
        this.id = id;
        this.name = name;
        this.emoji = emoji;
        this.speed = speed;  // 移動速度（像素/秒）
        
        // 位置和狀態
        this.x = 0;
        this.y = 0;
        this.targetX = 0;
        this.targetY = 0;
        this.state = 'idle';  // idle, walking, working
        this.direction = 'right';  // left, right
        
        // 任務
        this.currentTask = null;
        this.carryingItem = null;
        
        // DOM 元素
        this.element = null;
        this.createDOM();
    }
    
    createDOM() {
        this.element = document.createElement('div');
        this.element.className = 'character';
        this.element.innerHTML = `
            <div class="character-emoji">${this.emoji}</div>
            <div class="character-name">${this.name}</div>
            <div class="character-item"></div>
        `;
        this.element.style.cssText = `
            position: absolute;
            left: ${this.x}px;
            top: ${this.y}px;
            transition: transform 0.3s ease;
        `;
        document.getElementById('game-area').appendChild(this.element);
    }
    
    // 設定任務
    assignTask(task) {
        if (this.state !== 'idle') return false;
        
        this.currentTask = task;
        this.state = 'walking';
        return true;
    }
    
    // 移動到目標位置
    moveTo(x, y) {
        this.targetX = x;
        this.targetY = y;
        this.state = 'walking';
        
        // 設定方向
        if (x > this.x) {
            this.direction = 'right';
            this.element.style.transform = 'scaleX(1)';
        } else if (x < this.x) {
            this.direction = 'left';
            this.element.style.transform = 'scaleX(-1)';
        }
    }
    
    // 拾取物品
    pickupItem(item) {
        this.carryingItem = item;
        const itemElement = this.element.querySelector('.character-item');
        itemElement.textContent = item.emoji;
        itemElement.style.display = 'block';
    }
    
    // 放下物品
    dropItem() {
        const item = this.carryingItem;
        this.carryingItem = null;
        const itemElement = this.element.querySelector('.character-item');
        itemElement.textContent = '';
        itemElement.style.display = 'none';
        return item;
    }
    
    // 更新角色狀態
    update(deltaTime) {
        if (this.state === 'walking') {
            const dx = this.targetX - this.x;
            const dy = this.targetY - this.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance < 5) {
                // 到達目標
                this.x = this.targetX;
                this.y = this.targetY;
                this.state = 'idle';
                
                // 執行任務
                if (this.currentTask) {
                    this.executeTask();
                }
            } else {
                // 繼續移動
                const moveDistance = this.speed * deltaTime;
                const ratio = Math.min(moveDistance / distance, 1);
                this.x += dx * ratio;
                this.y += dy * ratio;
            }
            
            // 更新 DOM 位置
            this.element.style.left = this.x + 'px';
            this.element.style.top = this.y + 'px';
            
            // 行走動畫
            this.element.classList.add('walking');
        } else {
            this.element.classList.remove('walking');
        }
    }
    
    // 執行任務
    executeTask() {
        if (!this.currentTask) return;
        
        const task = this.currentTask;
        
        switch (task.action) {
            case 'pickup':
                // 拾取物品
                this.pickupItem(task.item);
                // 前往目的地
                this.moveTo(task.destination.x, task.destination.y);
                task.action = 'deliver';
                break;
                
            case 'deliver':
                // 送達物品
                const item = this.dropItem();
                if (task.onComplete) {
                    task.onComplete(item);
                }
                this.currentTask = null;
                // 返回待機位置
                this.moveTo(task.homeX, task.homeY);
                break;
        }
    }
}

// 角色管理器
class CharacterManager {
    constructor() {
        this.characters = {};
        this.taskQueue = [];
        
        // 創建三麗鷗角色
        this.createCharacters();
    }
    
    createCharacters() {
        // 大耳狗 - 負責玉米田
        this.characters.cinnamoroll = new Character(
            'cinnamoroll',
            '大耳狗',
            '🐶',
            150
        );
        
        // 庫洛米 - 負責市場
        this.characters.kuromi = new Character(
            'kuromi',
            '庫洛米',
            '😈',
            120
        );
        
        // 布丁狗 - 負責烤爐
        this.characters.pompompurin = new Character(
            'pompompurin',
            '布丁狗',
            '🐶',
            130
        );
        
        // 美樂蒂 - 負責外送
        this.characters.mymelody = new Character(
            'mymelody',
            '美樂蒂',
            '🐰',
            140
        );
        
        // 設定初始位置
        this.positionCharacters();
    }
    
    positionCharacters() {
        // 使用固定位置來設定角色初始位置
        // 這樣更可靠，不依賴建築的實際位置
        
        // 大耳狗在左上（玉米田旁）
        this.characters.cinnamoroll.x = 150;
        this.characters.cinnamoroll.y = 200;
        this.characters.cinnamoroll.element.style.left = this.characters.cinnamoroll.x + 'px';
        this.characters.cinnamoroll.element.style.top = this.characters.cinnamoroll.y + 'px';
        
        // 庫洛米在右上（市場旁）
        this.characters.kuromi.x = 450;
        this.characters.kuromi.y = 200;
        this.characters.kuromi.element.style.left = this.characters.kuromi.x + 'px';
        this.characters.kuromi.element.style.top = this.characters.kuromi.y + 'px';
        
        // 布丁狗在左下（烤爐旁）
        this.characters.pompompurin.x = 150;
        this.characters.pompompurin.y = 400;
        this.characters.pompompurin.element.style.left = this.characters.pompompurin.x + 'px';
        this.characters.pompompurin.element.style.top = this.characters.pompompurin.y + 'px';
        
        // 美樂蒂在右下（外送站旁）
        this.characters.mymelody.x = 450;
        this.characters.mymelody.y = 400;
        this.characters.mymelody.element.style.left = this.characters.mymelody.x + 'px';
        this.characters.mymelody.element.style.top = this.characters.mymelody.y + 'px';
        
        console.log('✅ 角色位置已設定');
    }
    
    // 創建運送任務
    createDeliveryTask(characterId, fromBuilding, toBuilding, item, onComplete) {
        const character = this.characters[characterId];
        if (!character || character.state !== 'idle') {
            // 角色忙碌，加入隊列
            this.taskQueue.push({ characterId, fromBuilding, toBuilding, item, onComplete });
            return false;
        }
        
        const fromRect = fromBuilding.getBoundingClientRect();
        const toRect = toBuilding.getBoundingClientRect();
        const gameArea = document.getElementById('game-area').getBoundingClientRect();
        
        const task = {
            action: 'pickup',
            item: item,
            source: {
                x: fromRect.left - gameArea.left + fromRect.width / 2,
                y: fromRect.top - gameArea.top + fromRect.height / 2
            },
            destination: {
                x: toRect.left - gameArea.left + toRect.width / 2,
                y: toRect.top - gameArea.top + toRect.height / 2
            },
            homeX: character.x,
            homeY: character.y,
            onComplete: onComplete
        };
        
        // 先移動到取貨點
        character.moveTo(task.source.x, task.source.y);
        character.assignTask(task);
        
        return true;
    }
    
    // 更新所有角色
    update(deltaTime) {
        for (const key in this.characters) {
            this.characters[key].update(deltaTime);
        }
        
        // 處理任務隊列
        if (this.taskQueue.length > 0) {
            const task = this.taskQueue[0];
            const character = this.characters[task.characterId];
            
            if (character && character.state === 'idle') {
                this.taskQueue.shift();
                this.createDeliveryTask(
                    task.characterId,
                    task.fromBuilding,
                    task.toBuilding,
                    task.item,
                    task.onComplete
                );
            }
        }
    }
    
    // 重置角色位置
    reset() {
        this.positionCharacters();
        this.taskQueue = [];
    }
}

