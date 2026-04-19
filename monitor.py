import requests
from bs4 import BeautifulSoup
import json
import os

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

URL = "https://recrutement.monoprix.fr/fr/annonces?workingTimes=2"
DB_FILE = "seen_jobs.json"

FILTER_LOCATIONS = [
    "paris", "75",
    "hauts-de-seine", "92",
    "seine-saint-denis", "93",
    "val-de-marne", "94",
    "ile de france"
]

def is_valid_location(location):
    location = location.lower()
    return any(x in location for x in FILTER_LOCATIONS)

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": message
    })

def scrape_jobs():
    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(URL, headers=headers, timeout=15)
    soup = BeautifulSoup(r.text, "html.parser")

    jobs = []

    for a in soup.find_all("a", href=True):
        title = a.get_text(strip=True)
        link = a["href"]

        if not title or len(title) < 10:
            continue

        if link.startswith("/"):
            link = "https://recrutement.monoprix.fr" + link

        location = "Non spécifiée"

        if is_valid_location(location):
            jobs.append({
                "id": link,
                "title": title,
                "location": location,
                "link": link
            })

    return jobs

def main():
    send_telegram_msg("Test de connexion : Le script s'est lancé !")
    seen = []

    if os.path.exists(DB_FILE):
        seen = json.load(open(DB_FILE))

    jobs = scrape_jobs()
    new_jobs = [j for j in jobs if j["id"] not in seen]

    if not new_jobs:
        print("Aucune offre")
        return

    message = f"🚀 {len(new_jobs)} nouvelles offres Monoprix\n\n"

    for job in new_jobs:
        message += f"📌 {job['title']}\n📍 {job['location']}\n🔗 {job['link']}\n\n"
        seen.append(job["id"])

    send_telegram_msg(message)

    json.dump(seen, open(DB_FILE, "w"))

if __name__ == "__main__":
    main()
