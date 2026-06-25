import requests
import time
import os
from datetime import datetime

# ==============================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID        = "8218401444"
# ==============================================

KAP_API_URL = "https://www.kap.org.tr/tr/api/disclosure-query"
CHECK_INTERVAL = 60

seen_ids = set()

def fetch_disclosures():
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Referer": "https://www.kap.org.tr/",
    }
    params = {
        "disclosureTypes": "ODA",
        "orderBy": "date",
        "orderDir": "desc",
        "pageSize": 20,
        "pageIndex": 0,
    }
    try:
        resp = requests.get(KAP_API_URL, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", [])
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Veri çekme hatası: {e}")
        return []

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Telegram hatası: {e}")

def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] KAP Bot başladı.")
    send_telegram("✅ KAP Bot aktif!\nÖzel durum açıklamaları anlık takip ediliyor.")
    
    while True:
        disclosures = fetch_disclosures()
        new_count = 0
        for item in disclosures:
            did = item.get("id") or item.get("disclosureIndex")
            if did and did not in seen_ids:
                seen_ids.add(did)
                title = item.get("title", "")
                company = item.get("companyName", "")
                date = item.get("publishDate", "")
                msg = f"📢 <b>{company}</b>\n{title}\n🕐 {date}"
                send_telegram(msg)
                new_count += 1
        
        if new_count == 0:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Yeni bildirim yok.")
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
