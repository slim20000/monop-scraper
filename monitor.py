import requests
import json
import os

# --- CONFIGURATION ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
# L'URL magique (l'API directe de leur système de recrutement)
API_URL = "https://recrutement.monoprix.fr/api/annonces?workingTimes=2"
DB_FILE = "seen_jobs.json"

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def main():
    # 1. Charger l'historique
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try:
                seen_ids = json.load(f)
            except:
                seen_ids = []
    else:
        seen_ids = []

    # 2. Appeler l'API
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(API_URL, headers=headers)
        data = response.json() # On récupère directement du JSON
        # La structure de leur API met les offres dans une liste 'items' ou 'data'
        # On s'adapte à leur format standard
        offers = data.get('data', []) 
    except Exception as e:
        print(f"Erreur API: {e}")
        return

    new_jobs = []
    for job in offers:
        job_id = str(job.get('id'))
        if job_id not in seen_ids:
            # Extraction des infos
            title = job.get('title', 'Poste sans titre')
            city = job.get('city', 'France')
            # Construction du lien direct vers l'annonce
            slug = job.get('slug', '')
            link = f"https://recrutement.monoprix.fr/fr/annonces/{slug}"
            
            new_jobs.append({
                "id": job_id,
                "msg": f"📌 *{title}*\n📍 {city}\n🔗 [Voir l'offre]({link})"
            })

    # 3. Envoyer et Sauvegarder
    if new_jobs:
        for job in new_jobs:
            send_telegram_msg(f"🚀 *Nouvelle offre Temps Partiel !*\n\n{job['msg']}")
            seen_ids.append(job['id'])
        
        with open(DB_FILE, "w") as f:
            json.dump(seen_ids, f)
        print(f"{len(new_jobs)} offres envoyées.")
    else:
        print("Aucune nouvelle offre sur l'API.")

if __name__ == "__main__":
    main()
