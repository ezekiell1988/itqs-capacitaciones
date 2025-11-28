from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
import random
import os
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from openai import AzureOpenAI
import mimetypes
import pdfplumber
import base64
import io

# Ensure .mjs files are served with the correct MIME type
mimetypes.add_type('application/javascript', '.mjs')

# Cargar variables de entorno
load_dotenv()

app = FastAPI()

# Configurar cliente de Azure OpenAI
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_key = os.getenv("AZURE_OPENAI_API_KEY")
deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-5.1") # Nombre del despliegue en Azure AI Studio
api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

client = None
if azure_endpoint and api_key:
    try:
        client = AzureOpenAI(
            azure_endpoint=azure_endpoint,
            api_key=api_key,
            api_version=api_version
        )
        print(f"Azure OpenAI Client initialized. Endpoint: {azure_endpoint}, Deployment: {deployment_name}, Version: {api_version}")
    except Exception as e:
        print(f"Error initializing Azure OpenAI client: {e}")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todos los orígenes para desarrollo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path(__file__).parent / "data"

@app.get("/pdfs/{filename}")
async def get_pdf(filename: str):
    file_path = DATA_DIR / filename
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path, media_type='application/pdf')
    raise HTTPException(status_code=404, detail="PDF not found")

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

class TranslateRequest(BaseModel):
    text: str

import pdfplumber

class PageTextRequest(BaseModel):
    page_number: int
    pdf_filename: str = "az-204.pdf"

@app.post("/extract-page-text")
async def extract_page_text(request: PageTextRequest):
    # Ruta al PDF en app/data
    pdf_path = DATA_DIR / request.pdf_filename
    
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail=f"PDF file not found: {request.pdf_filename}")
    
    try:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            # pdfplumber usa índice 0, pero el usuario ve página 1
            page_idx = request.page_number - 1
            if 0 <= page_idx < len(pdf.pages):
                page = pdf.pages[page_idx]
                text = page.extract_text()
            else:
                raise HTTPException(status_code=400, detail="Page number out of range")
        
        return {"text": text}
    except Exception as e:
        print(f"Error extracting text: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to extract text: {str(e)}")

class QuestionTranslationRequest(BaseModel):
    question_number: str
    pdf_filename: str = "az-204.pdf"
    start_page_hint: int = 1
    manual_start_page: Optional[int] = None
    manual_end_page: Optional[int] = None

@app.post("/translate-question")
async def translate_question(request: QuestionTranslationRequest):
    if not client:
        raise HTTPException(status_code=503, detail="Azure OpenAI service not configured")

    pdf_path = DATA_DIR / request.pdf_filename
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail=f"PDF file not found: {request.pdf_filename}")

    try:
        start_page_idx = -1
        end_page_idx = -1
        
        # Lógica de selección de páginas
        if request.manual_start_page is not None and request.manual_end_page is not None:
            # Usar rango manual proporcionado por el usuario
            start_page_idx = request.manual_start_page - 1
            end_page_idx = request.manual_end_page - 1
            
            # Validaciones básicas
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                if start_page_idx < 0 or end_page_idx >= total_pages or start_page_idx > end_page_idx:
                     raise HTTPException(status_code=400, detail=f"Invalid page range. PDF has {total_pages} pages.")
        else:
            # 1. Buscar la pregunta en el PDF (Lógica automática existente)
            with pdfplumber.open(pdf_path) as pdf:
                q_pattern = f"Question #{request.question_number}"
                next_q_pattern = f"Question #{int(request.question_number) + 1}"
                
                # Buscar página de inicio
                # Empezamos buscando desde la pista (hint) para eficiencia, si no, desde el principio
                search_order = list(range(max(0, request.start_page_hint - 1), len(pdf.pages)))
                if request.start_page_hint > 1:
                    search_order = search_order + list(range(0, request.start_page_hint - 1))
                
                for i in search_order:
                    text = pdf.pages[i].extract_text() or ""
                    if q_pattern in text:
                        start_page_idx = i
                        break
                
                if start_page_idx == -1:
                    raise HTTPException(status_code=404, detail=f"Question #{request.question_number} not found in PDF. Try specifying the page range manually.")

                # Buscar página final (donde empieza la siguiente pregunta o un límite razonable)
                end_page_idx = start_page_idx
                # Buscamos hasta 3 páginas adelante máximo
                for i in range(start_page_idx, min(start_page_idx + 4, len(pdf.pages))):
                    text = pdf.pages[i].extract_text() or ""
                    if i > start_page_idx and next_q_pattern in text:
                        # Si encontramos la siguiente pregunta, la página anterior es el fin seguro, 
                        # o esta página si la pregunta nueva empieza muy abajo. 
                        # Por seguridad, incluimos esta página para contexto.
                        end_page_idx = i
                        break
                    end_page_idx = i

        # 2. Convertir páginas a imágenes
        # Prompt refinado para cumplir con los 4 puntos solicitados y manejo de imágenes
        prompt_text = (
            f"Translate 'Question #{request.question_number}' to Spanish based on the provided images. "
            f"The content is from pages {start_page_idx + 1} to {end_page_idx + 1}. "
            "Output strictly in Markdown format with the following 4 sections:\n\n"
            f"1. **Pregunta {request.question_number} (Páginas {start_page_idx + 1}-{end_page_idx + 1})**\n"
            "2. **Contexto**: The full body of the question. If there are diagrams, architecture schemas, or screenshots in the question area, interpret them and describe them in detail in Spanish here.\n"
            "3. **Opciones**: List the multiple choice options. If the options are images (e.g., different graphs or icons), describe what each image option represents in Spanish.\n"
            "4. **Respuesta Correcta**: Provide the correct answer and the explanation. If the answer refers to an image or diagram, explain why that specific image is correct based on the visual evidence.\n\n"
            "Ignore any content belonging to the next question (e.g., 'Question #" + str(int(request.question_number) + 1) + "')."
        )

        content_payload = [
            {
                "type": "text", 
                "text": prompt_text
            }
        ]

        with pdfplumber.open(pdf_path) as pdf:
            for i in range(start_page_idx, end_page_idx + 1):
                page = pdf.pages[i]
                # Aumentamos un poco la resolución para mejor OCR de diagramas
                im = page.to_image(resolution=200)
                img_byte_arr = io.BytesIO()
                im.original.save(img_byte_arr, format='PNG')
                b64_img = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
                
                content_payload.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{b64_img}"
                    }
                })

        # 3. Enviar a Azure OpenAI
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert technical instructor for Azure certification exams. You are capable of analyzing complex network diagrams, code snippets, and UI screenshots within exam questions and explaining them clearly in Spanish."
                },
                {
                    "role": "user",
                    "content": content_payload
                }
            ],
            max_completion_tokens=3000
        )
        
        translation = response.choices[0].message.content
        return {"translation": translation, "pages_processed": f"{start_page_idx+1}-{end_page_idx+1}"}

    except Exception as e:
        print(f"Translation error: {e}")
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")

@app.post("/translate-page-image")
async def translate_page_image(request: PageTextRequest):
    if not client:
        raise HTTPException(status_code=503, detail="Azure OpenAI service not configured")

    # Ruta al PDF en app/data
    pdf_path = DATA_DIR / request.pdf_filename
    
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail=f"PDF file not found: {request.pdf_filename}")
    
    try:
        base64_image = ""
        with pdfplumber.open(pdf_path) as pdf:
            page_idx = request.page_number - 1
            if 0 <= page_idx < len(pdf.pages):
                page = pdf.pages[page_idx]
                # Renderizar página a imagen (resolución 150 DPI es un buen balance)
                im = page.to_image(resolution=150)
                img_byte_arr = io.BytesIO()
                im.original.save(img_byte_arr, format='PNG')
                img_byte_arr = img_byte_arr.getvalue()
                base64_image = base64.b64encode(img_byte_arr).decode('utf-8')
            else:
                raise HTTPException(status_code=400, detail="Page number out of range")

        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {
                    "role": "system", 
                    "content": "You are a helpful assistant that translates technical documentation from English to Spanish. The user provides an image of a PDF page. Translate the content (text, diagrams, code comments) to Spanish. Use markdown for formatting. If there is code, keep it as is but translate comments if possible."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Translate this page to Spanish."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_completion_tokens=2000
        )
        translation = response.choices[0].message.content
        return {"translation": translation}

    except Exception as e:
        print(f"Translation error: {e}")
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")

@app.post("/translate")
async def translate_text(request: TranslateRequest):
    if not client:
        raise HTTPException(status_code=503, detail="Azure OpenAI service not configured")
    
    try:
        response = client.chat.completions.create(
            model=deployment_name, # Usar la variable de entorno
            messages=[
                {"role": "system", "content": "You are a helpful assistant that translates technical text from English to Spanish. Maintain technical terms if appropriate but ensure the translation is natural and accurate."},
                {"role": "user", "content": f"Translate the following text to Spanish:\n\n{request.text}"}
            ],
            max_completion_tokens=2000
        )
        translation = response.choices[0].message.content
        return {"translation": translation}
    except Exception as e:
        print(f"Translation error: {e}")
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")

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
