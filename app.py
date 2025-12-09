from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import os

# Importer la base de connaissances complète
import sys
sys.path.append('/home/ubuntu')
from knowledge_base_complete import get_knowledge_base

app = FastAPI()

# Configuration CORS pour permettre les requêtes depuis tassouvra.com
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tassouvra.com",
        "https://www.tassouvra.com",
        "http://tassouvra.com",
        "http://www.tassouvra.com",
        "http://localhost:3000",
        "http://localhost:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialiser le client OpenAI
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
# Charger la base de connaissances
KNOWLEDGE_BASE = get_knowledge_base()

class Question(BaseModel):
    question: str
    category: str = "general"

@app.get("/")
async def root():
    return {
        "message": "API Encyclopédie Mauritanie - Tassouvra",
        "version": "2.0 - Base de connaissances complète",
        "status": "operational",
        "categories": 29
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "knowledge_base": "loaded"}

@app.post("/api/ask")
async def ask_question(question: Question):
    try:
        # Créer un prompt intelligent avec la base de connaissances
        system_prompt = f"""Tu es un assistant expert de l'Encyclopédie Mauritanie (Tassouvra.com).

BASE DE CONNAISSANCES COMPLÈTE :
{KNOWLEDGE_BASE}

INSTRUCTIONS :
1. Utilise UNIQUEMENT les informations de la base de connaissances ci-dessus
2. Réponds dans la langue de la question (arabe, français ou anglais) de manière professionnelle et structurée
3. Si la question concerne une catégorie spécifique, concentre-toi sur cette section
4. Fournis des informations précises avec des dates, des noms et des chiffres exacts
5. Structure ta réponse avec des titres, des paragraphes et des listes si approprié
6. Si l'information n'est pas dans la base de connaissances, dis-le clairement
7. Sois concis mais complet (maximum 500 mots)
8. Utilise un ton éducatif et accessible

CATÉGORIE DE LA QUESTION : {question.category}

Réponds maintenant à la question de l'utilisateur en utilisant la base de connaissances."""

        # Appeler l'API OpenAI
        response = client.chat.completions.create(
             model="gpt-4o",
             messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question.question}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        answer = response.choices[0].message.content
        
        return {
            "question": question.question,
            "answer": answer,
            "category": question.category,
            "status": "success"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/api/categories")
async def get_categories():
    """Retourne la liste des catégories disponibles"""
    categories = [
        {"id": "geographie", "name": "Géographie", "icon": "🗺️"},
        {"id": "histoire", "name": "Histoire", "icon": "📜"},
        {"id": "presidents", "name": "Présidents", "icon": "👑"},
        {"id": "ministres", "name": "Anciens Ministres", "icon": "🏛️"},
        {"id": "forces_armees", "name": "Forces Armées", "icon": "🪖"},
        {"id": "economie", "name": "Économie", "icon": "💰"},
        {"id": "villes", "name": "Villes", "icon": "🏙️"},
        {"id": "tribus", "name": "Tribus et Clans", "icon": "👥"},
        {"id": "religion", "name": "Religion", "icon": "🕌"},
        {"id": "langues", "name": "Langues", "icon": "🗣️"},
        {"id": "coutumes", "name": "Coutumes", "icon": "🍵"},
        {"id": "cuisine", "name": "Cuisine", "icon": "🍲"},
        {"id": "artisanat", "name": "Artisanat", "icon": "🏺"},
        {"id": "musique", "name": "Musique et Arts", "icon": "🎵"},
        {"id": "litterature", "name": "Littérature", "icon": "📚"},
        {"id": "architecture", "name": "Architecture", "icon": "🏛️"},
        {"id": "education", "name": "Éducation", "icon": "🎓"},
        {"id": "sante", "name": "Santé", "icon": "🏥"},
        {"id": "transport", "name": "Transport", "icon": "🚆"},
        {"id": "medias", "name": "Médias", "icon": "📰"},
        {"id": "faune_flore", "name": "Faune et Flore", "icon": "🦒"},
        {"id": "tourisme", "name": "Tourisme", "icon": "🏖️"},
        {"id": "sport", "name": "Sport", "icon": "⚽"},
        {"id": "culture", "name": "Culture", "icon": "🎭"},
        {"id": "proverbes", "name": "Proverbes", "icon": "💬"},
        {"id": "maladies", "name": "Maladies", "icon": "🩺"},
        {"id": "tabous", "name": "Tabous", "icon": "🚫"},
        {"id": "poetes", "name": "Poètes", "icon": "✍️"},
        {"id": "personnalites", "name": "Personnalités Politiques", "icon": "🎖️"}
    ]
    return {"categories": categories, "total": len(categories)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
