// 獲取 DOM 元素
const canvas = document.getElementById('drawingCanvas');
const ctx = canvas.getContext('2d');
const colorPicker = document.getElementById('colorPicker');
const brushSize = document.getElementById('brushSize');
const brushSizeValue = document.getElementById('brushSizeValue');
const opacity = document.getElementById('opacity');
const opacityValue = document.getElementById('opacityValue');
const clearBtn = document.getElementById('clearBtn');
const undoBtn = document.getElementById('undoBtn');
const redoBtn = document.getElementById('redoBtn');
const saveBtn = document.getElementById('saveBtn');

// 繪圖狀態
let isDrawing = false;
let currentTool = 'brush';
let currentBrushType = 'solid'; // solid, dashed, dotted, spray, marker
let currentColor = '#000000';
let currentBrushSize = 5;
let currentOpacity = 1;
let startX, startY;
let lastX, lastY;

// 縮放狀態
let zoomLevel = 1.0; // 1.0 = 100%
const MIN_ZOOM = 0.25;
const MAX_ZOOM = 5.0;
let canvasOffsetX = 0;
let canvasOffsetY = 0;
let isPanning = false;
let panStartX = 0;
let panStartY = 0;

// 歷史記錄
let history = [];
let historyIndex = -1;
const MAX_HISTORY = 50;

// 初始化 Canvas
function initCanvas() {
    // 設定畫布大小（使用固定尺寸，縮放通過 CSS transform 實現）
    canvas.width = 1200;
    canvas.height = 800;
    
    // 設定預設樣式
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // 保存初始狀態
    saveState();
    
    // 設定線條樣式
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    
    // 應用初始縮放
    applyZoom();
}

// 應用縮放
function applyZoom() {
    canvas.style.transform = `scale(${zoomLevel})`;
    canvas.style.transformOrigin = 'center center';
    const zoomValueEl = document.getElementById('zoomValue');
    const zoomSliderEl = document.getElementById('zoomSlider');
    if (zoomValueEl) zoomValueEl.textContent = Math.round(zoomLevel * 100) + '%';
    if (zoomSliderEl) zoomSliderEl.value = zoomLevel * 100;
}

// 縮放功能
function setZoom(level) {
    zoomLevel = Math.max(0.25, Math.min(5.0, level));
    applyZoom();
}

function zoomIn() {
    setZoom(zoomLevel + 0.1);
}

function zoomOut() {
    setZoom(zoomLevel - 0.1);
}

function resetZoom() {
    setZoom(1.0);
    canvasOffsetX = 0;
    canvasOffsetY = 0;
    canvas.style.left = '0px';
    canvas.style.top = '0px';
}

// 調整 Canvas 大小（已棄用，改用固定尺寸+縮放）
// function resizeCanvas() { ... }

// 保存狀態到歷史記錄
function saveState() {
    historyIndex++;
    if (historyIndex < history.length) {
        history = history.slice(0, historyIndex);
    }
    history.push(canvas.toDataURL());
    
    if (history.length > MAX_HISTORY) {
        history.shift();
        historyIndex--;
    }
    
    updateUndoRedoButtons();
}

// 撤銷
function undo() {
    if (historyIndex > 0) {
        historyIndex--;
        const img = new Image();
        img.onload = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0);
        };
        img.src = history[historyIndex];
        updateUndoRedoButtons();
    }
}

// 重做
function redo() {
    if (historyIndex < history.length - 1) {
        historyIndex++;
        const img = new Image();
        img.onload = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0);
        };
        img.src = history[historyIndex];
        updateUndoRedoButtons();
    }
}

// 更新撤銷/重做按鈕狀態
function updateUndoRedoButtons() {
    undoBtn.disabled = historyIndex <= 0;
    redoBtn.disabled = historyIndex >= history.length - 1;
}

// 獲取滑鼠/觸控座標（考慮縮放）
function getCoordinates(e) {
    const rect = canvas.getBoundingClientRect();
    // 考慮 CSS transform scale
    const scaleX = canvas.width / (rect.width / zoomLevel);
    const scaleY = canvas.height / (rect.height / zoomLevel);
    
    let clientX, clientY;
    if (e.touches) {
        clientX = e.touches[0].clientX;
        clientY = e.touches[0].clientY;
    } else {
        clientX = e.clientX;
        clientY = e.clientY;
    }
    
    return {
        x: (clientX - rect.left) * scaleX,
        y: (clientY - rect.top) * scaleY
    };
}

// 繪圖函數
function draw(e) {
    if (!isDrawing) return;
    
    const coords = getCoordinates(e);
    const x = coords.x;
    const y = coords.y;
    
    // 注意：不要在這裡統一設定 globalAlpha，讓各個工具自己控制
    // 特別是噴槍工具需要自己調整透明度
    
    switch (currentTool) {
        case 'brush':
            drawBrush(x, y);
            break;
        case 'eraser':
            drawEraser(x, y);
            break;
        case 'line':
            drawLine(x, y);
            break;
        case 'rect':
            drawRect(x, y);
            break;
        case 'circle':
            drawCircle(x, y);
            break;
    }
    
    lastX = x;
    lastY = y;
}

// 設定畫筆樣式
function setBrushStyle() {
    ctx.globalCompositeOperation = 'source-over';
    ctx.strokeStyle = currentColor;
    ctx.lineWidth = currentBrushSize;
    ctx.globalAlpha = currentOpacity;
    
    switch (currentBrushType) {
        case 'solid':
            ctx.setLineDash([]);
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';
            break;
        case 'dashed':
            ctx.setLineDash([currentBrushSize * 2, currentBrushSize]);
            ctx.lineCap = 'square';
            ctx.lineJoin = 'miter';
            break;
        case 'dotted':
            ctx.setLineDash([2, currentBrushSize * 2]);
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';
            break;
        case 'spray':
            ctx.setLineDash([]);
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';
            break;
        case 'marker':
            ctx.setLineDash([]);
            ctx.lineCap = 'square';
            ctx.lineJoin = 'bevel';
            ctx.globalAlpha = currentOpacity * 0.5; // 標記筆半透明
            break;
        default:
            ctx.setLineDash([]);
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';
    }
}

// 畫筆
function drawBrush(x, y) {
    if (currentBrushType === 'spray') {
        // 噴槍效果：繪製多個隨機點
        ctx.globalCompositeOperation = 'source-over';
        ctx.fillStyle = currentColor;
        
        // 增加噴槍密度，使其更明顯
        const sprayDensity = Math.max(10, currentBrushSize * 3);
        const sprayRadius = currentBrushSize;
        
        for (let i = 0; i < sprayDensity; i++) {
            // 使用圓形分布，而不是方形分布
            const angle = Math.random() * Math.PI * 2;
            const radius = Math.random() * sprayRadius;
            const offsetX = Math.cos(angle) * radius;
            const offsetY = Math.sin(angle) * radius;
            
            // 根據距離中心的位置調整透明度
            const distanceRatio = radius / sprayRadius;
            ctx.globalAlpha = currentOpacity * (1 - distanceRatio) * 0.8;
            
            // 繪製小圓點
            const dotSize = Math.max(1, sprayRadius / 8);
            ctx.beginPath();
            ctx.arc(x + offsetX, y + offsetY, dotSize, 0, Math.PI * 2);
            ctx.fill();
        }
        
        // 恢復透明度
        ctx.globalAlpha = currentOpacity;
    } else {
        // 普通畫筆
        setBrushStyle();
        ctx.beginPath();
        ctx.moveTo(lastX, lastY);
        ctx.lineTo(x, y);
        ctx.stroke();
    }
}

// 橡皮擦
function drawEraser(x, y) {
    ctx.globalCompositeOperation = 'destination-out';
    ctx.setLineDash([]);
    ctx.lineWidth = currentBrushSize * 2;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    
    ctx.beginPath();
    ctx.moveTo(lastX, lastY);
    ctx.lineTo(x, y);
    ctx.stroke();
}

// 直線（臨時預覽）
function drawLine(x, y) {
    // 清除並重繪到當前位置
    restoreState();
    setBrushStyle();
    
    ctx.beginPath();
    ctx.moveTo(startX, startY);
    ctx.lineTo(x, y);
    ctx.stroke();
}

// 矩形（臨時預覽）
function drawRect(x, y) {
    restoreState();
    setBrushStyle();
    
    const width = x - startX;
    const height = y - startY;
    
    ctx.strokeRect(startX, startY, width, height);
}

// 圓形（臨時預覽）
function drawCircle(x, y) {
    restoreState();
    setBrushStyle();
    
    const radius = Math.sqrt(Math.pow(x - startX, 2) + Math.pow(y - startY, 2));
    
    ctx.beginPath();
    ctx.arc(startX, startY, radius, 0, Math.PI * 2);
    ctx.stroke();
}

// 恢復狀態（用於形狀預覽）
function restoreState() {
    if (historyIndex >= 0) {
        const img = new Image();
        img.src = history[historyIndex];
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0);
    }
}

// 開始繪圖
function startDrawing(e) {
    isDrawing = true;
    const coords = getCoordinates(e);
    startX = lastX = coords.x;
    startY = lastY = coords.y;
    
    // 對於形狀工具，保存當前狀態
    if (['line', 'rect', 'circle'].includes(currentTool)) {
        saveState();
    }
}

// 結束繪圖
function stopDrawing(e) {
    if (!isDrawing) return;
    
    if (currentTool === 'line' || currentTool === 'rect' || currentTool === 'circle') {
        const coords = getCoordinates(e);
        const x = coords.x;
        const y = coords.y;
        
        // 最終繪製
        setBrushStyle();
        
        if (currentTool === 'line') {
            ctx.beginPath();
            ctx.moveTo(startX, startY);
            ctx.lineTo(x, y);
            ctx.stroke();
        } else if (currentTool === 'rect') {
            const width = x - startX;
            const height = y - startY;
            ctx.strokeRect(startX, startY, width, height);
        } else if (currentTool === 'circle') {
            const radius = Math.sqrt(Math.pow(x - startX, 2) + Math.pow(y - startY, 2));
            ctx.beginPath();
            ctx.arc(startX, startY, radius, 0, Math.PI * 2);
            ctx.stroke();
        }
        
        saveState();
    } else {
        saveState();
    }
    
    isDrawing = false;
}

// 事件監聽器
canvas.addEventListener('mousedown', startDrawing);
canvas.addEventListener('mousemove', draw);
canvas.addEventListener('mouseup', stopDrawing);
canvas.addEventListener('mouseout', stopDrawing);

// 觸控支援
canvas.addEventListener('touchstart', (e) => {
    e.preventDefault();
    startDrawing(e);
});
canvas.addEventListener('touchmove', (e) => {
    e.preventDefault();
    draw(e);
});
canvas.addEventListener('touchend', (e) => {
    e.preventDefault();
    stopDrawing(e);
});

// 工具選擇
document.querySelectorAll('.tool-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tool-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentTool = btn.dataset.tool;
    });
});

// 顏色選擇
colorPicker.addEventListener('input', (e) => {
    currentColor = e.target.value;
    updateBrushPreview();
});

document.querySelectorAll('.color-preset').forEach(preset => {
    preset.addEventListener('click', () => {
        currentColor = preset.dataset.color;
        colorPicker.value = currentColor;
        updateBrushPreview();
    });
});

// 筆刷大小
brushSize.addEventListener('input', (e) => {
    currentBrushSize = parseInt(e.target.value);
    brushSizeValue.textContent = currentBrushSize;
    updateBrushPreview();
});

// 透明度
opacity.addEventListener('input', (e) => {
    currentOpacity = parseFloat(e.target.value);
    opacityValue.textContent = Math.round(currentOpacity * 100) + '%';
    updateBrushPreview();
});

// 更新筆刷預覽
function updateBrushPreview() {
    const preview = document.querySelector('.brush-preview');
    preview.innerHTML = '';
    
    const previewCanvas = document.createElement('canvas');
    previewCanvas.width = 100;
    previewCanvas.height = 60;
    const previewCtx = previewCanvas.getContext('2d');
    
    previewCtx.fillStyle = '#f8f9fa';
    previewCtx.fillRect(0, 0, 100, 60);
    
    previewCtx.globalAlpha = currentOpacity;
    previewCtx.fillStyle = currentColor;
    previewCtx.beginPath();
    previewCtx.arc(50, 30, currentBrushSize / 2, 0, Math.PI * 2);
    previewCtx.fill();
    
    preview.appendChild(previewCanvas);
}

// 清除畫布
clearBtn.addEventListener('click', () => {
    if (confirm('確定要清除整個畫布嗎？')) {
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        saveState();
    }
});

// 撤銷
undoBtn.addEventListener('click', undo);

// 重做
redoBtn.addEventListener('click', redo);

// 鍵盤快捷鍵
document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        undo();
    } else if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
        e.preventDefault();
        redo();
    }
});

// 保存圖片
saveBtn.addEventListener('click', () => {
    const link = document.createElement('a');
    link.download = `drawing-${Date.now()}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
});

// 縮放控制
const zoomOutBtn = document.getElementById('zoomOutBtn');
const zoomInBtn = document.getElementById('zoomInBtn');
const zoomSlider = document.getElementById('zoomSlider');
const resetZoomBtn = document.getElementById('resetZoomBtn');

zoomOutBtn.addEventListener('click', zoomOut);
zoomInBtn.addEventListener('click', zoomIn);
resetZoomBtn.addEventListener('click', resetZoom);
zoomSlider.addEventListener('input', (e) => {
    setZoom(parseInt(e.target.value) / 100);
});

// 滑鼠滾輪縮放
const canvasWrapper = document.getElementById('canvasWrapper');
canvasWrapper.addEventListener('wheel', (e) => {
    if (e.ctrlKey || e.metaKey) {
        e.preventDefault();
        const delta = e.deltaY > 0 ? -0.1 : 0.1;
        setZoom(zoomLevel + delta);
    }
}, { passive: false });

// 視窗大小調整（不再需要 resizeCanvas，因為使用固定尺寸）
window.addEventListener('resize', () => {
    // Canvas 使用固定尺寸，通過 CSS transform 縮放
});

// Gallery 相關
const galleryModal = document.getElementById('galleryModal');
const galleryBtn = document.getElementById('galleryBtn');
const closeGalleryBtn = document.getElementById('closeGalleryBtn');
const galleryGrid = document.getElementById('galleryGrid');
const galleryLoading = document.getElementById('galleryLoading');
const imageSearch = document.getElementById('imageSearch');
const categoryFilter = document.getElementById('categoryFilter');
const loadImageBtn = document.getElementById('loadImageBtn');
const imageUpload = document.getElementById('imageUpload');
let selectedImageUrl = null;
let galleryImages = [];

// 預設著色圖（SVG 格式，直接嵌入）
const defaultColoringPages = [
    {
        id: 'flower_simple',
        name: '簡單花朵',
        category: '花卉',
        svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
            <circle cx="100" cy="100" r="40" fill="none" stroke="#000" stroke-width="2"/>
            <circle cx="100" cy="100" r="25" fill="none" stroke="#000" stroke-width="2"/>
            <ellipse cx="80" cy="80" rx="15" ry="25" fill="none" stroke="#000" stroke-width="2"/>
            <ellipse cx="120" cy="80" rx="15" ry="25" fill="none" stroke="#000" stroke-width="2"/>
            <ellipse cx="80" cy="120" rx="15" ry="25" fill="none" stroke="#000" stroke-width="2"/>
            <ellipse cx="120" cy="120" rx="15" ry="25" fill="none" stroke="#000" stroke-width="2"/>
            <rect x="95" y="140" width="10" height="30" fill="none" stroke="#000" stroke-width="2"/>
            <ellipse cx="70" cy="70" rx="8" ry="12" fill="none" stroke="#000" stroke-width="2"/>
            <ellipse cx="130" cy="70" rx="8" ry="12" fill="none" stroke="#000" stroke-width="2"/>
            <ellipse cx="70" cy="130" rx="8" ry="12" fill="none" stroke="#000" stroke-width="2"/>
            <ellipse cx="130" cy="130" rx="8" ry="12" fill="none" stroke="#000" stroke-width="2"/>
        </svg>`
    },
    {
        id: 'cat_simple',
        name: '可愛小貓',
        category: '動物',
        svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
            <circle cx="100" cy="90" r="50" fill="none" stroke="#000" stroke-width="2"/>
            <circle cx="80" cy="75" r="8" fill="none" stroke="#000" stroke-width="2"/>
            <circle cx="120" cy="75" r="8" fill="none" stroke="#000" stroke-width="2"/>
            <polygon points="100,85 95,95 105,95" fill="none" stroke="#000" stroke-width="2"/>
            <path d="M 85 100 Q 100 110 115 100" fill="none" stroke="#000" stroke-width="2"/>
            <ellipse cx="70" cy="60" rx="12" ry="20" fill="none" stroke="#000" stroke-width="2"/>
            <ellipse cx="130" cy="60" rx="12" ry="20" fill="none" stroke="#000" stroke-width="2"/>
            <path d="M 70 120 Q 70 160 100 160 Q 130 160 130 120" fill="none" stroke="#000" stroke-width="2"/>
            <line x1="50" y1="100" x2="30" y2="80" stroke="#000" stroke-width="2"/>
            <line x1="150" y1="100" x2="170" y2="80" stroke="#000" stroke-width="2"/>
        </svg>`
    },
    {
        id: 'butterfly_simple',
        name: '蝴蝶',
        category: '動物',
        svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
            <ellipse cx="100" cy="100" rx="8" ry="50" fill="none" stroke="#000" stroke-width="2"/>
            <path d="M 100 50 Q 60 70 50 100 Q 60 130 100 150" fill="none" stroke="#000" stroke-width="2"/>
            <path d="M 100 50 Q 140 70 150 100 Q 140 130 100 150" fill="none" stroke="#000" stroke-width="2"/>
            <path d="M 100 50 Q 80 60 70 80 Q 75 100 100 110" fill="none" stroke="#000" stroke-width="2"/>
            <path d="M 100 50 Q 120 60 130 80 Q 125 100 100 110" fill="none" stroke="#000" stroke-width="2"/>
            <path d="M 100 150 Q 80 140 70 160 Q 75 180 100 190" fill="none" stroke="#000" stroke-width="2"/>
            <path d="M 100 150 Q 120 140 130 160 Q 125 180 100 190" fill="none" stroke="#000" stroke-width="2"/>
            <circle cx="85" cy="85" r="5" fill="none" stroke="#000" stroke-width="2"/>
            <circle cx="115" cy="85" r="5" fill="none" stroke="#000" stroke-width="2"/>
            <circle cx="85" cy="115" r="5" fill="none" stroke="#000" stroke-width="2"/>
            <circle cx="115" cy="115" r="5" fill="none" stroke="#000" stroke-width="2"/>
        </svg>`
    },
    {
        id: 'mandala_simple',
        name: '曼陀羅',
        category: '幾何',
        svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
            <circle cx="100" cy="100" r="80" fill="none" stroke="#000" stroke-width="2"/>
            <circle cx="100" cy="100" r="60" fill="none" stroke="#000" stroke-width="2"/>
            <circle cx="100" cy="100" r="40" fill="none" stroke="#000" stroke-width="2"/>
            <circle cx="100" cy="100" r="20" fill="none" stroke="#000" stroke-width="2"/>
            <line x1="100" y1="20" x2="100" y2="180" stroke="#000" stroke-width="2"/>
            <line x1="20" y1="100" x2="180" y2="100" stroke="#000" stroke-width="2"/>
            <line x1="30" y1="30" x2="170" y2="170" stroke="#000" stroke-width="2"/>
            <line x1="170" y1="30" x2="30" y2="170" stroke="#000" stroke-width="2"/>
            <path d="M 100 20 Q 150 50 180 100 Q 150 150 100 180 Q 50 150 20 100 Q 50 50 100 20" fill="none" stroke="#000" stroke-width="2"/>
        </svg>`
    },
    {
        id: 'house_simple',
        name: '小房子',
        category: '建築',
        svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
            <rect x="60" y="100" width="80" height="70" fill="none" stroke="#000" stroke-width="2"/>
            <polygon points="50,100 100,50 150,100" fill="none" stroke="#000" stroke-width="2"/>
            <rect x="75" y="120" width="25" height="35" fill="none" stroke="#000" stroke-width="2"/>
            <line x1="87.5" y1="120" x2="87.5" y2="155" stroke="#000" stroke-width="2"/>
            <line x1="75" y1="137.5" x2="100" y2="137.5" stroke="#000" stroke-width="2"/>
            <circle cx="130" cy="130" r="8" fill="none" stroke="#000" stroke-width="2"/>
            <line x1="100" y1="50" x2="100" y2="30" stroke="#000" stroke-width="2"/>
            <rect x="92" y="30" width="16" height="8" fill="none" stroke="#000" stroke-width="2"/>
        </svg>`
    },
    {
        id: 'star_simple',
        name: '星星',
        category: '幾何',
        svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
            <path d="M 100 20 L 115 70 L 165 70 L 125 105 L 140 155 L 100 120 L 60 155 L 75 105 L 35 70 L 85 70 Z" fill="none" stroke="#000" stroke-width="2"/>
            <circle cx="100" cy="100" r="15" fill="none" stroke="#000" stroke-width="2"/>
        </svg>`
    }
];

// 將 SVG 轉換為圖片 URL
function svgToImageUrl(svgString) {
    const blob = new Blob([svgString], { type: 'image/svg+xml' });
    return URL.createObjectURL(blob);
}

// 載入圖片庫
async function loadGallery() {
    try {
        galleryLoading.style.display = 'block';
        galleryGrid.innerHTML = '';
        
        // 使用預設圖片
        galleryImages = defaultColoringPages.map(item => ({
            id: item.id,
            name: item.name,
            category: item.category,
            url: svgToImageUrl(item.svg),
            thumbnail: svgToImageUrl(item.svg),
            isSVG: true
        }));
        
        // 嘗試載入 JSON（可選）
        try {
            const response = await fetch('images.json');
            if (response.ok) {
                const data = await response.json();
                data.categories.forEach(category => {
                    category.images.forEach(img => {
                        if (!img.isPlaceholder && img.url) {
                            galleryImages.push({
                                ...img,
                                category: category.name
                            });
                        }
                    });
                });
            }
        } catch (e) {
            // JSON 載入失敗也無所謂，使用預設圖片即可
            console.log('使用預設圖片庫');
        }
        
        // 獲取所有分類
        const categories = [...new Set(galleryImages.map(img => img.category))];
        populateCategories(categories);
        
        renderGallery(galleryImages);
        
        galleryLoading.style.display = 'none';
    } catch (error) {
        console.error('載入圖片庫失敗:', error);
        // 即使出錯也顯示預設圖片
        galleryImages = defaultColoringPages.map(item => ({
            id: item.id,
            name: item.name,
            category: item.category,
            url: svgToImageUrl(item.svg),
            thumbnail: svgToImageUrl(item.svg),
            isSVG: true
        }));
        const categories = [...new Set(galleryImages.map(img => img.category))];
        populateCategories(categories);
        renderGallery(galleryImages);
        galleryLoading.style.display = 'none';
    }
}

// 填充分類選單
function populateCategories(categories) {
    categoryFilter.innerHTML = '<option value="">全部分類</option>';
    categories.forEach(cat => {
        const option = document.createElement('option');
        option.value = cat;
        option.textContent = cat;
        categoryFilter.appendChild(option);
    });
}

// 渲染圖片庫
function renderGallery(images) {
    galleryGrid.innerHTML = '';
    
    if (images.length === 0) {
        galleryGrid.innerHTML = '<div class="gallery-error">找不到圖片<br><br>💡 請使用「上傳本地圖片」功能載入您的著色圖</div>';
        return;
    }
    
    images.forEach(image => {
        // 跳過佔位符圖片
        if (image.isPlaceholder || !image.url) {
            return;
        }
        
        const item = document.createElement('div');
        item.className = 'gallery-item';
        item.dataset.imageUrl = image.url;
        item.dataset.imageId = image.id;
        
        const img = document.createElement('img');
        img.src = image.thumbnail || image.url;
        img.alt = image.name;
        img.loading = 'lazy';
        img.onerror = function() {
            this.src = 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22200%22 height=%22200%22%3E%3Crect fill=%22%23f0f0f0%22 width=%22200%22 height=%22200%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 dy=%22.3em%22 fill=%22%23999%22%3E圖片載入失敗%3C/text%3E%3C/svg%3E';
        };
        
        const label = document.createElement('div');
        label.className = 'image-label';
        label.textContent = image.name;
        
        const check = document.createElement('div');
        check.className = 'image-check';
        check.textContent = '✓';
        
        item.appendChild(img);
        item.appendChild(label);
        item.appendChild(check);
        
        item.addEventListener('click', () => {
            // 取消其他選項
            document.querySelectorAll('.gallery-item').forEach(i => i.classList.remove('selected'));
            item.classList.add('selected');
            selectedImageUrl = image.url;
        });
        
        galleryGrid.appendChild(item);
    });
}

// 過濾圖片
function filterGallery() {
    const searchTerm = imageSearch.value.toLowerCase().trim();
    const category = categoryFilter.value;
    
    let filtered = galleryImages;
    
    if (category) {
        filtered = filtered.filter(img => img.category === category);
    }
    
    if (searchTerm) {
        filtered = filtered.filter(img => 
            img.name.toLowerCase().includes(searchTerm) ||
            (img.category && img.category.toLowerCase().includes(searchTerm))
        );
    }
    
    renderGallery(filtered);
}

// 載入選中的圖片到畫布
function loadImageToCanvas(imageUrl) {
    const img = new Image();
    
    // 如果是 data URL 或 blob URL，不需要設置 crossOrigin
    if (!imageUrl.startsWith('data:') && !imageUrl.startsWith('blob:')) {
        img.crossOrigin = 'anonymous';
    }
    
    img.onload = () => {
        // 計算合適的大小，保持比例
        const maxWidth = canvas.width - 40;
        const maxHeight = canvas.height - 40;
        let width = img.width;
        let height = img.height;
        
        if (width > maxWidth || height > maxHeight) {
            const ratio = Math.min(maxWidth / width, maxHeight / height);
            width = width * ratio;
            height = height * ratio;
        }
        
        // 居中繪製
        const x = (canvas.width - width) / 2;
        const y = (canvas.height - height) / 2;
        
        // 清除畫布並繪製圖片
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, x, y, width, height);
        
        saveState();
        closeGallery();
        
        // 提示用戶可以開始著色
        alert('圖片已載入！現在可以使用畫筆工具進行著色。');
    };
    
    img.onerror = () => {
        alert('載入圖片失敗，請檢查圖片是否有效，或嘗試上傳本地圖片。');
    };
    
    img.src = imageUrl;
}

// 處理本地圖片上傳
function handleImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    if (!file.type.startsWith('image/')) {
        alert('請選擇圖片檔案');
        return;
    }
    
    const reader = new FileReader();
    reader.onload = (e) => {
        const imageUrl = e.target.result;
        loadImageToCanvas(imageUrl);
    };
    reader.readAsDataURL(file);
}

// 打開圖片庫
function openGallery() {
    galleryModal.classList.add('active');
    if (galleryImages.length === 0) {
        loadGallery();
    }
}

// 關閉圖片庫
function closeGallery() {
    galleryModal.classList.remove('active');
    selectedImageUrl = null;
    document.querySelectorAll('.gallery-item').forEach(i => i.classList.remove('selected'));
}

// Gallery 事件監聽器
galleryBtn.addEventListener('click', openGallery);
closeGalleryBtn.addEventListener('click', closeGallery);
loadImageBtn.addEventListener('click', () => {
    if (selectedImageUrl) {
        loadImageToCanvas(selectedImageUrl);
    } else {
        alert('請先選擇一張圖片');
    }
});

imageSearch.addEventListener('input', filterGallery);
categoryFilter.addEventListener('change', filterGallery);
imageUpload.addEventListener('change', handleImageUpload);

// 點擊模態框外部關閉
galleryModal.addEventListener('click', (e) => {
    if (e.target === galleryModal) {
        closeGallery();
    }
});

// 初始化
initCanvas();
updateBrushPreview();

