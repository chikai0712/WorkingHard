// 🔊 音效系統

class AudioManager {
    constructor() {
        this.audioContext = null;
        this.muted = false;
        this.volume = 0.3;
        
        // 初始化 Web Audio API
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        } catch (e) {
            console.warn('Web Audio API not supported');
        }
    }
    
    // 播放音效
    playSound(type) {
        if (this.muted || !this.audioContext) return;
        
        const sounds = {
            produce: { freq: 440, duration: 0.1 },      // 生產玉米
            sell: { freq: 523, duration: 0.15 },        // 賣出
            cook: { freq: 659, duration: 0.2 },         // 烤製
            deliver: { freq: 784, duration: 0.15 },     // 外送
            coin: { freq: 880, duration: 0.1 },         // 金幣
            unlock: { freq: 1047, duration: 0.3 },      // 解鎖
            upgrade: { freq: 1175, duration: 0.25 },    // 升級
            build: { freq: 698, duration: 0.2 },        // 建造
            error: { freq: 220, duration: 0.2 },        // 錯誤
            bad: { freq: 196, duration: 0.15 }          // 壞玉米
        };
        
        const sound = sounds[type];
        if (!sound) return;
        
        this.playTone(sound.freq, sound.duration);
    }
    
    // 播放音調
    playTone(frequency, duration) {
        const oscillator = this.audioContext.createOscillator();
        const gainNode = this.audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(this.audioContext.destination);
        
        oscillator.frequency.value = frequency;
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(this.volume, this.audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + duration);
        
        oscillator.start(this.audioContext.currentTime);
        oscillator.stop(this.audioContext.currentTime + duration);
    }
    
    // 播放成功音效（和弦）
    playSuccess() {
        if (this.muted || !this.audioContext) return;
        
        const notes = [523, 659, 784]; // C E G
        notes.forEach((freq, index) => {
            setTimeout(() => {
                this.playTone(freq, 0.2);
            }, index * 100);
        });
    }
    
    // 播放失敗音效
    playFailure() {
        if (this.muted || !this.audioContext) return;
        
        this.playTone(392, 0.1);
        setTimeout(() => this.playTone(349, 0.2), 100);
    }
    
    // 切換靜音
    toggleMute() {
        this.muted = !this.muted;
        return this.muted;
    }
    
    // 設定音量
    setVolume(volume) {
        this.volume = Math.max(0, Math.min(1, volume));
    }
}

