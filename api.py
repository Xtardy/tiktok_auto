import openai
import os
import requests

# Configuration du proxy
proxy = {
    "http": "http://cache.univ-st-etienne.fr:3128",
    "https": "http://cache.univ-st-etienne.fr:3128",
}

# Définir l'API key
api_key = "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"

# Configuration de l'API key dans l'environnement
os.environ["OPENAI_API_KEY"] = api_key

# Fonction pour appeler l'API ChatGPT
def get_response(prompt):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    data = {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 100,
    }

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=data,
        proxies=proxy
    )

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Error: {response.status_code} - {response.text}"

# Exemple d'utilisation
prompt = "Écris-moi un poème sur la beauté de la nature."
response = get_response(prompt)
print(response)
