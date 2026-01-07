#!/usr/bin/env node

import { generateFingerprint, generateCreep } from './generators/fingerprint.js';
import { getFuzzyHash } from './utils/fuzzyHash.js';
import crypto from 'crypto';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * 生成會話 ID
 */
function generateSessionId() {
  return crypto.randomBytes(16).toString('hex');
}

/**
 * 生成單個指紋數據
 */
async function generateFingerprintData(sessionId = null) {
  const sid = sessionId || generateSessionId();
  
  // 生成指紋
  const fingerprint = generateFingerprint();
  const creep = generateCreep(fingerprint);
  const fuzzyHash = await getFuzzyHash(fingerprint);
  
  // 計算時間（模擬）
  const timeEnd = Math.random() * 1000 + 500; // 500-1500ms
  
  // 計算哈希
  const fpHash = fingerprint.workerScope?.$hash || 
                crypto.createHash('sha256').update(JSON.stringify(fingerprint)).digest('hex');
  const cHash = crypto.createHash('sha256').update(JSON.stringify(creep)).digest('hex');
  
  return {
    sessionId: sid,
    timestamp: Date.now(),
    fingerprintHash: fpHash,
    creepHash: cHash,
    fuzzyHash: fuzzyHash,
    timeEnd: timeEnd,
    fingerprint: fingerprint,
    creep: creep
  };
}

/**
 * 批量生成
 */
async function batchGenerate(count = 10, outputDir = null) {
  console.log(`\n開始批量生成 ${count} 個指紋...\n`);
  
  const results = [];
  const startTime = Date.now();
  
  for (let i = 0; i < count; i++) {
    try {
      const data = await generateFingerprintData();
      results.push(data);
      
      // 顯示進度
      const progress = ((i + 1) / count * 100).toFixed(1);
      process.stdout.write(`\r進度: ${progress}% (${i + 1}/${count})`);
    } catch (error) {
      console.error(`\n生成第 ${i + 1} 個指紋時出錯:`, error.message);
    }
    
    // 小延遲避免過快
    await new Promise(resolve => setTimeout(resolve, 10));
  }
  
  const endTime = Date.now();
  const duration = ((endTime - startTime) / 1000).toFixed(2);
  
  console.log(`\n\n✓ 批量生成完成！`);
  console.log(`  - 總數: ${results.length}`);
  console.log(`  - 耗時: ${duration} 秒`);
  console.log(`  - 平均: ${(duration / results.length).toFixed(2)} 秒/個`);
  
  // 如果指定了輸出目錄，保存到文件
  if (outputDir) {
    const outputPath = path.join(outputDir, `fingerprints_${Date.now()}.json`);
    fs.writeFileSync(outputPath, JSON.stringify(results, null, 2));
    console.log(`  - 已保存到: ${outputPath}`);
  }
  
  return results;
}

/**
 * 主函數
 */
async function main() {
  const args = process.argv.slice(2);
  const command = args[0];
  
  try {
    if (command === '--generate' || command === '-g') {
      // 生成單個或多個指紋
      const count = parseInt(args[1]) || 1;
      
      if (count === 1) {
        // 單個：輸出到 stdout
        const data = await generateFingerprintData();
        console.log(JSON.stringify(data, null, 2));
      } else {
        // 多個：批量生成
        const outputDir = args[2] ? path.resolve(args[2]) : null;
        await batchGenerate(count, outputDir);
      }
    } else if (command === '--batch' || command === '-b') {
      // 批量生成
      const count = parseInt(args[1]) || 10;
      const outputDir = args[2] ? path.resolve(args[2]) : null;
      await batchGenerate(count, outputDir);
    } else if (command === '--output' || command === '-o') {
      // 生成並輸出到文件
      const outputPath = args[1] || `fingerprint_${Date.now()}.json`;
      const data = await generateFingerprintData();
      fs.writeFileSync(outputPath, JSON.stringify(data, null, 2));
      console.log(`✓ 指紋已保存到: ${outputPath}`);
    } else if (command === '--help' || command === '-h') {
      // 顯示幫助
      console.log('CreepJS 指紋數據生成器');
      console.log('');
      console.log('用法:');
      console.log('  node index.js [選項]');
      console.log('');
      console.log('選項:');
      console.log('  --generate, -g [數量] [輸出目錄]  生成指紋（默認 1 個，輸出到 stdout）');
      console.log('  --batch, -b [數量] [輸出目錄]     批量生成指紋（默認 10 個）');
      console.log('  --output, -o [文件路徑]           生成一個指紋並保存到文件');
      console.log('  --help, -h                       顯示此幫助信息');
      console.log('');
      console.log('示例:');
      console.log('  node index.js -g                    # 生成 1 個指紋，輸出到 stdout');
      console.log('  node index.js -g 5                  # 生成 5 個指紋，顯示進度');
      console.log('  node index.js -g 10 ./output        # 生成 10 個指紋，保存到 ./output');
      console.log('  node index.js -b 100                # 批量生成 100 個指紋');
      console.log('  node index.js -o data.json          # 生成 1 個指紋，保存到 data.json');
      console.log('');
      console.log('輸出格式:');
      console.log('  {');
      console.log('    "sessionId": "會話 ID",');
      console.log('    "timestamp": 時間戳,');
      console.log('    "fingerprintHash": "指紋哈希",');
      console.log('    "creepHash": "Creep 哈希",');
      console.log('    "fuzzyHash": "模糊哈希",');
      console.log('    "timeEnd": 執行時間(ms),');
      console.log('    "fingerprint": { ... },  // 完整的 Fingerprint 數據');
      console.log('    "creep": { ... }          // Creep (Stable) 數據');
      console.log('  }');
    } else {
      // 默認：生成一個並輸出到 stdout
      const data = await generateFingerprintData();
      console.log(JSON.stringify(data, null, 2));
    }
  } catch (error) {
    console.error('\n✗ 錯誤:', error.message);
    if (error.stack) {
      console.error(error.stack);
    }
    process.exit(1);
  }
}

// 運行主函數
main().catch(error => {
  console.error('未處理的錯誤:', error);
  process.exit(1);
});
