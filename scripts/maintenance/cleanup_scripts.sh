#!/bin/bash

# 腳本清理工具

echo "========================================"
echo "腳本清理工具"
echo "========================================"
echo ""

# 保留的腳本（推薦版本）
KEEP_SCRIPTS=(
    "/Users/ckchiu/id_globalping_multi_v2.1.sh"
    "/Users/ckchiu/id_globalping_multi_v2.sh"
    "/Users/ckchiu/Desktop/Project/id_globalping_auto_retry.sh"
    "/Users/ckchiu/Desktop/Project/id_globalping_cli.sh"
)

# 要刪除的腳本
DELETE_SCRIPTS=(
    "/Users/ckchiu/id_check_api_v3.sh"
    "/Users/ckchiu/id_check_expert.sh"
    "/Users/ckchiu/id_check_final.sh"
    "/Users/ckchiu/id_check_v2.sh"
    "/Users/ckchiu/id_dns_check.sh"
    "/Users/ckchiu/id_globalping_multi.sh"
    "/Users/ckchiu/id_globalping_v2.sh"
    "/Users/ckchiu/id_globalping.sh"
    "/Users/ckchiu/id_verify_api.sh"
    "/Users/ckchiu/Desktop/Project/id_globalping_v1.1.sh"
    "/Users/ckchiu/Desktop/Project/id_globalping_test.sh"
    "/Users/ckchiu/Desktop/Project/show_globalping_nodes.sh"
)

echo "📋 將保留以下腳本："
echo "========================================"
for script in "${KEEP_SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        version=$(head -20 "$script" 2>/dev/null | grep -E "^#.*v[0-9]|版本" | head -1 | sed 's/^# *//')
        echo "✅ $(basename $script)"
        [ -n "$version" ] && echo "   $version"
    fi
done

echo ""
echo "🗑️  將刪除以下腳本："
echo "========================================"
for script in "${DELETE_SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        echo "❌ $(basename $script)"
    fi
done

echo ""
echo "========================================"
read -p "確認刪除以上腳本？(y/N): " confirm

if [[ "$confirm" =~ ^[Yy]$ ]]; then
    echo ""
    echo "開始清理..."
    
    deleted_count=0
    for script in "${DELETE_SCRIPTS[@]}"; do
        if [ -f "$script" ]; then
            rm -f "$script"
            if [ $? -eq 0 ]; then
                echo "✅ 已刪除: $(basename $script)"
                ((deleted_count++))
            else
                echo "❌ 刪除失敗: $(basename $script)"
            fi
        fi
    done
    
    echo ""
    echo "========================================"
    echo "清理完成！"
    echo "========================================"
    echo "已刪除: $deleted_count 個腳本"
    echo ""
    echo "保留的腳本："
    echo "  1. v2.0 - ~/id_globalping_multi_v2.sh"
    echo "  2. v2.1 - ~/id_globalping_multi_v2.1.sh"
    echo "  3. v3.0 - ~/Desktop/Project/id_globalping_auto_retry.sh (推薦)"
    echo "  4. v4.0 - ~/Desktop/Project/id_globalping_cli.sh"
    echo "========================================"
else
    echo ""
    echo "已取消清理操作"
fi
