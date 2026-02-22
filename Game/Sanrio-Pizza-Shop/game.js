// 🍕 三麗鷗披薩店 - 遊戲主程式

class SanrioPizzaShop {
    constructor() {
        this.money = 0;
        this.reputation = 100;
        this.day = 1;
        this.currentCustomer = null;
        this.currentPizza = {
            toppings: [],
            cooked: false
        };
        this.customers = [];
        this.activeCharacter = 'cinnamoroll';
        this.unlockedCharacters = ['cinnamoroll', 'kuromi'];
        
        // 每日統計
        this.dailyIncome = 0;
        this.dailyCustomers = 0;
        this.dailyReputationChange = 0;
        
        // 遊戲設定
        this.maxCustomers = 5;
        this.customerSpawnInterval = 8000; // 8秒
        this.dayDuration = 120000; // 2分鐘
        
        // 角色走動
        this.characterPosition = 0;
        this.characterDirection = 1;
        this.walkingCharacter = null;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.spawnCustomer();
        this.startCustomerSpawner();
        this.startDayTimer();
        this.startCharacterWalking();
        this.updateUI();
    }
    
    setupEventListeners() {
        // 配料按鈕
        document.querySelectorAll('.topping-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                if (!this.currentCustomer) {
                    this.showMessage('請先選擇一位客人！');
                    return;
                }
                const topping = btn.dataset.topping;
                this.addTopping(topping);
            });
        });
        
        // 烤披薩
        document.getElementById('cook-btn').addEventListener('click', () => {
            this.cookPizza();
        });
        
        // 上菜
        document.getElementById('serve-btn').addEventListener('click', () => {
            this.servePizza();
        });
        
        // 重做
        document.getElementById('trash-btn').addEventListener('click', () => {
            this.resetPizza();
        });
        
        // 繼續按鈕
        document.getElementById('continue-btn').addEventListener('click', () => {
            document.getElementById('result-modal').classList.add('hidden');
        });
        
        // 下一天
        document.getElementById('next-day-btn').addEventListener('click', () => {
            this.startNextDay();
        });
        
        // 角色選擇
        document.querySelectorAll('.character').forEach(char => {
            char.addEventListener('click', () => {
                const character = char.dataset.character;
                if (char.classList.contains('locked')) {
                    this.tryUnlockCharacter(character);
                } else {
                    this.selectCharacter(character);
                }
            });
        });
    }
    
    // 客人系統
    spawnCustomer() {
        if (this.customers.length >= this.maxCustomers) return;
        
        const customerTypes = [
            { name: 'Hello Kitty', avatar: '🐱', patience: 45, order: this.generateOrder(2) },
            { name: 'Keroppi', avatar: '🐸', patience: 40, order: this.generateOrder(3) },
            { name: 'Bad Badtz-Maru', avatar: '🐧', patience: 35, order: this.generateOrder(2) },
            { name: 'Little Twin Stars', avatar: '⭐', patience: 50, order: this.generateOrder(4) },
            { name: 'Pochacco', avatar: '🐕', patience: 40, order: this.generateOrder(3) }
        ];
        
        const type = customerTypes[Math.floor(Math.random() * customerTypes.length)];
        const customer = {
            id: Date.now(),
            ...type,
            maxPatience: type.patience,
            startTime: Date.now()
        };
        
        this.customers.push(customer);
        this.renderCustomers();
        this.startPatienceTimer(customer);
    }
    
    generateOrder(count) {
        const allToppings = ['sauce', 'cheese', 'pepperoni', 'mushroom', 'olive', 'pineapple'];
        const order = ['sauce', 'cheese']; // 基本配料
        
        // 隨機添加其他配料
        const extraToppings = allToppings.filter(t => !order.includes(t));
        for (let i = 0; i < count - 2 && extraToppings.length > 0; i++) {
            const randomIndex = Math.floor(Math.random() * extraToppings.length);
            order.push(extraToppings.splice(randomIndex, 1)[0]);
        }
        
        return order;
    }
    
    renderCustomers() {
        const container = document.getElementById('customers');
        container.innerHTML = '';
        
        this.customers.forEach(customer => {
            const card = document.createElement('div');
            card.className = 'customer-card';
            if (this.currentCustomer && this.currentCustomer.id === customer.id) {
                card.classList.add('selected');
            }
            
            const toppingIcons = {
                sauce: '🍅',
                cheese: '🧀',
                pepperoni: '🍖',
                mushroom: '🍄',
                olive: '🫒',
                pineapple: '🍍'
            };
            
            const orderDisplay = customer.order.map(t => toppingIcons[t]).join(' ');
            
            card.innerHTML = `
                <div class="customer-avatar">${customer.avatar}</div>
                <div class="customer-name">${customer.name}</div>
                <div class="customer-order">想要：${orderDisplay}</div>
                <div class="patience-bar">
                    <div class="patience-fill" id="patience-${customer.id}" style="width: 100%"></div>
                </div>
            `;
            
            card.addEventListener('click', () => {
                this.selectCustomer(customer);
            });
            
            container.appendChild(card);
        });
    }
    
    selectCustomer(customer) {
        this.currentCustomer = customer;
        this.resetPizza();
        this.renderCustomers();
        this.updateCurrentOrder();
    }
    
    updateCurrentOrder() {
        const orderCard = document.querySelector('.order-card');
        if (!this.currentCustomer) {
            orderCard.innerHTML = '<p>選擇一位客人開始製作！</p>';
            return;
        }
        
        const toppingIcons = {
            sauce: '🍅',
            cheese: '🧀',
            pepperoni: '🍖',
            mushroom: '🍄',
            olive: '🫒',
            pineapple: '🍍'
        };
        
        const toppingNames = {
            sauce: '醬料',
            cheese: '起司',
            pepperoni: '臘腸',
            mushroom: '蘑菇',
            olive: '橄欖',
            pineapple: '鳳梨'
        };
        
        const orderItems = this.currentCustomer.order.map(t => 
            `<div class="order-item">${toppingIcons[t]} ${toppingNames[t]}</div>`
        ).join('');
        
        orderCard.innerHTML = `
            <p><strong>${this.currentCustomer.avatar} ${this.currentCustomer.name}</strong> 的訂單：</p>
            ${orderItems}
        `;
    }
    
    startPatienceTimer(customer) {
        const interval = setInterval(() => {
            const elapsed = Date.now() - customer.startTime;
            const remaining = customer.maxPatience - (elapsed / 1000);
            const percentage = (remaining / customer.maxPatience) * 100;
            
            const fill = document.getElementById(`patience-${customer.id}`);
            if (fill) {
                fill.style.width = `${Math.max(0, percentage)}%`;
                
                if (percentage < 30) {
                    fill.classList.add('danger');
                } else if (percentage < 60) {
                    fill.classList.add('warning');
                }
            }
            
            if (remaining <= 0) {
                clearInterval(interval);
                this.customerLeave(customer);
            }
        }, 100);
        
        customer.patienceInterval = interval;
    }
    
    customerLeave(customer) {
        const index = this.customers.findIndex(c => c.id === customer.id);
        if (index !== -1) {
            this.customers.splice(index, 1);
            this.reputation -= 10;
            this.dailyReputationChange -= 10;
            
            if (this.currentCustomer && this.currentCustomer.id === customer.id) {
                this.currentCustomer = null;
                this.resetPizza();
            }
            
            this.renderCustomers();
            this.updateUI();
            this.showMessage('😢 客人等太久離開了... -10⭐');
        }
    }
    
    startCustomerSpawner() {
        this.customerSpawner = setInterval(() => {
            this.spawnCustomer();
        }, this.customerSpawnInterval);
    }
    
    // 披薩製作
    addTopping(topping) {
        const canvas = document.getElementById('pizza-canvas');
        
        // 檢查是否已經烤過
        if (this.currentPizza.cooked) {
            this.showMessage('披薩已經烤好了，不能再加配料！');
            return;
        }
        
        // 添加配料
        this.currentPizza.toppings.push(topping);
        
        // 視覺效果
        const toppingIcons = {
            sauce: '🍅',
            cheese: '🧀',
            pepperoni: '🍖',
            mushroom: '🍄',
            olive: '🫒',
            pineapple: '🍍'
        };
        
        const toppingEl = document.createElement('div');
        toppingEl.className = 'topping';
        toppingEl.textContent = toppingIcons[topping];
        
        // 隨機位置
        const angle = Math.random() * Math.PI * 2;
        const radius = Math.random() * 80 + 20;
        const x = Math.cos(angle) * radius + 125;
        const y = Math.sin(angle) * radius + 125;
        
        toppingEl.style.left = `${x - 15}px`;
        toppingEl.style.top = `${y - 15}px`;
        
        canvas.appendChild(toppingEl);
        
        // 更新按鈕狀態
        this.updateActionButtons();
    }
    
    cookPizza() {
        if (this.currentPizza.toppings.length === 0) {
            this.showMessage('請先添加配料！');
            return;
        }
        
        // 顯示烤箱動畫
        const overlay = document.getElementById('oven-overlay');
        const progressFill = overlay.querySelector('.progress-fill');
        overlay.classList.remove('hidden');
        
        // 根據角色調整烤披薩時間
        let cookTime = 5000;
        if (this.activeCharacter === 'cinnamoroll') {
            cookTime = 4000; // 速度 +20%
        }
        
        let progress = 0;
        const interval = setInterval(() => {
            progress += 2;
            progressFill.style.width = `${progress}%`;
            
            if (progress >= 100) {
                clearInterval(interval);
                overlay.classList.add('hidden');
                progressFill.style.width = '0%';
                this.currentPizza.cooked = true;
                this.updateActionButtons();
                this.showMessage('🍕 披薩烤好了！');
            }
        }, cookTime / 50);
    }
    
    servePizza() {
        if (!this.currentCustomer) {
            this.showMessage('沒有選擇客人！');
            return;
        }
        
        if (!this.currentPizza.cooked) {
            this.showMessage('披薩還沒烤好！');
            return;
        }
        
        // 檢查訂單是否正確
        const result = this.checkOrder();
        this.showResult(result);
        
        // 移除客人
        clearInterval(this.currentCustomer.patienceInterval);
        const index = this.customers.findIndex(c => c.id === this.currentCustomer.id);
        if (index !== -1) {
            this.customers.splice(index, 1);
        }
        
        this.currentCustomer = null;
        this.resetPizza();
        this.renderCustomers();
        this.updateUI();
    }
    
    checkOrder() {
        const ordered = [...this.currentCustomer.order].sort();
        const made = [...this.currentPizza.toppings].sort();
        
        // 計算正確率
        let correct = 0;
        let total = Math.max(ordered.length, made.length);
        
        ordered.forEach(item => {
            const index = made.indexOf(item);
            if (index !== -1) {
                correct++;
                made.splice(index, 1);
            }
        });
        
        const accuracy = correct / total;
        
        // 計算耐心獎勵
        const elapsed = Date.now() - this.currentCustomer.startTime;
        const patiencePercent = 1 - (elapsed / 1000 / this.currentCustomer.maxPatience);
        
        let stars = 0;
        let money = 0;
        let reputation = 0;
        let title = '';
        let message = '';
        
        if (accuracy >= 1.0) {
            stars = 3;
            money = 50;
            reputation = 10;
            title = '完美！';
            message = '客人非常滿意！';
            
            if (patiencePercent > 0.8) {
                money += 20;
                reputation += 5;
                message += ' 超快速服務獎勵！';
            }
        } else if (accuracy >= 0.7) {
            stars = 2;
            money = 30;
            reputation = 5;
            title = '很好！';
            message = '客人還算滿意';
        } else if (accuracy >= 0.4) {
            stars = 1;
            money = 15;
            reputation = 0;
            title = '普通';
            message = '客人覺得還可以';
        } else {
            stars = 0;
            money = 5;
            reputation = -5;
            title = '糟糕...';
            message = '客人不太滿意';
        }
        
        // 角色加成
        if (this.activeCharacter === 'kuromi') {
            money = Math.floor(money * 1.3); // 收入 +30%
        }
        
        this.money += money;
        this.reputation += reputation;
        this.dailyIncome += money;
        this.dailyCustomers++;
        this.dailyReputationChange += reputation;
        
        return { stars, money, reputation, title, message };
    }
    
    showResult(result) {
        const modal = document.getElementById('result-modal');
        document.getElementById('result-title').textContent = result.title;
        document.getElementById('result-stars').textContent = '⭐'.repeat(result.stars);
        document.getElementById('result-message').textContent = result.message;
        document.getElementById('result-reward').textContent = 
            `+${result.money}💰 ${result.reputation >= 0 ? '+' : ''}${result.reputation}⭐`;
        
        modal.classList.remove('hidden');
        
        // 角色開心動畫
        if (result.stars >= 2) {
            this.updateWalkingCharacter();
        }
    }
    
    resetPizza() {
        this.currentPizza = {
            toppings: [],
            cooked: false
        };
        document.getElementById('pizza-canvas').innerHTML = '';
        this.updateActionButtons();
        this.updateCurrentOrder();
    }
    
    updateActionButtons() {
        const cookBtn = document.getElementById('cook-btn');
        const serveBtn = document.getElementById('serve-btn');
        
        cookBtn.disabled = this.currentPizza.toppings.length === 0 || this.currentPizza.cooked;
        serveBtn.disabled = !this.currentPizza.cooked;
    }
    
    // 角色系統
    selectCharacter(character) {
        if (!this.unlockedCharacters.includes(character)) return;
        
        this.activeCharacter = character;
        
        document.querySelectorAll('.character').forEach(char => {
            char.classList.remove('active');
        });
        
        document.querySelector(`[data-character="${character}"]`).classList.add('active');
        
        // 更新走動的角色
        this.updateWalkingCharacter();
    }
    
    tryUnlockCharacter(character) {
        const costs = {
            pompompurin: 500,
            mymelody: 1000
        };
        
        const cost = costs[character];
        if (this.money >= cost) {
            this.money -= cost;
            this.unlockedCharacters.push(character);
            
            const charEl = document.querySelector(`[data-character="${character}"]`);
            charEl.classList.remove('locked');
            charEl.querySelector('.character-skill').textContent = 
                character === 'pompompurin' ? '耐心 +50%' : '全能 +15%';
            
            this.updateUI();
            this.showMessage(`✨ 解鎖了 ${charEl.querySelector('.character-name').textContent}！`);
        } else {
            this.showMessage(`💰 需要 ${cost} 金幣才能解鎖！`);
        }
    }
    
    // 一天結束
    startDayTimer() {
        setTimeout(() => {
            this.endDay();
        }, this.dayDuration);
    }
    
    endDay() {
        clearInterval(this.customerSpawner);
        
        // 清除所有客人的計時器
        this.customers.forEach(c => clearInterval(c.patienceInterval));
        
        document.getElementById('daily-income').textContent = this.dailyIncome;
        document.getElementById('daily-customers').textContent = this.dailyCustomers;
        document.getElementById('daily-reputation').textContent = 
            (this.dailyReputationChange >= 0 ? '+' : '') + this.dailyReputationChange;
        
        document.getElementById('day-end-modal').classList.remove('hidden');
    }
    
    startNextDay() {
        this.day++;
        this.customers = [];
        this.currentCustomer = null;
        this.dailyIncome = 0;
        this.dailyCustomers = 0;
        this.dailyReputationChange = 0;
        
        document.getElementById('day-end-modal').classList.add('hidden');
        
        this.resetPizza();
        this.renderCustomers();
        this.spawnCustomer();
        this.startCustomerSpawner();
        this.startDayTimer();
        this.updateUI();
    }
    
    // UI 更新
    updateUI() {
        document.getElementById('money').textContent = this.money;
        document.getElementById('reputation').textContent = this.reputation;
        document.getElementById('day').textContent = this.day;
    }
    
    showMessage(message) {
        // 簡單的訊息提示（可以改成更好看的 toast）
        console.log(message);
    }
    
    // 角色走動系統
    startCharacterWalking() {
        const stage = document.getElementById('character-stage');
        const stageWidth = stage.offsetWidth;
        
        // 創建走動的角色
        const characterEmojis = {
            cinnamoroll: '🐶',
            kuromi: '😈',
            pompompurin: '🐶',
            mymelody: '🐰'
        };
        
        this.walkingCharacter = document.createElement('div');
        this.walkingCharacter.className = 'walking-character';
        this.walkingCharacter.textContent = characterEmojis[this.activeCharacter];
        this.walkingCharacter.style.left = '0px';
        stage.appendChild(this.walkingCharacter);
        
        // 開始走動動畫
        this.walkingInterval = setInterval(() => {
            this.characterPosition += this.characterDirection * 2;
            
            // 到達邊界時轉向
            if (this.characterPosition >= stageWidth - 60) {
                this.characterDirection = -1;
                this.walkingCharacter.classList.add('flip');
            } else if (this.characterPosition <= 0) {
                this.characterDirection = 1;
                this.walkingCharacter.classList.remove('flip');
            }
            
            this.walkingCharacter.style.left = `${this.characterPosition}px`;
        }, 30);
    }
    
    updateWalkingCharacter() {
        if (!this.walkingCharacter) return;
        
        const characterEmojis = {
            cinnamoroll: '🐶',
            kuromi: '😈',
            pompompurin: '🐶',
            mymelody: '🐰'
        };
        
        // 更新角色外觀
        this.walkingCharacter.textContent = characterEmojis[this.activeCharacter];
        
        // 添加開心動畫（當完成訂單時）
        this.walkingCharacter.classList.add('happy');
        setTimeout(() => {
            this.walkingCharacter.classList.remove('happy');
        }, 2000);
    }
}

// 啟動遊戲
window.addEventListener('DOMContentLoaded', () => {
    new SanrioPizzaShop();
});

