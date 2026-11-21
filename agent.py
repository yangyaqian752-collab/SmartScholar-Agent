import os
import json
from datetime import datetime
from google import genai
from google.genai import types

# 請在執行環境設定環境變數：export GEMINI_API_KEY="金鑰"
if not os.environ.get("GEMINI_API_KEY"):
    raise ValueError("請先設定 GEMINI_API_KEY 環境變數再執行程式。")

client = genai.Client(http_options={'timeout': 60000})

MOCK_CALENDAR = [
    {"date": "2026-11-23", "start": "19:00", "end": "21:00", "title": "社會學社團開會"},
    {"date": "2026-11-25", "start": "20:00", "end": "21:30", "title": "家教打工"},
]

def get_calendar_events(date: str) -> str:
    """查詢指定日期已排定的行事曆事件。"""
    print(f"\n[Tool Call] get_calendar_events(date='{date}')")
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        err = {"status": "error", "message": "日期格式錯誤，請使用 YYYY-MM-DD 格式。"}
        print(f"[Observation] {err}")
        return json.dumps(err, ensure_ascii=False)

    events = [e for e in MOCK_CALENDAR if e["date"] == date]
    result = {"status": "success", "date": date, "existing_events": events}
    print(f"[Observation] {result}")
    return json.dumps(result, ensure_ascii=False)

def add_study_schedule(task_name: str, date: str, start_time: str, end_time: str, priority: str) -> str:
    """將拆解後的讀書或作業子任務排入行事曆，並自動檢查時間衝突與單次讀書時長限制。"""
    print(f"\n[Tool Call] add_study_schedule(task='{task_name}', date='{date}', time='{start_time}-{end_time}', priority='{priority}')")
    try:
        datetime.strptime(date, "%Y-%m-%d")
        t_start = datetime.strptime(start_time, "%H:%M")
        t_end = datetime.strptime(end_time, "%H:%M")
    except ValueError:
        err = {"status": "error", "message": "日期或時間格式錯誤，請確認日期為 YYYY-MM-DD，時間為 HH:MM。"}
        print(f"[Observation] {err}")
        return json.dumps(err, ensure_ascii=False)

    duration_hours = (t_end - t_start).total_seconds() / 3600
    if duration_hours <= 0:
        err = {"status": "error", "message": "結束時間必須晚於開始時間。"}
        print(f"[Observation] {err}")
        return json.dumps(err, ensure_ascii=False)
    if duration_hours > 2.0:
        err = {
            "status": "error",
            "message": f"單次排程 {duration_hours} 小時過長！單次讀書區塊不得超過 2 小時，請拆分成更小的步驟。"
        }
        print(f"[Observation] {err}")
        return json.dumps(err, ensure_ascii=False)

    for event in MOCK_CALENDAR:
        if event["date"] == date:
            if not (end_time <= event["start"] or start_time >= event["end"]):
                err = {
                    "status": "conflict",
                    "message": f"時段衝突！{date} {start_time}-{end_time} 與既有行程「{event['title']} ({event['start']}-{event['end']})」重疊，請改排其他空檔。"
                }
                print(f"[Observation] {err}")
                return json.dumps(err, ensure_ascii=False)

    new_event = {
        "date": date,
        "start": start_time,
        "end": end_time,
        "title": f"[{priority}] {task_name}"
    }
    MOCK_CALENDAR.append(new_event)
    result = {"status": "success", "added_event": new_event}
    print(f"[Observation] {result}")
    return json.dumps(result, ensure_ascii=False)

SYSTEM_INSTRUCTION = """
你是 SmartScholar，一位專為大學生設計的智慧課業與時間管理 AI 助手。
今天日期是 2026-11-21（星期六）。

你的核心任務流程：
1. 分析使用者輸入的所有作業、報告與考試，評估其 Deadline 與「艾森豪矩陣」優先順序。
2. 凡是預估超過 2 小時的大型任務（如 3000 字報告），必須主動拆解成多個 1～1.5 小時的具體子步驟。
3. 在安排時間前，必須先呼叫 `get_calendar_events` 查詢目標日期的既有行程，避開衝突時段。
4. 確認空檔後，呼叫 `add_study_schedule` 將子任務逐一寫入行事曆。若工具回傳衝突或時長過長錯誤，請根據錯誤訊息自動調整時間並重新呼叫工具。
5. 所有任務排定後，向學生總結一份清晰的週讀書計畫表。
"""

def run_agent(user_prompt: str):
    print("=" * 60)
    print(f"[User Input]\n{user_prompt}")
    print("=" * 60)

    candidates = [
        m.name.replace("models/", "")
        for m in client.models.list()
        if "gemini" in m.name.lower() and "embedding" not in m.name.lower()
    ]

    for model_name in candidates:
        try:
            print(f"[System] 正在連線模型: {model_name} ...")
            response = client.models.generate_content(
                model=model_name,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    tools=[get_calendar_events, add_study_schedule],
                    temperature=0.2,
                ),
            )
            print("\n" + "=" * 60)
            print(f"[Final Output]\n{response.text}")
            print("=" * 60)
            return
        except Exception:
            print(f"[Skip] {model_name} 無法使用或超時，立即切換下一個...")
            continue

if __name__ == "__main__":
    sample_prompt = (
        "我下週三（11/25）要考統計學期中考，下週五（11/27）要交一篇 3000 字的社會學報告。"
        "我下週一（11/23）到週四（11/26）每天晚上 19:00 到 22:00 有空，請幫我把這週的讀書計畫排進行事曆！"
    )
    run_agent(sample_prompt)
