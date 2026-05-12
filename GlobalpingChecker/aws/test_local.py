#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地測試腳本 - 在部署到 AWS 前測試 Lambda 函數
"""

import json
import os
import sys

# 設置環境變數
os.environ['S3_BUCKET_NAME'] = 'test-bucket'
os.environ['DOMAINS_S3_KEY'] = 'domains.txt'
os.environ['SNS_TOPIC_ARN'] = ''
os.environ['GLOBALPING_TOKEN'] = ''

# 模擬 boto3 (本地測試不需要真實的 AWS 服務)
class MockS3Client:
    def get_object(self, Bucket, Key):
        # 讀取本地測試文件
        test_file = '../test_2_domains.txt'
        if os.path.exists(test_file):
            with open(test_file, 'r') as f:
                content = f.read()
            
            class Body:
                def __init__(self, content):
                    self.content = content
                
                def read(self):
                    return self.content.encode('utf-8')
            
            return {'Body': Body(content)}
        else:
            raise Exception(f"測試文件不存在: {test_file}")
    
    def put_object(self, Bucket, Key, Body, ContentType):
        # 保存到本地
        output_dir = './test_output'
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, os.path.basename(Key))
        with open(output_file, 'w') as f:
            f.write(Body if isinstance(Body, str) else Body.decode('utf-8'))
        
        print(f"✓ 結果已保存: {output_file}")

class MockSNSClient:
    def publish(self, TopicArn, Subject, Message):
        print(f"\n=== SNS 通知 ===")
        print(f"主題: {Subject}")
        print(f"內容:\n{Message}")

# 替換 boto3
sys.modules['boto3'] = type(sys)('boto3')
sys.modules['boto3'].client = lambda service: MockS3Client() if service == 's3' else MockSNSClient()

# 導入 Lambda 函數
from lambda_function import lambda_handler

def main():
    print("=" * 60)
    print("Globalping Checker - 本地測試")
    print("=" * 60)
    print()
    
    # 檢查測試文件
    test_file = '../test_2_domains.txt'
    if not os.path.exists(test_file):
        print(f"錯誤: 測試文件不存在: {test_file}")
        print("請先創建測試文件，例如:")
        print("  echo -e '7plusmm.com\\ndiamonds9bet.com' > ../test_2_domains.txt")
        sys.exit(1)
    
    print(f"✓ 使用測試文件: {test_file}")
    print()
    
    # 執行 Lambda 函數
    try:
        event = {}
        context = None
        
        result = lambda_handler(event, context)
        
        print()
        print("=" * 60)
        print("執行結果")
        print("=" * 60)
        print(json.dumps(json.loads(result['body']), indent=2, ensure_ascii=False))
        print()
        
        if result['statusCode'] == 200:
            print("✅ 測試成功！")
            print()
            print("下一步:")
            print("  1. 檢查 ./test_output/ 目錄中的結果文件")
            print("  2. 確認無誤後執行 ./deploy.sh 部署到 AWS")
        else:
            print("❌ 測試失敗")
            sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ 錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
