from flask import Flask, render_template, request, send_file
import os
import re
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# URL de base pour Ahmia
AHMIA_URL = "https://ahmia.fi/search/?q="  # Changer en https pour sécuriser la connexion

# Exemple de moteurs de recherche (les autres moteurs doivent être ajoutés)
ONIONSEARCH_URL = "https://onionsearchengine.com/search?q="
DARKSEARCH_URL = "https://darksearch.io/search?q="

# Fonction de recherche pour Ahmia
def search_onion_sites_ahmia(keyword, limit=10):
    url = f"{AHMIA_URL}{keyword}"

    try:
        response = requests.get(url, timeout=15)
        if response.status_code != 200:
            return [], f"❌ Erreur Ahmia : Accès échoué (Code {response.status_code})"
        
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        
        # Extraction des liens .onion
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
        return [], f"❌ Erreur réseau Ahmia : {e}"

# Fonction de recherche pour OnionSearch
def search_onion_sites_onionsearch(keyword, limit=10):
    url = f"{ONIONSEARCH_URL}{keyword}"

    try:
        response = requests.get(url, timeout=15)
        if response.status_code != 200:
            return [], f"❌ Erreur OnionSearch : Accès échoué (Code {response.status_code})"
        
        soup = BeautifulSoup(response.text, "html.parser")
        results = []

        for link in soup.find_all("a", href=True):
            href = link["href"]
            if ".onion" in href:
                if href not in results:
                    results.append(href)

            if len(results) >= limit:
                break

        return results, None

    except requests.RequestException as e:
        return [], f"❌ Erreur réseau OnionSearch : {e}"

# Fonction de recherche pour DarkSearch
def search_onion_sites_darksearch(keyword, limit=10):
    url = f"{DARKSEARCH_URL}{keyword}"

    try:
        response = requests.get(url, timeout=15)
        if response.status_code != 200:
            return [], f"❌ Erreur DarkSearch : Accès échoué (Code {response.status_code})"
        
        soup = BeautifulSoup(response.text, "html.parser")
        results = []

        for link in soup.find_all("a", href=True):
            href = link["href"]
            if ".onion" in href:
                if href not in results:
                    results.append(href)

            if len(results) >= limit:
                break

        return results, None

    except requests.RequestException as e:
        return [], f"❌ Erreur réseau DarkSearch : {e}"

# Route pour télécharger les résultats
@app.route("/download_results/<keyword>")
def download_results(keyword):
    results, _ = search_onion_sites_ahmia(keyword, limit=10)  # Obtenir les résultats depuis Ahmia par défaut
    filename = f"results_{keyword}.txt"
    
    with open(filename, "w") as f:
        f.write("\n".join(results))
    
    return send_file(filename, as_attachment=True)

# Route pour la recherche
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        keyword = request.form.get("keyword")
        limit = int(request.form.get("limit"))
        engine = request.form.get("engine")

        results = {}

        # Rechercher sur les moteurs choisis
        if engine == "ahmia":
            results['Ahmia'], error = search_onion_sites_ahmia(keyword, limit)
        elif engine == "onionsearch":
            results['OnionSearch'], error = search_onion_sites_onionsearch(keyword, limit)
        elif engine == "darksearch":
            results['DarkSearch'], error = search_onion_sites_darksearch(keyword, limit)

        if error:
            return render_template("index.html", error=error)

        return render_template("index.html", results=results)

    return render_template("index.html", results=None)

# Lancer l'application
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
