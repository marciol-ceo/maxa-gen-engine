import os
import random
import uvicorn
from typing import List, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from pathlib import Path

# Import de tes modules personnalisés
from maxa_get_meta import (
    get_random_metadata_from_each_namespace,
    get_random_metadata_from_one_random_namespace
)
from maxa_generer_epreuve import generate_new_epreuve_as_latex_string
from maxa_generer_epreuve_v2_robust import generate_new_epreuve_as_latex_string_v2

# Chargement des variables d'environnement (.env)
load_dotenv()

# Initialisation de l'application FastAPI
app = FastAPI(
    title="Maxa Gen Engine API",
    description="API pour la génération d'épreuves mathématiques avec GPT-5 + Structured Outputs. Support de l'UTF-8 garanti.",
    version="2.0.0"
)

# Middleware pour forcer UTF-8 dans toutes les réponses
@app.middleware("http")
async def add_utf8_header(request, call_next):
    response = await call_next(request)
    if "application/json" in response.headers.get("content-type", ""):
        response.headers["content-type"] = "application/json; charset=utf-8"
    return response

# --- CONFIGURATION CORS POUR FLUTTER ---
# Permet à votre application Flutter d'appeler l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, remplacez par l'URL de votre app Flutter
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MONTAGE DES FICHIERS STATIQUES ---
# Monte le dossier 'static' pour servir les fichiers CSS, JS, etc.
#app.mount("/static", StaticFiles(directory="static"), name="static")

# --- MODÈLES DE DONNÉES (Pydantic) ---

# Paramètres de base pour l'index Pinecone
class BaseRequest(BaseModel):
    index_name: str = Field("gen-engine-index", description="Nom de l'index Pinecone")

# Modèle dédié aux paramètres du MOTEUR de génération
class GenerationParams(BaseModel):
    n_variations_per_exercice: int = Field(3, ge=1, description="Nombre de variations par exercice (legacy mode)")
    temperature: float = Field(0.7, ge=0.0, le=1.0, description="Créativité du modèle (0.0 à 1.0)")
    return_all_latex: bool = Field(True, description="Retourner le code LaTeX complet ou partiel")
    model: str = Field("gpt-5", description="Modèle à utiliser: gpt-5, gpt-5-mini, gpt-4o")
    use_robust_mode: bool = Field(True, description="Utiliser le mode robuste avec Structured Outputs (recommandé)")

# Modèles spécifiques aux endpoints

class GenerateFromChunksRequest(BaseRequest, GenerationParams):
    """Pour la génération manuelle à partir de chunks externes."""
    chunks_list: List[Any] = Field(..., description="Liste des chunks (métadonnées) bruts")

class AutoGenerateRequest(BaseRequest, GenerationParams):
    """Pour l'auto-génération d'une épreuve complète."""
    mode: str = Field("mixed", description="Mode de sélection: 'mixed' (tous les namespaces) ou 'single' (un namespace aléatoire)")

class SingleExerciseRequest(BaseRequest, GenerationParams):
    """Pour l'auto-génération d'un seul exercice aléatoire."""
    pass

# --- ROUTES DE L'API ---

@app.get("/")
def health_check():
    """Route de vérification de l'état de l'API."""
    return {"status": "online", "service": "Maxa Gen Engine API", "version": "1.2.0"}

@app.get("/ui", response_class=HTMLResponse)
async def serve_ui():
    """Route pour servir l'interface utilisateur web."""
    html_path = Path("static/index.html")
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    return HTMLResponse(
        content="<h1>Interface non trouvée</h1><p>Assurez-vous que le dossier 'static' existe avec index.html</p>",
        status_code=404
    )

# Routes de Métadonnées

@app.post("/metadata/random-all")
def get_metadata_all_namespaces(payload: BaseRequest):
    """Récupère des métadonnées aléatoires depuis CHAQUE namespace."""
    try:
        pinecone_key = os.getenv("pinecone_api_key")
        if not pinecone_key:
            raise HTTPException(status_code=500, detail="Clé API Pinecone manquante.")

        chunks = get_random_metadata_from_each_namespace(
            index_name=payload.index_name,
            pinecone_api_key=pinecone_key
        )
        return {"count": len(chunks) if chunks else 0, "chunks": chunks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@app.post("/metadata/random-one")
def get_metadata_one_namespace(payload: BaseRequest):
    """Récupère des métadonnées aléatoires depuis UN SEUL namespace au hasard."""
    try:
        chunks = get_random_metadata_from_one_random_namespace(payload.index_name)
        return {"count": len(chunks) if chunks else 0, "chunks": chunks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


# Routes de Génération

@app.post("/generate/from-chunks")
def generate_epreuve_manual(payload: GenerateFromChunksRequest):
    """
    Génère le LaTeX à partir d'une liste de chunks et des paramètres de génération.
    Supporte le mode robuste (Structured Outputs) et le mode legacy.
    """
    try:
        if payload.use_robust_mode:
            # MODE ROBUSTE avec GPT-5 + Structured Outputs
            result = generate_new_epreuve_as_latex_string_v2(
                chunks_list=payload.chunks_list,
                n_variations_per_exercice=payload.n_variations_per_exercice,
                temperature=payload.temperature,
                model=payload.model,
                use_structured_outputs=True
            )
            return {
                "latex_result": result,
                "mode": "robust",
                "model_used": payload.model
            }
        else:
            # MODE LEGACY
            result = generate_new_epreuve_as_latex_string(
                chunks_list=payload.chunks_list,
                n_variations_per_exercice=payload.n_variations_per_exercice,
                temperature=payload.temperature,
                return_all_latex=payload.return_all_latex
            )
            return {
                "latex_result": result,
                "mode": "legacy"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de génération: {str(e)}")

@app.post("/generate/auto")
def generate_epreuve_auto(payload: AutoGenerateRequest):
    """
    Génère une épreuve COMPLÈTE automatiquement.
    Supporte le mode robuste (GPT-5 + Structured Outputs) et legacy.
    """
    try:
        pinecone_key = os.getenv("pinecone_api_key")

        if payload.mode == "single":
            chunks = get_random_metadata_from_one_random_namespace(payload.index_name)
        else:
            chunks = get_random_metadata_from_each_namespace(
                index_name=payload.index_name,
                pinecone_api_key=pinecone_key
            )

        if not chunks:
            raise HTTPException(status_code=404, detail="Aucun chunk trouvé dans l'index.")

        if payload.use_robust_mode:
            # MODE ROBUSTE
            result = generate_new_epreuve_as_latex_string_v2(
                chunks_list=chunks,
                n_variations_per_exercice=payload.n_variations_per_exercice,
                temperature=payload.temperature,
                model=payload.model,
                use_structured_outputs=True
            )
            return {
                "mode_used": payload.mode,
                "chunks_count": len(chunks),
                "latex_result": result,
                "generation_mode": "robust",
                "model_used": payload.model
            }
        else:
            # MODE LEGACY
            result = generate_new_epreuve_as_latex_string(
                chunks_list=chunks,
                n_variations_per_exercice=payload.n_variations_per_exercice,
                temperature=payload.temperature,
                return_all_latex=payload.return_all_latex
            )
            return {
                "mode_used": payload.mode,
                "chunks_count": len(chunks),
                "latex_result": result,
                "generation_mode": "legacy"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur auto-generation: {str(e)}")

@app.post("/generate/exercise/random")
def generate_single_random_exercise(payload: SingleExerciseRequest):
    """
    Génère UN SEUL exercice aléatoire en utilisant les paramètres de génération spécifiés.
    Supporte le mode robuste (GPT-5 + Structured Outputs).
    """
    try:
        chunks = get_random_metadata_from_one_random_namespace(payload.index_name)

        if not chunks:
            raise HTTPException(status_code=404, detail="Impossible de récupérer des exercices.")

        selected_chunk = random.choice(chunks)

        if payload.use_robust_mode:
            # MODE ROBUSTE
            result = generate_new_epreuve_as_latex_string_v2(
                chunks_list=[selected_chunk],
                n_variations_per_exercice=payload.n_variations_per_exercice,
                temperature=payload.temperature,
                model=payload.model,
                use_structured_outputs=True
            )
            return {
                "source_chunk_id": selected_chunk.get("id", "unknown"),
                "latex_result": result,
                "generation_mode": "robust",
                "model_used": payload.model
            }
        else:
            # MODE LEGACY
            result = generate_new_epreuve_as_latex_string(
                chunks_list=[selected_chunk],
                n_variations_per_exercice=payload.n_variations_per_exercice,
                temperature=payload.temperature,
                return_all_latex=payload.return_all_latex
            )
            return {
                "source_chunk_id": selected_chunk.get("id", "unknown"),
                "latex_result": result,
                "generation_mode": "legacy"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur single-exercise: {str(e)}")

# --- LANCEMENT DU SERVEUR ---
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 MAXA GEN ENGINE - Démarrage du serveur")
    print("=" * 60)
    print(f"📍 API disponible sur: http://localhost:5000")
    print(f"🎨 Interface UI sur: http://localhost:5000/ui")
    print(f"📚 Documentation API: http://localhost:5000/docs")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=5000)