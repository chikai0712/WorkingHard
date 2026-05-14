#!/usr/bin/env node

/**
 * 快速測試腳本
 * 用於驗證數據生成器是否正常工作
 */

import { generateFingerprint, generateCreep } from './generators/fingerprint.js';
import { getFuzzyHash } from './utils/fuzzyHash.js';
import crypto from 'crypto';

async function test() {
  console.log('🧪 開始測試 CreepJS 數據生成器...\n');

  try {
    // 測試 1: 生成指紋
    console.log('1. 測試指紋生成...');
    const fingerprint = generateFingerprint();
    console.log('   ✓ 指紋生成成功');
    console.log(`   - Worker Scope: ${fingerprint.workerScope ? '✓' : '✗'}`);
    console.log(`   - Navigator: ${fingerprint.navigator ? '✓' : '✗'}`);
    console.log(`   - Screen: ${fingerprint.screen ? '✓' : '✗'}`);
    console.log(`   - Canvas 2D: ${fingerprint.canvas2d ? '✓' : '✗'}`);
    console.log(`   - WebGL: ${fingerprint.canvasWebgl ? '✓' : '✗'}`);
    console.log(`   - Timezone: ${fingerprint.timezone ? '✓' : '✗'}`);
    console.log(`   - Fonts: ${fingerprint.fonts ? '✓' : '✗'}`);
    console.log(`   - Audio: ${fingerprint.offlineAudioContext ? '✓' : '✗'}`);

    // 驗證哈希
    if (fingerprint.workerScope?.$hash) {
      console.log(`   - Worker Scope Hash: ${fingerprint.workerScope.$hash.substring(0, 16)}...`);
    }

    // 測試 2: 生成 Creep
    console.log('\n2. 測試 Creep 生成...');
    const creep = generateCreep(fingerprint);
    console.log('   ✓ Creep 生成成功');
    console.log(`   - Navigator: ${creep.navigator ? '✓' : '✗'}`);
    console.log(`   - Screen: ${creep.screen ? '✓' : '✗'}`);
    console.log(`   - Worker Scope: ${creep.workerScope ? '✓' : '✗'}`);
    console.log(`   - Canvas 2D: ${creep.canvas2d ? '✓' : '✗'}`);
    console.log(`   - Canvas WebGL: ${creep.canvasWebgl ? '✓' : '✗'}`);
    console.log(`   - Force Renew: ${creep.forceRenew ? '✓' : '✗'}`);

    // 測試 3: 生成模糊哈希
    console.log('\n3. 測試模糊哈希生成...');
    const fuzzyHash = await getFuzzyHash(fingerprint);
    console.log(`   ✓ 模糊哈希生成成功: ${fuzzyHash.substring(0, 16)}...`);
    console.log(`   - 長度: ${fuzzyHash.length} (應為 64)`);
    
    if (fuzzyHash.length === 64) {
      console.log('   ✓ 模糊哈希長度正確');
    } else {
      console.log('   ✗ 模糊哈希長度不正確');
      return false;
    }

    // 測試 4: 驗證數據完整性
    console.log('\n4. 測試數據完整性...');
    const fpHash = fingerprint.workerScope?.$hash || 
                  crypto.createHash('sha256').update(JSON.stringify(fingerprint)).digest('hex');
    const cHash = crypto.createHash('sha256').update(JSON.stringify(creep)).digest('hex');
    
    console.log(`   ✓ Fingerprint Hash: ${fpHash.substring(0, 16)}...`);
    console.log(`   ✓ Creep Hash: ${cHash.substring(0, 16)}...`);
    console.log(`   ✓ Fuzzy Hash: ${fuzzyHash.substring(0, 16)}...`);

    // 測試 5: 批量生成測試
    console.log('\n5. 測試批量生成...');
    const batch = [];
    for (let i = 0; i < 5; i++) {
      const fp = generateFingerprint();
      const cr = generateCreep(fp);
      const fh = await getFuzzyHash(fp);
      batch.push({ fp, cr, fh });
    }
    console.log(`   ✓ 批量生成成功 (${batch.length} 個)`);
    
    // 驗證每個都有不同的哈希
    const hashes = batch.map(b => b.fp.workerScope?.$hash || '');
    const uniqueHashes = new Set(hashes);
    if (uniqueHashes.size === batch.length) {
      console.log('   ✓ 每個指紋都有唯一的哈希');
    } else {
      console.log(`   ⚠ 警告: 有重複的哈希 (${uniqueHashes.size}/${batch.length})`);
    }

    // 測試 6: 驗證 JSON 序列化
    console.log('\n6. 測試 JSON 序列化...');
    const json = JSON.stringify({
      fingerprint,
      creep,
      fuzzyHash
    });
    const parsed = JSON.parse(json);
    console.log('   ✓ JSON 序列化/反序列化成功');
    console.log(`   - JSON 大小: ${(json.length / 1024).toFixed(2)} KB`);

    console.log('\n✅ 所有測試通過！');
    return true;
  } catch (error) {
    console.error('\n❌ 測試失敗:', error.message);
    if (error.stack) {
      console.error(error.stack);
    }
    return false;
  }
}

// 運行測試
test().then(success => {
  process.exit(success ? 0 : 1);
}).catch(error => {
  console.error('未處理的錯誤:', error);
  process.exit(1);
});
