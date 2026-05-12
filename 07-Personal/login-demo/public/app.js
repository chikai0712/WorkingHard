// 等待 SentinelJS 加載完成
let fingerprintReady = false;
let fingerprintData = null;
let sentinelData = null;
let checkTimeout = null;
let maxCheckTime = 10000; // 最大檢查時間：10秒
let startCheckTime = Date.now();
let checkCount = 0;
let maxCheckCount = 100; // 最大檢查次數

// 檢查 SentinelJS 是否已加載
function checkSentinelJS() {
    checkCount++;
    const elapsed = Date.now() - startCheckTime;
    
    // 檢查是否超過最大時間或最大次數
    if (elapsed > maxCheckTime || checkCount > maxCheckCount) {
        handleSentinelJSTimeout();
        return;
    }
    
    // 檢查多種可能的 API 名稱
    // creep.js 暴露 window.Fingerprint 和 window.Creep
    const fingerprint = window.Fingerprint || window.fingerprint || window.creepjs?.Fingerprint;
    const creep = window.Creep || window.creep || window.creepjs?.Creep;
    
    if (fingerprint && creep) {
        fingerprintReady = true;
        updateFingerprintStatus();
        
        // 獲取指紋數據
        try {
            fingerprintData = fingerprint;
            sentinelData = creep; // creep.js 的 Creep 對象作為 sentinel 數據
            
            // 計算哈希
            const fpHash = fingerprintData?.workerScope?.$hash || 
                          fingerprintData?.$hash ||
                          calculateHash(JSON.stringify(fingerprintData));
            const sentinelHash = sentinelData?.$hash || 
                               calculateHash(JSON.stringify(sentinelData));
            
            // 顯示指紋信息
            document.getElementById('fpHash').textContent = fpHash || '-';
            document.getElementById('sentinelHash').textContent = sentinelHash || '-';
            document.getElementById('fuzzyHash').textContent = 
                fingerprintData?.$fuzzy || '-';
            
            document.getElementById('fingerprintDetails').style.display = 'block';
        } catch (error) {
            console.error('獲取指紋數據失敗:', error);
            document.getElementById('statusText').textContent = 
                '❌ 獲取指紋數據失敗: ' + error.message;
        }
    } else {
        // 如果還沒加載完成，繼續等待
        checkTimeout = setTimeout(checkSentinelJS, 100);
    }
}

// 處理 SentinelJS 加載超時
function handleSentinelJSTimeout() {
    if (checkTimeout) {
        clearTimeout(checkTimeout);
        checkTimeout = null;
    }
    
    const indicator = document.getElementById('statusIndicator');
    const statusText = document.getElementById('statusText');
    
    indicator.textContent = '⚠️';
    indicator.className = 'status-indicator';
    statusText.innerHTML = '⚠️ SentinelJS 加載超時，請檢查網絡連接<br><small style="color: #666;">登入功能仍可使用，但不會發送指紋數據</small>';
    
    // 檢查腳本是否加載失敗
    const script = document.querySelector('script[src*="creep.js"]');
    if (script) {
        script.addEventListener('error', () => {
            statusText.innerHTML = '❌ SentinelJS 腳本加載失敗<br><small style="color: #666;">請檢查網絡連接或使用本地文件</small>';
        });
    }
    
    console.warn('SentinelJS 加載超時，已停止檢查');
}

// 計算 SHA-256 哈希（簡化版，實際應該使用 crypto API）
function calculateHash(str) {
    // 這裡只是一個簡單的哈希，實際應用中應該使用 Web Crypto API
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Convert to 32bit integer
    }
    return Math.abs(hash).toString(16).substring(0, 16);
}

// 更新指紋狀態
function updateFingerprintStatus() {
    const indicator = document.getElementById('statusIndicator');
    const statusText = document.getElementById('statusText');
    
    if (fingerprintReady) {
        indicator.textContent = '✅';
        indicator.className = 'status-indicator ready';
        statusText.textContent = '指紋數據已就緒';
    } else {
        indicator.textContent = '⏳';
        indicator.className = 'status-indicator loading';
        statusText.textContent = '正在收集指紋數據...';
    }
}

// 自動登入函數
async function performAutoLogin() {
    const username = document.getElementById('username').value.trim();
    
    // 如果用戶名為空，不執行登入
    if (!username) {
        return;
    }
    
    // 自動填充密碼
    const password = '1234qwer';
    document.getElementById('password').value = password;
    
    const messageDiv = document.getElementById('message');
    
    // 禁用輸入框和顯示載入狀態
    const usernameInput = document.getElementById('username');
    usernameInput.disabled = true;
    usernameInput.style.opacity = '0.6';
    
    // 顯示載入消息
    messageDiv.style.display = 'block';
    messageDiv.className = 'message';
    messageDiv.textContent = '⏳ 正在登入...';
    
    try {
        // 準備登入數據
        const loginData = {
            username,
            password
        };
        
        // 如果指紋數據已就緒，添加到登入數據中
        if (fingerprintReady && fingerprintData && sentinelData) {
            loginData.fingerprint = fingerprintData;
            loginData.sentinel = sentinelData;
        }
        
        // 發送登入請求
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(loginData)
        });
        
        const result = await response.json();
        
        // 顯示結果
        messageDiv.style.display = 'block';
        if (result.success) {
            messageDiv.className = 'message success';
            messageDiv.textContent = `✅ ${result.message} | Session ID: ${result.sessionId}`;
            
            // 如果返回了指紋哈希，更新顯示
            if (result.fingerprintHash) {
                document.getElementById('fpHash').textContent = result.fingerprintHash;
            }
            if (result.sentinelHash) {
                document.getElementById('sentinelHash').textContent = result.sentinelHash;
            }
        } else {
            messageDiv.className = 'message error';
            messageDiv.textContent = `❌ ${result.message}`;
        }
    } catch (error) {
        console.error('登入錯誤:', error);
        messageDiv.style.display = 'block';
        messageDiv.className = 'message error';
        messageDiv.textContent = `❌ 登入失敗: ${error.message}`;
    } finally {
        // 恢復輸入框
        usernameInput.disabled = false;
        usernameInput.style.opacity = '1';
    }
}

// 處理登入表單提交
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    await performAutoLogin();
});

// 處理用戶名輸入框事件
let loginTimeout = null;
document.getElementById('username').addEventListener('input', (e) => {
    const username = e.target.value.trim();
    
    // 清除之前的定時器
    if (loginTimeout) {
        clearTimeout(loginTimeout);
    }
    
    // 如果用戶名不為空，等待 500ms 後自動登入（防抖）
    if (username) {
        loginTimeout = setTimeout(() => {
            performAutoLogin();
        }, 500);
    }
});

// 處理用戶名輸入框按 Enter 鍵
document.getElementById('username').addEventListener('keydown', async (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        // 清除定時器
        if (loginTimeout) {
            clearTimeout(loginTimeout);
        }
        await performAutoLogin();
    }
});

// 頁面加載完成後開始檢查 SentinelJS
window.addEventListener('DOMContentLoaded', () => {
    updateFingerprintStatus();
    startCheckTime = Date.now();
    checkCount = 0;
    checkSentinelJS();
    
    // 監聽腳本加載錯誤
    const script = document.querySelector('script[src*="creep.js"]');
    if (script) {
        script.addEventListener('error', () => {
            handleSentinelJSTimeout();
            const statusText = document.getElementById('statusText');
            statusText.innerHTML = '❌ SentinelJS 腳本加載失敗<br><small style="color: #666;">請檢查網絡連接或使用本地文件</small>';
        });
    }
});

