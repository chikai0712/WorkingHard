#!/usr/bin/env python3
"""
使用 GPT-4.0 分析域名檢測結果
自動生成專業的分析報告和建議
"""

import os
import sys
import json
from openai import OpenAI

def read_detection_log(log_file):
    """讀取檢測日誌"""
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ 錯誤: 找不到日誌文件 {log_file}")
        sys.exit(1)

def analyze_with_gpt4(log_content, api_key):
    """使用 GPT-4.0 分析檢測結果"""
    
    client = OpenAI(api_key=api_key)
    
    prompt = f"""你是一位專業的網絡安全和 DNS 專家。請分析以下域名檢測日誌，並提供詳細的分析報告。

檢測日誌：
{log_content}

請提供以下分析：

1. **執行摘要**
   - 總體健康狀況評估
   - 關鍵發現（3-5 點）
   - 緊急程度評級（低/中/高）

2. **詳細分析**
   - CLEAN 域名：正常運作的域名及其特徵
   - BLOCKED 域名：被 DNS 污染的域名，分析污染模式
   - TIMEOUT 域名：完全無法訪問的域名，可能原因
   - WARNING 域名：服務異常的域名，HTTP 錯誤分析
   - PARTIAL 域名：部分地區異常的域名，區域性問題分析

3. **風險評估**
   - 業務影響分析
   - 用戶體驗影響
   - 潛在的安全風險

4. **技術建議**
   - 短期應對措施（立即執行）
   - 中期優化方案（1-2 週內）
   - 長期架構改進（1-3 個月）

5. **監控建議**
   - 需要重點監控的域名
   - 建議的監控頻率
   - 告警閾值設定

請用繁體中文回答，使用專業但易懂的語言，並使用適當的 emoji 來增強可讀性。"""

    print("🤖 正在使用 GPT-4.0 分析檢測結果...")
    print("⏳ 這可能需要 10-30 秒，請稍候...\n")
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "你是一位專業的網絡安全和 DNS 專家，擅長分析域名檢測結果並提供可執行的建議。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2500
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"❌ GPT-4 API 調用失敗: {str(e)}")
        sys.exit(1)

def save_report(analysis, output_file):
    """保存分析報告"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("GPT-4.0 域名檢測分析報告\n")
        f.write("=" * 80 + "\n\n")
        f.write(analysis)
        f.write("\n\n" + "=" * 80 + "\n")
        f.write(f"報告生成時間: {os.popen('date').read().strip()}\n")
        f.write("=" * 80 + "\n")
    
    print(f"✅ 分析報告已保存: {output_file}")

def main():
    # 檢查參數
    if len(sys.argv) < 2:
        print("用法: python3 gpt4_domain_analyzer.py <檢測日誌文件> [OpenAI API Key]")
        print("\n範例:")
        print("  python3 gpt4_domain_analyzer.py ~/globalping_1215_1430.log")
        print("  python3 gpt4_domain_analyzer.py ~/globalping_1215_1430.log sk-xxx...")
        print("\n說明:")
        print("  - 如果不提供 API Key，將從環境變數 OPENAI_API_KEY 讀取")
        print("  - 可以在 ~/.bashrc 或 ~/.zshrc 中設置:")
        print("    export OPENAI_API_KEY='your-api-key-here'")
        sys.exit(1)
    
    log_file = sys.argv[1]
    
    # 獲取 API Key
    if len(sys.argv) >= 3:
        api_key = sys.argv[2]
    else:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌ 錯誤: 未提供 OpenAI API Key")
            print("\n請使用以下方式之一提供 API Key:")
            print("  1. 命令行參數: python3 gpt4_domain_analyzer.py <日誌> <API_KEY>")
            print("  2. 環境變數: export OPENAI_API_KEY='your-api-key-here'")
            sys.exit(1)
    
    print("=" * 80)
    print("GPT-4.0 域名檢測分析工具")
    print("=" * 80)
    print(f"📄 日誌文件: {log_file}")
    print(f"🤖 AI 模型: GPT-4.0")
    print("=" * 80)
    print()
    
    # 讀取日誌
    log_content = read_detection_log(log_file)
    
    # 使用 GPT-4 分析
    analysis = analyze_with_gpt4(log_content, api_key)
    
    # 顯示分析結果
    print("\n" + "=" * 80)
    print("📊 GPT-4.0 分析結果")
    print("=" * 80)
    print()
    print(analysis)
    print()
    
    # 保存報告
    output_file = log_file.replace('.log', '_gpt4_analysis.txt')
    if output_file == log_file:
        output_file = log_file + '_gpt4_analysis.txt'
    
    save_report(analysis, output_file)
    
    print()
    print("=" * 80)
    print("✅ 分析完成")
    print("=" * 80)

if __name__ == '__main__':
    main()
