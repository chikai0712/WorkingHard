#!/usr/bin/env python3
"""
測試系統可用的中文字體
"""
import pygame

pygame.init()

print("=" * 60)
print("🔍 檢測系統可用字體")
print("=" * 60)

# 獲取所有系統字體
all_fonts = pygame.font.get_fonts()
print(f"\n📊 系統共有 {len(all_fonts)} 個字體\n")

# 篩選可能支援中文的字體
chinese_keywords = ['ping', 'fang', 'hei', 'gothic', 'unicode', 'song', 'ming', 'kai', 'apple', 'arial']
chinese_fonts = [f for f in all_fonts if any(keyword in f.lower() for keyword in chinese_keywords)]

print("🈯 可能支援中文的字體:")
print("-" * 60)
for i, font in enumerate(chinese_fonts, 1):
    print(f"{i:2d}. {font}")

print("\n" + "=" * 60)
print("🧪 測試字體渲染中文")
print("=" * 60)

test_text = "噴火龍"
screen = pygame.display.set_mode((100, 100))

print("\n測試結果:")
print("-" * 60)

working_fonts = []
for font_name in chinese_fonts[:20]:  # 只測試前20個
    try:
        font = pygame.font.SysFont(font_name, 24)
        surface = font.render(test_text, True, (255, 255, 255))
        width = surface.get_width()
        
        if width > 50:  # 如果寬度合理，表示可能正確渲染了
            print(f"✅ {font_name:30s} - 寬度: {width}px")
            working_fonts.append(font_name)
        else:
            print(f"❌ {font_name:30s} - 寬度: {width}px (太窄)")
    except Exception as e:
        print(f"⚠️  {font_name:30s} - 錯誤: {e}")

print("\n" + "=" * 60)
print("📋 建議使用的字體:")
print("=" * 60)
if working_fonts:
    for i, font in enumerate(working_fonts, 1):
        print(f"{i}. {font}")
else:
    print("❌ 沒有找到可用的中文字體")

pygame.quit()

