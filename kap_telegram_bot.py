import requests
import time
from datetime import datetime

# ============================================================
TELEGRAM_TOKEN = "8868994040:AAFofEcW3F9Narz3tG88jnvW39wD45MErOk"
CHAT_ID        = "8218401444"
# ============================================================

KAP_API_URL = "https://www.kap.org.tr/tr/api/disclosures"
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
        return resp.json().get("data", [])
    except Exception as e:
        print(f"[{now()}] Veri çekme hatası: {e}")
        return []


def format_message(item):
    ticker   = item.get("stockCodes", ["?"])[0] if item.get("stockCodes") else "?"
    title    = item.get("disclosureTitle", "Başlık yok")
    company  = item.get("companyName", "")
    date_str = item.get("publishDate", "")
    url      = f"https://www.kap.org.tr/tr/Bildirim/{item.get('disclosureId','')}"

    keywords_high = ["ortaklık", "birleşme", "satın alma", "iflas", "konkordato",
                     "kayyum", "el koyma", "dava", "ceza", "yönetim kurulu değişiklik"]
    keywords_mid  = ["sözleşme", "ihale", "kredi", "yatırım", "tesis", "üretim"]

    title_lower = title.lower()
    if any(k in title_lower for k in keywords_high):
        icon = "🔴"
    elif any(k in title_lower for k in keywords_mid):
        icon = "🟡"
    else:
        icon = "🟢"

    return (
        f"{icon} *ÖDA | {ticker}*\n"
        f"🏢 {company}\n"
        f"📋 {title}\n"
        f"🕐 {date_str}\n"
        f"🔗 [KAP'ta Gör]({url})"
    )


def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        print(f"[{now()}] Mesaj gönderildi.")
    except Exception as e:
        print(f"[{now()}] Telegram hatası: {e}")


def now():
    return datetime.now().strftime("%H:%M:%S")


def main():
    print(f"[{now()}] KAP Bot başladı...")
    send_telegram("✅ *KAP Bot aktif!*\nÖzel durum açıklamaları anlık takip ediliyor.")

    initial = fetch_disclosures()
    for item in initial:
        seen_ids.add(item.get("disclosureId"))
    print(f"[{now()}] {len(seen_ids)} mevcut bildirim yüklendi.")

    while True:
        time.sleep(CHECK_INTERVAL)
        items = fetch_disclosures()
        new_count = 0

        for item in reversed(items):
            disc_id = item.get("disclosureId")
            if disc_id and disc_id not in seen_ids:
                seen_ids.add(disc_id)
                msg = format_message(item)
                send_telegram(msg)
                new_count += 1
                time.sleep(1)

        if new_count:
            print(f"[{now()}] {new_count} yeni bildirim gönderildi.")
        else:
            print(f"[{now()}] Yeni bildirim yok.")


if __name__ == "__main__":
    main()
