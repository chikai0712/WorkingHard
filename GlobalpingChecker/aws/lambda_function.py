#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Globalping 域名檢測 - AWS Lambda 函數
支持從 S3 讀取域名列表，執行檢測，並將結果存回 S3
"""

import json
import boto3
import subprocess
import tempfile
import os
from datetime import datetime
from typing import Dict, List, Any

s3_client = boto3.client('s3')
sns_client = boto3.client('sns')

# 環境變數
BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'globalping-checker')
DOMAINS_KEY = os.environ.get('DOMAINS_S3_KEY', 'domains.txt')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')
GLOBALPING_TOKEN = os.environ.get('GLOBALPING_TOKEN', '')


def lambda_handler(event, context):
    """
    Lambda 主函數
    """
    try:
        print(f"開始執行域名檢測 - {datetime.now().isoformat()}")
        
        # 1. 從 S3 下載域名列表
        domains = download_domains_from_s3()
        print(f"成功下載 {len(domains)} 個域名")
        
        # 2. 執行檢測
        results = check_domains(domains)
        
        # 3. 上傳結果到 S3
        upload_results_to_s3(results)
        
        # 4. 發送通知（如果配置了 SNS）
        if SNS_TOPIC_ARN:
            send_notification(results)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': '檢測完成',
                'total_domains': len(domains),
                'results': results['summary']
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        print(f"錯誤: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            }, ensure_ascii=False)
        }


def download_domains_from_s3() -> List[str]:
    """從 S3 下載域名列表"""
    try:
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=DOMAINS_KEY)
        content = response['Body'].read().decode('utf-8')
        
        # 過濾空行和註釋
        domains = [
            line.strip() 
            for line in content.split('\n') 
            if line.strip() and not line.startswith('#') and '.' in line
        ]
        
        return domains
        
    except Exception as e:
        print(f"下載域名列表失敗: {str(e)}")
        raise


def check_domains(domains: List[str]) -> Dict[str, Any]:
    """
    執行域名檢測
    使用 Python 實現，避免依賴 bash 腳本
    """
    import requests
    import time
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'total': len(domains),
        'details': [],
        'summary': {
            'CLEAN': 0,
            'BLOCKED': 0,
            'TIMEOUT': 0,
            'WARNING': 0,
            'PARTIAL': 0,
            'API_ERROR': 0
        }
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    if GLOBALPING_TOKEN:
        headers['Authorization'] = f'Bearer {GLOBALPING_TOKEN}'
    
    for idx, domain in enumerate(domains, 1):
        print(f"檢測 [{idx}/{len(domains)}]: {domain}")
        
        try:
            # 創建測量任務
            payload = {
                "type": "http",
                "target": domain,
                "limit": 3,
                "locations": [{"country": "ID"}]
            }
            
            response = requests.post(
                'https://api.globalping.io/v1/measurements',
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code != 202:
                print(f"  API 錯誤: {response.status_code}")
                results['details'].append({
                    'domain': domain,
                    'status': 'API_ERROR',
                    'error': f"HTTP {response.status_code}"
                })
                results['summary']['API_ERROR'] += 1
                time.sleep(5)
                continue
            
            measurement_id = response.json().get('id')
            
            # 等待結果
            time.sleep(8)
            
            # 獲取結果
            result_response = requests.get(
                f'https://api.globalping.io/v1/measurements/{measurement_id}',
                headers=headers,
                timeout=10
            )
            
            if result_response.status_code != 200:
                results['details'].append({
                    'domain': domain,
                    'status': 'API_ERROR',
                    'error': 'Failed to get results'
                })
                results['summary']['API_ERROR'] += 1
                continue
            
            # 解析結果
            measurement_data = result_response.json()
            domain_result = parse_measurement_result(domain, measurement_data)
            
            results['details'].append(domain_result)
            results['summary'][domain_result['status']] += 1
            
            # 延遲避免頻率限制
            time.sleep(8)
            
        except Exception as e:
            print(f"  檢測失敗: {str(e)}")
            results['details'].append({
                'domain': domain,
                'status': 'API_ERROR',
                'error': str(e)
            })
            results['summary']['API_ERROR'] += 1
    
    return results


def parse_measurement_result(domain: str, data: Dict) -> Dict[str, Any]:
    """解析測量結果"""
    result = {
        'domain': domain,
        'probes': [],
        'status': 'UNKNOWN'
    }
    
    clean_count = 0
    timeout_count = 0
    warning_count = 0
    blocked_count = 0
    
    for probe_result in data.get('results', []):
        probe = probe_result.get('probe', {})
        http_result = probe_result.get('result', {})
        
        resolved_ip = http_result.get('resolvedAddress', '')
        status_code = http_result.get('statusCode', 0)
        
        # 判斷狀態
        if resolved_ip == '36.86.63.185' or resolved_ip.startswith('10.'):
            status = 'BLOCKED'
            blocked_count += 1
        elif not resolved_ip or status_code == 0:
            status = 'TIMEOUT'
            timeout_count += 1
        elif str(status_code).startswith(('2', '3')) or status_code == 403:
            status = 'CLEAN'
            clean_count += 1
        else:
            status = 'WARNING'
            warning_count += 1
        
        result['probes'].append({
            'network': probe.get('network', 'Unknown'),
            'asn': probe.get('asn', ''),
            'city': probe.get('city', ''),
            'resolved_ip': resolved_ip,
            'status_code': status_code,
            'status': status
        })
    
    # 判斷整體狀態
    if clean_count == 3:
        result['status'] = 'CLEAN'
    elif timeout_count == 3:
        result['status'] = 'TIMEOUT'
    elif warning_count == 3:
        result['status'] = 'WARNING'
    elif blocked_count == 3:
        result['status'] = 'BLOCKED'
    else:
        result['status'] = 'PARTIAL'
    
    return result


def upload_results_to_s3(results: Dict[str, Any]):
    """上傳結果到 S3"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 上傳詳細 JSON 結果
    json_key = f'results/result_{timestamp}.json'
    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key=json_key,
        Body=json.dumps(results, ensure_ascii=False, indent=2),
        ContentType='application/json'
    )
    print(f"結果已上傳: s3://{BUCKET_NAME}/{json_key}")
    
    # 生成並上傳摘要報告
    summary_text = generate_summary_report(results)
    summary_key = f'results/summary_{timestamp}.txt'
    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key=summary_key,
        Body=summary_text,
        ContentType='text/plain; charset=utf-8'
    )
    print(f"摘要已上傳: s3://{BUCKET_NAME}/{summary_key}")


def generate_summary_report(results: Dict[str, Any]) -> str:
    """生成摘要報告"""
    summary = results['summary']
    
    report = f"""
========================================
Globalping 域名檢測報告
========================================
檢測時間: {results['timestamp']}
總域名數: {results['total']}

檢測結果統計:
----------------------------------------
✅ 正常連通 (CLEAN):   {summary['CLEAN']}
🚨 DNS 污染 (BLOCKED): {summary['BLOCKED']}
⚠️  完全超時 (TIMEOUT): {summary['TIMEOUT']}
⚠️  服務異常 (WARNING): {summary['WARNING']}
🔄 部分異常 (PARTIAL): {summary['PARTIAL']}
❌ 檢測失敗 (API_ERROR): {summary['API_ERROR']}
========================================

詳細結果:
"""
    
    for detail in results['details']:
        report += f"\n域名: {detail['domain']}\n"
        report += f"狀態: {detail['status']}\n"
        
        if 'probes' in detail:
            for probe in detail['probes']:
                report += f"  - {probe['network']} ({probe['city']}): "
                report += f"{probe['resolved_ip']} [HTTP {probe['status_code']}] - {probe['status']}\n"
        
        if 'error' in detail:
            report += f"  錯誤: {detail['error']}\n"
        
        report += "----------------------------------------\n"
    
    return report


def send_notification(results: Dict[str, Any]):
    """發送 SNS 通知"""
    try:
        summary = results['summary']
        
        message = f"""
Globalping 域名檢測完成

檢測時間: {results['timestamp']}
總域名數: {results['total']}

結果統計:
- 正常連通: {summary['CLEAN']}
- DNS 污染: {summary['BLOCKED']}
- 完全超時: {summary['TIMEOUT']}
- 服務異常: {summary['WARNING']}
- 部分異常: {summary['PARTIAL']}
- 檢測失敗: {summary['API_ERROR']}

詳細結果已存儲到 S3: s3://{BUCKET_NAME}/results/
"""
        
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject='Globalping 域名檢測報告',
            Message=message
        )
        
        print("通知已發送")
        
    except Exception as e:
        print(f"發送通知失敗: {str(e)}")
