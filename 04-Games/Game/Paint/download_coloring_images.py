#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
著色圖片下載工具
從 lovepik.com 等網站下載著色圖片
"""

import requests
from bs4 import BeautifulSoup
import os
import json
import re
import time
from urllib.parse import urljoin, urlparse
import random

class ColoringImageDownloader:
    def __init__(self, download_dir="downloaded_images"):
        self.download_dir = download_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
        })
        os.makedirs(download_dir, exist_ok=True)
        
    def download_image(self, url, filename):
        """下載單張圖片"""
        try:
            response = self.session.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            filepath = os.path.join(self.download_dir, filename)
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return filepath
        except Exception as e:
            print(f"❌ 下載失敗 {filename}: {str(e)}")
            return None
    
    def scrape_lovepik_coloring(self, url, max_images=20):
        """
        從 lovepik.com 爬取下載著色圖片
        
        Args:
            url: lovepik 著色圖片頁面 URL
            max_images: 最多下載圖片數量
        """
        print(f"🔍 正在訪問: {url}")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找圖片元素（根據網站結構調整選擇器）
            images = []
            seen_urls = set()
            
            # 方法1: 查找所有圖片標籤（優先查找大圖）
            # 嘗試多種可能的屬性
            img_tags = soup.find_all('img')
            
            for img in img_tags:
                # 嘗試多種可能的圖片 URL 屬性
                img_url = (img.get('data-src') or 
                          img.get('data-original') or 
                          img.get('data-lazy') or
                          img.get('src') or 
                          img.get('data-url'))
                
                if not img_url:
                    continue
                
                # 過濾掉小圖標和無用圖片
                skip_patterns = ['logo', 'icon', 'avatar', 'button', 'ad', 'banner', 'advertisement']
                if any(skip in img_url.lower() for skip in skip_patterns):
                    continue
                
                # 過濾掉太小的圖片（可能是縮圖）
                width = img.get('width') or img.get('data-width')
                height = img.get('height') or img.get('data-height')
                if width and height:
                    try:
                        if int(width) < 200 or int(height) < 200:
                            continue
                    except:
                        pass
                
                # 確保是完整 URL
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                elif img_url.startswith('/'):
                    img_url = urljoin(url, img_url)
                
                # 去重
                if img_url in seen_urls:
                    continue
                seen_urls.add(img_url)
                
                # 獲取圖片名稱
                alt_text = img.get('alt', '') or img.get('title', '')
                if alt_text:
                    # 清理檔案名
                    filename = re.sub(r'[^\w\s\u4e00-\u9fff-]', '', alt_text)
                    filename = filename.strip()[:50] or 'image'
                    filename += '.png'
                else:
                    filename = os.path.basename(urlparse(img_url).path)
                    if not filename or '.' not in filename:
                        filename = f'coloring_{len(images)}.png'
                
                # 確保是圖片格式（允許沒有擴展名的，可能是動態 URL）
                if '.' in img_url:
                    ext = os.path.splitext(img_url)[1].lower()
                    if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                        continue
                
                images.append({
                    'url': img_url,
                    'filename': filename,
                    'name': alt_text or filename.replace('.png', '')
                })
                
                if len(images) >= max_images:
                    break
            
            # 方法2: 查找連結中的圖片（有些網站圖片在 <a> 標籤中）
            if len(images) < max_images:
                links = soup.find_all('a', href=True)
                for link in links:
                    if len(images) >= max_images:
                        break
                    
                    href = link.get('href', '')
                    # 檢查是否是圖片連結
                    if any(href.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                        if href.startswith('//'):
                            img_url = 'https:' + href
                        elif href.startswith('/'):
                            img_url = urljoin(url, href)
                        else:
                            img_url = href
                        
                        if img_url not in seen_urls:
                            seen_urls.add(img_url)
                            alt_text = link.get('title', '') or link.get_text(strip=True)[:50]
                            filename = re.sub(r'[^\w\s\u4e00-\u9fff-]', '', alt_text)[:50] + '.png' if alt_text else os.path.basename(urlparse(img_url).path) or f'coloring_{len(images)}.png'
                            
                            images.append({
                                'url': img_url,
                                'filename': filename,
                                'name': alt_text or filename.replace('.png', '')
                            })
            
            print(f"✅ 找到 {len(images)} 張圖片")
            
            # 下載圖片
            downloaded = []
            for i, img_info in enumerate(images, 1):
                print(f"📥 [{i}/{len(images)}] 下載中: {img_info['name']}")
                filepath = self.download_image(img_info['url'], img_info['filename'])
                if filepath:
                    downloaded.append({
                        'filename': img_info['filename'],
                        'name': img_info['name'],
                        'path': filepath,
                        'url': img_info['url']
                    })
                time.sleep(0.5)  # 避免請求過快
            
            return downloaded
            
        except Exception as e:
            print(f"❌ 爬取失敗: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def save_metadata(self, downloaded_images, metadata_file="downloaded_metadata.json"):
        """保存下載圖片的元數據"""
        metadata = {
            'images': downloaded_images,
            'total': len(downloaded_images),
            'download_time': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        filepath = os.path.join(self.download_dir, metadata_file)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        print(f"💾 元數據已保存到: {filepath}")
        return filepath

def main():
    print("=" * 60)
    print("🎨 著色圖片下載工具")
    print("=" * 60)
    print()
    
    # 創建下載器
    downloader = ColoringImageDownloader(download_dir="downloaded_images")
    
    # 目標 URL
    url = "https://zh.lovepik.com/images/coloring.html"
    
    print("⚠️  注意事項:")
    print("1. 請確保遵守網站的服務條款和版權規定")
    print("2. 僅供個人學習使用，請勿用於商業用途")
    print("3. 下載速度已限制，避免對服務器造成壓力")
    print()
    
    # 詢問下載數量
    try:
        max_images = int(input("請輸入要下載的圖片數量 (預設 10): ") or "10")
    except ValueError:
        max_images = 10
    
    print()
    print(f"開始下載，最多下載 {max_images} 張圖片...")
    print()
    
    # 開始下載
    downloaded = downloader.scrape_lovepik_coloring(url, max_images=max_images)
    
    print()
    print("=" * 60)
    if downloaded:
        print(f"✅ 成功下載 {len(downloaded)} 張圖片")
        print(f"📁 保存位置: {downloader.download_dir}/")
        
        # 保存元數據
        downloader.save_metadata(downloaded)
        
        print()
        print("📝 使用說明:")
        print("1. 打開網站，點擊「圖片庫」")
        print("2. 點擊「上傳本地圖片」")
        print("3. 選擇下載的圖片進行著色")
    else:
        print("❌ 沒有下載到圖片")
        print()
        print("💡 提示:")
        print("- 網站結構可能已變更，需要調整爬蟲選擇器")
        print("- 可以手動從網站下載圖片，然後使用「上傳本地圖片」功能")
        print("- 或使用瀏覽器擴展（如 DownThemAll）批量下載")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  用戶中斷下載")
    except Exception as e:
        print(f"\n\n❌ 發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()

