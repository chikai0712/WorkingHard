import json
import pandas as pd
import os

# 1. 尋找資料夾中的 .har 檔案
har_files = [f for f in os.listdir('.') if f.endswith('.har')]
if not har_files:
    print("❌ 錯誤：資料夾內找不到 .har 檔案！")
    exit()

har_file = har_files[0]
print(f"🔍 正在深度分析: {har_file}")

with open(har_file, 'r', encoding='utf-8') as f:
    har_data = json.load(f)

rows = []
for entry in har_data['log']['entries']:
    req = entry['request']
    res = entry['response']
    
    # 提取 Request Payload (發送的 JSON 資料)
    payload = "N/A"
    if 'postData' in req and 'text' in req['postData']:
        payload = req['postData']['text']
    
    # 提取 Response Body (回傳的結果)
    # 僅提取 JSON 類型，避免抓到龐大的圖片或 JS 二進位檔
    response_text = "N/A"
    mime_type = res['content'].get('mimeType', '')
    if 'application/json' in mime_type and 'text' in res['content']:
        response_text = res['content']['text']

    rows.append({
        'Time': entry['startedDateTime'],
        'Method': req.get('method'),
        'URL': req.get('url'),
        'Payload': payload,
        'Response': response_text,
        'Status': res.get('status')
    })

# 2. 匯出 CSV (使用 utf-8-sig 以確保 Excel 開啟不編碼錯誤)
df = pd.DataFrame(rows)
output_name = 'dev_sequence_details.csv'
df.to_csv(output_name, index=False, encoding='utf-8-sig')

print(f"✅ 成功！已產生開發專用詳細表：{output_name}")
print(f"📊 共擷取 {len(df)} 筆互動細節。")
