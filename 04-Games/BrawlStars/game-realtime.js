// 即時戰鬥遊戲系統
class RealtimeBrawlGame {
    constructor(characterManager) {
        this.characterManager = characterManager;
        this.canvas = document.getElementById('gameCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.player = null;
        this.enemy = null;
        this.gameState = 'idle'; // idle, playing, paused, ended
        
        // 遊戲循環
        this.lastTime = 0;
        this.deltaTime = 0;
        this.gameLoop = null;
        
        // 輸入控制
        this.keys = {};
        this.touchControls = {
            move: { x: 0, y: 0, active: false },
            attack: { active: false }
        };
        
        // 子彈系統
        this.projectiles = [];
        
        // 彈藥系統（三格彈藥，自動回復）
        this.ammo = 3;
        this.maxAmmo = 3;
        this.reloadTimer = 0;
        this.reloadTime = 1.5; // 1.5秒回一格彈藥
        
        // 初始化
        this.init();
        this.setupControls();
    }

    init() {
        // 設定畫布大小
        this.canvas.width = 1000;
        this.canvas.height = 600;
        
        // 設定畫布樣式
        this.canvas.style.cursor = 'crosshair';
    }

    setupControls() {
        // 鍵盤控制
        document.addEventListener('keydown', (e) => {
            this.keys[e.key.toLowerCase()] = true;
        });
        
        document.addEventListener('keyup', (e) => {
            this.keys[e.key.toLowerCase()] = false;
        });
        
        // 觸控控制
        this.canvas.addEventListener('touchstart', (e) => {
            e.preventDefault();
            this.handleTouchStart(e);
        });
        
        this.canvas.addEventListener('touchmove', (e) => {
            e.preventDefault();
            this.handleTouchMove(e);
        });
        
        this.canvas.addEventListener('touchend', (e) => {
            e.preventDefault();
            this.handleTouchEnd(e);
        });
        
        // 滑鼠點擊攻擊
        this.canvas.addEventListener('click', (e) => {
            if (this.gameState === 'playing') {
                this.handleAttack(e);
            }
        });
    }

    // 開始遊戲
    startGame(playerCharacter, enemyCharacter = null) {
        this.player = {
            ...playerCharacter,
            currentHealth: playerCharacter.health,
            maxHealth: playerCharacter.health,
            x: 200,
            y: 300,
            direction: 0, // 角度（弧度）
            canAttack: true,
            attackCooldown: 0,
            isMoving: false
        };
        
        // 如果沒有指定敵人，隨機選擇一個
        if (!enemyCharacter) {
            const enemies = this.characterManager.getAllCharacters()
                .filter(char => char.id !== playerCharacter.id);
            enemyCharacter = enemies[Math.floor(Math.random() * enemies.length)] || this.characterManager.getAllCharacters()[0];
        }
        
        this.enemy = {
            ...enemyCharacter,
            currentHealth: enemyCharacter.health,
            maxHealth: enemyCharacter.health,
            x: 800,
            y: 300,
            direction: Math.PI, // 面向左
            canAttack: true,
            attackCooldown: 0,
            isMoving: false,
            aiTargetX: 800,
            aiTargetY: 300,
            aiState: 'patrol' // patrol, chase, attack
        };
        
        this.projectiles = [];
        
        // 重置彈藥系統
        this.ammo = 3;
        this.reloadTimer = 0;
        
        this.gameState = 'playing';
        this.updateUI();
        this.startGameLoop();
    }

    // 開始遊戲循環
    startGameLoop() {
        if (this.gameLoop) return;
        
        const loop = (currentTime) => {
            if (this.gameState !== 'playing') {
                this.gameLoop = null;
                return;
            }
            
            this.deltaTime = (currentTime - this.lastTime) / 1000; // 轉換為秒
            this.lastTime = currentTime;
            
            this.update(this.deltaTime);
            this.draw();
            
            this.gameLoop = requestAnimationFrame(loop);
        };
        
        this.lastTime = performance.now();
        this.gameLoop = requestAnimationFrame(loop);
    }

    // 更新遊戲邏輯
    update(deltaTime) {
        if (this.gameState !== 'playing') return;
        
        // 更新玩家
        this.updatePlayer(deltaTime);
        
        // 更新敵人（AI）
        this.updateEnemyAI(deltaTime);
        
        // 更新子彈
        this.updateProjectiles(deltaTime);
        
        // 檢查碰撞
        this.checkCollisions();
        
        // 彈藥自動回復（1.5秒回一格）
        if (this.ammo < this.maxAmmo) {
            this.reloadTimer += deltaTime;
            if (this.reloadTimer >= this.reloadTime) {
                this.ammo++;
                this.reloadTimer = 0;
                this.updateAmmoUI();
            }
        }
        
        // 檢查勝利條件
        if (this.player.currentHealth <= 0) {
            this.endGame('enemy');
        } else if (this.enemy.currentHealth <= 0) {
            this.endGame('player');
        }
        
        // 更新UI
        this.updateUI();
    }

    // 更新玩家
    updatePlayer(deltaTime) {
        // 處理移動
        let moveX = 0;
        let moveY = 0;
        const moveSpeed = this.player.moveSpeed * 60 * deltaTime; // 轉換為每秒移動距離
        
        // 鍵盤控制
        if (this.keys['w'] || this.keys['arrowup']) moveY -= moveSpeed;
        if (this.keys['s'] || this.keys['arrowdown']) moveY += moveSpeed;
        if (this.keys['a'] || this.keys['arrowleft']) moveX -= moveSpeed;
        if (this.keys['d'] || this.keys['arrowright']) moveX += moveSpeed;
        
        // 觸控控制
        if (this.touchControls.move.active) {
            moveX += this.touchControls.move.x * moveSpeed * 0.5;
            moveY += this.touchControls.move.y * moveSpeed * 0.5;
        }
        
        // 標準化移動向量（對角線移動速度修正）
        if (moveX !== 0 || moveY !== 0) {
            const length = Math.sqrt(moveX * moveX + moveY * moveY);
            moveX = (moveX / length) * moveSpeed;
            moveY = (moveY / length) * moveSpeed;
            this.player.isMoving = true;
        } else {
            this.player.isMoving = false;
        }
        
        // 應用移動（邊界檢查）
        const newX = Math.max(50, Math.min(this.canvas.width - 50, this.player.x + moveX));
        const newY = Math.max(50, Math.min(this.canvas.height - 50, this.player.y + moveY));
        
        this.player.x = newX;
        this.player.y = newY;
        
        // 更新方向（朝向滑鼠或移動方向）
        if (moveX !== 0 || moveY !== 0) {
            this.player.direction = Math.atan2(moveY, moveX);
        }
        
        // 更新攻擊冷卻
        if (this.player.attackCooldown > 0) {
            this.player.attackCooldown -= deltaTime;
            this.player.canAttack = this.player.attackCooldown <= 0;
        }
    }

    // 更新敵人AI（改進版）
    updateEnemyAI(deltaTime) {
        const distance = this.getDistance(this.enemy, this.player);
        const moveSpeed = this.enemy.moveSpeed * 60 * deltaTime;
        const healthPercent = this.enemy.currentHealth / this.enemy.maxHealth;
        
        // 改進的AI行為邏輯
        if (this.enemy.canAttack && distance <= this.enemy.range * 50) {
            // 在攻擊範圍內且可以攻擊
            const angle = Math.atan2(this.player.y - this.enemy.y, this.player.x - this.enemy.x);
            this.enemy.direction = angle;
            
            // 根據角色類型決定是否攻擊
            if (this.enemy.attackType === 'melee' && distance <= this.enemy.range * 50) {
                this.enemyAttack();
            } else if (this.enemy.attackType !== 'melee') {
                this.enemyAttack();
            }
            this.enemy.isMoving = false;
        } else if (distance > this.enemy.range * 50) {
            // 距離太遠，追擊玩家
            const angle = Math.atan2(this.player.y - this.enemy.y, this.player.x - this.enemy.x);
            this.enemy.x += Math.cos(angle) * moveSpeed;
            this.enemy.y += Math.sin(angle) * moveSpeed;
            this.enemy.direction = angle;
            this.enemy.isMoving = true;
        } else if (healthPercent < 0.3 && distance < this.enemy.range * 40) {
            // 生命值低且距離太近，後退
            const retreatAngle = Math.atan2(this.enemy.y - this.player.y, this.enemy.x - this.player.x);
            this.enemy.x += Math.cos(retreatAngle) * moveSpeed * 0.5;
            this.enemy.y += Math.sin(retreatAngle) * moveSpeed * 0.5;
            this.enemy.isMoving = true;
        } else {
            // 保持最佳攻擊距離
            const optimalDistance = this.enemy.range * 45;
            if (distance > optimalDistance + 30) {
                // 太遠，靠近
                const angle = Math.atan2(this.player.y - this.enemy.y, this.player.x - this.enemy.x);
                this.enemy.x += Math.cos(angle) * moveSpeed * 0.7;
                this.enemy.y += Math.sin(angle) * moveSpeed * 0.7;
                this.enemy.direction = angle;
                this.enemy.isMoving = true;
            } else if (distance < optimalDistance - 30) {
                // 太近，後退（僅遠程角色）
                if (this.enemy.attackType !== 'melee') {
                    const angle = Math.atan2(this.enemy.y - this.player.y, this.enemy.x - this.player.x);
                    this.enemy.x += Math.cos(angle) * moveSpeed * 0.5;
                    this.enemy.y += Math.sin(angle) * moveSpeed * 0.5;
                    this.enemy.isMoving = true;
                } else {
                    this.enemy.isMoving = false;
                }
            } else {
                this.enemy.isMoving = false;
            }
        }
        
        // 邊界檢查
        this.enemy.x = Math.max(50, Math.min(this.canvas.width - 50, this.enemy.x));
        this.enemy.y = Math.max(50, Math.min(this.canvas.height - 50, this.enemy.y));
        
        // 更新攻擊冷卻
        if (this.enemy.attackCooldown > 0) {
            this.enemy.attackCooldown -= deltaTime;
            this.enemy.canAttack = this.enemy.attackCooldown <= 0;
        }
    }

    // 更新子彈
    updateProjectiles(deltaTime) {
        for (let i = this.projectiles.length - 1; i >= 0; i--) {
            const proj = this.projectiles[i];
            proj.x += Math.cos(proj.direction) * proj.speed * deltaTime;
            proj.y += Math.sin(proj.direction) * proj.speed * deltaTime;
            
            // 移除超出邊界的子彈
            if (proj.x < 0 || proj.x > this.canvas.width || 
                proj.y < 0 || proj.y > this.canvas.height) {
                this.projectiles.splice(i, 1);
            }
        }
    }

    // 檢查碰撞
    checkCollisions() {
        for (let i = this.projectiles.length - 1; i >= 0; i--) {
            const proj = this.projectiles[i];
            const target = proj.owner === 'player' ? this.enemy : this.player;
            
            const distance = Math.sqrt(
                Math.pow(proj.x - target.x, 2) + 
                Math.pow(proj.y - target.y, 2)
            );
            
            if (distance < 40) { // 碰撞半徑
                // 造成傷害
                const damage = Math.max(1, proj.damage - target.defense);
                target.currentHealth = Math.max(0, target.currentHealth - damage);
                
                // 顯示傷害
                this.showDamage(target.x, target.y, damage);
                
                // 移除子彈
                this.projectiles.splice(i, 1);
            }
        }
    }

    // 處理攻擊（改進版：自動瞄準最近的敵人，添加彈藥檢查）
    handleAttack(e) {
        // 檢查彈藥（核心機制：三格彈藥限制）
        if (this.ammo <= 0) {
            return; // 沒有彈藥，無法攻擊
        }
        
        if (!this.player.canAttack) return;
        
        const rect = this.canvas.getBoundingClientRect();
        const targetX = e.clientX - rect.left;
        const targetY = e.clientY - rect.top;
        
        // 計算方向（朝向滑鼠位置）
        let angle = Math.atan2(targetY - this.player.y, targetX - this.player.x);
        
        // 如果敵人在射程內，可以選擇自動瞄準敵人
        const distanceToEnemy = this.getDistance(this.player, this.enemy);
        if (distanceToEnemy <= this.player.range * 50) {
            // 可選：啟用自動瞄準（輕微調整角度朝向敵人）
            const enemyAngle = Math.atan2(this.enemy.y - this.player.y, this.enemy.x - this.player.x);
            // 只在角度差異不大時使用自動瞄準（避免感覺太"粘"）
            const angleDiff = Math.abs(angle - enemyAngle);
            if (angleDiff < Math.PI / 4) { // 45度內
                angle = enemyAngle;
            }
        }
        
        this.player.direction = angle;
        
        // 發射攻擊
        this.playerAttack(angle);
    }

    // 玩家攻擊（添加彈藥消耗）
    playerAttack(direction = null) {
        // 檢查彈藥
        if (this.ammo <= 0) return;
        
        if (!this.player.canAttack) return;
        
        const angle = direction !== null ? direction : this.player.direction;
        
        if (this.player.attackType === 'melee') {
            // 近戰攻擊 - 直接檢查敵人距離
            const distance = this.getDistance(this.player, this.enemy);
            if (distance <= this.player.range * 50) {
                const damage = Math.max(1, this.player.attack - this.enemy.defense);
                this.enemy.currentHealth = Math.max(0, this.enemy.currentHealth - damage);
                this.showDamage(this.enemy.x, this.enemy.y, damage);
            }
        } else if (this.player.attackType === 'ranged') {
            // 遠程攻擊 - 發射子彈
            this.projectiles.push({
                x: this.player.x,
                y: this.player.y,
                direction: angle,
                speed: 400, // 像素/秒
                damage: this.player.attack,
                owner: 'player',
                color: this.player.color
            });
        } else if (this.player.attackType === 'area') {
            // 範圍攻擊 - 發射較大的子彈
            this.projectiles.push({
                x: this.player.x,
                y: this.player.y,
                direction: angle,
                speed: 300,
                damage: this.player.attack,
                owner: 'player',
                color: this.player.color,
                radius: 15 // 更大的碰撞半徑
            });
        }
        
        // 消耗彈藥
        this.ammo--;
        this.reloadTimer = 0; // 重置裝彈計時器
        this.updateAmmoUI();
        
        // 設置攻擊冷卻
        this.player.attackCooldown = this.player.reloadSpeed;
        this.player.canAttack = false;
    }

    // 敵人攻擊（改進版：預測玩家位置）
    enemyAttack() {
        if (!this.enemy.canAttack) return;
        
        // 計算目標角度（預測玩家移動）
        let angle = Math.atan2(this.player.y - this.enemy.y, this.player.x - this.enemy.x);
        
        // 如果玩家在移動，預測未來位置
        if (this.player.isMoving) {
            const predictionDistance = 50; // 預測距離
            const predictedX = this.player.x + Math.cos(this.player.direction) * predictionDistance;
            const predictedY = this.player.y + Math.sin(this.player.direction) * predictionDistance;
            angle = Math.atan2(predictedY - this.enemy.y, predictedX - this.enemy.x);
        }
        
        this.enemy.direction = angle;
        
        if (this.enemy.attackType === 'melee') {
            const distance = this.getDistance(this.enemy, this.player);
            if (distance <= this.enemy.range * 50) {
                const damage = Math.max(1, this.enemy.attack - this.player.defense);
                this.player.currentHealth = Math.max(0, this.player.currentHealth - damage);
                this.showDamage(this.player.x, this.player.y, damage);
            }
        } else {
            // 遠程攻擊
            const projectileSize = this.enemy.attackType === 'area' ? 12 : 5;
            this.projectiles.push({
                x: this.enemy.x,
                y: this.enemy.y,
                direction: angle,
                speed: this.enemy.attackType === 'area' ? 300 : 400,
                damage: this.enemy.attack,
                owner: 'enemy',
                color: this.enemy.color,
                radius: projectileSize
            });
        }
        
        this.enemy.attackCooldown = this.enemy.reloadSpeed;
        this.enemy.canAttack = false;
    }

    // 獲取距離
    getDistance(obj1, obj2) {
        return Math.sqrt(
            Math.pow(obj1.x - obj2.x, 2) + 
            Math.pow(obj1.y - obj2.y, 2)
        );
    }

    // 顯示傷害數字
    showDamage(x, y, damage) {
        // 簡單的傷害數字動畫（可以在這裡添加更複雜的效果）
        const damageText = {
            x: x,
            y: y,
            text: `-${damage}`,
            alpha: 1,
            yOffset: 0,
            lifetime: 1.0
        };
        
        // 可以使用一個數組來追蹤所有傷害數字
        if (!this.damageTexts) this.damageTexts = [];
        this.damageTexts.push(damageText);
    }

    // 更新UI
    updateUI() {
        if (!this.player || !this.enemy) return;
        
        // 更新玩家資訊
        const playerHealthPercent = (this.player.currentHealth / this.player.maxHealth) * 100;
        document.getElementById('playerHealth').style.width = `${playerHealthPercent}%`;
        document.getElementById('playerAttack').textContent = this.player.attack;
        document.getElementById('playerAvatar').textContent = this.player.emoji || '⚔️';
        document.getElementById('playerAvatar').style.backgroundColor = this.player.color;
        
        // 更新敵人資訊
        const enemyHealthPercent = (this.enemy.currentHealth / this.enemy.maxHealth) * 100;
        document.getElementById('enemyHealth').style.width = `${enemyHealthPercent}%`;
        document.getElementById('enemyAttack').textContent = this.enemy.attack;
        document.getElementById('enemyAvatar').textContent = this.enemy.emoji || '⚔️';
        document.getElementById('enemyAvatar').style.backgroundColor = this.enemy.color;
        
        // 更新彈藥UI
        this.updateAmmoUI();
    }
    
    // 更新彈藥UI
    updateAmmoUI() {
        let ammoElement = document.getElementById('ammoDisplay');
        if (!ammoElement) {
            // 創建彈藥顯示元素
            const playerStats = document.querySelector('.player-stats');
            if (playerStats) {
                ammoElement = document.createElement('div');
                ammoElement.id = 'ammoDisplay';
                ammoElement.className = 'stat';
                ammoElement.style.marginTop = '10px';
                playerStats.appendChild(ammoElement);
            }
        }
        
        if (ammoElement) {
            let ammoBars = '';
            for (let i = 0; i < this.maxAmmo; i++) {
                if (i < this.ammo) {
                    ammoBars += '●'; // 實心圓點表示有彈藥
                } else {
                    // 如果正在裝彈，顯示半透明
                    if (i === this.ammo && this.reloadTimer > 0) {
                        const reloadProgress = this.reloadTimer / this.reloadTime;
                        const opacity = Math.max(0.3, reloadProgress);
                        ammoBars += `<span style="opacity: ${opacity}">○</span>`;
                    } else {
                        ammoBars += '○'; // 空心圓點表示無彈藥
                    }
                }
            }
            ammoElement.innerHTML = `<span class="stat-label">彈藥:</span> ${ammoBars}`;
        }
    }

    // 繪製遊戲畫面
    draw() {
        // 清空畫布
        this.ctx.fillStyle = '#1a1a2e';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 繪製背景網格
        this.drawGrid();
        
        // 繪製角色
        this.drawCharacter(this.player);
        this.drawCharacter(this.enemy);
        
        // 繪製子彈
        this.drawProjectiles();
        
        // 繪製射程指示器
        this.drawRangeIndicator(this.player);
        
        // 繪製傷害數字
        this.drawDamageTexts();
    }

    // 繪製網格（改進版：更細緻的網格）
    drawGrid() {
        this.ctx.strokeStyle = '#2d3748';
        this.ctx.lineWidth = 0.5;
        
        // 細網格（每25像素）
        for (let i = 0; i < this.canvas.width; i += 25) {
            this.ctx.beginPath();
            this.ctx.moveTo(i, 0);
            this.ctx.lineTo(i, this.canvas.height);
            this.ctx.stroke();
        }
        
        for (let i = 0; i < this.canvas.height; i += 25) {
            this.ctx.beginPath();
            this.ctx.moveTo(0, i);
            this.ctx.lineTo(this.canvas.width, i);
            this.ctx.stroke();
        }
        
        // 粗網格（每100像素）
        this.ctx.strokeStyle = '#1a202c';
        this.ctx.lineWidth = 1;
        
        for (let i = 0; i < this.canvas.width; i += 100) {
            this.ctx.beginPath();
            this.ctx.moveTo(i, 0);
            this.ctx.lineTo(i, this.canvas.height);
            this.ctx.stroke();
        }
        
        for (let i = 0; i < this.canvas.height; i += 100) {
            this.ctx.beginPath();
            this.ctx.moveTo(0, i);
            this.ctx.lineTo(this.canvas.width, i);
            this.ctx.stroke();
        }
    }

    // 繪製角色（改進版：添加方向指示器）
    drawCharacter(character) {
        const size = 40;
        
        // 繪製角色圓形
        this.ctx.save();
        this.ctx.translate(character.x, character.y);
        this.ctx.rotate(character.direction);
        
        // 身體
        this.ctx.beginPath();
        this.ctx.arc(0, 0, size / 2, 0, Math.PI * 2);
        this.ctx.fillStyle = character.color;
        this.ctx.fill();
        this.ctx.strokeStyle = '#fff';
        this.ctx.lineWidth = 3;
        this.ctx.stroke();
        
        // 方向指示器（小三角形）
        if (character.isMoving || character.attackCooldown > 0) {
            this.ctx.fillStyle = '#fff';
            this.ctx.beginPath();
            this.ctx.moveTo(size / 2 - 5, 0);
            this.ctx.lineTo(size / 2 + 5, -8);
            this.ctx.lineTo(size / 2 + 5, 8);
            this.ctx.closePath();
            this.ctx.fill();
        }
        
        // Emoji
        this.ctx.rotate(-character.direction); // 恢復角度
        this.ctx.font = '24px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        this.ctx.fillText(character.emoji || '⚔️', 0, 0);
        
        this.ctx.restore();
        
        // 繪製生命值條
        this.drawHealthBar(character);
    }

    // 繪製生命值條
    drawHealthBar(character) {
        const barWidth = 80;
        const barHeight = 8;
        const barX = character.x - barWidth / 2;
        const barY = character.y - 35;
        
        // 背景
        this.ctx.fillStyle = '#2d3748';
        this.ctx.fillRect(barX - 2, barY - 2, barWidth + 4, barHeight + 4);
        
        // 生命值
        const healthPercent = character.currentHealth / character.maxHealth;
        this.ctx.fillStyle = healthPercent > 0.5 ? '#48bb78' : 
                            healthPercent > 0.25 ? '#ed8936' : '#f56565';
        this.ctx.fillRect(barX, barY, barWidth * healthPercent, barHeight);
        
        // 名稱
        this.ctx.fillStyle = '#fff';
        this.ctx.font = '12px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.fillText(character.name, character.x, barY - 8);
    }

    // 繪製射程指示器（改進版：更明顯的視覺效果）
    drawRangeIndicator(character) {
        if (!character || character.attackType === 'melee') return;
        
        const range = character.range * 50;
        
        this.ctx.save();
        
        // 外圈（半透明填充）
        this.ctx.fillStyle = 'rgba(102, 126, 234, 0.1)';
        this.ctx.beginPath();
        this.ctx.arc(character.x, character.y, range, 0, Math.PI * 2);
        this.ctx.fill();
        
        // 邊框（虛線）
        this.ctx.strokeStyle = 'rgba(102, 126, 234, 0.5)';
        this.ctx.lineWidth = 2;
        this.ctx.setLineDash([8, 4]);
        this.ctx.beginPath();
        this.ctx.arc(character.x, character.y, range, 0, Math.PI * 2);
        this.ctx.stroke();
        
        this.ctx.restore();
    }

    // 繪製子彈（改進版：根據攻擊類型繪製不同樣式）
    drawProjectiles() {
        this.projectiles.forEach(proj => {
            const radius = proj.radius || 5;
            
            // 根據攻擊類型繪製不同效果
            if (proj.radius > 8) {
                // 範圍攻擊 - 較大的圓形
                this.ctx.beginPath();
                this.ctx.arc(proj.x, proj.y, radius, 0, Math.PI * 2);
                const gradient = this.ctx.createRadialGradient(proj.x, proj.y, 0, proj.x, proj.y, radius);
                gradient.addColorStop(0, proj.color);
                gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
                this.ctx.fillStyle = gradient;
                this.ctx.fill();
            } else {
                // 普通子彈
                this.ctx.beginPath();
                this.ctx.arc(proj.x, proj.y, radius, 0, Math.PI * 2);
                this.ctx.fillStyle = proj.color;
                this.ctx.fill();
                this.ctx.strokeStyle = '#fff';
                this.ctx.lineWidth = 2;
                this.ctx.stroke();
                
                // 添加光暈效果
                this.ctx.beginPath();
                this.ctx.arc(proj.x, proj.y, radius + 3, 0, Math.PI * 2);
                this.ctx.fillStyle = `rgba(255, 255, 255, 0.3)`;
                this.ctx.fill();
            }
        });
    }

    // 繪製傷害數字（改進版：更好的動畫效果）
    drawDamageTexts() {
        if (!this.damageTexts) return;
        
        for (let i = this.damageTexts.length - 1; i >= 0; i--) {
            const dt = this.damageTexts[i];
            dt.yOffset += 60 * 0.016; // 基於時間的移動
            dt.alpha -= 60 * 0.016 / dt.lifetime;
            dt.lifetime -= 0.016;
            
            if (dt.lifetime <= 0) {
                this.damageTexts.splice(i, 1);
                continue;
            }
            
            this.ctx.save();
            
            // 添加描邊效果
            this.ctx.globalAlpha = dt.alpha;
            this.ctx.strokeStyle = '#000';
            this.ctx.lineWidth = 4;
            this.ctx.font = 'bold 24px Arial';
            this.ctx.textAlign = 'center';
            this.ctx.textBaseline = 'middle';
            this.ctx.strokeText(dt.text, dt.x, dt.y - dt.yOffset);
            
            // 填充文字
            this.ctx.fillStyle = '#ff6b6b';
            this.ctx.fillText(dt.text, dt.x, dt.y - dt.yOffset);
            
            this.ctx.restore();
        }
    }

    // 處理觸控開始
    handleTouchStart(e) {
        const touch = e.touches[0];
        const rect = this.canvas.getBoundingClientRect();
        const x = touch.clientX - rect.left;
        const y = touch.clientY - rect.top;
        
        // 判斷是移動還是攻擊
        if (x < this.canvas.width / 2) {
            // 左半邊：移動控制
            this.touchControls.move.active = true;
        } else {
            // 右半邊：攻擊
            this.handleAttack({ clientX: touch.clientX, clientY: touch.clientY });
        }
    }

    // 處理觸控移動
    handleTouchMove(e) {
        if (!this.touchControls.move.active) return;
        
        const touch = e.touches[0];
        const rect = this.canvas.getBoundingClientRect();
        const x = touch.clientX - rect.left;
        const y = touch.clientY - rect.top;
        
        // 計算移動方向（相對於畫布中心）
        const centerX = this.canvas.width / 4;
        const centerY = this.canvas.height / 2;
        
        const deltaX = x - centerX;
        const deltaY = y - centerY;
        const length = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
        
        if (length > 0) {
            this.touchControls.move.x = deltaX / length;
            this.touchControls.move.y = deltaY / length;
        }
    }

    // 處理觸控結束
    handleTouchEnd(e) {
        this.touchControls.move.active = false;
        this.touchControls.move.x = 0;
        this.touchControls.move.y = 0;
    }

    // 結束遊戲
    endGame(winner) {
        this.gameState = 'ended';
        if (this.gameLoop) {
            cancelAnimationFrame(this.gameLoop);
            this.gameLoop = null;
        }
        
        const message = winner === 'player' ? '🎉 你贏了！' : '💀 你輸了！';
        setTimeout(() => {
            alert(message);
        }, 500);
    }

    // 停止遊戲
    stop() {
        this.gameState = 'idle';
        if (this.gameLoop) {
            cancelAnimationFrame(this.gameLoop);
            this.gameLoop = null;
        }
        this.damageTexts = [];
    }
}

