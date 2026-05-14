#!/usr/bin/env python3
"""
AWS 狀態檢查工具 - 完全繞過代理
適用於 Cursor IDE 環境
"""

import os
import sys
import subprocess
import json

def run_aws_command(cmd):
    """執行 AWS CLI 命令，完全禁用代理"""
    env = os.environ.copy()
    
    # 移除所有代理相關環境變數
    proxy_vars = [
        'http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY',
        'all_proxy', 'ALL_PROXY', 'no_proxy', 'NO_PROXY',
        'socks_proxy', 'SOCKS_PROXY', 'socks5_proxy', 'SOCKS5_PROXY',
        'GIT_HTTP_PROXY', 'GIT_HTTPS_PROXY'
    ]
    
    for var in proxy_vars:
        env.pop(var, None)
    
    # 設置 NO_PROXY
    env['NO_PROXY'] = '*'
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            env=env,
            timeout=30
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    print("🔍 AWS 運行狀況檢查（Python 版本）")
    print("=" * 60)
    print()
    
    # 1. 測試 AWS 連線
    print("1️⃣  檢查 AWS 連線...")
    success, stdout, stderr = run_aws_command("aws sts get-caller-identity --output json")
    
    if success:
        print("   ✅ AWS CLI 連線正常")
        try:
            identity = json.loads(stdout)
            print(f"   帳號: {identity.get('Account', 'N/A')}")
            print(f"   用戶: {identity.get('Arn', 'N/A')}")
        except:
            pass
    else:
        print("   ❌ AWS CLI 連線失敗")
        print(f"   錯誤: {stderr}")
        print()
        print("   請確認：")
        print("   1. AWS CLI 已安裝: aws --version")
        print("   2. AWS 憑證已配置: aws configure")
        sys.exit(1)
    
    print()
    
    # 2. 檢查 EC2 實例
    print("2️⃣  檢查 EC2 實例...")
    cmd = """aws ec2 describe-instances \
        --region ap-northeast-1 \
        --query 'Reservations[].Instances[].[InstanceId,State.Name,PublicIpAddress,InstanceType,Tags[?Key==\`Name\`].Value|[0]]' \
        --output json"""
    
    success, stdout, stderr = run_aws_command(cmd)
    
    if success:
        try:
            instances = json.loads(stdout)
            
            if not instances:
                print("   ℹ️  沒有 EC2 實例")
            else:
                print()
                print(f"   {'名稱':<30} {'狀態':<12} {'IP 地址':<16} {'類型':<12}")
                print("   " + "-" * 75)
                
                for inst in instances:
                    instance_id = inst[0]
                    state = inst[1]
                    public_ip = inst[2] or "N/A"
                    instance_type = inst[3]
                    name = inst[4] or "未命名"
                    
                    # 狀態圖標
                    if state == "running":
                        status = f"🟢 {state}"
                    elif state == "stopped":
                        status = f"🔴 {state}"
                    else:
                        status = f"⚪ {state}"
                    
                    print(f"   {name:<30} {status:<12} {public_ip:<16} {instance_type:<12}")
        except Exception as e:
            print(f"   ❌ 解析失敗: {e}")
    else:
        print(f"   ❌ 查詢失敗: {stderr}")
    
    print()
    
    # 3. 檢查運行中的實例詳情
    print("3️⃣  運行中實例詳情...")
    cmd = """aws ec2 describe-instances \
        --region ap-northeast-1 \
        --filters "Name=instance-state-name,Values=running" \
        --query 'Reservations[].Instances[].[InstanceId,PublicIpAddress,Tags[?Key==\`Name\`].Value|[0],KeyName]' \
        --output json"""
    
    success, stdout, stderr = run_aws_command(cmd)
    
    if success:
        try:
            running = json.loads(stdout)
            
            if not running:
                print("   ℹ️  沒有運行中的實例")
            else:
                print()
                for inst in running:
                    instance_id = inst[0]
                    public_ip = inst[1]
                    name = inst[2] or "未命名"
                    key_name = inst[3]
                    
                    print(f"   📦 {name}")
                    print(f"      實例: {instance_id}")
                    print(f"      IP: {public_ip}")
                    print(f"      Key: {key_name}")
                    
                    # 根據名稱顯示訪問方式
                    if "Pokemon" in name:
                        print(f"      🎮 遊戲: http://{public_ip}")
                    elif "Globalping" in name:
                        print(f"      🔍 SSH: ssh -i ~/.ssh/{key_name}.pem ec2-user@{public_ip}")
                        print(f"      📝 檢測: ssh -i ~/.ssh/{key_name}.pem ec2-user@{public_ip} '/opt/globalping-checker/run_check.sh'")
                    elif "DNS" in name:
                        print(f"      🌐 API: http://{public_ip}:8000/docs")
                    
                    print()
        except Exception as e:
            print(f"   ❌ 解析失敗: {e}")
    
    print("=" * 60)
    print("✅ 檢查完成")
    print("=" * 60)
    print()
    print("💡 快速操作：")
    print("   更新代碼: cd ~/Desktop/Project/AWS-deploy && ./update-globalping-code.sh")
    print("   管理界面: cd ~/Desktop/Project/AWS-deploy && ./aws-manager.sh")
    print()

if __name__ == "__main__":
    main()
