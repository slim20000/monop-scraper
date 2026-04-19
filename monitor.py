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
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    try:
        response = requests.get(URL, headers=headers, timeout=15)
        # Si Monoprix bloque les requêtes simples, on le verra ici
        if response.status_code != 200:
            print(f"Erreur HTTP : {response.status_code}")
            return []
    except Exception as e:
        print(f"Erreur de connexion : {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    jobs = []
    
    # Nouveau sélecteur plus large pour capturer les offres
    # On cherche tous les liens qui pointent vers une annonce
    listings = soup.select('a[href*="/annonces/"]') 

    for a in listings:
        try:
            # On cherche le titre dans le texte du lien ou les balises parentes
            title = a.text.strip()
            link = "https://recrutement.monoprix.fr" + a['href'] if a['href'].startswith('/') else a['href']
            
            # Pour la localisation, on regarde les éléments autour du lien
            parent = a.find_parent()
            location = "Paris / IDF" # Valeur par défaut si non trouvé
            
            job_id = link.split('/')[-1]

            if title and job_id not in [j['id'] for j in jobs]:
                # On ne garde que si le titre n'est pas vide (évite les faux positifs)
                if len(title) > 5:
                    jobs.append({
                        "id": job_id,
                        "title": title,
                        "location": location,
                        "link": link
                    })
        except Exception as e:
            continue
            
    print(f"Nombre d'offres détectées sur la page : {len(jobs)}")
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
