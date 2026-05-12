// 初始化
const idiomManager = new IdiomManager();
const pictureGenerator = new IdiomPictureGenerator();
let game = null;

// 全局暴露圖片生成器（方便配置 AI）
window.pictureGenerator = pictureGenerator;

// DOM 元素
const gameSelection = document.getElementById('gameSelection');
const gameArea = document.getElementById('gameArea');
const resultScreen = document.getElementById('resultScreen');
const helpModal = document.getElementById('helpModal');

// 初始化
function init() {
    setupEventListeners();
}

// 設置事件監聽器
function setupEventListeners() {
    // 遊戲模式選擇
    document.querySelectorAll('.mode-card').forEach(card => {
        card.addEventListener('click', () => {
            const mode = card.getAttribute('data-mode');
            startGame(mode);
        });
    });

    // Header 按鈕
    document.getElementById('startGameBtn')?.addEventListener('click', () => {
        gameSelection.classList.remove('hidden');
        gameArea.classList.add('hidden');
        resultScreen.classList.add('hidden');
    });

    document.getElementById('helpBtn')?.addEventListener('click', () => {
        helpModal.classList.remove('hidden');
    });

    document.getElementById('closeHelpBtn')?.addEventListener('click', () => {
        helpModal.classList.add('hidden');
    });

    // 遊戲控制按鈕
    document.getElementById('hintBtn')?.addEventListener('click', () => {
        if (game) game.showHint();
    });

    document.getElementById('skipBtn')?.addEventListener('click', () => {
        if (game) game.skipQuestion();
    });

    document.getElementById('endGameBtn')?.addEventListener('click', () => {
        if (game) game.endGame();
    });

    // 結果畫面按鈕
    document.getElementById('playAgainBtn')?.addEventListener('click', () => {
        if (game && game.currentMode) {
            game.startGame(game.currentMode);
            resultScreen.classList.add('hidden');
            gameArea.classList.remove('hidden');
        }
    });

    document.getElementById('backToMenuBtn')?.addEventListener('click', () => {
        gameSelection.classList.remove('hidden');
        gameArea.classList.add('hidden');
        resultScreen.classList.add('hidden');
    });

    // 點擊模態背景關閉
    helpModal.addEventListener('click', (e) => {
        if (e.target === helpModal) {
            helpModal.classList.add('hidden');
        }
    });
}

// 開始遊戲
function startGame(mode) {
    if (!game) {
        game = new IdiomGame(idiomManager, pictureGenerator);
    }
    
    game.startGame(mode);
    gameSelection.classList.add('hidden');
    gameArea.classList.remove('hidden');
    resultScreen.classList.add('hidden');
}

// 初始化
init();

