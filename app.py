from flask import Flask, render_template, request, send_file
import os
import re
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

# Initialiser l'application Flask
app = Flask(__name__)

# URL Ahmia en .onion (Tor)
AHMIA_ONION_URL = "https://ahmia.fi/search/?q="

# Récupérer les variables d'environnement pour le proxy
PROXY_HOST = os.getenv("PROXY_HOST", "127.0.0.1")  # Utilise 127.0.0.1 par défaut
PROXY_PORT = os.getenv("PROXY_PORT", "9050")  # Utilise 9050 par défaut
PROXY_URL = f"socks5h://{PROXY_HOST}:{PROXY_PORT}"

# Fonction pour la recherche .onion
def search_onion_sites(keyword, limit=10):
    url = f"{AHMIA_ONION_URL}{keyword}"
    proxies = {
        "http": PROXY_URL,
        "https": PROXY_URL,
    }

    try:
        response = requests.get(url, proxies=proxies, timeout=15)

        if response.status_code != 200:
            return [], f"❌ Erreur : Accès à Ahmia échoué ! (Code {response.status_code})"

        soup = BeautifulSoup(response.text, "html.parser")
        results = []

        # Extraction des liens `.onion`
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if ".onion" in href:
                if href.startswith("/search/redirect?"):
                    match = re.search(r"redirect_url=(http[s]?://[a-z0-9]+\.onion)", href)
                    if match:
                        onion_url = match.group(1)
                        if onion_url not in results:
                            results.append(onion_url)
                else:
                    if href not in results:
                        results.append(href)

            if len(results) >= limit:
                break

        return results, None

    except requests.RequestException as e:
        return [], f"❌ Erreur réseau : {e}"

# Route pour télécharger les résultats
@app.route("/download_results/<keyword>")
def download_results(keyword):
    results, _ = search_onion_sites(keyword, limit=10)  # Obtenir les résultats
    filename = f"results_{keyword}.txt"
    
    with open(filename, "w") as f:
        f.write("\n".join(results))
    
    return send_file(filename, as_attachment=True)

# Page d'accueil et formulaire de recherche
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        keyword = request.form.get("keyword")
        limit = int(request.form.get("limit"))

        results, error = search_onion_sites(keyword, limit)

        if error:
            return render_template("index.html", error=error)

        return render_template("index.html", results=results)

    return render_template("index.html", results=None)

# Lancer l'application
if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0")
