// 角色管理系統
class CharacterManager {
    constructor() {
        this.characters = this.loadCharacters();
        this.selectedCharacter = null;
    }

    // 從 localStorage 載入角色
    loadCharacters() {
        const saved = localStorage.getItem('brawlStarsCharacters');
        if (saved) {
            return JSON.parse(saved);
        }
        // 預設角色
        return this.getDefaultCharacters();
    }

    // 保存角色到 localStorage
    saveCharacters() {
        localStorage.setItem('brawlStarsCharacters', JSON.stringify(this.characters));
    }

    // 預設角色
    getDefaultCharacters() {
        return [
            {
                id: '1',
                name: '火焰戰士',
                description: '擁有強大火焰能力的近戰戰士',
                health: 150,
                attack: 30,
                defense: 15,
                speed: 60,
                range: 3, // 射程（1-10）
                attackType: 'melee', // melee | ranged | area
                reloadSpeed: 1.0, // 裝彈速度（秒）
                moveSpeed: 5, // 移動速度（像素/幀）
                color: '#ff6b6b',
                special: '火焰斬擊',
                specialType: 'damage',
                image: null,
                emoji: '🔥'
            },
            {
                id: '2',
                name: '冰霜法師',
                description: '精通冰系魔法的遠程法師',
                health: 100,
                attack: 40,
                defense: 10,
                speed: 50,
                range: 8, // 遠程
                attackType: 'ranged',
                reloadSpeed: 1.2,
                moveSpeed: 4,
                color: '#74b9ff',
                special: '冰霜風暴',
                specialType: 'control',
                image: null,
                emoji: '❄️'
            },
            {
                id: '3',
                name: '暗影刺客',
                description: '速度極快的暗殺專家',
                health: 80,
                attack: 50,
                defense: 5,
                speed: 90,
                range: 6, // 中距離
                attackType: 'ranged',
                reloadSpeed: 0.8,
                moveSpeed: 8,
                color: '#636e72',
                special: '暗影突襲',
                specialType: 'dash',
                image: null,
                emoji: '🗡️'
            },
            {
                id: '4',
                name: '鋼鐵坦克',
                description: '防禦力極高的重裝戰士',
                health: 200,
                attack: 20,
                defense: 30,
                speed: 30,
                range: 2, // 近戰
                attackType: 'area',
                reloadSpeed: 1.5,
                moveSpeed: 3,
                color: '#fd79a8',
                special: '鋼鐵護盾',
                specialType: 'defense',
                image: null,
                emoji: '🛡️'
            }
        ];
    }

    // 獲取所有角色
    getAllCharacters() {
        return this.characters;
    }

    // 根據 ID 獲取角色
    getCharacterById(id) {
        return this.characters.find(char => char.id === id);
    }

    // 新增角色
    addCharacter(characterData) {
        const newCharacter = {
            id: Date.now().toString(),
            // 設置默認值
            range: characterData.range || 5,
            attackType: characterData.attackType || 'ranged',
            reloadSpeed: characterData.reloadSpeed || 1.0,
            moveSpeed: characterData.moveSpeed || 5,
            specialType: characterData.specialType || 'damage',
            ...characterData,
            emoji: characterData.emoji || '⚔️'
        };
        this.characters.push(newCharacter);
        this.saveCharacters();
        return newCharacter;
    }

    // 更新角色
    updateCharacter(id, characterData) {
        const index = this.characters.findIndex(char => char.id === id);
        if (index !== -1) {
            this.characters[index] = {
                ...this.characters[index],
                ...characterData
            };
            this.saveCharacters();
            return this.characters[index];
        }
        return null;
    }

    // 刪除角色
    deleteCharacter(id) {
        const index = this.characters.findIndex(char => char.id === id);
        if (index !== -1) {
            this.characters.splice(index, 1);
            this.saveCharacters();
            return true;
        }
        return false;
    }

    // 搜尋角色
    searchCharacters(query) {
        const lowerQuery = query.toLowerCase();
        return this.characters.filter(char => 
            char.name.toLowerCase().includes(lowerQuery) ||
            char.description.toLowerCase().includes(lowerQuery)
        );
    }
}

// 攻擊類型名稱映射
function getAttackTypeName(type) {
    const names = {
        'melee': '近戰',
        'ranged': '遠程',
        'area': '範圍'
    };
    return names[type] || type;
}

// 角色卡片渲染
class CharacterRenderer {
    constructor(characterManager) {
        this.characterManager = characterManager;
    }

    // 渲染角色卡片
    renderCharacterCard(character, container, showActions = false) {
        const card = document.createElement('div');
        card.className = 'character-card';
        card.dataset.characterId = character.id;
        
        const avatarStyle = character.image 
            ? `background-image: url('${character.image}'); background-size: cover;`
            : `background-color: ${character.color};`;
        
        card.innerHTML = `
            <div class="character-avatar" style="${avatarStyle}">
                ${character.image ? '' : (character.emoji || '⚔️')}
            </div>
            <div class="character-name">${character.name}</div>
            <div class="character-stats">
                <div class="stat-item">
                    <span>❤️ 生命:</span>
                    <span>${character.health}</span>
                </div>
                <div class="stat-item">
                    <span>⚔️ 攻擊:</span>
                    <span>${character.attack}</span>
                </div>
                <div class="stat-item">
                    <span>🛡️ 防禦:</span>
                    <span>${character.defense}</span>
                </div>
                <div class="stat-item">
                    <span>⚡ 速度:</span>
                    <span>${character.speed}</span>
                </div>
            </div>
            ${character.special ? `<div style="margin-top: 0.5rem; font-size: 0.85rem; color: #667eea;">✨ ${character.special}</div>` : ''}
            ${showActions ? `
                <div class="character-actions">
                    <button class="btn btn-primary edit-btn" style="font-size: 0.8rem;">✏️ 編輯</button>
                    <button class="btn btn-danger delete-btn" style="font-size: 0.8rem;">🗑️ 刪除</button>
                </div>
            ` : ''}
        `;
        
        container.appendChild(card);
        return card;
    }

    // 渲染角色網格
    renderCharacterGrid(characters, container, showActions = false, onSelect = null) {
        container.innerHTML = '';
        characters.forEach(character => {
            const card = this.renderCharacterCard(character, container, showActions);
            
            if (!showActions && onSelect) {
                card.addEventListener('click', () => {
                    // 移除其他選中狀態
                    container.querySelectorAll('.character-card').forEach(c => {
                        c.classList.remove('selected');
                    });
                    card.classList.add('selected');
                    onSelect(character);
                });
            }
        });
    }
}

