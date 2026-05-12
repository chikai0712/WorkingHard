// ===================================
// 視覺特效系統
// ===================================

class EffectsManager {
    constructor() {
        this.particles = [];
        this.canvas = null;
        this.ctx = null;
        this.animationFrame = null;
        
        this.init();
    }
    
    init() {
        // 創建特效畫布
        this.canvas = document.createElement('canvas');
        this.canvas.id = 'effects-canvas';
        this.canvas.style.position = 'absolute';
        this.canvas.style.top = '0';
        this.canvas.style.left = '0';
        this.canvas.style.width = '100%';
        this.canvas.style.height = '100%';
        this.canvas.style.pointerEvents = 'none';
        this.canvas.style.zIndex = '999';
        
        this.ctx = this.canvas.getContext('2d');
        
        // 添加到遊戲容器
        const gameContainer = document.getElementById('game-container');
        if (gameContainer) {
            gameContainer.appendChild(this.canvas);
            this.resize();
        }
        
        // 監聽視窗大小變化
        window.addEventListener('resize', () => this.resize());
        
        // 開始動畫循環
        this.animate();
    }
    
    resize() {
        const rect = this.canvas.getBoundingClientRect();
        this.canvas.width = rect.width;
        this.canvas.height = rect.height;
    }
    
    animate() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 更新和繪製所有粒子
        this.particles = this.particles.filter(particle => {
            particle.update();
            particle.draw(this.ctx);
            return particle.life > 0;
        });
        
        this.animationFrame = requestAnimationFrame(() => this.animate());
    }
    
    // 創建粒子爆炸效果
    createExplosion(x, y, color = '#FFD700', count = 20) {
        for (let i = 0; i < count; i++) {
            const angle = (Math.PI * 2 * i) / count;
            const speed = 2 + Math.random() * 3;
            
            this.particles.push(new Particle({
                x: x,
                y: y,
                vx: Math.cos(angle) * speed,
                vy: Math.sin(angle) * speed,
                color: color,
                size: 3 + Math.random() * 3,
                life: 1,
                decay: 0.02
            }));
        }
    }
    
    // 創建星星效果
    createStars(x, y, count = 10) {
        for (let i = 0; i < count; i++) {
            this.particles.push(new StarParticle({
                x: x + (Math.random() - 0.5) * 100,
                y: y + (Math.random() - 0.5) * 100,
                vx: (Math.random() - 0.5) * 2,
                vy: -Math.random() * 3,
                color: ['#FFD700', '#FFA500', '#FF69B4'][Math.floor(Math.random() * 3)],
                size: 4 + Math.random() * 4,
                life: 1,
                decay: 0.015
            }));
        }
    }
    
    // 創建愛心效果
    createHearts(x, y, count = 5) {
        for (let i = 0; i < count; i++) {
            this.particles.push(new HeartParticle({
                x: x + (Math.random() - 0.5) * 50,
                y: y,
                vx: (Math.random() - 0.5) * 1,
                vy: -1 - Math.random() * 2,
                color: '#FF69B4',
                size: 10 + Math.random() * 10,
                life: 1,
                decay: 0.01
            }));
        }
    }
    
    // 創建彩虹軌跡
    createRainbowTrail(x, y) {
        const colors = ['#FF0000', '#FF7F00', '#FFFF00', '#00FF00', '#0000FF', '#4B0082', '#9400D3'];
        
        for (let i = 0; i < 7; i++) {
            this.particles.push(new Particle({
                x: x,
                y: y,
                vx: (Math.random() - 0.5) * 2,
                vy: (Math.random() - 0.5) * 2,
                color: colors[i],
                size: 5,
                life: 1,
                decay: 0.02
            }));
        }
    }
    
    // 創建文字特效
    createTextEffect(text, x, y, color = '#FFD700') {
        const textParticle = new TextParticle({
            text: text,
            x: x,
            y: y,
            vy: -2,
            color: color,
            size: 30,
            life: 1,
            decay: 0.015
        });
        
        this.particles.push(textParticle);
    }
    
    // 創建閃光效果
    createFlash(x, y, color = '#FFFFFF') {
        this.particles.push(new FlashParticle({
            x: x,
            y: y,
            color: color,
            size: 50,
            life: 1,
            decay: 0.1
        }));
    }
    
    // 創建連擊特效
    createComboEffect(x, y, combo) {
        // 爆炸效果
        this.createExplosion(x, y, '#FFD700', 30);
        
        // 文字效果
        this.createTextEffect(`${combo} COMBO!`, x, y, '#FFD700');
        
        // 星星效果
        this.createStars(x, y, 15);
    }
    
    // 創建 Fever Time 特效
    createFeverEffect() {
        const canvas = this.canvas;
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        
        // 從中心向外爆發
        for (let i = 0; i < 50; i++) {
            const angle = (Math.PI * 2 * i) / 50;
            const speed = 5 + Math.random() * 5;
            
            this.particles.push(new Particle({
                x: centerX,
                y: centerY,
                vx: Math.cos(angle) * speed,
                vy: Math.sin(angle) * speed,
                color: ['#FFD700', '#FF69B4', '#00FFFF'][Math.floor(Math.random() * 3)],
                size: 5 + Math.random() * 5,
                life: 1,
                decay: 0.01
            }));
        }
        
        // 星星效果
        this.createStars(centerX, centerY, 30);
    }
    
    // 清除所有特效
    clear() {
        this.particles = [];
    }
}

// 粒子基類
class Particle {
    constructor(options) {
        this.x = options.x || 0;
        this.y = options.y || 0;
        this.vx = options.vx || 0;
        this.vy = options.vy || 0;
        this.color = options.color || '#FFFFFF';
        this.size = options.size || 5;
        this.life = options.life || 1;
        this.decay = options.decay || 0.02;
        this.gravity = options.gravity || 0.1;
    }
    
    update() {
        this.x += this.vx;
        this.y += this.vy;
        this.vy += this.gravity;
        this.life -= this.decay;
    }
    
    draw(ctx) {
        ctx.save();
        ctx.globalAlpha = this.life;
        ctx.fillStyle = this.color;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
    }
}

// 星星粒子
class StarParticle extends Particle {
    draw(ctx) {
        ctx.save();
        ctx.globalAlpha = this.life;
        ctx.fillStyle = this.color;
        
        // 繪製星星
        const spikes = 5;
        const outerRadius = this.size;
        const innerRadius = this.size / 2;
        
        ctx.beginPath();
        for (let i = 0; i < spikes * 2; i++) {
            const radius = i % 2 === 0 ? outerRadius : innerRadius;
            const angle = (Math.PI * i) / spikes;
            const x = this.x + Math.cos(angle) * radius;
            const y = this.y + Math.sin(angle) * radius;
            
            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        }
        ctx.closePath();
        ctx.fill();
        
        ctx.restore();
    }
}

// 愛心粒子
class HeartParticle extends Particle {
    draw(ctx) {
        ctx.save();
        ctx.globalAlpha = this.life;
        ctx.fillStyle = this.color;
        
        // 繪製愛心
        const size = this.size;
        ctx.beginPath();
        ctx.moveTo(this.x, this.y + size / 4);
        ctx.bezierCurveTo(
            this.x, this.y,
            this.x - size / 2, this.y,
            this.x - size / 2, this.y + size / 4
        );
        ctx.bezierCurveTo(
            this.x - size / 2, this.y + size / 2,
            this.x, this.y + size * 0.75,
            this.x, this.y + size
        );
        ctx.bezierCurveTo(
            this.x, this.y + size * 0.75,
            this.x + size / 2, this.y + size / 2,
            this.x + size / 2, this.y + size / 4
        );
        ctx.bezierCurveTo(
            this.x + size / 2, this.y,
            this.x, this.y,
            this.x, this.y + size / 4
        );
        ctx.fill();
        
        ctx.restore();
    }
}

// 文字粒子
class TextParticle extends Particle {
    constructor(options) {
        super(options);
        this.text = options.text || '';
        this.gravity = 0;
    }
    
    draw(ctx) {
        ctx.save();
        ctx.globalAlpha = this.life;
        ctx.fillStyle = this.color;
        ctx.font = `bold ${this.size}px Arial`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        
        // 添加描邊
        ctx.strokeStyle = '#000000';
        ctx.lineWidth = 3;
        ctx.strokeText(this.text, this.x, this.y);
        ctx.fillText(this.text, this.x, this.y);
        
        ctx.restore();
    }
}

// 閃光粒子
class FlashParticle extends Particle {
    constructor(options) {
        super(options);
        this.gravity = 0;
        this.vx = 0;
        this.vy = 0;
    }
    
    update() {
        this.size += 5;
        this.life -= this.decay;
    }
    
    draw(ctx) {
        ctx.save();
        ctx.globalAlpha = this.life * 0.5;
        
        // 創建徑向漸變
        const gradient = ctx.createRadialGradient(
            this.x, this.y, 0,
            this.x, this.y, this.size
        );
        gradient.addColorStop(0, this.color);
        gradient.addColorStop(1, 'transparent');
        
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();
        
        ctx.restore();
    }
}

// 創建全局特效管理器
const effectsManager = new EffectsManager();

// 導出供其他模組使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EffectsManager;
}

