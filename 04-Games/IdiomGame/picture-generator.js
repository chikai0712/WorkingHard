// 成語圖片生成器
// 可以使用 AI API 或簡單的 Canvas 繪圖

class IdiomPictureGenerator {
    constructor() {
        // 可以配置 AI API（如 OpenAI DALL-E, Stable Diffusion 等）
        this.useAIGeneration = false; // 預設使用簡單繪圖
        this.apiKey = null;
        this.apiEndpoint = null;
    }

    // 配置 AI API
    configureAI(apiKey, endpoint) {
        this.useAIGeneration = true;
        this.apiKey = apiKey;
        this.apiEndpoint = endpoint;
    }

    // 生成成語圖片（主要方法）
    async generatePicture(idiom) {
        if (this.useAIGeneration) {
            return await this.generateAIPicture(idiom);
        } else {
            return this.generateSimplePicture(idiom);
        }
    }

    // 使用 AI 生成圖片（需要配置 API）
    async generateAIPicture(idiom) {
        try {
            const prompt = this.createPicturePrompt(idiom);
            console.log('🎨 AI 生成提示詞:', prompt);
            
            // OpenAI DALL-E 3 API 調用（推薦，生成更好的卡通效果）
            if (this.apiKey && (this.apiEndpoint || this.apiEndpoint === null)) {
                const endpoint = this.apiEndpoint || 'https://api.openai.com/v1/images/generations';
                
                const requestBody = {
                    model: "dall-e-3",  // 使用 DALL-E 3 獲得更好的卡通效果
                    prompt: prompt,
                    n: 1,
                    size: "1024x1024",
                    quality: "standard",
                    style: "vivid"  // vivid 風格更適合卡通/漫畫
                };
                
                console.log('📤 發送 AI 請求:', requestBody);
                
                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${this.apiKey}`
                    },
                    body: JSON.stringify(requestBody)
                });
                
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(`API 錯誤 ${response.status}: ${JSON.stringify(errorData)}`);
                }
                
                const data = await response.json();
                console.log('✅ AI 生成成功:', data);
                
                if (data.data && data.data[0] && data.data[0].url) {
                    return data.data[0].url; // 返回圖片 URL
                } else {
                    throw new Error('API 響應格式錯誤');
                }
            }
            
            // Stable Diffusion API 調用（備選方案）
            if (this.apiKey && this.apiEndpoint && this.apiEndpoint.includes('stability')) {
                const response = await fetch(this.apiEndpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${this.apiKey}`
                    },
                    body: JSON.stringify({
                        text_prompts: [{ 
                            text: prompt,
                            weight: 1.0
                        }],
                        cfg_scale: 7,
                        height: 512,
                        width: 512,
                        steps: 30,
                        style_preset: "comic-book"  // 使用漫畫風格預設
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`API 錯誤: ${response.status}`);
                }
                
                const data = await response.json();
                if (data.artifacts && data.artifacts[0]) {
                    return `data:image/png;base64,${data.artifacts[0].base64}`;
                }
            }
            
            // 如果沒有配置 API 或調用失敗，返回簡單繪圖
            console.warn('⚠️ AI API 未配置或調用失敗，使用簡單繪圖');
            return this.generateSimplePicture(idiom);
        } catch (error) {
            console.error('❌ AI 圖片生成失敗:', error);
            console.error('錯誤詳情:', error.message);
            // 發生錯誤時回退到簡單繪圖
            return this.generateSimplePicture(idiom);
        }
    }

    // 創建圖片提示詞（優化為卡通/漫畫風格）
    createPicturePrompt(idiom) {
        // 根據成語創建描述性的提示詞，強調卡通和漫畫風格
        const idiomDescriptions = {
            '一石二鳥': '一隻鳥扔石頭打中兩隻鳥，卡通漫畫風格，簡筆畫，可愛風格，線條清晰，適合兒童教育',
            '畫蛇添足': '一條蛇被畫上多餘的腳，卡通漫畫風格，簡筆畫，幽默風格，線條清晰，適合兒童教育',
            '守株待兔': '一個人在樹樁旁邊等待兔子，卡通漫畫風格，簡筆畫，可愛風格，線條清晰，適合兒童教育',
            '亡羊補牢': '羊跑了，人在修補圍欄，卡通漫畫風格，簡筆畫，可愛風格，線條清晰，適合兒童教育',
            '馬到成功': '一匹馬到達終點勝利，卡通漫畫風格，簡筆畫，可愛風格，線條清晰，適合兒童教育',
            '虎頭蛇尾': '老虎的頭和蛇的尾巴組合，卡通漫畫風格，簡筆畫，幽默風格，線條清晰，適合兒童教育',
            '井底之蛙': '一隻青蛙在井底，卡通漫畫風格，簡筆畫，可愛風格，線條清晰，適合兒童教育',
            '對牛彈琴': '一個人對著牛彈琴，卡通漫畫風格，簡筆畫，幽默風格，線條清晰，適合兒童教育',
            '一鳴驚人': '一隻鳥突然發出響亮的叫聲，卡通漫畫風格，簡筆畫，可愛風格，線條清晰，適合兒童教育',
            '一舉兩得': '一個動作獲得兩個好處，卡通漫畫風格，簡筆畫，可愛風格，線條清晰，適合兒童教育',
            '三心二意': '一個人猶豫不決，卡通漫畫風格，簡筆畫，可愛風格，線條清晰，適合兒童教育',
            '三思而行': '一個人仔細思考，卡通漫畫風格，簡筆畫，可愛風格，線條清晰，適合兒童教育',
            '三言兩語': '簡短的對話，卡通漫畫風格，簡筆畫，可愛風格，線條清晰，適合兒童教育',
            // 可以添加更多...
        };

        // 如果沒有特定描述，使用通用模板
        const basePrompt = idiomDescriptions[idiom] || `${idiom}的場景`;
        
        // 添加強制性的風格描述
        const styleSuffix = '，卡通漫畫風格，簡筆畫，可愛幽默風格，線條清晰，黑白或彩色，適合兒童教育，類似兒童繪本插圖';
        
        return basePrompt + styleSuffix;
    }

    // 生成簡單的 Canvas 繪圖（不需要 API）
    generateSimplePicture(idiom) {
        try {
            console.log('🎨 開始 Canvas 繪圖，成語:', idiom);
            
            // 創建 Canvas 元素
            const canvas = document.createElement('canvas');
            canvas.width = 400;
            canvas.height = 400;
            const ctx = canvas.getContext('2d');

            // 根據成語繪製不同的圖案
            this.drawIdiomPicture(ctx, idiom, canvas.width, canvas.height);

            // 返回 Canvas 的 data URL
            const dataUrl = canvas.toDataURL('image/png');
            console.log('✅ Canvas 繪圖完成，數據長度:', dataUrl.length);
            
            // 驗證數據 URL 格式
            if (!dataUrl || !dataUrl.startsWith('data:image')) {
                throw new Error('Canvas 生成的數據 URL 格式錯誤');
            }
            
            return dataUrl;
        } catch (error) {
            console.error('❌ Canvas 繪圖失敗:', error);
            // 返回一個簡單的錯誤圖片
            const errorCanvas = document.createElement('canvas');
            errorCanvas.width = 400;
            errorCanvas.height = 400;
            const errorCtx = errorCanvas.getContext('2d');
            errorCtx.fillStyle = '#f0f0f0';
            errorCtx.fillRect(0, 0, 400, 400);
            errorCtx.fillStyle = '#999';
            errorCtx.font = '20px Arial';
            errorCtx.textAlign = 'center';
            errorCtx.fillText('圖片生成失敗', 200, 200);
            return errorCanvas.toDataURL('image/png');
        }
    }

    // 繪製成語圖片
    drawIdiomPicture(ctx, idiom, width, height) {
        ctx.clearRect(0, 0, width, height);
        // 使用更亮的背景色
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, width, height);

        // 根據不同的成語繪製不同的圖案
        switch (idiom) {
            case '一石二鳥':
                this.drawOneStoneTwoBirds(ctx, width, height);
                break;
            case '畫蛇添足':
                this.drawSnakeWithFeet(ctx, width, height);
                break;
            case '守株待兔':
                this.drawWaitingForRabbit(ctx, width, height);
                break;
            case '亡羊補牢':
                this.drawRepairFence(ctx, width, height);
                break;
            case '馬到成功':
                this.drawHorseSuccess(ctx, width, height);
                break;
            case '虎頭蛇尾':
                this.drawTigerHeadSnakeTail(ctx, width, height);
                break;
            case '井底之蛙':
                this.drawFrogInWell(ctx, width, height);
                break;
            case '對牛彈琴':
                this.drawPlayPianoToCow(ctx, width, height);
                break;
            case '雨過天晴':
                this.drawRainThenSunny(ctx, width, height);
                break;
            case '風和日麗':
                this.drawSunnyDay(ctx, width, height);
                break;
            case '雪中送炭':
                this.drawCoalInSnow(ctx, width, height);
                break;
            case '火中取栗':
                this.drawChestnutFromFire(ctx, width, height);
                break;
            case '畫龍點睛':
                this.drawDragonEye(ctx, width, height);
                break;
            case '胸有成竹':
                this.drawBambooPlan(ctx, width, height);
                break;
            case '朝三暮四':
                this.drawMorningThreeEveningFour(ctx, width, height);
                break;
            case '三言兩語':
                this.drawFewWords(ctx, width, height);
                break;
            default:
                this.drawDefaultPicture(ctx, idiom, width, height);
        }
    }

    // 一石二鳥
    drawOneStoneTwoBirds(ctx, width, height) {
        ctx.strokeStyle = '#333';
        ctx.lineWidth = 3;
        
        // 繪製石頭
        ctx.beginPath();
        ctx.arc(width * 0.5, height * 0.3, 20, 0, Math.PI * 2);
        ctx.fillStyle = '#666';
        ctx.fill();
        ctx.stroke();
        
        // 繪製兩隻鳥
        this.drawBird(ctx, width * 0.3, height * 0.6);
        this.drawBird(ctx, width * 0.7, height * 0.6);
    }

    // 畫蛇添足
    drawSnakeWithFeet(ctx, width, height) {
        ctx.strokeStyle = '#333';
        ctx.lineWidth = 3;
        
        // 繪製蛇身（彎曲的線）
        ctx.beginPath();
        ctx.moveTo(width * 0.2, height * 0.5);
        for (let i = 1; i <= 10; i++) {
            ctx.lineTo(
                width * 0.2 + (width * 0.6 * i / 10),
                height * 0.5 + Math.sin(i * 0.5) * 30
            );
        }
        ctx.stroke();
        
        // 繪製蛇頭
        ctx.beginPath();
        ctx.arc(width * 0.8, height * 0.5, 15, 0, Math.PI * 2);
        ctx.fill();
        
        // 繪製多餘的腳
        ctx.beginPath();
        ctx.moveTo(width * 0.5, height * 0.5);
        ctx.lineTo(width * 0.5, height * 0.6);
        ctx.moveTo(width * 0.6, height * 0.5);
        ctx.lineTo(width * 0.6, height * 0.6);
        ctx.stroke();
    }

    // 守株待兔
    drawWaitingForRabbit(ctx, width, height) {
        ctx.strokeStyle = '#333';
        ctx.lineWidth = 3;
        
        // 繪製樹樁
        ctx.fillStyle = '#8B4513';
        ctx.fillRect(width * 0.4, height * 0.4, 30, 40);
        
        // 繪製人（簡單線條）
        ctx.beginPath();
        ctx.arc(width * 0.6, height * 0.3, 15, 0, Math.PI * 2);
        ctx.fillStyle = '#333';
        ctx.fill();
        
        // 繪製身體
        ctx.beginPath();
        ctx.moveTo(width * 0.6, height * 0.45);
        ctx.lineTo(width * 0.6, height * 0.65);
        ctx.stroke();
        
        // 繪製兔子
        this.drawRabbit(ctx, width * 0.3, height * 0.7);
    }

    // 亡羊補牢
    drawRepairFence(ctx, width, height) {
        ctx.strokeStyle = '#333';
        ctx.lineWidth = 3;
        
        // 繪製圍欄
        for (let i = 0; i < 5; i++) {
            ctx.beginPath();
            ctx.moveTo(width * 0.3 + i * 20, height * 0.3);
            ctx.lineTo(width * 0.3 + i * 20, height * 0.6);
            ctx.stroke();
        }
        
        // 繪製破洞
        ctx.strokeStyle = '#f00';
        ctx.beginPath();
        ctx.moveTo(width * 0.5, height * 0.4);
        ctx.lineTo(width * 0.6, height * 0.5);
        ctx.stroke();
        
        // 繪製羊（逃跑）
        this.drawSheep(ctx, width * 0.7, height * 0.5);
    }

    // 馬到成功
    drawHorseSuccess(ctx, width, height) {
        ctx.strokeStyle = '#333';
        ctx.lineWidth = 3;
        
        // 繪製終點線
        ctx.beginPath();
        ctx.moveTo(0, height * 0.3);
        ctx.lineTo(width, height * 0.3);
        ctx.strokeStyle = '#0f0';
        ctx.stroke();
        
        // 繪製馬
        this.drawHorse(ctx, width * 0.5, height * 0.5);
    }

    // 虎頭蛇尾
    drawTigerHeadSnakeTail(ctx, width, height) {
        ctx.strokeStyle = '#333';
        ctx.lineWidth = 3;
        
        // 繪製虎頭（左側，較大）
        ctx.beginPath();
        ctx.arc(width * 0.2, height * 0.5, 40, 0, Math.PI * 2);
        ctx.stroke();
        
        // 繪製眼睛
        ctx.fillStyle = '#f00';
        ctx.beginPath();
        ctx.arc(width * 0.15, height * 0.45, 5, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.arc(width * 0.25, height * 0.45, 5, 0, Math.PI * 2);
        ctx.fill();
        
        // 繪製蛇尾（右側，細小）
        ctx.beginPath();
        ctx.moveTo(width * 0.6, height * 0.5);
        ctx.lineTo(width * 0.8, height * 0.5);
        ctx.stroke();
    }

    // 井底之蛙
    drawFrogInWell(ctx, width, height) {
        ctx.strokeStyle = '#333';
        ctx.lineWidth = 3;
        
        // 繪製井（圓形）
        ctx.beginPath();
        ctx.arc(width * 0.5, height * 0.5, 80, 0, Math.PI * 2);
        ctx.stroke();
        
        // 繪製青蛙
        this.drawFrog(ctx, width * 0.5, height * 0.5);
        
        // 繪製天空（上方）
        ctx.fillStyle = '#87CEEB';
        ctx.fillRect(0, 0, width, height * 0.2);
    }

    // 對牛彈琴
    drawPlayPianoToCow(ctx, width, height) {
        ctx.strokeStyle = '#333';
        ctx.lineWidth = 3;
        
        // 繪製牛
        this.drawCow(ctx, width * 0.7, height * 0.6);
        
        // 繪製人（左側）
        ctx.beginPath();
        ctx.arc(width * 0.3, height * 0.4, 15, 0, Math.PI * 2);
        ctx.fillStyle = '#333';
        ctx.fill();
        
        // 繪製琴
        ctx.beginPath();
        ctx.rect(width * 0.25, height * 0.5, 30, 20);
        ctx.stroke();
    }

    // 預設圖片（改進版：繪製簡單的圖案而不是文字）
    drawDefaultPicture(ctx, idiom, width, height) {
        // 繪製背景
        const gradient = ctx.createLinearGradient(0, 0, width, height);
        gradient.addColorStop(0, '#e3f2fd');
        gradient.addColorStop(1, '#bbdefb');
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, width, height);
        
        // 繪製簡單的裝飾圖案（避免顯示文字）
        ctx.strokeStyle = '#667eea';
        ctx.lineWidth = 4;
        
        // 繪製一些簡單的圖案（圓圈、線條等）
        for (let i = 0; i < 4; i++) {
            const x = width * (0.2 + i * 0.2);
            const y = height * 0.5;
            ctx.beginPath();
            ctx.arc(x, y, 30, 0, Math.PI * 2);
            ctx.stroke();
        }
        
        // 添加提示文字（小字）
        ctx.fillStyle = '#999';
        ctx.font = '16px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('請根據圖片選擇成語', width / 2, height - 30);
    }
    
    // 雨過天晴
    drawRainThenSunny(ctx, width, height) {
        // 繪製天空背景
        const gradient = ctx.createLinearGradient(0, 0, 0, height);
        gradient.addColorStop(0, '#87CEEB');
        gradient.addColorStop(0.7, '#E0F6FF');
        gradient.addColorStop(1, '#F0F8FF');
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, width, height);
        
        // 繪製雨滴
        ctx.strokeStyle = '#4A90E2';
        ctx.lineWidth = 2;
        for (let i = 0; i < 20; i++) {
            const x = width * (0.1 + Math.random() * 0.8);
            const y = height * (0.2 + Math.random() * 0.4);
            ctx.beginPath();
            ctx.moveTo(x, y);
            ctx.lineTo(x, y + 15);
            ctx.stroke();
        }
        
        // 繪製太陽（右上角）
        ctx.fillStyle = '#FFD700';
        ctx.beginPath();
        ctx.arc(width * 0.8, height * 0.2, 40, 0, Math.PI * 2);
        ctx.fill();
        
        // 太陽光線
        ctx.strokeStyle = '#FFD700';
        ctx.lineWidth = 3;
        for (let i = 0; i < 8; i++) {
            const angle = (i / 8) * Math.PI * 2;
            const x1 = width * 0.8 + Math.cos(angle) * 50;
            const y1 = height * 0.2 + Math.sin(angle) * 50;
            const x2 = width * 0.8 + Math.cos(angle) * 65;
            const y2 = height * 0.2 + Math.sin(angle) * 65;
            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.stroke();
        }
        
        // 繪製彩虹（可選）
        ctx.strokeStyle = '#FF6B6B';
        ctx.lineWidth = 5;
        ctx.beginPath();
        ctx.arc(width * 0.5, height * 0.7, 80, Math.PI, 0, false);
        ctx.stroke();
    }
    
    // 風和日麗
    drawSunnyDay(ctx, width, height) {
        // 藍天背景
        const gradient = ctx.createLinearGradient(0, 0, 0, height);
        gradient.addColorStop(0, '#87CEEB');
        gradient.addColorStop(1, '#E0F6FF');
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, width, height);
        
        // 繪製太陽
        ctx.fillStyle = '#FFD700';
        ctx.beginPath();
        ctx.arc(width * 0.5, height * 0.3, 50, 0, Math.PI * 2);
        ctx.fill();
        
        // 太陽光線
        ctx.strokeStyle = '#FFD700';
        ctx.lineWidth = 4;
        for (let i = 0; i < 12; i++) {
            const angle = (i / 12) * Math.PI * 2;
            const x1 = width * 0.5 + Math.cos(angle) * 60;
            const y1 = height * 0.3 + Math.sin(angle) * 60;
            const x2 = width * 0.5 + Math.cos(angle) * 80;
            const y2 = height * 0.3 + Math.sin(angle) * 80;
            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.stroke();
        }
        
        // 繪製雲朵
        ctx.fillStyle = '#FFFFFF';
        this.drawCloud(ctx, width * 0.3, height * 0.5, 40);
        this.drawCloud(ctx, width * 0.7, height * 0.6, 35);
    }
    
    // 雪中送炭
    drawCoalInSnow(ctx, width, height) {
        // 雪地背景
        ctx.fillStyle = '#F0F8FF';
        ctx.fillRect(0, 0, width, height);
        
        // 繪製雪花
        ctx.fillStyle = '#FFFFFF';
        for (let i = 0; i < 30; i++) {
            const x = width * Math.random();
            const y = height * Math.random();
            ctx.beginPath();
            ctx.arc(x, y, 3, 0, Math.PI * 2);
            ctx.fill();
        }
        
        // 繪製人（簡化）
        ctx.fillStyle = '#333';
        ctx.beginPath();
        ctx.arc(width * 0.5, height * 0.4, 20, 0, Math.PI * 2);
        ctx.fill();
        
        // 繪製身體
        ctx.beginPath();
        ctx.moveTo(width * 0.5, height * 0.5);
        ctx.lineTo(width * 0.5, height * 0.7);
        ctx.strokeStyle = '#333';
        ctx.lineWidth = 4;
        ctx.stroke();
        
        // 繪製炭（黑色方塊）
        ctx.fillStyle = '#000';
        ctx.fillRect(width * 0.45, height * 0.6, 30, 20);
    }
    
    // 火中取栗
    drawChestnutFromFire(ctx, width, height) {
        // 背景
        ctx.fillStyle = '#FFF8DC';
        ctx.fillRect(0, 0, width, height);
        
        // 繪製火焰
        ctx.fillStyle = '#FF4500';
        ctx.beginPath();
        ctx.moveTo(width * 0.4, height * 0.7);
        ctx.lineTo(width * 0.5, height * 0.4);
        ctx.lineTo(width * 0.6, height * 0.7);
        ctx.closePath();
        ctx.fill();
        
        // 繪製栗子
        ctx.fillStyle = '#8B4513';
        ctx.beginPath();
        ctx.arc(width * 0.5, height * 0.5, 15, 0, Math.PI * 2);
        ctx.fill();
        
        // 繪製手（簡化）
        ctx.strokeStyle = '#FFD700';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(width * 0.3, height * 0.3);
        ctx.lineTo(width * 0.5, height * 0.5);
        ctx.stroke();
    }
    
    // 畫龍點睛
    drawDragonEye(ctx, width, height) {
        // 背景
        ctx.fillStyle = '#F5F5DC';
        ctx.fillRect(0, 0, width, height);
        
        // 繪製龍身（簡化為曲線）
        ctx.strokeStyle = '#8B4513';
        ctx.lineWidth = 8;
        ctx.beginPath();
        ctx.moveTo(width * 0.2, height * 0.5);
        for (let i = 1; i <= 10; i++) {
            ctx.lineTo(
                width * 0.2 + (width * 0.6 * i / 10),
                height * 0.5 + Math.sin(i * 0.8) * 40
            );
        }
        ctx.stroke();
        
        // 繪製龍頭
        ctx.fillStyle = '#8B4513';
        ctx.beginPath();
        ctx.arc(width * 0.8, height * 0.5, 30, 0, Math.PI * 2);
        ctx.fill();
        
        // 繪製眼睛（重點）
        ctx.fillStyle = '#FF0000';
        ctx.beginPath();
        ctx.arc(width * 0.75, height * 0.45, 8, 0, Math.PI * 2);
        ctx.fill();
        
        // 繪製筆（點睛）
        ctx.strokeStyle = '#000';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(width * 0.9, height * 0.3);
        ctx.lineTo(width * 0.75, height * 0.45);
        ctx.stroke();
    }
    
    // 胸有成竹
    drawBambooPlan(ctx, width, height) {
        // 背景
        ctx.fillStyle = '#F0FFF0';
        ctx.fillRect(0, 0, width, height);
        
        // 繪製竹子
        ctx.strokeStyle = '#228B22';
        ctx.lineWidth = 6;
        for (let i = 0; i < 3; i++) {
            const x = width * (0.3 + i * 0.2);
            ctx.beginPath();
            ctx.moveTo(x, height * 0.2);
            ctx.lineTo(x, height * 0.8);
            ctx.stroke();
            
            // 竹節
            for (let j = 1; j < 5; j++) {
                ctx.beginPath();
                ctx.moveTo(x - 3, height * (0.2 + j * 0.15));
                ctx.lineTo(x + 3, height * (0.2 + j * 0.15));
                ctx.stroke();
            }
        }
        
        // 繪製人（簡化）
        ctx.fillStyle = '#333';
        ctx.beginPath();
        ctx.arc(width * 0.7, height * 0.4, 15, 0, Math.PI * 2);
        ctx.fill();
    }
    
    // 朝三暮四
    drawMorningThreeEveningFour(ctx, width, height) {
        // 背景分為兩部分：早晨和晚上
        // 早晨（左側）
        const morningGradient = ctx.createLinearGradient(0, 0, width / 2, height);
        morningGradient.addColorStop(0, '#FFE4B5');
        morningGradient.addColorStop(1, '#FFF8DC');
        ctx.fillStyle = morningGradient;
        ctx.fillRect(0, 0, width / 2, height);
        
        // 晚上（右側）
        const eveningGradient = ctx.createLinearGradient(width / 2, 0, width, height);
        eveningGradient.addColorStop(0, '#191970');
        eveningGradient.addColorStop(1, '#000080');
        ctx.fillStyle = eveningGradient;
        ctx.fillRect(width / 2, 0, width / 2, height);
        
        // 繪製數字 3（早晨）
        ctx.fillStyle = '#FF4500';
        ctx.font = 'bold 80px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('3', width * 0.25, height * 0.5);
        
        // 繪製數字 4（晚上）
        ctx.fillStyle = '#FFD700';
        ctx.fillText('4', width * 0.75, height * 0.5);
        
        // 繪製太陽（早晨）
        ctx.fillStyle = '#FFD700';
        ctx.beginPath();
        ctx.arc(width * 0.25, height * 0.2, 25, 0, Math.PI * 2);
        ctx.fill();
        
        // 繪製月亮（晚上）
        ctx.fillStyle = '#FFFFFF';
        ctx.beginPath();
        ctx.arc(width * 0.75, height * 0.2, 20, 0, Math.PI * 2);
        ctx.fill();
    }
    
    // 三言兩語
    drawFewWords(ctx, width, height) {
        // 背景
        ctx.fillStyle = '#F5F5F5';
        ctx.fillRect(0, 0, width, height);
        
        // 繪製對話框
        ctx.fillStyle = '#FFFFFF';
        ctx.strokeStyle = '#333';
        ctx.lineWidth = 3;
        
        // 第一個對話框（三言）
        this.drawRoundedRect(ctx, width * 0.2, height * 0.3, 120, 60, 10);
        ctx.fill();
        ctx.stroke();
        
        // 第二個對話框（兩語）
        this.drawRoundedRect(ctx, width * 0.6, height * 0.5, 100, 50, 10);
        ctx.fill();
        ctx.stroke();
        
        // 繪製簡短的線條（代表話語）
        ctx.strokeStyle = '#333';
        ctx.lineWidth = 2;
        for (let i = 0; i < 3; i++) {
            ctx.beginPath();
            ctx.moveTo(width * 0.25 + i * 15, height * 0.35);
            ctx.lineTo(width * 0.25 + i * 15 + 10, height * 0.35);
            ctx.stroke();
        }
        
        for (let i = 0; i < 2; i++) {
            ctx.beginPath();
            ctx.moveTo(width * 0.65 + i * 15, height * 0.55);
            ctx.lineTo(width * 0.65 + i * 15 + 10, height * 0.55);
            ctx.stroke();
        }
    }
    
    // 繪製雲朵（輔助方法）
    drawCloud(ctx, x, y, size) {
        ctx.fillStyle = '#FFFFFF';
        ctx.beginPath();
        ctx.arc(x, y, size, 0, Math.PI * 2);
        ctx.arc(x + size * 0.6, y, size * 0.8, 0, Math.PI * 2);
        ctx.arc(x - size * 0.6, y, size * 0.8, 0, Math.PI * 2);
        ctx.arc(x, y - size * 0.5, size * 0.7, 0, Math.PI * 2);
        ctx.fill();
    }
    
    // 繪製圓角矩形（輔助方法）
    drawRoundedRect(ctx, x, y, width, height, radius) {
        ctx.beginPath();
        ctx.moveTo(x + radius, y);
        ctx.lineTo(x + width - radius, y);
        ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
        ctx.lineTo(x + width, y + height - radius);
        ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
        ctx.lineTo(x + radius, y + height);
        ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
        ctx.lineTo(x, y + radius);
        ctx.quadraticCurveTo(x, y, x + radius, y);
        ctx.closePath();
    }

    // 輔助繪圖方法
    drawBird(ctx, x, y) {
        ctx.fillStyle = '#333';
        ctx.beginPath();
        ctx.arc(x, y, 15, 0, Math.PI * 2);
        ctx.fill();
        
        // 翅膀
        ctx.beginPath();
        ctx.arc(x - 10, y, 8, 0, Math.PI * 2);
        ctx.fill();
    }

    drawRabbit(ctx, x, y) {
        ctx.fillStyle = '#333';
        // 身體
        ctx.beginPath();
        ctx.ellipse(x, y, 12, 20, 0, 0, Math.PI * 2);
        ctx.fill();
        // 耳朵
        ctx.beginPath();
        ctx.ellipse(x - 8, y - 15, 5, 15, -0.3, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.ellipse(x + 8, y - 15, 5, 15, 0.3, 0, Math.PI * 2);
        ctx.fill();
    }

    drawSheep(ctx, x, y) {
        ctx.fillStyle = '#fff';
        ctx.beginPath();
        ctx.arc(x, y, 20, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = '#333';
        ctx.stroke();
    }

    drawHorse(ctx, x, y) {
        ctx.fillStyle = '#8B4513';
        // 身體
        ctx.beginPath();
        ctx.ellipse(x, y, 30, 20, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = '#333';
        ctx.stroke();
        // 頭
        ctx.beginPath();
        ctx.ellipse(x - 30, y - 10, 15, 12, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
    }

    drawFrog(ctx, x, y) {
        ctx.fillStyle = '#4CAF50';
        ctx.beginPath();
        ctx.arc(x, y, 20, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = '#333';
        ctx.stroke();
        // 眼睛
        ctx.fillStyle = '#000';
        ctx.beginPath();
        ctx.arc(x - 8, y - 10, 3, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.arc(x + 8, y - 10, 3, 0, Math.PI * 2);
        ctx.fill();
    }

    drawCow(ctx, x, y) {
        ctx.fillStyle = '#fff';
        ctx.beginPath();
        ctx.ellipse(x, y, 40, 30, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = '#333';
        ctx.stroke();
        // 斑點
        ctx.fillStyle = '#000';
        ctx.beginPath();
        ctx.arc(x - 15, y - 10, 8, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.arc(x + 15, y + 10, 8, 0, Math.PI * 2);
        ctx.fill();
    }
}

// 導出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = IdiomPictureGenerator;
}

