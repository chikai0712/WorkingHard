#!/usr/bin/env node

import express from 'express';
import cors from 'cors';
import bodyParser from 'body-parser';
import crypto from 'crypto';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

// 中間件
app.use(cors());
app.use(bodyParser.json({ limit: '10mb' }));
app.use(bodyParser.urlencoded({ extended: true }));

// 靜態文件服務
app.use(express.static(join(__dirname, 'public')));

// 存儲登入記錄（實際應用中應該使用數據庫）
const loginLogs = [];
const fingerprintData = [];

// API: 登入
app.post('/api/login', async (req, res) => {
  try {
    const { username, password, fingerprint, sentinel } = req.body;
    
    // 簡單的驗證（實際應用中應該使用數據庫和加密）
    const isValid = username && password && password.length >= 6;
    
    const loginRecord = {
      id: Date.now().toString(),
      timestamp: new Date().toISOString(),
      username: username || 'anonymous',
      success: isValid,
      ip: req.ip || req.headers['x-forwarded-for'] || req.connection.remoteAddress,
      userAgent: req.headers['user-agent'],
      fingerprint: fingerprint || null,
      sentinel: sentinel || null,
      fingerprintHash: fingerprint?.workerScope?.$hash || null,
      sentinelHash: sentinel ? crypto.createHash('sha256').update(JSON.stringify(sentinel)).digest('hex') : null
    };
    
    loginLogs.push(loginRecord);
    
    if (fingerprint || sentinel) {
      fingerprintData.push({
        ...loginRecord,
        fullFingerprint: fingerprint,
        fullSentinel: sentinel
      });
    }
    
    // 保存到文件（可選）
    saveLogsToFile();
    
    if (isValid) {
      res.json({
        success: true,
        message: '登入成功',
        sessionId: loginRecord.id,
        fingerprintHash: loginRecord.fingerprintHash,
        sentinelHash: loginRecord.sentinelHash
      });
    } else {
      res.status(401).json({
        success: false,
        message: '登入失敗：用戶名或密碼無效'
      });
    }
  } catch (error) {
    console.error('登入錯誤:', error);
    res.status(500).json({
      success: false,
      message: '服務器錯誤',
      error: error.message
    });
  }
});

// API: 獲取登入記錄
app.get('/api/logs', (req, res) => {
  const limit = parseInt(req.query.limit) || 100;
  res.json({
    success: true,
    count: loginLogs.length,
    logs: loginLogs.slice(-limit).reverse()
  });
});

// API: 獲取指紋數據
app.get('/api/fingerprints', (req, res) => {
  const limit = parseInt(req.query.limit) || 100;
  res.json({
    success: true,
    count: fingerprintData.length,
    fingerprints: fingerprintData.slice(-limit).reverse()
  });
});

// API: 清除記錄（僅用於測試）
app.delete('/api/logs', (req, res) => {
  loginLogs.length = 0;
  fingerprintData.length = 0;
  res.json({ success: true, message: '記錄已清除' });
});

// 保存日誌到文件
function saveLogsToFile() {
  const logsDir = join(__dirname, 'logs');
  if (!fs.existsSync(logsDir)) {
    fs.mkdirSync(logsDir, { recursive: true });
  }
  
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const logFile = join(logsDir, `login-${timestamp}.json`);
  
  try {
    fs.writeFileSync(logFile, JSON.stringify({
      loginLogs,
      fingerprintData
    }, null, 2));
  } catch (error) {
    console.error('保存日誌失敗:', error);
  }
}

// 啟動服務器
app.listen(PORT, () => {
  console.log(`🚀 登入網站服務器運行在 http://localhost:${PORT}`);
  console.log(`📝 API 文檔:`);
  console.log(`   POST /api/login - 登入`);
  console.log(`   GET  /api/logs - 獲取登入記錄`);
  console.log(`   GET  /api/fingerprints - 獲取指紋數據`);
  console.log(`   DELETE /api/logs - 清除記錄`);
});

