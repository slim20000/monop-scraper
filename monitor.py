import requests
from bs4 import BeautifulSoup
import json
import os
import time

# --- CONFIGURATION ---
# Remplace ces valeurs ou utilise des variables d'environnement
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
URL = "https://recrutement.monoprix.fr/fr/annonces?workingTimes=2"
DB_FILE = "seen_jobs.json"
FILTER_LOCATIONS = ["Paris", "Île-de-France", "75", "92", "93", "94"] # Filtres bonus

def send_telegram_msg(message):
    if not TOKEN or not CHAT_ID:
        print("Erreur: Token ou Chat ID manquant.")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Erreur envoi Telegram: {e}")

def scrape_jobs():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(URL, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Erreur lors du crawl : {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    jobs = []
    
    # Sélecteur basé sur la structure typique de Monoprix (balises <li> ou <div> d'offres)
    # Note : Les sélecteurs peuvent varier si le site change.
    listings = soup.find_all('li', class_='list-item') 

    for item in listings:
        try:
            title_elem = item.find('h3') or item.find('a', class_='title')
            link_elem = item.find('a', href=True)
            loc_elem = item.find('span', class_='location') # À ajuster selon le HTML réel
            
            title = title_elem.text.strip() if title_elem else "Sans titre"
            link = "https://recrutement.monoprix.fr" + link_elem['href'] if link_elem else ""
            location = loc_elem.text.strip() if loc_elem else "Non spécifiée"
            job_id = link.split('/')[-1] # On utilise la fin de l'URL comme ID unique

            # Filtre Bonus : Localisation
            if any(loc.lower() in location.lower() for loc in FILTER_LOCATIONS) or not FILTER_LOCATIONS:
                jobs.append({
                    "id": job_id,
                    "title": title,
                    "location": location,
                    "link": link
                })
        except Exception as e:
            continue
            
    return jobs

def main():
    # 1. Charger les anciennes offres
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            seen_ids = json.load(f)
    else:
        seen_ids = []

    # 2. Scraper
    current_jobs = scrape_jobs()
    new_jobs = [j for j in current_jobs if j['id'] not in seen_ids]

    # 3. Traiter les nouvelles offres
    if new_jobs:
        print(f"{len(new_jobs)} nouvelle(s) offre(s) trouvée(s) !")
        
        if len(new_jobs) > 1:
            header = f"🚀 *{len(new_jobs)} nouvelles opportunités chez Monoprix !*\n\n"
        else:
            header = "🚀 *Nouvelle offre Monoprix trouvée !*\n\n"

        for job in new_jobs:
            msg = (f"📌 *{job['title']}*\n"
                   f"📍 {job['location']}\n"
                   f"🔗 [Postuler ici]({job['link']})\n\n")
            send_telegram_msg(header + msg)
            seen_ids.append(job['id'])

        # 4. Sauvegarder
        with open(DB_FILE, "w") as f:
            json.dump(seen_ids, f)
    else:
        print("Aucune nouvelle offre.")

if __name__ == "__main__":
    main()