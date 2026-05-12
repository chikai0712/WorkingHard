// ===================================
// 音效管理系統
// ===================================

class AudioManager {
    constructor() {
        this.sounds = {};
        this.bgm = null;
        this.isMuted = false;
        this.bgmVolume = 0.3;
        this.sfxVolume = 0.5;
        
        // 使用 Web Audio API
        this.audioContext = null;
        
        // 初始化音效（使用音頻合成）
        this.initSynthSounds();
    }
    
    initSynthSounds() {
        // 由於沒有實際音頻文件，我們使用 Web Audio API 合成音效
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        } catch (e) {
            console.warn('Web Audio API 不支援');
        }
    }
    
    // 播放音效
    playSound(soundName) {
        if (this.isMuted || !this.audioContext) return;
        
        switch(soundName) {
            case 'cornCatch':
                this.playCornCatch();
                break;
            case 'goldenCorn':
                this.playGoldenCorn();
                break;
            case 'badCorn':
                this.playBadCorn();
                break;
            case 'heat':
                this.playHeat();
                break;
            case 'explode':
                this.playExplode();
                break;
            case 'perfect':
                this.playPerfect();
                break;
            case 'great':
                this.playGreat();
                break;
            case 'good':
                this.playGood();
                break;
            case 'miss':
                this.playMiss();
                break;
            case 'boxFull':
                this.playBoxFull();
                break;
            case 'customerHappy':
                this.playCustomerHappy();
                break;
            case 'customerAngry':
                this.playCustomerAngry();
                break;
            case 'feverStart':
                this.playFeverStart();
                break;
            case 'combo':
                this.playCombo();
                break;
        }
    }
    
    // 玉米接住音效
    playCornCatch() {
        this.playTone(800, 0.1, 'sine', 0.3);
    }
    
    // 金色玉米音效
    playGoldenCorn() {
        this.playTone(1200, 0.2, 'sine', 0.4);
        setTimeout(() => this.playTone(1600, 0.2, 'sine', 0.4), 100);
    }
    
    // 壞玉米音效
    playBadCorn() {
        this.playTone(200, 0.3, 'sawtooth', 0.5);
    }
    
    // 加熱音效
    playHeat() {
        this.playTone(400, 0.05, 'sine', 0.2);
    }
    
    // 爆炸音效
    playExplode() {
        this.playTone(100, 0.1, 'sawtooth', 0.6);
        setTimeout(() => this.playTone(200, 0.2, 'sine', 0.5), 50);
        setTimeout(() => this.playTone(400, 0.3, 'sine', 0.4), 100);
    }
    
    // Perfect 音效
    playPerfect() {
        this.playTone(1000, 0.1, 'sine', 0.5);
        setTimeout(() => this.playTone(1200, 0.1, 'sine', 0.5), 80);
        setTimeout(() => this.playTone(1500, 0.2, 'sine', 0.5), 160);
    }
    
    // Great 音效
    playGreat() {
        this.playTone(900, 0.1, 'sine', 0.4);
        setTimeout(() => this.playTone(1100, 0.2, 'sine', 0.4), 80);
    }
    
    // Good 音效
    playGood() {
        this.playTone(800, 0.2, 'sine', 0.3);
    }
    
    // Miss 音效
    playMiss() {
        this.playTone(300, 0.3, 'sawtooth', 0.4);
    }
    
    // 箱子裝滿音效
    playBoxFull() {
        this.playTone(600, 0.1, 'square', 0.4);
        setTimeout(() => this.playTone(800, 0.2, 'square', 0.4), 100);
    }
    
    // 客人開心音效
    playCustomerHappy() {
        this.playTone(1000, 0.1, 'sine', 0.5);
        setTimeout(() => this.playTone(1200, 0.1, 'sine', 0.5), 100);
        setTimeout(() => this.playTone(1500, 0.1, 'sine', 0.5), 200);
        setTimeout(() => this.playTone(2000, 0.2, 'sine', 0.5), 300);
    }
    
    // 客人生氣音效
    playCustomerAngry() {
        this.playTone(200, 0.5, 'sawtooth', 0.5);
    }
    
    // Fever Time 開始音效
    playFeverStart() {
        for (let i = 0; i < 5; i++) {
            setTimeout(() => {
                this.playTone(1000 + i * 200, 0.1, 'sine', 0.6);
            }, i * 100);
        }
    }
    
    // 連擊音效
    playCombo() {
        this.playTone(1500, 0.1, 'sine', 0.4);
    }
    
    // 基礎音調播放
    playTone(frequency, duration, type = 'sine', volume = 0.5) {
        if (!this.audioContext) return;
        
        const oscillator = this.audioContext.createOscillator();
        const gainNode = this.audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(this.audioContext.destination);
        
        oscillator.frequency.value = frequency;
        oscillator.type = type;
        
        gainNode.gain.setValueAtTime(volume * this.sfxVolume, this.audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + duration);
        
        oscillator.start(this.audioContext.currentTime);
        oscillator.stop(this.audioContext.currentTime + duration);
    }
    
    // 播放背景音樂（簡單的旋律循環）
    playBGM() {
        if (this.isMuted || !this.audioContext) return;
        
        // 簡單的旋律音符
        const melody = [
            { freq: 523, duration: 0.3 }, // C
            { freq: 587, duration: 0.3 }, // D
            { freq: 659, duration: 0.3 }, // E
            { freq: 698, duration: 0.3 }, // F
            { freq: 784, duration: 0.3 }, // G
            { freq: 659, duration: 0.3 }, // E
            { freq: 523, duration: 0.6 }, // C
        ];
        
        let currentTime = 0;
        melody.forEach(note => {
            setTimeout(() => {
                if (!this.isMuted) {
                    this.playTone(note.freq, note.duration, 'sine', 0.1);
                }
            }, currentTime * 1000);
            currentTime += note.duration;
        });
        
        // 循環播放
        setTimeout(() => this.playBGM(), currentTime * 1000 + 1000);
    }
    
    // 停止背景音樂
    stopBGM() {
        this.isMuted = true;
    }
    
    // 切換靜音
    toggleMute() {
        this.isMuted = !this.isMuted;
        return this.isMuted;
    }
    
    // 設置音量
    setVolume(type, volume) {
        if (type === 'bgm') {
            this.bgmVolume = volume;
        } else if (type === 'sfx') {
            this.sfxVolume = volume;
        }
    }
}

// 創建全局音效管理器
const audioManager = new AudioManager();

// 導出供其他模組使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AudioManager;
}

