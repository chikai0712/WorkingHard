// 🎬 動畫效果系統

class AnimationManager {
    constructor() {
        this.canvas = document.getElementById('animation-canvas');
        this.ctx = this.canvas.getContext('2d');
        this.particles = [];
        this.floatingTexts = [];
        
        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());
    }
    
    resizeCanvas() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }
    
    // 創建粒子效果
    createParticles(x, y, color, count = 10) {
        for (let i = 0; i < count; i++) {
            this.particles.push({
                x: x,
                y: y,
                vx: (Math.random() - 0.5) * 4,
                vy: (Math.random() - 0.5) * 4 - 2,
                life: 1.0,
                color: color,
                size: Math.random() * 4 + 2
            });
        }
    }
    
    // 創建浮動文字
    createFloatingText(x, y, text, color = '#FFD700') {
        this.floatingTexts.push({
            x: x,
            y: y,
            text: text,
            color: color,
            life: 1.0,
            vy: -2
        });
    }
    
    // 玉米飛行動畫
    animateCornFly(fromElement, toElement, isGood = true) {
        const from = fromElement.getBoundingClientRect();
        const to = toElement.getBoundingClientRect();
        
        const corn = document.createElement('div');
        corn.textContent = isGood ? '🌽' : '🥀';
        corn.style.cssText = `
            position: fixed;
            left: ${from.left + from.width / 2}px;
            top: ${from.top + from.height / 2}px;
            font-size: 30px;
            z-index: 999;
            pointer-events: none;
            transition: all 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        `;
        
        document.body.appendChild(corn);
        
        setTimeout(() => {
            corn.style.left = `${to.left + to.width / 2}px`;
            corn.style.top = `${to.top + to.height / 2}px`;
            corn.style.transform = 'scale(0.5)';
            corn.style.opacity = '0';
        }, 50);
        
        setTimeout(() => {
            corn.remove();
        }, 850);
    }
    
    // 爆米花飛行動畫
    animatePopcornFly(fromElement, toElement) {
        const from = fromElement.getBoundingClientRect();
        const to = toElement.getBoundingClientRect();
        
        const popcorn = document.createElement('div');
        popcorn.textContent = '🍿';
        popcorn.style.cssText = `
            position: fixed;
            left: ${from.left + from.width / 2}px;
            top: ${from.top + from.height / 2}px;
            font-size: 30px;
            z-index: 999;
            pointer-events: none;
            transition: all 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        `;
        
        document.body.appendChild(popcorn);
        
        setTimeout(() => {
            popcorn.style.left = `${to.left + to.width / 2}px`;
            popcorn.style.top = `${to.top + to.height / 2}px`;
            popcorn.style.transform = 'scale(0.5) rotate(360deg)';
            popcorn.style.opacity = '0';
        }, 50);
        
        setTimeout(() => {
            popcorn.remove();
        }, 850);
    }
    
    // 金幣飛行動畫
    animateGoldGain(element, amount) {
        const rect = element.getBoundingClientRect();
        const goldTarget = document.getElementById('gold-value').getBoundingClientRect();
        
        const coin = document.createElement('div');
        coin.textContent = '💰';
        coin.style.cssText = `
            position: fixed;
            left: ${rect.left + rect.width / 2}px;
            top: ${rect.top + rect.height / 2}px;
            font-size: 30px;
            z-index: 999;
            pointer-events: none;
            transition: all 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        `;
        
        document.body.appendChild(coin);
        
        // 創建金額文字
        const text = document.createElement('div');
        text.textContent = amount > 0 ? `+${amount}` : `${amount}`;
        text.style.cssText = `
            position: fixed;
            left: ${rect.left + rect.width / 2}px;
            top: ${rect.top + rect.height / 2 - 40}px;
            font-size: 24px;
            font-weight: bold;
            color: ${amount > 0 ? '#4CAF50' : '#F44336'};
            z-index: 999;
            pointer-events: none;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
            animation: floatUp 1s ease;
        `;
        
        document.body.appendChild(text);
        
        setTimeout(() => {
            coin.style.left = `${goldTarget.left}px`;
            coin.style.top = `${goldTarget.top}px`;
            coin.style.transform = 'scale(0.5)';
            coin.style.opacity = '0';
        }, 50);
        
        setTimeout(() => {
            coin.remove();
            text.remove();
        }, 650);
    }
    
    // 建築閃光效果
    flashBuilding(element) {
        element.classList.add('pulse');
        setTimeout(() => {
            element.classList.remove('pulse');
        }, 500);
    }
    
    // 建築發光效果
    glowBuilding(element, duration = 2000) {
        element.classList.add('glow');
        setTimeout(() => {
            element.classList.remove('glow');
        }, duration);
    }
    
    // 更新動畫
    update(deltaTime) {
        // 清空畫布
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 更新粒子
        for (let i = this.particles.length - 1; i >= 0; i--) {
            const p = this.particles[i];
            
            p.x += p.vx;
            p.y += p.vy;
            p.vy += 0.2; // 重力
            p.life -= deltaTime * 2;
            
            if (p.life <= 0) {
                this.particles.splice(i, 1);
                continue;
            }
            
            // 繪製粒子
            this.ctx.globalAlpha = p.life;
            this.ctx.fillStyle = p.color;
            this.ctx.beginPath();
            this.ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            this.ctx.fill();
        }
        
        // 更新浮動文字
        for (let i = this.floatingTexts.length - 1; i >= 0; i--) {
            const t = this.floatingTexts[i];
            
            t.y += t.vy;
            t.life -= deltaTime;
            
            if (t.life <= 0) {
                this.floatingTexts.splice(i, 1);
                continue;
            }
            
            // 繪製文字
            this.ctx.globalAlpha = t.life;
            this.ctx.fillStyle = t.color;
            this.ctx.font = 'bold 24px Arial';
            this.ctx.textAlign = 'center';
            this.ctx.fillText(t.text, t.x, t.y);
        }
        
        this.ctx.globalAlpha = 1.0;
    }
}

// 添加 CSS 動畫
const style = document.createElement('style');
style.textContent = `
    @keyframes floatUp {
        0% {
            transform: translateY(0);
            opacity: 1;
        }
        100% {
            transform: translateY(-50px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

