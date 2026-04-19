import requests
import json
import os

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
# Nouvelle URL : On pointe directement vers le moteur de recherche interne
API_URL = "https://recrutement.monoprix.fr/api/annonces?workingTimes=2"
DB_FILE = "seen_jobs.json"

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def main():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try: seen_ids = json.load(f)
            except: seen_ids = []
    else:
        seen_ids = []

    # --- CONFIGURATION ANTI-BLOCAGE ---
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://recrutement.monoprix.fr/fr/annonces?workingTimes=2",
    }
    
    try:
        response = requests.get(API_URL, headers=headers)
        # On vérifie si la réponse est vide
        if not response.text:
            print("Le serveur a renvoyé une réponse vide. Blocage probable.")
            return
            
        data = response.json()
        # On cherche la liste des jobs dans 'data' (format habituel de Monoprix)
        offers = data.get('data', [])
        print(f"Connexion réussie ! Nombre d'offres : {len(offers)}")

    except Exception as e:
        print(f"Erreur : {e}")
        return

    new_jobs_found = []
    for job in offers:
        job_id = str(job.get('id'))
        if job_id not in seen_ids:
            title = job.get('title', 'Nouveau Poste')
            city = job.get('city', 'IDF')
            slug = job.get('slug', '')
            link = f"https://recrutement.monoprix.fr/fr/annonces/{slug}"
            
            msg = f"🚀 *Nouveau Job Étudiant !*\n\n📌 *{title}*\n📍 {city}\n🔗 [Voir l'offre]({link})"
            send_telegram_msg(msg)
            seen_ids.append(job_id)
            new_jobs_found.append(job_id)

    if new_jobs_found:
        with open(DB_FILE, "w") as f:
            json.dump(seen_ids, f)
        print(f"Terminé : {len(new_jobs_found)} nouvelles offres envoyées.")
    else:
        print("Fin : Aucune nouvelle offre.")

if __name__ == "__main__":
    main()
