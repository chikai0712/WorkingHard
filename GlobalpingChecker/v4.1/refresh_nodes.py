#!/usr/bin/env python3
"""
重新拉取节点清单脚本
"""
import asyncio
import sys
from pathlib import Path

# 添加 app 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

async def refresh_nodes():
    """重新拉取节点清单"""
    try:
        from app.node_pool import NodePoolManager
        from app.database import init_db
        
        print("🔄 开始重新拉取节点清单...")
        print()
        
        # 初始化数据库
        init_db()
        
        # 创建节点池管理器
        pool_manager = NodePoolManager()
        
        # 刷新节点池
        await pool_manager.refresh_node_pool()
        
        # 显示统计信息
        print()
        print("📊 节点池统计:")
        stats = pool_manager.get_node_pool_stats()
        for country, info in stats.items():
            print(f"   {country}: {info['total']} 个节点 (TOP30 ISP: {info['top30_count']} 个)")
            if info['top30_isps']:
                for isp_info in info['top30_isps'][:5]:
                    print(f"      - TOP{isp_info['rank']} {isp_info['brand']}: {isp_info['isp']} ({isp_info['city']})")
        
        print()
        print("✅ 节点清单拉取完成！")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(refresh_nodes())
