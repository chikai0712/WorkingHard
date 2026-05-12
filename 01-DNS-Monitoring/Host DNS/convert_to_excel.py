#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
將 Markdown 文檔中的表格轉換為 Excel 可用的格式（Tab 分隔）
"""

import re

def extract_tables_from_markdown(content):
    """從 Markdown 內容中提取所有表格"""
    # 找到所有表格（以 | 開頭的行，跳過分隔線）
    lines = content.split('\n')
    tables = []
    current_table = []
    in_table = False
    
    for line in lines:
        # 檢查是否是表格行
        if '|' in line:
            # 跳過分隔線（只包含 - 和 | 和空格的行的行）
            if not re.match(r'^[\|\s\-:]+$', line):
                # 解析表格行
                cells = [cell.strip() for cell in line.split('|')[1:-1]]
                current_table.append(cells)
                in_table = True
        else:
            # 表格結束
            if in_table and current_table:
                tables.append(current_table)
                current_table = []
                in_table = False
    
    # 處理最後一個表格
    if current_table:
        tables.append(current_table)
    
    return tables

def format_for_excel(tables_data):
    """將表格數據格式化為 Excel 可用的格式（Tab 分隔）"""
    output = []
    output.append("DNS 三種方案完整比較分析 - Excel 格式\n")
    output.append("=" * 100 + "\n")
    output.append("幣別：所有費用均以美金（USD）計價\n")
    output.append("費用計算基準：20億次/月，峰值20k QPS\n\n")
    
    for i, table in enumerate(tables_data):
        if not table:
            continue
        
        # 輸出表格（使用 Tab 分隔）
        for row in table:
            # 清理 Markdown 格式（移除 ** 等）
            cleaned_row = [re.sub(r'\*\*(.*?)\*\*', r'\1', cell) for cell in row]
            output.append('\t'.join(cleaned_row) + '\n')
        
        # 表格之間添加空行
        output.append('\n')
    
    return ''.join(output)

def main():
    # 讀取 Markdown 文件
    with open('DNS三種方案完整比較分析.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取所有表格
    tables = extract_tables_from_markdown(content)
    
    # 格式化為 Excel 格式
    excel_content = format_for_excel(tables)
    
    # 寫入文件（使用 UTF-8 with BOM，Excel 可以正確識別中文）
    with open('DNS三種方案完整比較分析_Excel格式.txt', 'w', encoding='utf-8-sig') as f:
        f.write(excel_content)
    
    print(f"已創建 Excel 格式文件: DNS三種方案完整比較分析_Excel格式.txt")
    print(f"共提取 {len(tables)} 個表格")
    print("\n使用方法：")
    print("1. 直接打開 .txt 文件（Excel 會自動識別 Tab 分隔）")
    print("2. 或複製內容貼到 Excel 中")

if __name__ == '__main__':
    main()

