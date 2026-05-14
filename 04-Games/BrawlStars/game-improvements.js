// 遊戲改進：基於 Brawl Stars 的遊戲機制

/**
 * 主要改進點：
 * 1. 改進 AI 行為（更智能的追擊和攻擊）
 * 2. 添加自動瞄準系統
 * 3. 改進移動和攻擊的流暢度
 * 4. 添加障礙物和地形
 * 5. 改進視覺反饋
 */

// 改進的 AI 行為類
class ImprovedAI {
    constructor(character) {
        this.character = character;
        this.state = 'idle'; // idle, chase, attack, retreat
        this.lastDecisionTime = 0;
        this.decisionCooldown = 0.5; // 每 0.5 秒重新評估
    }

    // 更新 AI 行為
    update(deltaTime, target, projectiles) {
        this.lastDecisionTime += deltaTime;
        
        if (this.lastDecisionTime >= this.decisionCooldown) {
            this.makeDecision(target, projectiles);
            this.lastDecisionTime = 0;
        }
        
        this.executeBehavior(deltaTime, target, projectiles);
    }

    // 做決策
    makeDecision(target, projectiles) {
        const distance = this.getDistance(this.character, target);
        const healthPercent = this.character.currentHealth / this.character.maxHealth;
        
        // 檢查是否有危險（附近有子彈）
        const dangerNearby = this.checkDanger(projectiles);
        
        // 決策邏輯
        if (dangerNearby && healthPercent < 0.3) {
            // 生命值低且附近有危險，撤退
            this.state = 'retreat';
        } else if (distance > this.character.range * 50) {
            // 距離太遠，追擊
            this.state = 'chase';
        } else if (distance <= this.character.range * 50 && this.character.canAttack) {
            // 在攻擊範圍內且可以攻擊
            this.state = 'attack';
        } else {
            // 保持距離
            this.state = 'maintain';
        }
    }

    // 執行行為
    executeBehavior(deltaTime, target, projectiles) {
        const moveSpeed = this.character.moveSpeed * 60 * deltaTime;
        const distance = this.getDistance(this.character, target);
        
        switch (this.state) {
            case 'chase':
                // 追擊目標
                if (distance > this.character.range * 50) {
                    const angle = Math.atan2(target.y - this.character.y, target.x - this.character.x);
                    this.character.x += Math.cos(angle) * moveSpeed;
                    this.character.y += Math.sin(angle) * moveSpeed;
                    this.character.direction = angle;
                }
                break;
                
            case 'attack':
                // 攻擊目標
                if (this.character.canAttack) {
                    const angle = Math.atan2(target.y - this.character.y, target.x - this.character.x);
                    this.character.direction = angle;
                    // 這裡會觸發攻擊（由主遊戲循環處理）
                    return 'attack';
                }
                break;
                
            case 'retreat':
                // 撤退（遠離目標和危險）
                const retreatAngle = Math.atan2(this.character.y - target.y, this.character.x - target.x);
                this.character.x += Math.cos(retreatAngle) * moveSpeed * 0.5;
                this.character.y += Math.sin(retreatAngle) * moveSpeed * 0.5;
                break;
                
            case 'maintain':
                // 保持距離（移動到最佳攻擊距離）
                const optimalDistance = this.character.range * 40;
                if (distance > optimalDistance + 20) {
                    // 太遠，靠近
                    const angle = Math.atan2(target.y - this.character.y, target.x - this.character.x);
                    this.character.x += Math.cos(angle) * moveSpeed * 0.7;
                    this.character.y += Math.sin(angle) * moveSpeed * 0.7;
                } else if (distance < optimalDistance - 20) {
                    // 太近，後退
                    const angle = Math.atan2(this.character.y - target.y, this.character.x - target.x);
                    this.character.x += Math.cos(angle) * moveSpeed * 0.7;
                    this.character.y += Math.sin(angle) * moveSpeed * 0.7;
                }
                break;
        }
        
        return null;
    }

    // 檢查危險（附近是否有子彈）
    checkDanger(projectiles) {
        const dangerRadius = 80;
        for (const proj of projectiles) {
            if (proj.owner === 'player') {
                const distance = this.getDistance(
                    { x: proj.x, y: proj.y },
                    this.character
                );
                if (distance < dangerRadius) {
                    return true;
                }
            }
        }
        return false;
    }

    getDistance(obj1, obj2) {
        return Math.sqrt(
            Math.pow(obj1.x - obj2.x, 2) + 
            Math.pow(obj1.y - obj2.y, 2)
        );
    }
}

// 自動瞄準系統
class AutoAimSystem {
    constructor(character, targets) {
        this.character = character;
        this.targets = targets;
        this.aimAngle = 0;
    }

    // 找到最近的目標
    findNearestTarget() {
        let nearest = null;
        let minDistance = Infinity;

        for (const target of this.targets) {
            const distance = this.getDistance(this.character, target);
            if (distance <= this.character.range * 50 && distance < minDistance) {
                minDistance = distance;
                nearest = target;
            }
        }

        return nearest;
    }

    // 計算瞄準角度
    calculateAimAngle(target) {
        if (!target) return this.character.direction;
        
        // 預測目標移動方向（簡單預測）
        const dx = target.x - this.character.x;
        const dy = target.y - this.character.y;
        
        // 如果目標在移動，預測未來位置
        if (target.isMoving) {
            const speed = target.moveSpeed * 60 * 0.016; // 假設下一幀的位置
            const predictedX = target.x + Math.cos(target.direction) * speed * 10;
            const predictedY = target.y + Math.sin(target.direction) * speed * 10;
            
            return Math.atan2(predictedY - this.character.y, predictedX - this.character.x);
        }
        
        return Math.atan2(dy, dx);
    }

    getDistance(obj1, obj2) {
        return Math.sqrt(
            Math.pow(obj1.x - obj2.x, 2) + 
            Math.pow(obj1.y - obj2.y, 2)
        );
    }
}

// 障礙物系統
class ObstacleSystem {
    constructor(canvas) {
        this.canvas = canvas;
        this.obstacles = [];
        this.initObstacles();
    }

    // 初始化障礙物
    initObstacles() {
        // 添加一些障礙物
        this.obstacles = [
            { x: 400, y: 200, width: 100, height: 100 },
            { x: 600, y: 400, width: 80, height: 80 },
            { x: 200, y: 500, width: 120, height: 60 }
        ];
    }

    // 檢查碰撞
    checkCollision(x, y, radius) {
        for (const obstacle of this.obstacles) {
            const closestX = Math.max(obstacle.x, Math.min(x, obstacle.x + obstacle.width));
            const closestY = Math.max(obstacle.y, Math.min(y, obstacle.y + obstacle.height));
            
            const distance = Math.sqrt(
                Math.pow(x - closestX, 2) + 
                Math.pow(y - closestY, 2)
            );
            
            if (distance < radius) {
                return true;
            }
        }
        return false;
    }

    // 檢查子彈是否擊中障礙物
    checkProjectileCollision(projectile) {
        for (const obstacle of this.obstacles) {
            if (projectile.x >= obstacle.x && 
                projectile.x <= obstacle.x + obstacle.width &&
                projectile.y >= obstacle.y && 
                projectile.y <= obstacle.y + obstacle.height) {
                return true;
            }
        }
        return false;
    }

    // 繪製障礙物
    draw(ctx) {
        ctx.fillStyle = '#4a5568';
        ctx.strokeStyle = '#2d3748';
        ctx.lineWidth = 3;

        for (const obstacle of this.obstacles) {
            ctx.fillRect(obstacle.x, obstacle.y, obstacle.width, obstacle.height);
            ctx.strokeRect(obstacle.x, obstacle.y, obstacle.width, obstacle.height);
        }
    }
}

// 改進的遊戲系統（擴展現有的 RealtimeBrawlGame）
class EnhancedGameFeatures {
    constructor(game) {
        this.game = game;
        this.obstacleSystem = new ObstacleSystem(game.canvas);
        this.autoAim = null;
        this.enemyAI = null;
    }

    // 初始化
    init() {
        // 初始化自動瞄準
        this.autoAim = new AutoAimSystem(this.game.player, [this.game.enemy]);
        
        // 初始化敵人 AI
        if (this.game.enemy) {
            this.enemyAI = new ImprovedAI(this.game.enemy);
        }
    }

    // 更新（在遊戲循環中調用）
    update(deltaTime) {
        // 更新敵人 AI
        if (this.enemyAI && this.game.enemy) {
            const action = this.enemyAI.update(deltaTime, this.game.player, this.game.projectiles);
            
            if (action === 'attack') {
                this.game.enemyAttack();
            }
        }
        
        // 更新自動瞄準
        if (this.autoAim) {
            const target = this.autoAim.findNearestTarget();
            if (target) {
                this.game.player.direction = this.autoAim.calculateAimAngle(target);
            }
        }
        
        // 檢查障礙物碰撞
        this.checkObstacleCollisions();
    }

    // 檢查障礙物碰撞
    checkObstacleCollisions() {
        // 檢查玩家
        if (this.obstacleSystem.checkCollision(this.game.player.x, this.game.player.y, 40)) {
            // 推回玩家
            this.pushAwayFromObstacles(this.game.player);
        }
        
        // 檢查敵人
        if (this.obstacleSystem.checkCollision(this.game.enemy.x, this.game.enemy.y, 40)) {
            this.pushAwayFromObstacles(this.game.enemy);
        }
        
        // 檢查子彈
        for (let i = this.game.projectiles.length - 1; i >= 0; i--) {
            if (this.obstacleSystem.checkProjectileCollision(this.game.projectiles[i])) {
                this.game.projectiles.splice(i, 1);
            }
        }
    }

    // 推離障礙物
    pushAwayFromObstacles(character) {
        // 簡單的推離邏輯
        for (const obstacle of this.obstacleSystem.obstacles) {
            const closestX = Math.max(obstacle.x, Math.min(character.x, obstacle.x + obstacle.width));
            const closestY = Math.max(obstacle.y, Math.min(character.y, obstacle.y + obstacle.height));
            
            const dx = character.x - closestX;
            const dy = character.y - closestY;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance < 40 && distance > 0) {
                const pushDistance = 40 - distance;
                character.x += (dx / distance) * pushDistance;
                character.y += (dy / distance) * pushDistance;
            }
        }
    }

    // 繪製（在 draw 方法中調用）
    draw(ctx) {
        this.obstacleSystem.draw(ctx);
    }
}

