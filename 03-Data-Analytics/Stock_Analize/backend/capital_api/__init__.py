"""
群益 API 模組
用於連接群益證券 API，訂閱台指期即時報價

Note: CapitalClient / FuturesSubscriber 需要 Windows + SKCOM，
      在 Mac/Linux 執行 Mock 測試時不會自動載入。
"""

# Windows-only 模組使用 lazy import，避免在 Mac/Linux 執行 mock 測試時爆炸
import sys as _sys

if _sys.platform == 'win32':
    from .client import CapitalClient
    from .futures_subscriber import FuturesSubscriber
    __all__ = ['CapitalClient', 'FuturesSubscriber']
else:
    # Mac/Linux：提供 stub，避免 ImportError
    class CapitalClient:  # type: ignore
        def __init__(self, *a, **kw):
            raise RuntimeError('CapitalClient 僅支援 Windows + SKCOM')

    class FuturesSubscriber:  # type: ignore
        def __init__(self, *a, **kw):
            raise RuntimeError('FuturesSubscriber 僅支援 Windows + SKCOM')

    __all__ = ['CapitalClient', 'FuturesSubscriber']
