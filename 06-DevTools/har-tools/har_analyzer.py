import json
import pandas as pd
import os

# 1. 自動尋找資料夾中的 .har 檔案
har_files = [f for f in os.listdir('.') if f.endswith('.har')]
if not har_files:
    print("找不到 .har 檔案！請確保檔案放在此目錄下。")
    exit()

har_file = har_files[0]
print(f"正在分析檔案: {har_file}")

with open(har_file, 'r', encoding='utf-8') as f:
    har_data = json.load(f)

rows = []
for entry in har_data['log']['entries']:
    req = entry['request']
    res = entry['response']
    
    rows.append({
        'StartedTime': entry['startedDateTime'],
        'Method': req.get('method'),
        'URL': req.get('url'),
        'Path': req.get('url').split('?')[0],
        'Status': res.get('status'),
        'MimeType': res['content'].get('mimeType'),
        'Wait_TTFB(ms)': entry['timings'].get('wait'),
        'TransferSize(bytes)': res.get('_transferSize', 0),
        'Initiator': entry.get('_initiator', {}).get('type', 'N/A')
    })

df = pd.DataFrame(rows)
output_name = 'website_structure_analysis.csv'
df.to_csv(output_name, index=False, encoding='utf-8-sig')

print(f"--- 轉換完成 ---")
print(f"已產出檔案: {output_name}")
