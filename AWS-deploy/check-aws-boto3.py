#!/usr/bin/env python3
"""
AWS 狀態檢查工具 - 使用 boto3 直接連線
完全繞過代理和 AWS CLI
"""

import os
import sys

# 完全禁用代理
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('all_proxy', None)
os.environ.pop('ALL_PROXY', None)
os.environ.pop('no_proxy', None)
os.environ.pop('NO_PROXY', None)

try:
    import boto3
    from botocore.config import Config
except ImportError:
    print("❌ boto3 未安裝")
    print()
    print("請執行以下命令安裝：")
    print("  pip3 install boto3")
    print()
    sys.exit(1)

# 配置 boto3 完全禁用代理
config = Config(
    proxies={},
    proxies_config={
        'proxy_use_forwarding_for_https': False
    }
)

def main():
    print("🔍 AWS 運行狀況檢查（boto3 版本）")
    print("=" * 70)
    print()
    
    try:
        # 1. 測試 AWS 連線
        print("1️⃣  檢查 AWS 連線...")
        sts = boto3.client('sts', config=config)
        identity = sts.get_caller_identity()
        
        print("   ✅ AWS 連線正常")
        print(f"   帳號: {identity['Account']}")
        print(f"   用戶: {identity['Arn']}")
        print()
        
    except Exception as e:
        print(f"   ❌ AWS 連線失敗: {e}")
        print()
        print("   請確認：")
        print("   1. AWS 憑證已配置: aws configure")
        print("   2. 或設置環境變數:")
        print("      export AWS_ACCESS_KEY_ID=your_key")
        print("      export AWS_SECRET_ACCESS_KEY=your_secret")
        sys.exit(1)
    
    try:
        # 2. 檢查 EC2 實例
        print("2️⃣  檢查 EC2 實例...")
        ec2 = boto3.client('ec2', region_name='ap-northeast-1', config=config)
        response = ec2.describe_instances()
        
        instances = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                name = "未命名"
                for tag in instance.get('Tags', []):
                    if tag['Key'] == 'Name':
                        name = tag['Value']
                        break
                
                instances.append({
                    'id': instance['InstanceId'],
                    'state': instance['State']['Name'],
                    'ip': instance.get('PublicIpAddress', 'N/A'),
                    'type': instance['InstanceType'],
                    'name': name,
                    'key': instance.get('KeyName', 'N/A')
                })
        
        if not instances:
            print("   ℹ️  沒有 EC2 實例")
        else:
            print()
            print(f"   {'名稱':<30} {'狀態':<15} {'IP 地址':<16} {'類型':<12}")
            print("   " + "-" * 80)
            
            for inst in instances:
                # 狀態圖標
                if inst['state'] == 'running':
                    status = f"🟢 {inst['state']}"
                elif inst['state'] == 'stopped':
                    status = f"🔴 {inst['state']}"
                elif inst['state'] == 'pending':
                    status = f"🟡 {inst['state']}"
                else:
                    status = f"⚪ {inst['state']}"
                
                print(f"   {inst['name']:<30} {status:<15} {inst['ip']:<16} {inst['type']:<12}")
        
        print()
        
        # 3. 檢查運行中的實例詳情
        print("3️⃣  運行中實例詳情...")
        running = [i for i in instances if i['state'] == 'running']
        
        if not running:
            print("   ℹ️  沒有運行中的實例")
        else:
            print()
            for inst in running:
                print(f"   📦 {inst['name']}")
                print(f"      實例 ID: {inst['id']}")
                print(f"      公網 IP: {inst['ip']}")
                print(f"      SSH Key: {inst['key']}")
                print(f"      類型: {inst['type']}")
                
                # 根據名稱顯示訪問方式
                if "Pokemon" in inst['name']:
                    print(f"      🎮 遊戲網址: http://{inst['ip']}")
                elif "Globalping" in inst['name']:
                    print(f"      🔍 SSH 連線: ssh -i ~/.ssh/{inst['key']}.pem ec2-user@{inst['ip']}")
                    print(f"      📝 執行檢測: ssh -i ~/.ssh/{inst['key']}.pem ec2-user@{inst['ip']} '/opt/globalping-checker/run_check.sh'")
                elif "DNS" in inst['name']:
                    print(f"      🌐 API 端點: http://{inst['ip']}:8000/docs")
                
                print()
        
        # 4. 成本估算
        print("4️⃣  成本估算...")
        running_count = len(running)
        stopped_count = len([i for i in instances if i['state'] == 'stopped'])
        
        print()
        print(f"   運行中實例: {running_count}")
        print(f"   停止的實例: {stopped_count}")
        
        if running_count > 0:
            # 簡單估算
            cost = 0
            for inst in running:
                if 't3.micro' in inst['type'] or 't2.micro' in inst['type']:
                    cost += 7.5
                elif 't3.small' in inst['type']:
                    cost += 15.0
                elif 't3.medium' in inst['type']:
                    cost += 30.0
            
            print(f"   預估月成本: ~${cost:.2f} USD")
            print(f"   （假設 24/7 運行）")
        
        print()
        
    except Exception as e:
        print(f"   ❌ 查詢失敗: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 70)
    print("✅ 檢查完成")
    print("=" * 70)
    print()
    print("💡 快速操作：")
    print("   更新代碼: cd ~/Desktop/Project/AWS-deploy && ./update-globalping-code.sh")
    print("   停止實例: python3 ~/Desktop/Project/AWS-deploy/aws-control.py stop")
    print("   啟動實例: python3 ~/Desktop/Project/AWS-deploy/aws-control.py start")
    print()

if __name__ == "__main__":
    main()
