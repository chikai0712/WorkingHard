"""
群益 Capital API 客戶端
基於官方 CapitalAPI_2/PythonExampleV2 改寫

注意：
- 僅支援 Windows（COM 介面）
- SKCOM.dll 必須與此檔案在同一目錄，或已透過 install.bat 安裝
- 執行前需先安裝 comtypes: pip install comtypes
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# 嘗試載入群益 COM 元件
try:
    import comtypes.client
    # 優先從同目錄載入 SKCOM.dll
    _dll_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'SKCOM.dll')
    if os.path.exists(_dll_path):
        comtypes.client.GetModule(_dll_path)
    else:
        # 已透過 install.bat 安裝到系統，直接使用
        comtypes.client.GetModule('SKCOM.dll')
    import comtypes.gen.SKCOMLib as sk
    SKCOM_AVAILABLE = True
except Exception as e:
    SKCOM_AVAILABLE = False
    logger.warning(f"無法載入 SKCOM：{e}")
    logger.warning("請確認已執行 CapitalAPI_2/元件/x64/install.bat 安裝 SKCOM")


class CapitalClient:
    """
    群益證券 Capital API 客戶端

    使用方式（with 語法）：
        with CapitalClient() as client:
            # client 已登入並連線報價主機
            ...

    使用方式（手動）：
        client = CapitalClient()
        if client.connect() and client.login_quote():
            ...
            client.disconnect()
    """

    def __init__(self, account: Optional[str] = None, password: Optional[str] = None):
        """
        Args:
            account: 群益帳號（預設從環境變數 CAPITAL_ACCOUNT 讀取）
            password: 群益密碼（預設從環境變數 CAPITAL_PASSWORD 讀取）
        """
        if not SKCOM_AVAILABLE:
            raise RuntimeError(
                "SKCOM 未載入。請確認：\n"
                "1. 已執行 CapitalAPI_2/元件/x64/install.bat\n"
                "2. 已安裝 comtypes: pip install comtypes"
            )

        self.account = account or os.getenv('CAPITAL_ACCOUNT', '')
        self.password = password or os.getenv('CAPITAL_PASSWORD', '')

        if not self.account or not self.password:
            raise ValueError(
                "請提供群益帳號密碼，或設定環境變數：\n"
                "CAPITAL_ACCOUNT=你的帳號\n"
                "CAPITAL_PASSWORD=你的密碼"
            )

        # COM 物件
        self.skC = None   # SKCenterLib — 登入、錯誤訊息
        self.skQ = None   # SKQuoteLib  — 報價訂閱
        self.skR = None   # SKReplyLib  — 回報事件

        # 狀態
        self.is_connected = False
        self.is_quote_connected = False

    def connect(self) -> bool:
        """
        登入群益 API（SKCenterLib_Login）
        必須在 login_quote() 之前呼叫
        """
        try:
            # 建立 COM 物件
            self.skC = comtypes.client.CreateObject(sk.SKCenterLib, interface=sk.ISKCenterLib)
            self.skQ = comtypes.client.CreateObject(sk.SKQuoteLib,  interface=sk.ISKQuoteLib)
            self.skR = comtypes.client.CreateObject(sk.SKReplyLib,  interface=sk.ISKReplyLib)

            # 設定 LOG 路徑（放在執行目錄下）
            log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'CapitalLog')
            os.makedirs(log_path, exist_ok=True)
            self.skC.SKCenterLib_SetLogPath(log_path)

            # 登入
            nCode = self.skC.SKCenterLib_Login(self.account, self.password)
            if nCode == 0:
                self.is_connected = True
                logger.info(f"群益 API 登入成功（帳號：{self.account}）")
                return True
            else:
                err_msg = self.skC.SKCenterLib_GetReturnCodeMessage(nCode)
                logger.error(f"群益 API 登入失敗：{err_msg}（代碼：{nCode}）")
                return False

        except Exception as e:
            logger.error(f"群益 API 連線時發生例外：{e}")
            return False

    def login_quote(self) -> bool:
        """
        連線報價主機（SKQuoteLib_EnterMonitorLONG）
        必須在 connect() 成功後呼叫
        """
        if not self.is_connected:
            logger.error("請先呼叫 connect() 完成登入")
            return False

        try:
            nCode = self.skQ.SKQuoteLib_EnterMonitorLONG()
            if nCode == 0:
                self.is_quote_connected = True
                logger.info("報價主機連線成功")
                return True
            else:
                err_msg = self.skC.SKCenterLib_GetReturnCodeMessage(nCode)
                logger.error(f"報價主機連線失敗：{err_msg}（代碼：{nCode}）")
                return False

        except Exception as e:
            logger.error(f"連線報價主機時發生例外：{e}")
            return False

    def disconnect(self):
        """中斷所有連線"""
        try:
            if self.skQ and self.is_quote_connected:
                self.skQ.SKQuoteLib_LeaveMonitor()
                self.is_quote_connected = False
                logger.info("已中斷報價主機連線")

            if self.skC and self.is_connected:
                self.skC.SKCenterLib_Logout(self.account)
                self.is_connected = False
                logger.info("已登出群益 API")

        except Exception as e:
            logger.error(f"中斷連線時發生例外：{e}")

    def get_error_message(self, nCode: int) -> str:
        """取得錯誤代碼對應的說明文字"""
        if self.skC:
            return self.skC.SKCenterLib_GetReturnCodeMessage(nCode)
        return f"錯誤代碼：{nCode}"

    def __enter__(self):
        """支援 with 語法"""
        if self.connect():
            self.login_quote()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """支援 with 語法"""
        self.disconnect()
