from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
import random
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todos los orígenes para desarrollo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path(__file__).parent / "data"

class Option(BaseModel):
    letra: str
    texto: str
    es_correcta: bool

class Question(BaseModel):
    numero: str
    pregunta: str
    opciones: List[Option]
    respuesta_correcta: str
    explicacion: Optional[str] = ""

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Service is healthy"}

@app.get("/exams")
def get_exams():
    return [
        {"id": "az-204", "name": "AZ-204: Developing Solutions for Microsoft Azure"},
        {"id": "dp-300", "name": "DP-300: Administering Microsoft Azure SQL Solutions"}
    ]

@app.get("/questions/{exam_id}")
def get_questions(
    exam_id: str, 
    lang: str = Query("es", regex="^(es|en)$"), 
    limit: int = 10, 
    randomize: bool = False
):
    filename = f"{exam_id}_questions_{lang}.json" if lang == "es" else f"{exam_id}_questions.json"
    file_path = DATA_DIR / filename
    
    if not file_path.exists():
        # Fallback logic or error if file doesn't exist
        # Try to map English structure to Spanish structure if needed, 
        # but for now assuming files exist as generated previously.
        # Note: The English JSONs have keys: number, question, options (letter, text, is_correct), correct_answer, explanation
        # The Spanish JSONs have keys: numero, pregunta, opciones (letra, texto, es_correcta), respuesta_correcta, explicacion
        raise HTTPException(status_code=404, detail=f"Questions file not found: {filename}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # Normalize data structure if English
        if lang == "en":
            normalized_data = []
            for q in data:
                normalized_data.append({
                    "numero": q.get("number"),
                    "pregunta": q.get("question"),
                    "opciones": [
                        {
                            "letra": opt.get("letter"),
                            "texto": opt.get("text"),
                            "es_correcta": opt.get("is_correct")
                        } for opt in q.get("options", [])
                    ],
                    "respuesta_correcta": q.get("correct_answer"),
                    "explicacion": q.get("explanation", "")
                })
            data = normalized_data

        if randomize:
            random.shuffle(data)
        
        if limit > 0:
            data = data[:limit]
            
        return data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount frontend
frontend_path = Path(__file__).parent.parent / "frontend" / "www"

@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    if not frontend_path.exists():
        raise HTTPException(status_code=404, detail="Frontend not found. Please build the Ionic app first.")
        
    file_path = frontend_path / full_path
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    
    # Fallback to index.html for SPA routing (e.g. /home)
    index_path = frontend_path / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
        
    raise HTTPException(status_code=404, detail="index.html not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
