# 歐洲廁所地圖

一個可在本機測試、以 FastAPI 提供 API 的互動式歐洲地圖。可點選國家，新增廁所 code、城市、地點、日期與備註，並編輯或刪除紀錄。資料以 JSON 檔保存於 `data/records.json`。

## 本機啟動

1. 建立並啟用虛擬環境：`python3 -m venv .venv`，再執行 `source .venv/bin/activate`。
2. 安裝套件：`pip install -r requirements.txt`。
3. 啟動服務：`uvicorn api.index:app --reload`。
4. 開啟 `http://127.0.0.1:8000`。

需要網路連線以載入 Leaflet、OpenStreetMap 圖磚及 GeoJSON 國界資料。

## 部署到 Vercel

將此資料夾推送到 GitHub，在 Vercel 選擇 **Add New → Project** 並匯入該 repository；Vercel 會使用根目錄的 `vercel.json` 與 `requirements.txt` 部署 Python function。

**Vercel Blob 儲存：** 本專案會在 Vercel 上將整份紀錄 JSON 儲存到 private Vercel Blob 的 `restroom-records/records.json`。在 Vercel 專案的 **Storage** 建立一個 **Private Blob** store，並將它連結到此專案的 Production（需要預覽環境時也連結 Preview）。連結後 Vercel 會提供 Blob 所需的環境變數；不需手動把 token 寫入程式或提交到 Git。重新部署後，新增、修改、刪除會讀寫 Blob。若 Blob 尚無紀錄檔，第一次讀取會先以部署包內的 `data/records.json` 作為初始資料，首次寫入時建立 Blob 檔案。

本機若未設定 Blob 環境變數，仍會使用 `data/records.json`。若要在本機連同 Vercel Blob 測試，可先安裝 Vercel CLI、在專案目錄執行 `vercel link` 和 `vercel env pull`，再用 `uvicorn api.index:app --reload --env-file .env.local` 啟動 FastAPI。請勿提交 `.env.local` 或將 Blob token 貼到前端。

這個原型會以覆寫單一 JSON Blob 的方式保存，適合個人低流量使用；不同 serverless 執行個體同時寫入時，最後寫入可能覆蓋較早的變更。API 目前沒有登入驗證，請勿儲存高度敏感的個人資訊或使用公開分享。

## 備註

- 地圖國界資料取自 geo-countries；底圖由 OpenStreetMap 提供。
- 此為單使用者原型，尚未加入登入、資料備份或多人同步。
