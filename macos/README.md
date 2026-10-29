# Azeroth Survivors for this Mac

以原作者 Aethus 的 **v0.123.0（425f2391）網頁遊戲核心**製作 Apple Silicon macOS App。遊戲核心使用 WebAssembly／WebGPU，Electron 的 Chromium 透過 Metal 顯示畫面。

這個工作目錄包含本次修改的啟動器及打包工具。遊戲核心與大型資源保留於外接磁碟，不加入版本控制。

## 來源及版本

- 原作者及官方網頁：[Aethus](https://wow.aethus.pl/)。
- Mac 封裝基礎：[myslithell/azeroth-survivors v0.120.5](https://github.com/myslithell/azeroth-survivors/releases/tag/v0.120.5)。
- 基礎啟動器 commit：`a65664af64f4377159463cd128424eeb6f132102`。
- 使用者提供的 `AzerothSurvivorsWindowsNew.rar` SHA-256：`6cf1108db4e8bd7f55e214e24e976a6f24ab657a3eed86c16743ff76e6b85671`，與該 release 的 Windows RAR 完全一致。
- Windows EXE 可見 `f78e6fab`／`0.102.3` 版本字串；基礎 Mac ZIP 是 `e0e2410c`／`0.120.5`，本次再更新為官網 `425f2391`／`0.123.0`，網頁 stamp 為 `aaf932e1a8fb`。RAR 雜湊一致不代表 Windows EXE 與 Mac WASM 是同一版核心。
- Mac ZIP SHA-256：`f948d53b6a5dd201e91bdbdd2ac20178a42181954756ce63ff0596251d17886d`。

本次選擇保留原版玩法。另有 [OutThisLife 開源重建版](https://github.com/OutThisLife/azeroth-survivors-re)，其玩法及功能與原版有差異，因此本次未採用。

## 啟動器變更

保留產品名稱及固定本機網址 `http://127.0.0.1:47615`，避免改變存檔位置。修正錯誤 URL 導致程序結束的問題，限制靜態服務讀取範圍，處理檔案串流錯誤，並明確啟用 Electron renderer sandbox、context isolation 及關閉 Node integration。

遊戲視窗維持本機內容。官方網站及 Discord 的 HTTPS 連結透過系統瀏覽器開啟。未加入自動更新；遊戲 WASM 更新為官方原始檔，沒有修改核心二進位。完整下載快照與 SHA-256 記錄於 `assets/latest-web-core/core-manifest.json`。

原始 Mac 包缺少遊戲專用的中、日、韓字型，選簡體中文後會出現方框。本次從官方網站取得 `azs_sc.ttf`、`azs_jp.ttf`、`azs_kr.ttf` 原始檔，補入資源及資源索引。四套既有拉丁字型保持原始內容；沒有合併或替換字形。下載網址、大小及 SHA-256 記錄於 `assets/official-fonts/font-patch.json`，補丁版本為 `official-cjk-v3`。

語言選擇沿用遊戲自己的設定，沒有強制英文或改寫瀏覽器語言。簡體中文主選單已用實際 App 畫面及字型 HTTP 200 回應驗證；日文、韓文字型已驗證檔案及樣本字形，尚未逐頁驗證介面。

每個核心建置與字型補丁首次啟動只清除本 App 的 HTTP 資源快取，讓先前以 immutable 快取的舊字型重新讀取。存檔、localStorage、Cookie 與設定保留。

中文字型解決顯示問題，名稱欄的中文輸入仍有限制，目前請使用英文字母命名。完整原作 Rust 原始碼尚未找到，沒有宣稱已修復輸入法或名稱驗證。

## 存檔

App 的進度獨立於官方網站，儲存在 `~/Library/Application Support/Azeroth Survivors` 的 Chromium profile。備份時先結束遊戲，再複製整個資料夾。重新打包或替換 App 不會刪除它。

官方網站的進度可用遊戲內 Options → Saves 匯出，再於 App 匯入。Windows 存檔的直接相容性尚未驗證。

互動測試時使用獨立的 `azeroth-mac-` profile。若使用者在該 profile 開始遊戲，可由一次性的 `~/Library/Application Support/Azeroth Survivors.pending-profile.json` 記錄來源與原程序 PID。一般啟動會在建立 Chromium session 及取得單一程序鎖之前處理它：原程序仍在執行時沿用來源並聚焦既有視窗；結束後才複製至正式 profile。複製保留存檔、偏好、Cookie 和 IndexedDB，略過快取及程序鎖，保留來源資料。正式 profile 已有檔案時會停止並顯示錯誤，避免覆寫任何既有進度。

明確傳入 `--user-data-dir=/absolute/path` 時使用指定 profile，不執行上述移轉。移轉是否完成，以 pending JSON 的 `completed` 及實際正式資料夾為準。

## 重建

需要 macOS、Python 3.11+、Node.js 及 Xcode Command Line Tools。使用既有 release 的 Electron runtime 及原版遊戲資源，不必安裝 npm 套件或重新產生字型。`assets/official-fonts` 必須包含 manifest 及三套通過雜湊驗證的官方字型；`assets/latest-web-core` 必須包含完成下載的核心快照與 `core-manifest.json`。

```sh
node --test mac/static-server.test.js mac/profile-migration.test.js mac/coop-proxy.test.js
python3 scripts/package_macos.py \
  --archive /path/to/AzerothSurvivors-macOS-AppleSilicon.zip \
  --output /path/to/new-output-directory \
  --web-core /path/to/verified-latest-web-core
```

工具先核對 ZIP 與最新官方核心快照的 SHA-256，再解壓、覆蓋對應核心及新增資源、加入本次啟動器，更新本機 ad-hoc signature，並驗證完整 App 簽章。輸出目錄必須尚未存在。這不是 Apple Developer ID 簽署或公證版本。

三套官方字型的名稱表識別為 Noto Sans SC／JP／KR，並記載 SIL Open Font License 1.1。對應 Adobe 版權聲明及 OFL 授權文字隨 App 放在 `Contents/Resources/NotoSansSC-OFL.txt`。

本機測試與安裝結果記錄於 `evidence/verification.json`。

## 聯機修復

原始網頁核心使用目前頁面的主機組合 `/coop/lobby/` 等 WebSocket 網址。離線 Mac 包從本機網址載入，卻沒有轉送聯機路由，因此大廳握手收到本機 HTTP 404。`mac/coop-proxy.js` 將這些路由固定轉發至官方 `wow.aethus.pl` HTTPS／WebSocket 服務，保留雙向二進位資料及本機 Origin。官方服務已接受此 Origin；不需要停用 TLS 憑證驗證或 Electron webSecurity。其他網站及任意目標不能經此轉發。

遊戲內以「合作」建立房間並分享代碼，另一端使用「輸入代碼加入」。雙方應核對遊戲畫面顯示的版本；官方大廳按版本分組，舊版原生 Windows RAR 不保證可加入新版網頁核心。最新 App 的實際建房、加入和同步驗證狀態見 `evidence/verification.json`。

更新前的正式 profile 已保存在 `~/Library/Application Support/Azeroth Survivors Profile Backups/before-latest-core-20261028`。原存檔資料夾未覆寫，沒有建立 pending profile 移轉記錄。

## 本次驗證結果

14項本機測試通過，App的deep/strict簽章驗證通過。已在Mac App與另一個獨立Chromium程序間，透過官方服務完成大廳列表、建房、代碼加入、雙方入圖及移動同步；這是同一台Mac上的兩個程序，尚未和實體Windows電腦測試。長時間通關及斷線重連不在已完成驗證範圍內。

Windows朋友應啟動原作並完成官方更新，確認遊戲顯示0.123.0。官方更新清單 `https://wow.aethus.pl/exe/latest.json` 明確要求房主與客人使用此版本。

右鍵藍線來自本機BetterAndBetter的全域手勢。已透過其應用程式黑名單，僅排除本App的bundle identifier `pl.aethus.azeroth-survivors.local`；其他應用的規則保留。設定已落盤，原生右鍵按下/放開事件已進入遊戲且沒有彈出選單；沒有修改遊戲滑鼠控制或全域關閉該工具。
