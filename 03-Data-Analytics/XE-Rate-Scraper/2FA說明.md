# XE.com 2FA（兩步驟驗證）說明

## 🔐 什麼是 2FA？

XE.com 使用兩步驟驗證（2FA）來增強帳號安全性。登入後可能需要：
- 手機簡訊驗證碼
- 驗證器 App 代碼
- 或其他安全驗證方式

## ⚠️ 自動登入的限制

如果您的帳號啟用了 2FA，**自動登入會遇到挑戰**：
1. 登入後會被重定向到 2FA 驗證頁面
2. 需要手動輸入驗證碼
3. 自動化無法完全自動完成

## ✅ 解決方案

### 方案 1: 使用 Cookies 方式（最推薦 ⭐⭐⭐）

**這是最可靠的方式，可以完全繞過 2FA 問題**：

```bash
# 1. 手動登入（包括 2FA）並保存 cookies
python3 manual_login_helper.py

# 2. 使用保存的 cookies 執行抓取
python3 xe_scraper.py --use-cookies
```

**優點**：
- ✅ 只需手動登入一次（包括 2FA）
- ✅ 之後可以自動使用，無需再次驗證
- ✅ Cookies 可以持續使用（直到過期）

### 方案 2: 使用 --no-headless 手動完成 2FA

如果仍想使用自動登入，可以在非 headless 模式下手動完成 2FA：

```bash
python3 xe_scraper.py --email your-email --password your-password --no-headless
```

**流程**：
1. 程式會自動填寫 Email 和密碼
2. 點擊登入按鈕
3. 當檢測到 2FA 頁面時，會暫停並提示
4. 您在瀏覽器中手動完成 2FA
5. 回到終端機按 Enter 繼續

## 🎯 建議

**對於啟用 2FA 的帳號，強烈建議使用 Cookies 方式**：
- 更簡單：只需手動登入一次
- 更可靠：不會因為 2FA 而中斷
- 更穩定：Cookies 可以重複使用

## 📝 使用 Cookies 方式的步驟

1. **執行手動登入工具**：
   ```bash
   python3 manual_login_helper.py
   ```

2. **在瀏覽器中完成登入**：
   - 輸入 Email 和密碼
   - 完成 2FA 驗證（輸入驗證碼）
   - 確認已成功登入

3. **回到終端機按 Enter**：
   - 程式會保存 cookies 到 `xe_cookies.json`

4. **使用 cookies 執行抓取**：
   ```bash
   python3 xe_scraper.py --use-cookies
   ```

5. **之後每次執行**：
   - 直接使用 `--use-cookies` 即可
   - 無需再次登入或驗證
   - 直到 cookies 過期（通常幾天到幾週）

## 🔄 Cookies 過期處理

如果 cookies 過期，會看到登入頁面。解決方法：

```bash
# 重新執行手動登入
python3 manual_login_helper.py
```

---

**最後更新**: 2025-12-29

