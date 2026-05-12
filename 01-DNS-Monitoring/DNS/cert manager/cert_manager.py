"""SSL 憑證自動更新與監控系統

功能：
1. 自動檢查憑證到期時間
2. 自動更新免費憑證（Let's Encrypt）
3. 在憑證剩餘 14 天內，每天發出 Alert
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import paramiko
import requests
from cryptography import x509
from cryptography.hazmat.backends import default_backend

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cert_manager.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class CertificateInfo:
    """憑證資訊"""
    domain: str
    cert_path: str
    key_path: Optional[str] = None
    expiry_date: Optional[datetime] = None
    days_remaining: Optional[int] = None
    auto_renew: bool = True
    alert_sent_today: bool = False

    def __post_init__(self):
        """初始化後計算到期資訊"""
        if self.cert_path and os.path.exists(self.cert_path):
            self.expiry_date, self.days_remaining = self._get_cert_expiry()

    def _get_cert_expiry(self) -> tuple[Optional[datetime], Optional[int]]:
        """讀取憑證檔案並計算到期時間"""
        try:
            with open(self.cert_path, 'rb') as f:
                cert_data = f.read()
            
            # 嘗試解析 PEM 格式
            try:
                cert = x509.load_pem_x509_certificate(cert_data, default_backend())
            except ValueError:
                # 嘗試 DER 格式
                cert = x509.load_der_x509_certificate(cert_data, default_backend())
            
            expiry = cert.not_valid_after.replace(tzinfo=None)
            days_remaining = (expiry - datetime.now()).days
            
            return expiry, days_remaining
        except Exception as e:
            logger.error(f"無法讀取憑證 {self.cert_path}: {e}")
            return None, None

    def needs_renewal(self, threshold_days: int = 30) -> bool:
        """檢查是否需要更新（預設剩餘 30 天）"""
        if self.days_remaining is None:
            return True
        return self.days_remaining <= threshold_days

    def needs_alert(self, threshold_days: int = 14) -> bool:
        """檢查是否需要發送警報（剩餘 14 天內）"""
        if self.days_remaining is None:
            return True
        return self.days_remaining <= threshold_days


class AlertManager:
    """警報管理器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.alert_methods = config.get('alert_methods', {})
    
    def send_alert(self, cert_info: CertificateInfo, message: str) -> bool:
        """發送警報"""
        success = True
        
        # Email 警報
        if self.alert_methods.get('email', {}).get('enabled'):
            success &= self._send_email_alert(cert_info, message)
        
        # Webhook 警報
        if self.alert_methods.get('webhook', {}).get('enabled'):
            success &= self._send_webhook_alert(cert_info, message)
        
        # 日誌警報
        if self.alert_methods.get('log', {}).get('enabled', True):
            logger.warning(f"ALERT: {cert_info.domain} - {message}")
        
        return success
    
    def _send_email_alert(self, cert_info: CertificateInfo, message: str) -> bool:
        """發送 Email 警報"""
        email_config = self.alert_methods.get('email', {})
        try:
            # 這裡可以整合 SMTP 或第三方服務（如 SendGrid, AWS SES）
            # 範例使用 SMTP
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg['From'] = email_config.get('from')
            msg['To'] = ', '.join(email_config.get('to', []))
            msg['Subject'] = f"SSL 憑證警報: {cert_info.domain}"
            
            body = f"""
憑證域名: {cert_info.domain}
剩餘天數: {cert_info.days_remaining} 天
到期時間: {cert_info.expiry_date}
憑證路徑: {cert_info.cert_path}

警報訊息: {message}
            """
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            smtp = smtplib.SMTP(
                email_config.get('smtp_host', 'localhost'),
                email_config.get('smtp_port', 587)
            )
            if email_config.get('use_tls', True):
                smtp.starttls()
            if email_config.get('username') and email_config.get('password'):
                smtp.login(email_config['username'], email_config['password'])
            
            smtp.send_message(msg)
            smtp.quit()
            logger.info(f"Email 警報已發送: {cert_info.domain}")
            return True
        except Exception as e:
            logger.error(f"發送 Email 警報失敗: {e}")
            return False
    
    def _send_webhook_alert(self, cert_info: CertificateInfo, message: str) -> bool:
        """發送 Webhook 警報"""
        webhook_config = self.alert_methods.get('webhook', {})
        try:
            url = webhook_config.get('url')
            if not url:
                return False
            
            payload = {
                'domain': cert_info.domain,
                'days_remaining': cert_info.days_remaining,
                'expiry_date': cert_info.expiry_date.isoformat() if cert_info.expiry_date else None,
                'cert_path': cert_info.cert_path,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }
            
            headers = webhook_config.get('headers', {})
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            logger.info(f"Webhook 警報已發送: {cert_info.domain}")
            return True
        except Exception as e:
            logger.error(f"發送 Webhook 警報失敗: {e}")
            return False


class CertificateRenewer:
    """憑證更新器（支援 Let's Encrypt）"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.certbot_path = config.get('certbot_path', 'certbot')
        self.acme_dir = config.get('acme_dir', '/etc/letsencrypt')
        self.webroot = config.get('webroot', None)
        self.email = config.get('email', None)
        self.use_staging = config.get('use_staging', False)
        self.save_dir = config.get('save_dir', None)  # 憑證保存目錄
    
    def renew_certificate(self, cert_info: CertificateInfo) -> bool:
        """更新憑證"""
        if not cert_info.auto_renew:
            logger.info(f"憑證 {cert_info.domain} 已設定為不自動更新")
            return False
        
        try:
            logger.info(f"開始更新憑證: {cert_info.domain}")
            
            # 使用 certbot certonly 來更新憑證
            # 如果憑證已存在，使用 --keep-until-expiring 或 --force-renewal
            cmd = [
                self.certbot_path,
                'certonly',
                '--non-interactive',
                '--agree-tos',
                '--force-renewal',  # 強制更新
            ]
            
            if self.use_staging:
                cmd.append('--staging')
            
            if self.email:
                cmd.extend(['--email', self.email])
            else:
                cmd.append('--register-unsafely-without-email')
            
            # 選擇驗證方式
            if self.webroot:
                cmd.extend([
                    '--webroot',
                    '--webroot-path', self.webroot,
                    '-d', cert_info.domain
                ])
            else:
                # 使用 standalone 模式（需要停止 web server）
                cmd.extend([
                    '--standalone',
                    '-d', cert_info.domain
                ])
            
            # 執行 certbot
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                logger.info(f"憑證更新成功: {cert_info.domain}")
                
                # 將憑證複製到指定資料夾
                if self.save_dir:
                    self._save_certificate_to_folder(cert_info)
                
                # 重新載入憑證資訊
                cert_info.expiry_date, cert_info.days_remaining = cert_info._get_cert_expiry()
                return True
            else:
                logger.error(f"憑證更新失敗: {cert_info.domain}")
                logger.error(f"錯誤訊息: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"憑證更新超時: {cert_info.domain}")
            return False
        except Exception as e:
            logger.error(f"憑證更新發生錯誤: {cert_info.domain}: {e}")
            return False
    
    def _save_certificate_to_folder(self, cert_info: CertificateInfo):
        """將憑證保存到指定資料夾"""
        try:
            save_dir = Path(self.save_dir)
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # 建立域名子目錄
            domain_dir = save_dir / cert_info.domain
            domain_dir.mkdir(parents=True, exist_ok=True)
            
            # 複製憑證檔案
            if os.path.exists(cert_info.cert_path):
                dest_cert = domain_dir / 'fullchain.pem'
                shutil.copy2(cert_info.cert_path, dest_cert)
                logger.info(f"憑證已保存到: {dest_cert}")
            
            # 複製私鑰檔案
            if cert_info.key_path and os.path.exists(cert_info.key_path):
                dest_key = domain_dir / 'privkey.pem'
                shutil.copy2(cert_info.key_path, dest_key)
                logger.info(f"私鑰已保存到: {dest_key}")
            
            # 如果 cert_path 指向 fullchain.pem，也複製 chain.pem 和 cert.pem
            cert_dir = Path(cert_info.cert_path).parent
            if (cert_dir / 'chain.pem').exists():
                shutil.copy2(cert_dir / 'chain.pem', domain_dir / 'chain.pem')
            if (cert_dir / 'cert.pem').exists():
                shutil.copy2(cert_dir / 'cert.pem', domain_dir / 'cert.pem')
            
        except Exception as e:
            logger.error(f"保存憑證到資料夾失敗: {e}")


class CertificateUploader:
    """憑證上傳器（支援 SSH/SCP）"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.save_dir = config.get('save_dir', None)
        
        # 優先讀取獨立的 serverlist 檔案
        serverlist_path = config.get('serverlist_path', None)
        if serverlist_path:
            self.upload_targets = self._load_serverlist(serverlist_path)
        else:
            # 如果沒有指定 serverlist_path，則使用 config 中的 upload_targets（向後兼容）
            self.upload_targets = config.get('upload_targets', [])
    
    def _load_serverlist(self, serverlist_path: str) -> List[Dict]:
        """從獨立的 serverlist 檔案載入伺服器列表"""
        try:
            # 處理相對路徑和 ~ 擴展
            serverlist_path = os.path.expanduser(serverlist_path)
            if not os.path.isabs(serverlist_path):
                # 如果是相對路徑，相對於配置檔案所在目錄
                config_dir = Path(self.config.get('_config_dir', '.'))
                serverlist_path = str(config_dir / serverlist_path)
            
            if not os.path.exists(serverlist_path):
                logger.warning(f"Serverlist 檔案不存在: {serverlist_path}，使用空列表")
                return []
            
            with open(serverlist_path, 'r', encoding='utf-8') as f:
                serverlist_data = json.load(f)
            
            servers = serverlist_data.get('servers', [])
            # 只返回啟用的伺服器
            enabled_servers = [s for s in servers if s.get('enabled', True)]
            logger.info(f"從 {serverlist_path} 載入了 {len(enabled_servers)} 台啟用的伺服器")
            return enabled_servers
            
        except json.JSONDecodeError as e:
            logger.error(f"Serverlist 檔案格式錯誤: {serverlist_path}: {e}")
            return []
        except Exception as e:
            logger.error(f"讀取 Serverlist 檔案失敗: {serverlist_path}: {e}")
            return []
    
    def upload_certificate(self, cert_info: CertificateInfo) -> bool:
        """上傳憑證到所有目標機器"""
        if not self.upload_targets:
            logger.info("沒有配置上傳目標，跳過上傳")
            return True
        
        if not self.save_dir:
            logger.warning("未配置 save_dir，無法上傳憑證")
            return False
        
        success = True
        domain_dir = Path(self.save_dir) / cert_info.domain
        
        if not domain_dir.exists():
            logger.error(f"憑證目錄不存在: {domain_dir}")
            return False
        
        for target in self.upload_targets:
            try:
                server_name = target.get('name', target.get('host', 'unknown'))
                if self._upload_to_target(cert_info, domain_dir, target):
                    logger.info(f"憑證已成功上傳到: {server_name} ({target.get('host', 'unknown')})")
                else:
                    logger.error(f"憑證上傳失敗: {server_name} ({target.get('host', 'unknown')})")
                    success = False
            except Exception as e:
                server_name = target.get('name', target.get('host', 'unknown'))
                logger.error(f"上傳到 {server_name} ({target.get('host', 'unknown')}) 時發生錯誤: {e}")
                success = False
        
        return success
    
    def _upload_to_target(self, cert_info: CertificateInfo, local_dir: Path, target: Dict) -> bool:
        """上傳憑證到單一目標機器"""
        server_name = target.get('name', 'Unknown')
        host = target.get('host')
        port = target.get('port', 22)
        username = target.get('username')
        password = target.get('password')
        key_file = target.get('key_file')  # SSH 私鑰路徑
        remote_path = target.get('remote_path', '/etc/ssl/certs')
        remote_dir = target.get('remote_dir', cert_info.domain)  # 遠端子目錄
        
        if not host or not username:
            logger.error(f"上傳目標配置不完整 ({server_name})：缺少 host 或 username")
            return False
        
        try:
            # 建立 SSH 客戶端
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 連接選項
            connect_kwargs = {
                'hostname': host,
                'port': port,
                'username': username,
                'timeout': 30
            }
            
            # 處理 key_file 路徑（支援 ~ 和相對路徑）
            if key_file:
                key_file = os.path.expanduser(key_file)
                if not os.path.isabs(key_file):
                    # 如果是相對路徑，相對於配置檔案所在目錄
                    config_dir = Path(self.config.get('_config_dir', '.'))
                    key_file = str(config_dir / key_file)
            
            # 使用密碼或私鑰認證
            if key_file and os.path.exists(key_file):
                ssh.connect(**connect_kwargs, key_filename=key_file)
            elif password:
                ssh.connect(**connect_kwargs, password=password)
            else:
                logger.error(f"無法連接到 {host} ({server_name})：缺少認證資訊（password 或 key_file）")
                return False
            
            # 建立 SCP 客戶端
            scp = ssh.open_sftp()
            
            # 建立遠端目錄
            remote_full_path = f"{remote_path.rstrip('/')}/{remote_dir}"
            self._ensure_remote_directory(ssh, remote_full_path)
            
            # 上傳檔案
            files_to_upload = [
                ('fullchain.pem', 'fullchain.pem'),
                ('privkey.pem', 'privkey.pem'),
                ('chain.pem', 'chain.pem'),
                ('cert.pem', 'cert.pem')
            ]
            
            uploaded_count = 0
            for local_file, remote_file in files_to_upload:
                local_file_path = local_dir / local_file
                if local_file_path.exists():
                    remote_file_path = f"{remote_full_path}/{remote_file}"
                    scp.put(str(local_file_path), remote_file_path)
                    # 設定適當的權限（憑證 644，私鑰 600）
                    if 'key' in local_file:
                        ssh.exec_command(f"chmod 600 {remote_file_path}")
                    else:
                        ssh.exec_command(f"chmod 644 {remote_file_path}")
                    uploaded_count += 1
                    logger.info(f"已上傳 {local_file} 到 {server_name} ({host}):{remote_file_path}")
            
            scp.close()
            ssh.close()
            
            if uploaded_count > 0:
                logger.info(f"成功上傳 {uploaded_count} 個檔案到 {server_name} ({host})")
                return True
            else:
                logger.warning(f"沒有檔案需要上傳到 {server_name} ({host})")
                return False
                
        except paramiko.AuthenticationException:
            logger.error(f"認證失敗: {server_name} ({host})")
            return False
        except paramiko.SSHException as e:
            logger.error(f"SSH 連接錯誤: {server_name} ({host}): {e}")
            return False
        except Exception as e:
            logger.error(f"上傳憑證時發生錯誤: {server_name} ({host}): {e}")
            return False
    
    def _ensure_remote_directory(self, ssh: paramiko.SSHClient, remote_path: str):
        """確保遠端目錄存在"""
        try:
            ssh.exec_command(f"mkdir -p {remote_path}")
        except Exception as e:
            logger.warning(f"建立遠端目錄失敗: {remote_path}: {e}")


class CertificateManager:
    """憑證管理器主類別"""
    
    def __init__(self, config_path: str = 'config.json'):
        self.config = self._load_config(config_path)
        self.certificates: List[CertificateInfo] = []
        self.alert_manager = AlertManager(self.config)
        self.renewer = CertificateRenewer(self.config.get('renewer', {}))
        self.uploader = CertificateUploader(self.config.get('uploader', {}))
        self.alert_threshold = self.config.get('alert_threshold_days', 14)
        self.renew_threshold = self.config.get('renew_threshold_days', 30)
        self._load_certificates()
    
    def _load_config(self, config_path: str) -> Dict:
        """載入配置檔案"""
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            # 保存配置檔案所在目錄，用於解析相對路徑
            config['_config_dir'] = str(Path(config_path).parent.absolute())
            return config
        else:
            logger.warning(f"配置檔案不存在: {config_path}，使用預設配置")
            return {}
    
    def _load_certificates(self):
        """載入憑證列表"""
        certs_config = self.config.get('certificates', [])
        for cert_config in certs_config:
            cert_info = CertificateInfo(
                domain=cert_config['domain'],
                cert_path=cert_config['cert_path'],
                key_path=cert_config.get('key_path'),
                auto_renew=cert_config.get('auto_renew', True)
            )
            self.certificates.append(cert_info)
            logger.info(f"已載入憑證: {cert_info.domain}")
    
    def check_all_certificates(self):
        """檢查所有憑證"""
        logger.info("開始檢查所有憑證...")
        for cert_info in self.certificates:
            self._check_certificate(cert_info)
    
    def _check_certificate(self, cert_info: CertificateInfo):
        """檢查單一憑證"""
        # 重新計算到期資訊
        cert_info.expiry_date, cert_info.days_remaining = cert_info._get_cert_expiry()
        
        if cert_info.days_remaining is None:
            logger.error(f"無法讀取憑證資訊: {cert_info.domain}")
            self.alert_manager.send_alert(
                cert_info,
                f"無法讀取憑證檔案: {cert_info.cert_path}"
            )
            return
        
        logger.info(
            f"憑證 {cert_info.domain}: "
            f"剩餘 {cert_info.days_remaining} 天 "
            f"(到期: {cert_info.expiry_date})"
        )
        
        # 檢查是否需要更新
        if cert_info.needs_renewal(self.renew_threshold):
            logger.warning(
                f"憑證 {cert_info.domain} 需要更新 "
                f"(剩餘 {cert_info.days_remaining} 天)"
            )
            if cert_info.auto_renew:
                success = self.renewer.renew_certificate(cert_info)
                if success:
                    # 更新成功後，上傳到目標機器
                    logger.info(f"開始上傳憑證 {cert_info.domain} 到目標機器...")
                    upload_success = self.uploader.upload_certificate(cert_info)
                    if not upload_success:
                        logger.warning(f"憑證 {cert_info.domain} 上傳到部分機器失敗")
                        self.alert_manager.send_alert(
                            cert_info,
                            f"憑證更新成功，但上傳到部分機器失敗"
                        )
                else:
                    self.alert_manager.send_alert(
                        cert_info,
                        f"憑證自動更新失敗，剩餘 {cert_info.days_remaining} 天"
                    )
        
        # 檢查是否需要發送警報（剩餘 14 天內，每天發送一次）
        if cert_info.needs_alert(self.alert_threshold):
            # 檢查今天是否已發送過警報
            alert_sent_file = Path(f".alert_sent_{cert_info.domain}")
            today = datetime.now().date()
            
            last_sent_date = None
            if alert_sent_file.exists():
                try:
                    last_sent_date = datetime.fromisoformat(
                        alert_sent_file.read_text().strip()
                    ).date()
                except:
                    pass
            
            # 如果今天還沒發送過，則發送警報
            if last_sent_date != today:
                self.alert_manager.send_alert(
                    cert_info,
                    f"憑證將在 {cert_info.days_remaining} 天後到期！"
                )
                # 記錄今天已發送
                alert_sent_file.write_text(today.isoformat())
                cert_info.alert_sent_today = True
                logger.info(f"已發送警報: {cert_info.domain}")


def main():
    """主程式"""
    import argparse
    
    parser = argparse.ArgumentParser(description='SSL 憑證自動更新與監控系統')
    parser.add_argument(
        '--config',
        default='config.json',
        help='配置檔案路徑 (預設: config.json)'
    )
    parser.add_argument(
        '--check-only',
        action='store_true',
        help='僅檢查憑證，不進行更新'
    )
    
    args = parser.parse_args()
    
    try:
        manager = CertificateManager(args.config)
        manager.check_all_certificates()
        logger.info("憑證檢查完成")
    except Exception as e:
        logger.error(f"執行錯誤: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

