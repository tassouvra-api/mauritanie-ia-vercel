from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import os
import json
from typing import Optional, List
from datetime import datetime
import hashlib

app = FastAPI(title="Mauritanie IA API - Version Améliorée")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tassouvra.com",
        "http://tassouvra.com",
        "https://www.tassouvra.com",
        "http://www.tassouvra.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialisation du client OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Cache simple en mémoire
response_cache = {}

# Base de connaissances structurée
KNOWLEDGE_BASE = {
    "proverbes": {
        "description": "Proverbes traditionnels des différentes ethnies mauritaniennes",
        "ethnies": ["Maures (Hassaniya)", "Peuls (Pulaar)", "Soninkés", "Wolofs", "Bambaras"],
        "themes": ["Patience", "Sagesse des anciens", "Communauté", "Parole", "Conséquences"]
    },
    "maladies": {
        "description": "Maladies courantes et endémiques en Mauritanie",
        "categories": {
            "endemiques": ["Paludisme", "Tuberculose", "Bilharziose", "Fièvre de la Vallée du Rift"],
            "courantes": ["Infections respiratoires", "Maladies diarrhéiques", "Malnutrition", "Anémie"],
            "chroniques": ["Diabète", "Hypertension", "Maladies cardiovasculaires"]
        },
        "prevention": "Vaccination, eau potable, hygiène, nutrition"
    },
    "tabous": {
        "description": "Tabous culturels, sociaux et religieux en Mauritanie",
        "categories": {
            "religieux": ["Porc", "Alcool", "Blasphème", "Apostasie"],
            "sociaux": ["Relations hors mariage", "Homosexualité", "Contact physique public"],
            "femmes": ["Voile obligatoire", "Voyage seule", "Mariage arrangé"],
            "alimentaires": ["Main gauche", "Gaspillage nourriture"],
            "hierarchie": ["Respect des anciens", "Castes", "Marabouts"]
        },
        "importance": "Respect essentiel pour visiteurs et étrangers"
    },
    "poetes": {
        "description": "Poètes mauritaniens célèbres et tradition poétique",
        "categories": {
            "classiques": ["Sidi Ahmed Ould Ahmed Aïda", "Sidi Abdallah Ould El Hajj Ibrahim", "Mohamed Ould Taleb"],
            "modernes": ["Oumar Ba", "Tene Youssouf Gueye", "Ousmane Moussa Diagana"],
            "contemporains": ["Mbarek Ould Beyrouk", "Fatimetou Mint Abdel Malick"],
            "poetesses": ["Malouma Mint Meidah", "Dimi Mint Abba", "Noura Mint Seymali"]
        },
        "genres": ["Ghazal (amour)", "Madih (éloge)", "Hija (satire)", "Fakhr (fierté)", "Ritha (élégie)"],
        "tradition": "Griots et griottes, transmission orale, instruments (Tidinit, Ardin, Tbal)"
    },
    "geographie": {
        "description": "Géographie de la Mauritanie",
        "superficie": "1 030 700 km²",
        "regions": ["Adrar", "Assaba", "Brakna", "Dakhlet Nouadhibou", "Gorgol", "Guidimakha", "Hodh Ech Chargui", "Hodh El Gharbi", "Inchiri", "Nouakchott", "Tagant", "Tiris Zemmour", "Trarza"],
        "villes": ["Nouakchott (capitale)", "Nouadhibou", "Rosso", "Kaédi", "Kiffa", "Zouérate"],
        "climat": "Désertique, sahélien au sud",
        "relief": "Déserts, plateaux, dunes"
    },
    "histoire": {
        "description": "Histoire de la Mauritanie",
        "independance": "28 novembre 1960",
        "presidents": [
            "Moktar Ould Daddah (1960-1978)",
            "Mohamed Khouna Ould Haidalla (1980-1984)",
            "Maaouya Ould Sid'Ahmed Taya (1984-2005)",
            "Ely Ould Mohamed Vall (2005-2007)",
            "Sidi Ould Cheikh Abdallahi (2007-2008)",
            "Mohamed Ould Abdel Aziz (2008-2019)",
            "Mohamed Ould Ghazouani (2019-présent)"
        ],
        "periodes": ["Empires anciens", "Colonisation française", "Indépendance", "République"]
    },
    "economie": {
        "description": "Économie mauritanienne",
        "secteurs": ["Pêche", "Mines (fer, or, cuivre)", "Agriculture", "Élevage", "Services"],
        "monnaie": "Ouguiya (MRU)",
        "ressources": "Fer, or, cuivre, pétrole, gaz, poisson"
    },
    "culture": {
        "description": "Culture mauritanienne",
        "langues": ["Arabe (officielle)", "Français", "Pulaar", "Soninké", "Wolof", "Hassaniya"],
        "religion": "Islam (100%)",
        "musique": ["Azawan", "Tidinit", "Ardin", "Griots"],
        "cuisine": ["Thiéboudienne", "Couscous", "Méchoui", "Thé à la menthe"]
    }
}

# Modèle de requête
class QuestionRequest(BaseModel):
    question: str
    language: Optional[str] = "fr"
    conversation_history: Optional[List[dict]] = []

# Modèle de réponse
class AnswerResponse(BaseModel):
    response: str
    status: str
    suggestions: Optional[List[str]] = []
    sources: Optional[List[str]] = []
    cached: Optional[bool] = False

def detect_language(text: str) -> str:
    """Détecte la langue du texte"""
    # Détection simple basée sur les caractères
    if any('\u0600' <= char <= '\u06FF' for char in text):
        return "ar"
    elif any(word in text.lower() for word in ['the', 'is', 'are', 'what', 'how', 'where']):
        return "en"
    else:
        return "fr"

def get_cache_key(question: str, language: str) -> str:
    """Génère une clé de cache pour la question"""
    return hashlib.md5(f"{question.lower()}_{language}".encode()).hexdigest()

def find_relevant_knowledge(question: str) -> dict:
    """Trouve les connaissances pertinentes dans la base"""
    question_lower = question.lower()
    relevant = {}
    
    keywords_map = {
        "proverbes": ["proverbe", "dicton", "sagesse", "ethnie", "maure", "peul", "soninké", "wolof"],
        "maladies": ["maladie", "santé", "paludisme", "tuberculose", "médecine", "hôpital", "traitement"],
        "tabous": ["tabou", "interdit", "haram", "tradition", "coutume", "respect", "comportement"],
        "poetes": ["poète", "poésie", "littérature", "ghazal", "madih", "griot", "malouma", "dimi"],
        "geographie": ["géographie", "région", "ville", "climat", "désert", "nouakchott", "adrar"],
        "histoire": ["histoire", "président", "indépendance", "colonisation", "empire"],
        "economie": ["économie", "pêche", "mine", "agriculture", "ouguiya", "ressource"],
        "culture": ["culture", "langue", "religion", "musique", "cuisine", "tradition"]
    }
    
    for category, keywords in keywords_map.items():
        if any(keyword in question_lower for keyword in keywords):
            relevant[category] = KNOWLEDGE_BASE.get(category, {})
    
    return relevant

def generate_suggestions(question: str, language: str) -> List[str]:
    """Génère des suggestions de questions basées sur le contexte"""
    suggestions_fr = [
        "Quels sont les proverbes des différentes ethnies ?",
        "Quelles sont les maladies courantes en Mauritanie ?",
        "Quels sont les tabous culturels à respecter ?",
        "Qui sont les poètes mauritaniens célèbres ?",
        "Quelle est l'histoire de la Mauritanie ?",
        "Quelles sont les principales villes mauritaniennes ?"
    ]
    
    suggestions_ar = [
        "ما هي أمثال القبائل المختلفة؟",
        "ما هي الأمراض الشائعة في موريتانيا؟",
        "ما هي المحرمات الثقافية التي يجب احترامها؟",
        "من هم الشعراء الموريتانيون المشهورون؟",
        "ما هو تاريخ موريتانيا؟",
        "ما هي المدن الرئيسية في موريتانيا؟"
    ]
    
    suggestions_en = [
        "What are the proverbs of different ethnic groups?",
        "What are the common diseases in Mauritania?",
        "What are the cultural taboos to respect?",
        "Who are the famous Mauritanian poets?",
        "What is the history of Mauritania?",
        "What are the main Mauritanian cities?"
    ]
    
    if language == "ar":
        return suggestions_ar[:3]
    elif language == "en":
        return suggestions_en[:3]
    else:
        return suggestions_fr[:3]

def create_system_prompt(language: str, relevant_knowledge: dict) -> str:
    """Crée un prompt système optimisé"""
    
    if language == "ar":
        base_prompt = """أنت مساعد ذكي متخصص في موريتانيا. أنت خبير في:
- الثقافة والتقاليد الموريتانية
- التاريخ والجغرافيا
- الأمثال والشعر
- الأمراض والصحة
- المحرمات الاجتماعية والدينية

قدم إجابات دقيقة ومفصلة ومهنية. استخدم تنسيق واضح مع:
- فقرات منظمة
- قوائم عند الضرورة
- معلومات دقيقة ومحدثة

كن محترماً ومراعياً للثقافة المحلية."""
    
    elif language == "en":
        base_prompt = """You are an intelligent assistant specialized in Mauritania. You are an expert in:
- Mauritanian culture and traditions
- History and geography
- Proverbs and poetry
- Diseases and health
- Social and religious taboos

Provide accurate, detailed, and professional answers. Use clear formatting with:
- Organized paragraphs
- Lists when necessary
- Accurate and updated information

Be respectful and culturally sensitive."""
    
    else:  # French
        base_prompt = """Tu es un assistant intelligent spécialisé sur la Mauritanie. Tu es expert en:
- Culture et traditions mauritaniennes
- Histoire et géographie
- Proverbes et poésie
- Maladies et santé
- Tabous sociaux et religieux

Fournis des réponses précises, détaillées et professionnelles. Utilise un formatage clair avec:
- Paragraphes organisés
- Listes quand nécessaire
- Informations exactes et à jour

Sois respectueux et sensible à la culture locale."""
    
    # Ajouter les connaissances pertinentes au prompt
    if relevant_knowledge:
        knowledge_text = "\n\nConnaissances pertinentes:\n"
        for category, data in relevant_knowledge.items():
            knowledge_text += f"\n{category.upper()}:\n{json.dumps(data, ensure_ascii=False, indent=2)}\n"
        base_prompt += knowledge_text
    
    return base_prompt

@app.get("/")
async def root():
    return {
        "message": "Mauritanie IA API - Version Améliorée",
        "version": "2.0",
        "features": [
            "Base de connaissances structurée",
            "GPT-4 pour précision maximale",
            "Système de cache",
            "Détection automatique de langue",
            "Suggestions intelligentes",
            "Support multilingue (FR/AR/EN)"
        ],
        "status": "operational"
    }

@app.post("/api/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    try:
        # Détection automatique de la langue si non spécifiée
        language = request.language or detect_language(request.question)
        
        # Vérifier le cache
        cache_key = get_cache_key(request.question, language)
        if cache_key in response_cache:
            cached_response = response_cache[cache_key]
            cached_response["cached"] = True
            return cached_response
        
        # Trouver les connaissances pertinentes
        relevant_knowledge = find_relevant_knowledge(request.question)
        
        # Créer le prompt système
        system_prompt = create_system_prompt(language, relevant_knowledge)
        
        # Préparer les messages
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Ajouter l'historique de conversation si disponible
        if request.conversation_history:
            messages.extend(request.conversation_history[-5:])  # Garder les 5 derniers messages
        
        # Ajouter la question actuelle
        messages.append({"role": "user", "content": request.question})
        
        # Appeler l'API OpenAI avec GPT-4
        response = client.chat.completions.create(
            model="gpt-4",  # Utilisation de GPT-4 pour plus de précision
            messages=messages,
            temperature=0.7,
            max_tokens=1000,
            top_p=0.9,
            frequency_penalty=0.3,
            presence_penalty=0.3
        )
        
        answer = response.choices[0].message.content
        
        # Générer des suggestions
        suggestions = generate_suggestions(request.question, language)
        
        # Identifier les sources utilisées
        sources = list(relevant_knowledge.keys()) if relevant_knowledge else []
        
        # Créer la réponse
        result = {
            "response": answer,
            "status": "success",
            "suggestions": suggestions,
            "sources": sources,
            "cached": False
        }
        
        # Mettre en cache
        response_cache[cache_key] = result.copy()
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/api/suggestions")
async def get_suggestions(language: str = "fr"):
    """Obtenir des suggestions de questions"""
    return {
        "suggestions": generate_suggestions("", language),
        "status": "success"
    }

@app.get("/api/categories")
async def get_categories():
    """Obtenir la liste des catégories disponibles"""
    return {
        "categories": list(KNOWLEDGE_BASE.keys()),
        "details": {k: v.get("description", "") for k, v in KNOWLEDGE_BASE.items()},
        "status": "success"
    }

@app.get("/api/health")
async def health_check():
    """Vérification de l'état de l'API"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "cache_size": len(response_cache),
        "knowledge_categories": len(KNOWLEDGE_BASE)
    }
