// 主應用程式
const characterManager = new CharacterManager();
const characterRenderer = new CharacterRenderer(characterManager);
const aiGenerator = new AIGenerator(characterManager);
let game = null; // 使用 RealtimeBrawlGame 而不是 BrawlGame

// DOM 元素
const characterSelection = document.getElementById('characterSelection');
const gameArena = document.getElementById('gameArena');
const characterGrid = document.getElementById('characterGrid');
const managerModal = document.getElementById('characterManagerModal');
const formModal = document.getElementById('characterFormModal');
const aiModal = document.getElementById('aiGenerateModal');

let selectedCharacter = null;
let editingCharacterId = null;

// 初始化
function init() {
    renderCharacterSelection();
    setupEventListeners();
}

// 渲染角色選擇界面
function renderCharacterSelection() {
    const characters = characterManager.getAllCharacters();
    characterRenderer.renderCharacterGrid(characters, characterGrid, false, (character) => {
        selectedCharacter = character;
    });
}

// 設置事件監聽器
function setupEventListeners() {
    // Header 按鈕
    document.getElementById('characterManagerBtn').addEventListener('click', () => {
        openCharacterManager();
    });
    
    document.getElementById('aiGenerateBtn').addEventListener('click', () => {
        openAIGenerator();
    });
    
    document.getElementById('startGameBtn').addEventListener('click', () => {
        if (selectedCharacter) {
            startGame();
        } else {
            alert('請先選擇一個角色！');
        }
    });
    
    
    // Modal 關閉按鈕
    document.getElementById('closeManagerBtn').addEventListener('click', () => {
        closeModal(managerModal);
    });
    
    document.getElementById('closeFormBtn').addEventListener('click', () => {
        closeModal(formModal);
    });
    
    document.getElementById('closeAIBtn').addEventListener('click', () => {
        closeModal(aiModal);
    });
    
    // 角色管理
    document.getElementById('addCharacterBtn').addEventListener('click', () => {
        openCharacterForm();
    });
    
    document.getElementById('characterSearch').addEventListener('input', (e) => {
        const query = e.target.value;
        const results = query ? characterManager.searchCharacters(query) : characterManager.getAllCharacters();
        renderManagerGrid(results);
    });
    
    // 角色表單
    document.getElementById('characterForm').addEventListener('submit', (e) => {
        e.preventDefault();
        saveCharacter();
    });
    
    document.getElementById('cancelFormBtn').addEventListener('click', () => {
        closeModal(formModal);
        resetForm();
    });
    
    // AI 生成
    document.getElementById('generateCharacterBtn').addEventListener('click', () => {
        generateCharacter();
    });
    
    document.getElementById('saveGeneratedBtn').addEventListener('click', () => {
        saveGeneratedCharacter();
    });
    
    document.getElementById('regenerateBtn').addEventListener('click', () => {
        generateCharacter();
    });
    
    // 遊戲控制（即時戰鬥不需要這些按鈕，但保留特殊技能）
    document.getElementById('specialBtn').addEventListener('click', () => {
        if (game && game.player) {
            // 特殊技能可以在這裡實現
            alert('特殊技能功能開發中...');
        }
    });
    
    document.getElementById('endGameBtn').addEventListener('click', () => {
        endGame();
    });
    
    // 點擊模態框外部關閉
    [managerModal, formModal, aiModal].forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal(modal);
            }
        });
    });
}

// 打開角色管理器
function openCharacterManager() {
    renderManagerGrid();
    openModal(managerModal);
}

// 渲染管理界面網格
function renderManagerGrid(characters = null) {
    const grid = document.getElementById('managerCharacterGrid');
    const chars = characters || characterManager.getAllCharacters();
    characterRenderer.renderCharacterGrid(chars, grid, true);
    
    // 添加編輯和刪除事件
    grid.querySelectorAll('.edit-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const card = btn.closest('.character-card');
            const id = card.dataset.characterId;
            editCharacter(id);
        });
    });
    
    grid.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const card = btn.closest('.character-card');
            const id = card.dataset.characterId;
            deleteCharacter(id);
        });
    });
}

// 打開角色表單
function openCharacterForm(character = null) {
    editingCharacterId = character ? character.id : null;
    document.getElementById('formTitle').textContent = character ? '✏️ 編輯角色' : '➕ 新增角色';
    
    if (character) {
        document.getElementById('charId').value = character.id;
        document.getElementById('charName').value = character.name;
        document.getElementById('charDescription').value = character.description || '';
        document.getElementById('charHealth').value = character.health;
        document.getElementById('charAttack').value = character.attack;
        document.getElementById('charDefense').value = character.defense;
        document.getElementById('charSpeed').value = character.speed;
        document.getElementById('charRange').value = character.range || 5;
        document.getElementById('charAttackType').value = character.attackType || 'ranged';
        document.getElementById('charReloadSpeed').value = character.reloadSpeed || 1.0;
        document.getElementById('charMoveSpeed').value = character.moveSpeed || 5;
        document.getElementById('charColor').value = character.color;
        document.getElementById('charSpecial').value = character.special || '';
        document.getElementById('charImage').value = character.image || '';
    } else {
        resetForm();
    }
    
    openModal(formModal);
}

// 重置表單
function resetForm() {
    document.getElementById('characterForm').reset();
    document.getElementById('charId').value = '';
    editingCharacterId = null;
}

// 保存角色
function saveCharacter() {
    const formData = {
        name: document.getElementById('charName').value,
        description: document.getElementById('charDescription').value,
        health: parseInt(document.getElementById('charHealth').value),
        attack: parseInt(document.getElementById('charAttack').value),
        defense: parseInt(document.getElementById('charDefense').value),
        speed: parseInt(document.getElementById('charSpeed').value),
        range: parseInt(document.getElementById('charRange').value),
        attackType: document.getElementById('charAttackType').value,
        reloadSpeed: parseFloat(document.getElementById('charReloadSpeed').value),
        moveSpeed: parseInt(document.getElementById('charMoveSpeed').value),
        color: document.getElementById('charColor').value,
        special: document.getElementById('charSpecial').value,
        image: document.getElementById('charImage').value || null
    };
    
    if (editingCharacterId) {
        characterManager.updateCharacter(editingCharacterId, formData);
    } else {
        characterManager.addCharacter(formData);
    }
    
    closeModal(formModal);
    resetForm();
    renderCharacterSelection();
    renderManagerGrid();
}

// 編輯角色
function editCharacter(id) {
    const character = characterManager.getCharacterById(id);
    if (character) {
        openCharacterForm(character);
    }
}

// 刪除角色
function deleteCharacter(id) {
    if (confirm('確定要刪除這個角色嗎？')) {
        characterManager.deleteCharacter(id);
        renderManagerGrid();
        renderCharacterSelection();
    }
}

// 打開 AI 生成器
function openAIGenerator() {
    document.getElementById('aiPrompt').value = '';
    document.getElementById('aiStyle').value = 'warrior';
    document.getElementById('aiResult').classList.add('hidden');
    document.getElementById('aiLoading').classList.add('hidden');
    openModal(aiModal);
}

let generatedCharacter = null;

// 生成角色
async function generateCharacter() {
    const prompt = document.getElementById('aiPrompt').value;
    const style = document.getElementById('aiStyle').value;
    
    if (!prompt.trim()) {
        alert('請輸入角色描述！');
        return;
    }
    
    document.getElementById('aiLoading').classList.remove('hidden');
    document.getElementById('aiResult').classList.add('hidden');
    
    try {
        generatedCharacter = await aiGenerator.generateCharacter(prompt, style);
        displayGeneratedCharacter(generatedCharacter);
        document.getElementById('aiLoading').classList.add('hidden');
        document.getElementById('aiResult').classList.remove('hidden');
    } catch (error) {
        console.error('生成失敗:', error);
        alert('生成角色失敗，請重試');
        document.getElementById('aiLoading').classList.add('hidden');
    }
}

// 顯示生成的角色
function displayGeneratedCharacter(character) {
    const preview = document.getElementById('generatedCharacterPreview');
    preview.innerHTML = `
        <div class="character-card">
            <div class="character-avatar" style="background-color: ${character.color};">
                ${character.emoji}
            </div>
            <div class="character-name">${character.name}</div>
            <div style="margin: 0.5rem 0; color: #666;">${character.description}</div>
            <div class="character-stats">
                <div class="stat-item"><span>❤️ 生命:</span><span>${character.health}</span></div>
                <div class="stat-item"><span>⚔️ 攻擊:</span><span>${character.attack}</span></div>
                <div class="stat-item"><span>🛡️ 防禦:</span><span>${character.defense}</span></div>
                <div class="stat-item"><span>⚡ 速度:</span><span>${character.speed}</span></div>
            </div>
            ${character.special ? `<div style="margin-top: 0.5rem; color: #667eea;">✨ ${character.special}</div>` : ''}
        </div>
    `;
}

// 保存生成的角色
function saveGeneratedCharacter() {
    if (!generatedCharacter) return;
    
    characterManager.addCharacter(generatedCharacter);
    closeModal(aiModal);
    renderCharacterSelection();
    renderManagerGrid();
    alert('角色已保存！');
}

// 開始遊戲
function startGame() {
    if (!selectedCharacter) {
        alert('請先選擇一個角色！');
        return;
    }
    
    characterSelection.classList.add('hidden');
    gameArena.classList.remove('hidden');
    
    if (!game) {
        game = new RealtimeBrawlGame(characterManager);
    }
    
    game.startGame(selectedCharacter);
}

// 結束遊戲
function endGame() {
    if (game) {
        game.stop();
    }
    characterSelection.classList.remove('hidden');
    gameArena.classList.add('hidden');
}

// Modal 工具函數
function openModal(modal) {
    modal.classList.add('active');
}

function closeModal(modal) {
    modal.classList.remove('active');
}

// 初始化應用
init();

