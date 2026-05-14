// 遊戲系統
class BrawlGame {
    constructor(characterManager) {
        this.characterManager = characterManager;
        this.canvas = document.getElementById('gameCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.player = null;
        this.enemy = null;
        this.gameState = 'idle'; // idle, playing, paused, ended
        
        this.init();
    }

    init() {
        // 設定畫布大小
        this.canvas.width = 800;
        this.canvas.height = 600;
    }

    // 開始遊戲
    startGame(playerCharacter, enemyCharacter = null) {
        this.player = {
            ...playerCharacter,
            currentHealth: playerCharacter.health,
            x: 150,
            y: 300
        };
        
        // 如果沒有指定敵人，隨機選擇一個
        if (!enemyCharacter) {
            const enemies = this.characterManager.getAllCharacters()
                .filter(char => char.id !== playerCharacter.id);
            enemyCharacter = enemies[Math.floor(Math.random() * enemies.length)];
        }
        
        this.enemy = {
            ...enemyCharacter,
            currentHealth: enemyCharacter.health,
            x: 650,
            y: 300
        };
        
        this.gameState = 'playing';
        this.updateUI();
        this.draw();
    }

    // 攻擊
    attack(attacker, defender) {
        const damage = Math.max(1, attacker.attack - defender.defense);
        defender.currentHealth = Math.max(0, defender.currentHealth - damage);
        return damage;
    }

    // 防禦
    defend(character) {
        // 防禦時減少受到的傷害
        character.isDefending = true;
        setTimeout(() => {
            character.isDefending = false;
        }, 1000);
    }

    // 使用特殊技能
    useSpecial(attacker, defender) {
        const specialDamage = Math.max(1, attacker.attack * 1.5 - defender.defense);
        defender.currentHealth = Math.max(0, defender.currentHealth - specialDamage);
        return specialDamage;
    }

    // 玩家攻擊
    playerAttack() {
        if (this.gameState !== 'playing') return;
        
        const damage = this.attack(this.player, this.enemy);
        this.showDamage(this.enemy.x, this.enemy.y, damage);
        this.updateUI();
        this.draw();
        
        if (this.enemy.currentHealth <= 0) {
            this.endGame('player');
            return;
        }
        
        // 敵人反擊
        setTimeout(() => {
            this.enemyAttack();
        }, 500);
    }

    // 敵人攻擊
    enemyAttack() {
        if (this.gameState !== 'playing') return;
        
        const damage = this.attack(this.enemy, this.player);
        this.showDamage(this.player.x, this.player.y, damage);
        this.updateUI();
        this.draw();
        
        if (this.player.currentHealth <= 0) {
            this.endGame('enemy');
        }
    }

    // 玩家防禦
    playerDefend() {
        if (this.gameState !== 'playing') return;
        
        this.defend(this.player);
        this.draw();
        
        // 敵人攻擊（但傷害減少）
        setTimeout(() => {
            const damage = Math.max(1, Math.floor(this.enemy.attack * 0.5 - this.player.defense));
            this.player.currentHealth = Math.max(0, this.player.currentHealth - damage);
            this.showDamage(this.player.x, this.player.y, damage);
            this.updateUI();
            this.draw();
        }, 500);
    }

    // 玩家使用特殊技能
    playerSpecial() {
        if (this.gameState !== 'playing') return;
        
        const damage = this.useSpecial(this.player, this.enemy);
        this.showDamage(this.enemy.x, this.enemy.y, damage, true);
        this.updateUI();
        this.draw();
        
        if (this.enemy.currentHealth <= 0) {
            this.endGame('player');
            return;
        }
        
        // 敵人反擊
        setTimeout(() => {
            this.enemyAttack();
        }, 500);
    }

    // 顯示傷害數字
    showDamage(x, y, damage, isSpecial = false) {
        const damageText = document.createElement('div');
        damageText.textContent = `-${damage}`;
        damageText.style.position = 'absolute';
        damageText.style.left = `${x + 50}px`;
        damageText.style.top = `${y}px`;
        damageText.style.color = isSpecial ? '#ffd43b' : '#ff6b6b';
        damageText.style.fontSize = '24px';
        damageText.style.fontWeight = 'bold';
        damageText.style.pointerEvents = 'none';
        damageText.style.transition = 'all 1s';
        document.body.appendChild(damageText);
        
        setTimeout(() => {
            damageText.style.transform = 'translateY(-50px)';
            damageText.style.opacity = '0';
            setTimeout(() => damageText.remove(), 1000);
        }, 10);
    }

    // 更新 UI
    updateUI() {
        // 更新玩家資訊
        document.getElementById('playerHealth').style.width = 
            `${(this.player.currentHealth / this.player.health) * 100}%`;
        document.getElementById('playerAttack').textContent = this.player.attack;
        document.getElementById('playerAvatar').textContent = this.player.emoji || '⚔️';
        document.getElementById('playerAvatar').style.backgroundColor = this.player.color;
        
        // 更新敵人資訊
        document.getElementById('enemyHealth').style.width = 
            `${(this.enemy.currentHealth / this.enemy.health) * 100}%`;
        document.getElementById('enemyAttack').textContent = this.enemy.attack;
        document.getElementById('enemyAvatar').textContent = this.enemy.emoji || '⚔️';
        document.getElementById('enemyAvatar').style.backgroundColor = this.enemy.color;
    }

    // 繪製遊戲畫面
    draw() {
        // 清空畫布
        this.ctx.fillStyle = '#2d3436';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 繪製背景
        this.drawBackground();
        
        // 繪製角色
        this.drawCharacter(this.player);
        this.drawCharacter(this.enemy);
        
        // 繪製 UI
        this.drawGameUI();
    }

    // 繪製背景
    drawBackground() {
        // 繪製格線
        this.ctx.strokeStyle = '#636e72';
        this.ctx.lineWidth = 1;
        for (let i = 0; i < this.canvas.width; i += 50) {
            this.ctx.beginPath();
            this.ctx.moveTo(i, 0);
            this.ctx.lineTo(i, this.canvas.height);
            this.ctx.stroke();
        }
        for (let i = 0; i < this.canvas.height; i += 50) {
            this.ctx.beginPath();
            this.ctx.moveTo(0, i);
            this.ctx.lineTo(this.canvas.width, i);
            this.ctx.stroke();
        }
    }

    // 繪製角色
    drawCharacter(character) {
        const size = 80;
        
        // 繪製角色圓形
        this.ctx.beginPath();
        this.ctx.arc(character.x, character.y, size / 2, 0, Math.PI * 2);
        this.ctx.fillStyle = character.color;
        this.ctx.fill();
        this.ctx.strokeStyle = '#fff';
        this.ctx.lineWidth = 3;
        this.ctx.stroke();
        
        // 繪製 emoji（簡化版，實際應該使用圖片）
        this.ctx.font = '40px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        this.ctx.fillText(character.emoji || '⚔️', character.x, character.y);
        
        // 繪製生命值條
        const barWidth = 100;
        const barHeight = 10;
        const barX = character.x - barWidth / 2;
        const barY = character.y - size / 2 - 20;
        
        // 背景
        this.ctx.fillStyle = '#e9ecef';
        this.ctx.fillRect(barX, barY, barWidth, barHeight);
        
        // 生命值
        const healthPercent = character.currentHealth / character.health;
        this.ctx.fillStyle = healthPercent > 0.5 ? '#51cf66' : healthPercent > 0.25 ? '#fdcb6e' : '#ff6b6b';
        this.ctx.fillRect(barX, barY, barWidth * healthPercent, barHeight);
        
        // 邊框
        this.ctx.strokeStyle = '#333';
        this.ctx.lineWidth = 2;
        this.ctx.strokeRect(barX, barY, barWidth, barHeight);
        
        // 名稱
        this.ctx.fillStyle = '#fff';
        this.ctx.font = '14px Arial';
        this.ctx.fillText(character.name, character.x, barY - 5);
    }

    // 繪製遊戲 UI
    drawGameUI() {
        // 可以在這裡繪製額外的 UI 元素
    }

    // 結束遊戲
    endGame(winner) {
        this.gameState = 'ended';
        const message = winner === 'player' ? '你贏了！' : '你輸了！';
        setTimeout(() => {
            alert(message);
        }, 500);
    }

    // 結束遊戲
    stop() {
        this.gameState = 'idle';
    }
}

