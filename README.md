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

**重要：** Vercel 的 serverless 檔案系統不保證持久，也不適合多個 function instance 共用。這個初版在 Vercel 上可瀏覽地圖與讀取初始 JSON，但新增、修改、刪除會回傳提示並停用，避免讓人誤以為資料已永久保存。本機則會寫入 `data/records.json`。正式在線使用前，請將儲存層接至 Vercel Blob、Postgres 或其他持久化資料庫。

## 備註

- 地圖國界資料取自 geo-countries；底圖由 OpenStreetMap 提供。
- 此為單使用者原型，尚未加入登入、資料備份或多人同步。
