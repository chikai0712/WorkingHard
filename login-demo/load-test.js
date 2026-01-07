#!/usr/bin/env node

/**
 * 壓測工具：使用 Puppeteer 模擬瀏覽器登入
 * 
 * 用法:
 *   node load-test.js [選項]
 * 
 * 選項:
 *   --url <url>           目標網站 URL (默認: http://localhost:3000)
 *   --count <number>      登入次數 (默認: 10)
 *   --concurrent <number> 並發數 (默認: 3)
 *   --delay <ms>          每次登入間隔 (毫秒, 默認: 1000)
 *   --username <name>     用戶名 (默認: testuser)
 *   --password <pass>     密碼 (默認: testpass123)
 *   --headless            無頭模式 (默認: false)
 *   --help                顯示幫助
 */

import puppeteer from 'puppeteer';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// 解析命令行參數
const args = process.argv.slice(2);
const config = {
  url: 'http://localhost:3000',
  count: 10,
  concurrent: 3,
  delay: 1000,
  username: 'testuser',
  password: 'testpass123',
  headless: false
};

// 解析參數
for (let i = 0; i < args.length; i++) {
  const arg = args[i];
  if (arg === '--url' && args[i + 1]) {
    config.url = args[i + 1];
    i++;
  } else if (arg === '--count' && args[i + 1]) {
    config.count = parseInt(args[i + 1]);
    i++;
  } else if (arg === '--concurrent' && args[i + 1]) {
    config.concurrent = parseInt(args[i + 1]);
    i++;
  } else if (arg === '--delay' && args[i + 1]) {
    config.delay = parseInt(args[i + 1]);
    i++;
  } else if (arg === '--username' && args[i + 1]) {
    config.username = args[i + 1];
    i++;
  } else if (arg === '--password' && args[i + 1]) {
    config.password = args[i + 1];
    i++;
  } else if (arg === '--headless') {
    config.headless = true;
  } else if (arg === '--help' || arg === '-h') {
    console.log(`
壓測工具：使用 Puppeteer 模擬瀏覽器登入

用法:
  node load-test.js [選項]

選項:
  --url <url>           目標網站 URL (默認: http://localhost:3000)
  --count <number>      登入次數 (默認: 10)
  --concurrent <number> 並發數 (默認: 3)
  --delay <ms>          每次登入間隔 (毫秒, 默認: 1000)
  --username <name>     用戶名 (默認: testuser)
  --password <pass>     密碼 (默認: testpass123)
  --headless            無頭模式 (默認: false)
  --help                顯示幫助

示例:
  node load-test.js --count 20 --concurrent 5
  node load-test.js --url http://localhost:3000 --count 50 --headless
    `);
    process.exit(0);
  }
}

// 統計信息
const stats = {
  total: 0,
  success: 0,
  failed: 0,
  errors: [],
  startTime: null,
  endTime: null
};

/**
 * 執行單次登入
 */
async function performLogin(browser, index) {
  const page = await browser.newPage();
  
  try {
    // 設置視窗大小
    await page.setViewport({ width: 1920, height: 1080 });
    
    // 訪問登入頁面
    console.log(`[${index}] 訪問登入頁面...`);
    await page.goto(config.url, { 
      waitUntil: 'networkidle2',
      timeout: 30000 
    });
    
    // 等待 SentinelJS 加載完成（最多等待 10 秒）
    console.log(`[${index}] 等待 SentinelJS 加載...`);
    await page.waitForFunction(
      () => window.Fingerprint && window.Creep,
      { timeout: 10000 }
    ).catch(() => {
      console.warn(`[${index}] ⚠️ SentinelJS 加載超時，繼續執行...`);
    });
    
    // 填寫表單
    console.log(`[${index}] 填寫登入表單...`);
    await page.type('#username', config.username);
    await page.type('#password', config.password);
    
    // 提交表單
    console.log(`[${index}] 提交登入表單...`);
    const [response] = await Promise.all([
      page.waitForResponse(resp => resp.url().includes('/api/login')),
      page.click('#submitBtn')
    ]);
    
    // 獲取響應結果
    const result = await response.json();
    
    if (result.success) {
      console.log(`[${index}] ✅ 登入成功 | Session: ${result.sessionId}`);
      if (result.fingerprintHash) {
        console.log(`[${index}]   指紋哈希: ${result.fingerprintHash.substring(0, 16)}...`);
      }
      stats.success++;
      return { success: true, index, result };
    } else {
      console.log(`[${index}] ❌ 登入失敗: ${result.message}`);
      stats.failed++;
      return { success: false, index, error: result.message };
    }
  } catch (error) {
    console.error(`[${index}] ❌ 錯誤:`, error.message);
    stats.failed++;
    stats.errors.push({ index, error: error.message });
    return { success: false, index, error: error.message };
  } finally {
    await page.close();
  }
}

/**
 * 執行並發登入
 */
async function runConcurrentLogins(browser, count) {
  const tasks = [];
  for (let i = 0; i < count; i++) {
    tasks.push(performLogin(browser, stats.total + i + 1));
    stats.total++;
    
    // 延遲
    if (i < count - 1) {
      await new Promise(resolve => setTimeout(resolve, config.delay));
    }
  }
  
  return Promise.all(tasks);
}

/**
 * 主函數
 */
async function main() {
  console.log('\n🚀 開始壓測...\n');
  console.log('配置:');
  console.log(`  目標 URL: ${config.url}`);
  console.log(`  總次數: ${config.count}`);
  console.log(`  並發數: ${config.concurrent}`);
  console.log(`  延遲: ${config.delay}ms`);
  console.log(`  用戶名: ${config.username}`);
  console.log(`  無頭模式: ${config.headless}\n`);
  
  stats.startTime = Date.now();
  
  // 啟動瀏覽器
  const browser = await puppeteer.launch({
    headless: config.headless,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage'
    ]
  });
  
  try {
    // 分批執行
    const batchCount = Math.ceil(config.count / config.concurrent);
    
    for (let batch = 0; batch < batchCount; batch++) {
      const remaining = config.count - (batch * config.concurrent);
      const currentBatch = Math.min(config.concurrent, remaining);
      
      console.log(`\n📦 批次 ${batch + 1}/${batchCount} (${currentBatch} 個並發請求)\n`);
      
      await runConcurrentLogins(browser, currentBatch);
      
      // 批次間延遲
      if (batch < batchCount - 1) {
        await new Promise(resolve => setTimeout(resolve, config.delay * 2));
      }
    }
  } finally {
    await browser.close();
  }
  
  stats.endTime = Date.now();
  const duration = ((stats.endTime - stats.startTime) / 1000).toFixed(2);
  
  // 輸出統計結果
  console.log('\n' + '='.repeat(50));
  console.log('📊 壓測結果');
  console.log('='.repeat(50));
  console.log(`總次數: ${stats.total}`);
  console.log(`成功: ${stats.success} (${((stats.success / stats.total) * 100).toFixed(1)}%)`);
  console.log(`失敗: ${stats.failed} (${((stats.failed / stats.total) * 100).toFixed(1)}%)`);
  console.log(`總耗時: ${duration} 秒`);
  console.log(`平均: ${(duration / stats.total).toFixed(2)} 秒/次`);
  console.log(`QPS: ${(stats.total / parseFloat(duration)).toFixed(2)} 次/秒`);
  
  if (stats.errors.length > 0) {
    console.log('\n❌ 錯誤列表:');
    stats.errors.forEach(({ index, error }) => {
      console.log(`  [${index}] ${error}`);
    });
  }
  
  console.log('='.repeat(50) + '\n');
}

// 運行主函數
main().catch(error => {
  console.error('\n❌ 壓測失敗:', error);
  process.exit(1);
});

