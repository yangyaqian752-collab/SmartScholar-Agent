# SmartScholar-Agent

SmartScholar 是一款專為大學生設計的智慧課業拆解與時間管理 ReAct AI Agent，基於 Google GenAI SDK 開發。

## 核心功能
- **任務急迫性評估**：根據截止日期自動套用艾森豪矩陣（重要且緊急 / 重要不緊急）排序任務。
- **大型作業自動拆解**：將超過 2 小時的長篇報告或考試複習拆解為 1～1.5 小時的具體子任務。
- **行事曆衝突防護**：寫入行程前自動查詢既有行程，偵測重疊時自動避開並重新安排空檔。

## 安裝與執行方式
1. 安裝相依套件：
   ```bash
   pip install -r requirements.txt
