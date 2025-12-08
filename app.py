import os
from openai import OpenAI

from fastapi import FastAPI # Assurez-vous que cet import est là

# ... (Le reste de vos imports)

# --- NOUVEAU CODE POUR LIRE LA CLÉ DE L'ENVIRONNEMENT ---
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    # Ceci est une sécurité, Vercel s'assurera que la clé est là
    print("Erreur: La clé OPENAI_API_KEY n'est pas définie dans l'environnement.")
    # Vous pouvez laisser le programme planter ici si la clé est absente, c'est plus sûr.

client = OpenAI(api_key=OPENAI_API_KEY)
# --- FIN DU NOUVEAU CODE ---

# ... (Le reste de votre application FastAPI)