// AI 角色生成器
class AIGenerator {
    constructor(characterManager) {
        this.characterManager = characterManager;
    }

    // 根據提示詞生成角色（使用本地邏輯模擬 AI）
    async generateCharacter(prompt, style) {
        // 模擬 AI 生成的延遲
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // 根據提示詞和風格生成角色屬性
        const character = this.parsePrompt(prompt, style);
        return character;
    }

    // 解析提示詞並生成角色屬性
    parsePrompt(prompt, style) {
        const lowerPrompt = prompt.toLowerCase();
        
        // 提取關鍵詞
        const hasFire = lowerPrompt.includes('火') || lowerPrompt.includes('fire');
        const hasIce = lowerPrompt.includes('冰') || lowerPrompt.includes('ice');
        const hasLightning = lowerPrompt.includes('雷') || lowerPrompt.includes('lightning') || lowerPrompt.includes('電');
        const hasDark = lowerPrompt.includes('暗') || lowerPrompt.includes('dark') || lowerPrompt.includes('黑');
        const hasLight = lowerPrompt.includes('光') || lowerPrompt.includes('light');
        
        // 根據風格設定基礎屬性
        let baseStats = this.getStyleBaseStats(style);
        
        // 根據關鍵詞調整屬性
        if (lowerPrompt.includes('快') || lowerPrompt.includes('fast') || lowerPrompt.includes('速度')) {
            baseStats.speed = Math.min(100, baseStats.speed + 20);
            baseStats.attack = Math.max(10, baseStats.attack - 5);
        }
        
        if (lowerPrompt.includes('慢') || lowerPrompt.includes('slow')) {
            baseStats.speed = Math.max(20, baseStats.speed - 20);
            baseStats.defense = Math.min(50, baseStats.defense + 10);
        }
        
        if (lowerPrompt.includes('高攻擊') || lowerPrompt.includes('high attack') || lowerPrompt.includes('強攻擊')) {
            baseStats.attack = Math.min(80, baseStats.attack + 20);
        }
        
        if (lowerPrompt.includes('高防禦') || lowerPrompt.includes('high defense') || lowerPrompt.includes('高防')) {
            baseStats.defense = Math.min(50, baseStats.defense + 15);
            baseStats.health = Math.min(250, baseStats.health + 50);
        }
        
        if (lowerPrompt.includes('高生命') || lowerPrompt.includes('high health') || lowerPrompt.includes('高血量')) {
            baseStats.health = Math.min(300, baseStats.health + 80);
        }

        // 生成名稱
        const name = this.generateName(prompt, style);
        
        // 生成描述
        const description = this.generateDescription(prompt, style);
        
        // 生成特殊技能
        const special = this.generateSpecialSkill(prompt, style);
        
        // 生成顏色和 emoji
        const { color, emoji } = this.generateAppearance(hasFire, hasIce, hasLightning, hasDark, hasLight, style);
        
        // 根據風格和提示詞決定攻擊類型和射程
        let attackType = 'ranged';
        let range = 5;
        
        if (style === 'tank' || lowerPrompt.includes('近戰') || lowerPrompt.includes('melee')) {
            attackType = 'melee';
            range = Math.floor(Math.random() * 3) + 2; // 2-4
        } else if (style === 'mage' || style === 'archer' || lowerPrompt.includes('遠程') || lowerPrompt.includes('ranged')) {
            attackType = 'ranged';
            range = Math.floor(Math.random() * 4) + 6; // 6-10
        } else if (lowerPrompt.includes('範圍') || lowerPrompt.includes('area')) {
            attackType = 'area';
            range = Math.floor(Math.random() * 3) + 4; // 4-6
        }
        
        const reloadSpeed = style === 'assassin' ? 0.8 : style === 'tank' ? 1.5 : 1.0;
        const moveSpeed = style === 'assassin' ? 8 : style === 'tank' ? 3 : 5;
        
        return {
            name,
            description,
            health: baseStats.health,
            attack: baseStats.attack,
            defense: baseStats.defense,
            speed: baseStats.speed,
            range,
            attackType,
            reloadSpeed,
            moveSpeed,
            color,
            special,
            specialType: 'damage',
            emoji,
            image: null
        };
    }

    // 根據風格獲取基礎屬性
    getStyleBaseStats(style) {
        const stats = {
            warrior: { health: 150, attack: 30, defense: 15, speed: 50 },
            mage: { health: 100, attack: 40, defense: 10, speed: 50 },
            archer: { health: 120, attack: 35, defense: 12, speed: 70 },
            tank: { health: 200, attack: 20, defense: 30, speed: 30 },
            assassin: { health: 80, attack: 50, defense: 5, speed: 90 }
        };
        return { ...stats[style] || stats.warrior };
    }

    // 生成名稱
    generateName(prompt, style) {
        const styleNames = {
            warrior: ['戰士', '勇士', '劍士'],
            mage: ['法師', '術士', '巫師'],
            archer: ['弓箭手', '遊俠', '獵人'],
            tank: ['坦克', '守衛', '盾衛'],
            assassin: ['刺客', '殺手', '暗殺者']
        };
        
        const prefixes = ['火焰', '冰霜', '雷電', '暗影', '光明', '風暴', '大地', '天空'];
        const styleName = styleNames[style]?.[Math.floor(Math.random() * styleNames[style].length)] || '戰士';
        
        // 從提示詞中提取關鍵詞作為前綴
        const lowerPrompt = prompt.toLowerCase();
        let prefix = '';
        
        if (lowerPrompt.includes('火') || lowerPrompt.includes('fire')) prefix = '火焰';
        else if (lowerPrompt.includes('冰') || lowerPrompt.includes('ice')) prefix = '冰霜';
        else if (lowerPrompt.includes('雷') || lowerPrompt.includes('lightning')) prefix = '雷電';
        else if (lowerPrompt.includes('暗') || lowerPrompt.includes('dark')) prefix = '暗影';
        else if (lowerPrompt.includes('光') || lowerPrompt.includes('light')) prefix = '光明';
        else prefix = prefixes[Math.floor(Math.random() * prefixes.length)];
        
        return prefix + styleName;
    }

    // 生成描述
    generateDescription(prompt, style) {
        const styleDescs = {
            warrior: '強大的近戰戰士',
            mage: '精通魔法的法師',
            archer: '精準的遠程射手',
            tank: '防禦力極高的守護者',
            assassin: '速度極快的暗殺者'
        };
        
        const baseDesc = styleDescs[style] || '強大的戰士';
        return prompt.trim() || baseDesc;
    }

    // 生成特殊技能
    generateSpecialSkill(prompt, style) {
        const lowerPrompt = prompt.toLowerCase();
        const skills = {
            fire: ['火焰斬擊', '烈焰風暴', '火球術'],
            ice: ['冰霜風暴', '冰凍斬擊', '寒冰箭'],
            lightning: ['雷電衝擊', '閃電鏈', '雷霆一擊'],
            dark: ['暗影突襲', '暗黑之刃', '影分身'],
            light: ['聖光護體', '光明斬', '神聖審判']
        };
        
        let skillList = [];
        if (lowerPrompt.includes('火') || lowerPrompt.includes('fire')) skillList = skills.fire;
        else if (lowerPrompt.includes('冰') || lowerPrompt.includes('ice')) skillList = skills.ice;
        else if (lowerPrompt.includes('雷') || lowerPrompt.includes('lightning')) skillList = skills.lightning;
        else if (lowerPrompt.includes('暗') || lowerPrompt.includes('dark')) skillList = skills.dark;
        else if (lowerPrompt.includes('光') || lowerPrompt.includes('light')) skillList = skills.light;
        else skillList = ['強力攻擊', '護體術', '疾風斬'];
        
        return skillList[Math.floor(Math.random() * skillList.length)];
    }

    // 生成外觀（顏色和 emoji）
    generateAppearance(hasFire, hasIce, hasLightning, hasDark, hasLight, style) {
        const appearances = {
            fire: { color: '#ff6b6b', emoji: '🔥' },
            ice: { color: '#74b9ff', emoji: '❄️' },
            lightning: { color: '#fdcb6e', emoji: '⚡' },
            dark: { color: '#636e72', emoji: '🌑' },
            light: { color: '#ffeaa7', emoji: '✨' }
        };
        
        if (hasFire) return appearances.fire;
        if (hasIce) return appearances.ice;
        if (hasLightning) return appearances.lightning;
        if (hasDark) return appearances.dark;
        if (hasLight) return appearances.light;
        
        // 預設根據風格
        const styleAppearances = {
            warrior: { color: '#ff6b6b', emoji: '⚔️' },
            mage: { color: '#74b9ff', emoji: '🔮' },
            archer: { color: '#51cf66', emoji: '🏹' },
            tank: { color: '#fd79a8', emoji: '🛡️' },
            assassin: { color: '#636e72', emoji: '🗡️' }
        };
        
        return styleAppearances[style] || { color: '#667eea', emoji: '⚔️' };
    }
}

