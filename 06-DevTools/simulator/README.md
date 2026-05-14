# CreepJS 指紋數據生成器

這個工具可以生成 CreepJS 識別玩家時產生的指紋數據，輸出為 JSON 格式。

## 功能特點

- ✅ 生成完整的 CreepJS 指紋數據結構
- ✅ 生成 Stable Fingerprint (Creep) 數據
- ✅ 生成模糊指紋哈希 (Fuzzy Hash)
- ✅ 支持單個或批量生成
- ✅ 輸出為 JSON 格式，方便集成到現有系統

## 安裝

```bash
cd simulator
npm install
```

## 使用方法

### 生成單個指紋（輸出到 stdout）

```bash
node index.js
# 或
node index.js --generate
# 或
npm start
```

輸出為 JSON 格式，可以直接管道到其他程序：

```bash
node index.js | jq .
```

### 生成單個指紋並保存到文件

```bash
node index.js --output data.json
# 或
node index.js -o data.json
```

### 生成多個指紋

```bash
node index.js --generate 10
# 或
node index.js -g 10
```

### 批量生成並保存到目錄

```bash
node index.js --batch 100
# 或
node index.js --batch 100 ./output
# 或
node index.js -b 100 ./output
```

### 查看幫助

```bash
node index.js --help
# 或
node index.js -h
```

## 輸出格式

生成的數據結構如下：

```json
{
  "sessionId": "會話 ID",
  "timestamp": 時間戳,
  "fingerprintHash": "指紋哈希 (SHA-256)",
  "creepHash": "Creep 哈希 (SHA-256)",
  "fuzzyHash": "模糊哈希 (64 位)",
  "timeEnd": 執行時間(ms),
  "fingerprint": {
    "workerScope": { ... },
    "navigator": { ... },
    "screen": { ... },
    "canvas2d": { ... },
    "canvasWebgl": { ... },
    "timezone": { ... },
    "fonts": { ... },
    "offlineAudioContext": { ... },
    "voices": { ... },
    "media": { ... },
    "cssMedia": { ... },
    "css": { ... },
    "lies": { ... },
    "resistance": { ... },
    "headless": { ... },
    ...
  },
  "creep": {
    "navigator": { ... },
    "screen": { ... },
    "workerScope": { ... },
    "media": { ... },
    "canvas2d": { ... },
    "canvasWebgl": { ... },
    "cssMedia": { ... },
    "css": { ... },
    "timezone": { ... },
    "offlineAudioContext": { ... },
    "fonts": { ... },
    "forceRenew": 時間戳
  }
}
```

## 數據結構說明

### Fingerprint (Loose Fingerprint)

包含所有原始收集的數據：
- **workerScope** - Worker 環境數據（設備內存、CPU 核心數、GPU 信息等）
- **navigator** - Navigator API 數據（User Agent、語言、權限等）
- **screen** - 螢幕屬性（分辨率、顏色深度等）
- **canvas2d** - Canvas 2D 指紋數據
- **canvasWebgl** - WebGL 指紋數據
- **timezone** - 時區信息
- **fonts** - 字體信息
- **offlineAudioContext** - 音頻指紋
- **voices** - 語音合成信息
- **media** - 媒體設備信息
- **cssMedia** - CSS 媒體查詢
- **css** - CSS 相關數據
- **lies** - 謊言檢測結果
- **resistance** - 反指紋檢測結果
- **headless** - 無頭瀏覽器檢測

### Creep (Stable Fingerprint)

過濾後的穩定指紋，只包含可信的數據（過濾掉有 `lied: true` 的數據）。

### Fuzzy Hash

64 位的模糊指紋哈希，用於相似度匹配。基於 CreepJS 的模糊哈希算法。

## 程序化使用

### 在 Node.js 中使用

```javascript
import { generateFingerprint, generateCreep } from './generators/fingerprint.js';
import { getFuzzyHash } from './utils/fuzzyHash.js';

// 生成指紋
const fingerprint = generateFingerprint();
const creep = generateCreep(fingerprint);
const fuzzyHash = await getFuzzyHash(fingerprint);

// 使用數據
console.log('Fingerprint Hash:', fingerprint.workerScope?.$hash);
console.log('Creep Hash:', crypto.createHash('sha256').update(JSON.stringify(creep)).digest('hex'));
console.log('Fuzzy Hash:', fuzzyHash);
```

### 批量生成

```javascript
import { generateFingerprint, generateCreep } from './generators/fingerprint.js';
import { getFuzzyHash } from './utils/fuzzyHash.js';

async function generateBatch(count) {
  const results = [];
  
  for (let i = 0; i < count; i++) {
    const fingerprint = generateFingerprint();
    const creep = generateCreep(fingerprint);
    const fuzzyHash = await getFuzzyHash(fingerprint);
    
    results.push({
      fingerprint,
      creep,
      fuzzyHash
    });
  }
  
  return results;
}

const batch = await generateBatch(100);
console.log(`生成了 ${batch.length} 個指紋`);
```

## 集成到現有系統

由於輸出為標準 JSON 格式，可以輕鬆集成到現有系統：

### 保存到數據庫

```bash
# 生成並保存到 MongoDB
node index.js | mongoimport --db creepjs --collection fingerprints

# 生成並保存到 PostgreSQL
node index.js | psql -c "COPY fingerprints FROM STDIN JSON"
```

### 發送到 API

```bash
# 發送到 REST API
node index.js | curl -X POST https://api.example.com/fingerprints \
  -H "Content-Type: application/json" \
  -d @-
```

### 處理數據流

```bash
# 使用 jq 處理數據
node index.js | jq '.fingerprint.workerScope.system'

# 提取特定字段
node index.js | jq '{sessionId, fingerprintHash, fuzzyHash}'
```

## 自定義數據生成

可以修改 `generators/fingerprint.js` 來自定義數據生成邏輯：

```javascript
// 例如：只生成 Windows 系統的指紋
export function generateWorkerScope() {
  const data = {
    platform: 'Win32',
    system: 'Windows',
    // ... 其他數據
  };
  return { ...data, $hash: hashify(data) };
}
```

## 注意事項

- 生成的數據是模擬數據，僅用於測試和開發
- 所有數據都是隨機生成的，不代表真實的瀏覽器環境
- 可以根據需要修改生成器來產生特定類型的數據

## 開發

### 添加新的數據生成器

在 `generators/fingerprint.js` 中添加新的生成函數，然後在 `generateFingerprint()` 中調用。

### 修改數據結構

直接修改 `generators/fingerprint.js` 中的生成函數來調整數據結構。

## 許可證

與 CreepJS 主項目相同。
