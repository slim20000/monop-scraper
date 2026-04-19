import requests
import json
import os

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
# URL de l'API Monoprix
API_URL = "https://recrutement.monoprix.fr/api/annonces?workingTimes=2"
DB_FILE = "seen_jobs.json"

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def main():
    # Chargement de la mémoire
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try:
                seen_ids = json.load(f)
            except:
                seen_ids = []
    else:
        seen_ids = []

    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(API_URL, headers=headers)
        data = response.json()
        
        # --- DEBUG : On affiche les clés reçues pour comprendre la structure ---
        print(f"Clés reçues de l'API : {data.keys()}")
        
        # Tentative de trouver la liste des offres dans différentes clés possibles
        # Monoprix peut utiliser 'data', 'items', 'annonces' ou être une liste directe
        offers = []
        if isinstance(data, list):
            offers = data
        elif 'data' in data:
            offers = data['data']
        elif 'items' in data:
            offers = data['items']
        elif 'annonces' in data:
            offers = data['annonces']
            
        print(f"Nombre d'offres trouvées : {len(offers)}")

    except Exception as e:
        print(f"Erreur lors de l'appel API : {e}")
        return

    new_jobs = []
    for job in offers:
        # On récupère l'ID (peut être sous 'id' ou 'reference')
        job_id = str(job.get('id') or job.get('reference'))
        
        if job_id and job_id not in seen_ids:
            title = job.get('title') or job.get('libelle') or "Poste"
            city = job.get('city') or job.get('ville') or "IDF"
            slug = job.get('slug') or job_id
            link = f"https://recrutement.monoprix.fr/fr/annonces/{slug}"
            
            new_jobs.append({
                "id": job_id,
                "msg": f"📌 *{title}*\n📍 {city}\n🔗 [Voir l'offre]({link})"
            })

    if new_jobs:
        for job in new_jobs:
            send_telegram_msg(f"🚀 *Nouvelle offre Monoprix !*\n\n{job['msg']}")
            seen_ids.append(job['id'])
        
        with open(DB_FILE, "w") as f:
            json.dump(seen_ids, f)
        print(f"Succès : {len(new_jobs)} messages envoyés.")
    else:
        print("Fin du script : Aucune nouvelle offre à traiter.")

if __name__ == "__main__":
    main()
