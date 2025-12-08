import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # AJOUT POUR CORS
from pydantic import BaseModel
from openai import OpenAI

# --- 1. CONFIGURATION DE L'APPLICATION ET DE L'API KEY ---

# L'instance de l'application doit être ici pour que Vercel la trouve
app = FastAPI()

# --- AJOUT DU MIDDLEWARE CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://tassouvra.com", "http://tassouvra.com"],  # Autoriser votre site
    allow_credentials=True,
    allow_methods=["*"],  # Autoriser toutes les méthodes HTTP
    allow_headers=["*"],  # Autoriser tous les en-têtes
 )
# --- FIN AJOUT CORS ---

# Récupération de la clé API
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Initialisation du client OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# --- 2. DÉFINITION DU MODÈLE DE DONNÉES ---

class AskRequest(BaseModel):
    """Modèle pour la requête POST de l'API."""
    question: str
    language: str = "fr" # Langue par défaut

# --- 3. DÉFINITION DE LA ROUTE DE L'API ---

@app.post("/api/ask")
async def ask_ai(request: AskRequest):
    """Endpoint pour interroger l'IA."""
    try:
        # Construction du prompt pour l'IA
        prompt = (
            f"Tu es un expert en Mauritanie. Réponds à la question suivante en {request.language}. "
            f"Question: {request.question}"
        )

        # Appel à l'API OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # Modèle rapide pour le test
            messages=[
                {"role": "system", "content": "Tu es un expert en Mauritanie."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )

        # Retourne la réponse de l'IA
        return {
            "response": response.choices[0].message.content,
            "status": "success"
        }

    except Exception as e:
        # Gestion des erreurs (très important pour le débogage Vercel)
        print(f"Erreur lors de l'appel à l'IA: {e}")
        return {"response": f"Erreur interne du serveur: {e}", "status": "error"}, 500

# --- 4. ROUTE DE TEST (OPTIONNELLE) ---

@app.get("/")
def read_root():
    """Route de base pour vérifier que l'API est en ligne."""
    return {"message": "API Mauritanie IA est en ligne. Utilisez l'endpoint /api/ask (POST)."}

# --- FIN DU FICHIER ---
