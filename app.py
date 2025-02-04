from flask import Flask, render_template, request, send_file
import os
import re
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# Moteurs de recherche dark web
SEARCH_ENGINES = {
    "Ahmia": "https://ahmia.fi/search/?q=",
    "OnionLand": "https://onionlandsearchengine.com/search?q=",
    "Phobos": "https://phobos.engineering/?q=",
}

# Fonction pour rechercher sur plusieurs moteurs
def search_onion_sites(keyword, limit=10):
    results = []
    errors = []

    for engine, base_url in SEARCH_ENGINES.items():
        try:
            url = f"{base_url}{keyword}"
            response = requests.get(url, timeout=15)

            if response.status_code != 200:
                errors.append(f"❌ {engine} inaccessible (Code {response.status_code})")
                continue

            soup = BeautifulSoup(response.text, "html.parser")

            for link in soup.find_all("a", href=True):
                href = link["href"]
                if ".onion" in href:
                    if href not in results:
                        results.append({"url": href, "source": engine})

                if len(results) >= limit:
                    break

        except requests.RequestException as e:
            errors.append(f"❌ Erreur {engine} : {e}")

    return results, errors

# Route pour télécharger les résultats
@app.route("/download_results/<keyword>")
def download_results(keyword):
    results, _ = search_onion_sites(keyword, limit=10)
    filename = f"results_{keyword}.txt"

    with open(filename, "w") as f:
        for res in results:
            f.write(f"{res['url']} (Source: {res['source']})\n")

    return send_file(filename, as_attachment=True)

# Page d'accueil et formulaire de recherche
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        keyword = request.form.get("keyword")
        limit = int(request.form.get("limit"))

        results, errors = search_onion_sites(keyword, limit)

        return render_template("index.html", results=results, errors=errors)

    return render_template("index.html", results=None)

# Lancer l'application
if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0")
