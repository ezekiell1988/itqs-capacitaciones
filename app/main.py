from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
import random
import os
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response, HTMLResponse
from dotenv import load_dotenv
from openai import AzureOpenAI
import mimetypes
import pdfplumber
import base64
import io
import markdown

# Ensure .mjs files are served with the correct MIME type
mimetypes.add_type("application/javascript", ".mjs")

# Cargar variables de entorno
load_dotenv()

app = FastAPI()

# Configurar cliente de Azure OpenAI
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_key = os.getenv("AZURE_OPENAI_API_KEY")
deployment_name = os.getenv(
    "AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-5.1"
)  # Nombre del despliegue en Azure AI Studio
api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

client = None
if azure_endpoint and api_key:
    try:
        client = AzureOpenAI(
            azure_endpoint=azure_endpoint, api_key=api_key, api_version=api_version
        )
        print(
            f"Azure OpenAI Client initialized. Endpoint: {azure_endpoint}, Deployment: {deployment_name}, Version: {api_version}"
        )
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
        return FileResponse(file_path, media_type="application/pdf")
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
        raise HTTPException(
            status_code=404, detail=f"PDF file not found: {request.pdf_filename}"
        )

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


def json_to_markdown(data: dict, pages: str, lang: str = "es") -> str:
    title = "Pregunta" if lang == "es" else "Question"
    pages_label = "Páginas" if lang == "es" else "Pages"
    summary_label = "Resumen" if lang == "es" else "Summary"
    answer_label = "Respuesta Correcta" if lang == "es" else "Correct Answer"

    md = f"## {title} {data.get('id_question')} ({pages_label} {pages})\n\n"
    md += f"**{summary_label}**\n\n{data.get('short_question')}\n\n"
    md += f"**{answer_label}**\n\n{data.get('correct_answer')}"
    return md


def json_to_markdown_full(data: dict, pages: str, lang: str) -> str:
    # Header
    title = "Pregunta" if lang == "es" else "Question"
    md = f"## {title} {data.get('id_question')} (Pages {pages})\n\n"

    # Context / Full Question
    context_title = "Contexto" if lang == "es" else "Context"
    md += f"**{context_title}**\n\n{data.get('question_context')}\n\n"

    # Image Explanation (if present)
    img_exp = data.get("image_explanation")
    if img_exp:
        img_title = "Explicación de la Imagen" if lang == "es" else "Image Explanation"
        md += f"**{img_title}**\n\n{img_exp}\n\n"

    # Options
    options_title = "Opciones" if lang == "es" else "Options"
    md += f"**{options_title}**\n\n"
    for opt in data.get("options", []):
        check = "(Correcta)" if opt.get("is_correct") else ""
        if lang == "en":
            check = "(Correct)" if opt.get("is_correct") else ""
        md += f"- **{opt.get('letter')}**: {opt.get('text')} {check}\n"
    md += "\n"

    # Correct Answer
    ans_title = "Respuesta Correcta" if lang == "es" else "Correct Answer"
    md += f"**{ans_title}**\n\n{data.get('correct_answer')}\n\n"

    # Explanation
    exp_title = "Explicación" if lang == "es" else "Explanation"
    md += f"**{exp_title}**\n\n{data.get('explanation')}\n\n"

    # Community Discussion
    comm_disc = data.get("community_discussion")
    if comm_disc:
        comm_title = (
            "Discusión de la Comunidad" if lang == "es" else "Community Discussion"
        )
        md += f"**{comm_title}**\n\n{comm_disc}\n\n"

    return md


@app.post("/translate-question")
async def translate_question(request: QuestionTranslationRequest):
    exam_id = Path(request.pdf_filename).stem
    json_en_dir = DATA_DIR / exam_id / "questions_json" / "en"
    json_es_dir = DATA_DIR / exam_id / "questions_json" / "es"

    # Markdown directories separated by language
    md_en_dir = DATA_DIR / exam_id / "questions_md" / "en"
    md_es_dir = DATA_DIR / exam_id / "questions_md" / "es"

    # Ensure directories exist
    json_en_dir.mkdir(parents=True, exist_ok=True)
    json_es_dir.mkdir(parents=True, exist_ok=True)
    md_en_dir.mkdir(parents=True, exist_ok=True)
    md_es_dir.mkdir(parents=True, exist_ok=True)

    json_en_path = json_en_dir / f"{request.question_number}.json"
    json_es_path = json_es_dir / f"{request.question_number}.json"

    # Define paths for all 4 markdown files
    md_es_path = md_es_dir / f"{request.question_number}.md"
    md_es_full_path = md_es_dir / f"{request.question_number}_full.md"
    md_en_path = md_en_dir / f"{request.question_number}.md"
    md_en_full_path = md_en_dir / f"{request.question_number}_full.md"

    # 0. Check if question is already saved (checking Spanish JSON and MD)
    if json_es_path.exists() and md_es_path.exists():
        try:
            # Read all 4 files if they exist, otherwise return what we have or regenerate
            # For simplicity, if the main ES markdown exists, we assume others might too or we just return it.
            # But to be robust, let's try to read all.

            saved_md_es = ""
            saved_md_es_full = ""
            saved_md_en = ""
            saved_md_en_full = ""

            if md_es_path.exists():
                with open(md_es_path, "r", encoding="utf-8") as f:
                    saved_md_es = f.read()
            if md_es_full_path.exists():
                with open(md_es_full_path, "r", encoding="utf-8") as f:
                    saved_md_es_full = f.read()
            if md_en_path.exists():
                with open(md_en_path, "r", encoding="utf-8") as f:
                    saved_md_en = f.read()
            if md_en_full_path.exists():
                with open(md_en_full_path, "r", encoding="utf-8") as f:
                    saved_md_en_full = f.read()

            return {
                "markdown": saved_md_es,
                "markdown_full": saved_md_es_full,
                "markdown_en": saved_md_en,
                "markdown_full_en": saved_md_en_full,
                "pages_processed": "Saved File",
                "saved": True,
            }
        except Exception as e:
            print(f"Error reading saved files: {e}")

    if not client:
        raise HTTPException(
            status_code=503, detail="Azure OpenAI service not configured"
        )

    pdf_path = DATA_DIR / request.pdf_filename
    if not pdf_path.exists():
        raise HTTPException(
            status_code=404, detail=f"PDF file not found: {request.pdf_filename}"
        )

    try:
        start_page_idx = -1
        end_page_idx = -1

        # Lógica de selección de páginas
        if (
            request.manual_start_page is not None
            and request.manual_end_page is not None
        ):
            # Usar rango manual proporcionado por el usuario
            start_page_idx = request.manual_start_page - 1
            end_page_idx = request.manual_end_page - 1

            # Validaciones básicas
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                if (
                    start_page_idx < 0
                    or end_page_idx >= total_pages
                    or start_page_idx > end_page_idx
                ):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid page range. PDF has {total_pages} pages.",
                    )
        else:
            # 1. Buscar la pregunta en el PDF (Lógica automática existente)
            with pdfplumber.open(pdf_path) as pdf:
                q_pattern = f"Question #{request.question_number}"
                next_q_pattern = f"Question #{int(request.question_number) + 1}"

                # Buscar página de inicio
                # Empezamos buscando desde la pista (hint) para eficiencia, si no, desde el principio
                search_order = list(
                    range(max(0, request.start_page_hint - 1), len(pdf.pages))
                )
                if request.start_page_hint > 1:
                    search_order = search_order + list(
                        range(0, request.start_page_hint - 1)
                    )

                for i in search_order:
                    text = pdf.pages[i].extract_text() or ""
                    if q_pattern in text:
                        start_page_idx = i
                        break

                if start_page_idx == -1:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Question #{request.question_number} not found in PDF. Try specifying the page range manually.",
                    )

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
        # Prompt refinado para solicitar JSON
        prompt_text = (
            f"Analyze 'Question #{request.question_number}' from the provided images (pages {start_page_idx + 1}-{end_page_idx + 1}). "
            "1. Identify the question text, options, and official answer.\n"
            "2. Look for a 'Community Discussion' section. If present, extract the key points and determine if the community suggests a different answer than the official one.\n"
            "3. Create a summary of the question ('short_question').\n"
            "4. If there are images or diagrams, provide a detailed description/explanation of them in the English section ('image_explanation').\n"
            "5. Provide the output in TWO languages: English ('en') and Spanish ('es').\n"
            "IMPORTANT: When translating to Spanish, KEEP technical terms (like 'Azure Functions', 'Blob Storage', 'VNet', etc.) in ENGLISH. Do not translate them.\n"
            "Return ONLY a valid JSON object with the following structure:\n"
            "{\n"
            '  "en": {\n'
            f'    "id_question": {request.question_number},\n'
            '    "short_question": "Summary of the question",\n'
            '    "question_context": "Full question text",\n'
            '    "image_explanation": "Detailed description of any images/diagrams (if present, else null)",\n'
            '    "community_discussion": "Summary of the community discussion if present, else null",\n'
            '    "options": [\n'
            '      {"letter": "A", "text": "Option text", "is_correct_pdf": boolean, "is_correct_community": boolean|null, "is_correct": boolean}\n'
            "    ],\n"
            '    "correct_answer": "The correct option letter and text",\n'
            '    "explanation": "Detailed explanation"\n'
            "  },\n"
            '  "es": {\n'
            f'    "id_question": {request.question_number},\n'
            '    "short_question": "Resumen de la pregunta en español (mantener términos técnicos en inglés)",\n'
            '    "question_context": "Texto completo de la pregunta en español. Incluye aquí la descripción de diagramas/imágenes si las hay. (mantener términos técnicos en inglés)",\n'
            '    "community_discussion": "Resumen de la discusión de la comunidad en español si existe, sino null",\n'
            '    "options": [\n'
            '      {"letter": "A", "text": "Texto de la opción en español (mantener términos técnicos en inglés)", "is_correct_pdf": boolean, "is_correct_community": boolean|null, "is_correct": boolean}\n'
            "    ],\n"
            '    "correct_answer": "Letra y texto de la respuesta correcta en español",\n'
            '    "explanation": "Explicación detallada en español (mantener términos técnicos en inglés)"\n'
            "  }\n"
            "}\n"
            "Do not include markdown formatting (like ```json) around the output. Just the raw JSON string."
        )

        content_payload = [{"type": "text", "text": prompt_text}]

        with pdfplumber.open(pdf_path) as pdf:
            for i in range(start_page_idx, end_page_idx + 1):
                page = pdf.pages[i]
                # Aumentamos un poco la resolución para mejor OCR de diagramas
                im = page.to_image(resolution=200)
                img_byte_arr = io.BytesIO()
                im.original.save(img_byte_arr, format="PNG")
                b64_img = base64.b64encode(img_byte_arr.getvalue()).decode("utf-8")

                content_payload.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64_img}"},
                    }
                )

        # 3. Enviar a Azure OpenAI
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert technical instructor. You extract exam questions from images and return them in structured JSON format translated to Spanish. IMPORTANT: Keep technical terms in English.",
                },
                {"role": "user", "content": content_payload},
            ],
            max_completion_tokens=4000,
            response_format={"type": "json_object"},
        )

        translation_json_str = response.choices[0].message.content
        try:
            full_data = json.loads(translation_json_str)
            data_en = full_data.get("en")
            data_es = full_data.get("es")

            if not data_en or not data_es:
                raise ValueError("Missing 'en' or 'es' keys in response")

        except json.JSONDecodeError:
            # Fallback if model returns markdown code block
            if "```json" in translation_json_str:
                translation_json_str = (
                    translation_json_str.split("```json")[1].split("```")[0].strip()
                )
                full_data = json.loads(translation_json_str)
                data_en = full_data.get("en")
                data_es = full_data.get("es")
            else:
                raise ValueError("Could not parse JSON response")

        # 4. Generate Markdown (from Spanish and English data)
        pages_str = f"{start_page_idx+1}-{end_page_idx+1}"

        # Spanish Markdowns
        markdown_es = json_to_markdown(data_es, pages_str, "es")
        markdown_es_full = json_to_markdown_full(data_es, pages_str, "es")

        # English Markdowns
        markdown_en = json_to_markdown(data_en, pages_str, "en")
        markdown_en_full = json_to_markdown_full(data_en, pages_str, "en")

        # 5. Save JSONs and Markdowns
        with open(json_en_path, "w", encoding="utf-8") as f:
            json.dump(data_en, f, indent=2, ensure_ascii=False)

        with open(json_es_path, "w", encoding="utf-8") as f:
            json.dump(data_es, f, indent=2, ensure_ascii=False)

        with open(md_es_path, "w", encoding="utf-8") as f:
            f.write(markdown_es)

        with open(md_es_full_path, "w", encoding="utf-8") as f:
            f.write(markdown_es_full)

        with open(md_en_path, "w", encoding="utf-8") as f:
            f.write(markdown_en)

        with open(md_en_full_path, "w", encoding="utf-8") as f:
            f.write(markdown_en_full)

        return {
            "markdown": markdown_es,
            "markdown_full": markdown_es_full,
            "markdown_en": markdown_en,
            "markdown_full_en": markdown_en_full,
            "pages_processed": pages_str,
            "saved": True,
        }

    except Exception as e:
        print(f"Translation error: {e}")
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


@app.post("/translate-page-image")
async def translate_page_image(request: PageTextRequest):
    if not client:
        raise HTTPException(
            status_code=503, detail="Azure OpenAI service not configured"
        )

    # Ruta al PDF en app/data
    pdf_path = DATA_DIR / request.pdf_filename

    if not pdf_path.exists():
        raise HTTPException(
            status_code=404, detail=f"PDF file not found: {request.pdf_filename}"
        )

    try:
        base64_image = ""
        with pdfplumber.open(pdf_path) as pdf:
            page_idx = request.page_number - 1
            if 0 <= page_idx < len(pdf.pages):
                page = pdf.pages[page_idx]
                # Renderizar página a imagen (resolución 150 DPI es un buen balance)
                im = page.to_image(resolution=150)
                img_byte_arr = io.BytesIO()
                im.original.save(img_byte_arr, format="PNG")
                img_byte_arr = img_byte_arr.getvalue()
                base64_image = base64.b64encode(img_byte_arr).decode("utf-8")
            else:
                raise HTTPException(status_code=400, detail="Page number out of range")

        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that translates technical documentation from English to Spanish. The user provides an image of a PDF page. Translate the content (text, diagrams, code comments) to Spanish. Use markdown for formatting. If there is code, keep it as is but translate comments if possible. IMPORTANT: Keep technical terms in English.",
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Translate this page to Spanish."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            },
                        },
                    ],
                },
            ],
            max_completion_tokens=2000,
        )
        translation = response.choices[0].message.content
        return {"translation": translation}

    except Exception as e:
        print(f"Translation error: {e}")
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


@app.post("/translate")
async def translate_text(request: TranslateRequest):
    if not client:
        raise HTTPException(
            status_code=503, detail="Azure OpenAI service not configured"
        )

    try:
        response = client.chat.completions.create(
            model=deployment_name,  # Usar la variable de entorno
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that translates technical text from English to Spanish. Maintain technical terms in English but ensure the translation is natural and accurate.",
                },
                {
                    "role": "user",
                    "content": f"Translate the following text to Spanish:\n\n{request.text}",
                },
            ],
            max_completion_tokens=2000,
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
        {"id": "dp-300", "name": "DP-300: Administering Microsoft Azure SQL Solutions"},
    ]


@app.get("/questions/{exam_id}")
def get_questions(
    exam_id: str,
    lang: str = Query("es", regex="^(es|en)$"),
    limit: int = 10,
    randomize: bool = False,
):
    filename = (
        f"{exam_id}_questions_{lang}.json"
        if lang == "es"
        else f"{exam_id}_questions.json"
    )
    file_path = DATA_DIR / filename

    if not file_path.exists():
        # Fallback logic or error if file doesn't exist
        # Try to map English structure to Spanish structure if needed,
        # but for now assuming files exist as generated previously.
        # Note: The English JSONs have keys: number, question, options (letter, text, is_correct), correct_answer, explanation
        # The Spanish JSONs have keys: numero, pregunta, opciones (letra, texto, es_correcta), respuesta_correcta, explicacion
        raise HTTPException(
            status_code=404, detail=f"Questions file not found: {filename}"
        )

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Normalize data structure if English
        if lang == "en":
            normalized_data = []
            for q in data:
                normalized_data.append(
                    {
                        "numero": q.get("number"),
                        "pregunta": q.get("question"),
                        "opciones": [
                            {
                                "letra": opt.get("letter"),
                                "texto": opt.get("text"),
                                "es_correcta": opt.get("is_correct"),
                            }
                            for opt in q.get("options", [])
                        ],
                        "respuesta_correcta": q.get("correct_answer"),
                        "explicacion": q.get("explanation", ""),
                    }
                )
            data = normalized_data

        if randomize:
            random.shuffle(data)

        if limit > 0:
            data = data[:limit]

        return data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analyze-pages")
async def analyze_pages(
    start_question: int = Query(...),
    end_question: int = Query(...),
    pdf_filename: str = Query("az-204.pdf"),
):
    pdf_path = DATA_DIR / pdf_filename
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF not found")

    results = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            page_texts = {}

            def get_text(page_idx):
                if page_idx not in page_texts:
                    if 0 <= page_idx < total_pages:
                        page_texts[page_idx] = pdf.pages[page_idx].extract_text() or ""
                    else:
                        page_texts[page_idx] = ""
                return page_texts[page_idx]

            # Las primeras 17 páginas son el menú, comenzamos desde la 18 (índice 17)
            scan_idx = 17

            for q_num in range(start_question, end_question + 1):
                q_pattern = f"Question #{q_num}"
                next_pattern = f"Question #{q_num + 1}"

                q_start = -1
                q_end = -1

                # Search for start
                found_start = False
                for i in range(scan_idx, total_pages):
                    text = get_text(i)
                    if q_pattern in text:
                        q_start = i
                        scan_idx = i
                        found_start = True
                        break

                if not found_start:
                    # Try searching from beginning if not found (in case of disorder or restart)
                    # But for now, assume sequential.
                    results.append(
                        {
                            "question": q_num,
                            "start_page": None,
                            "end_page": None,
                            "status": "Not Found",
                        }
                    )
                    continue

                # Search for end (start of next question)
                found_end = False
                for i in range(q_start, total_pages):
                    text = get_text(i)
                    if next_pattern in text:
                        q_end = i
                        found_end = True
                        break

                if not found_end:
                    # Heuristic: assume it ends 2 pages later or at end of doc
                    q_end = min(q_start + 2, total_pages - 1)

                results.append(
                    {
                        "question": q_num,
                        "start_page": q_start + 1,
                        "end_page": q_end + 1,
                        "status": "Found",
                    }
                )

                if found_end:
                    scan_idx = q_end
                else:
                    scan_idx = q_start

            return results

    except Exception as e:
        print(f"Error analyzing pages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/questions-md/{exam_id}/README.md")
async def get_unified_markdown(
    exam_id: str,
    full: bool = Query(False),
    lang: str = Query("es", regex="^(es|en)$"),
):
    md_dir = DATA_DIR / exam_id / "questions_md" / lang

    if not md_dir.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Markdown directory not found for exam {exam_id} and language {lang}",
        )

    files = []
    for f in md_dir.iterdir():
        if f.suffix != ".md":
            continue

        is_full_file = f.stem.endswith("_full")

        if full and is_full_file:
            files.append(f)
        elif not full and not is_full_file:
            files.append(f)

    # Sort files numerically
    def get_question_number(file_path):
        name = file_path.stem
        if "_full" in name:
            name = name.replace("_full", "")
        try:
            return int(name)
        except ValueError:
            return float("inf")  # Put non-numeric at the end

    files.sort(key=get_question_number)

    unified_content = ""
    for f in files:
        with open(f, "r", encoding="utf-8") as file:
            unified_content += file.read() + "\n\n---\n\n"

    html_content = markdown.markdown(unified_content, extensions=['fenced_code', 'tables'])
    
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Exam Questions</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.2.0/github-markdown.min.css">
        <style>
            .markdown-body {{
                box-sizing: border-box;
                min-width: 200px;
                max-width: 980px;
                margin: 0 auto;
                padding: 45px;
            }}
            @media (max-width: 767px) {{
                .markdown-body {{
                    padding: 15px;
                }}
            }}
        </style>
    </head>
    <body>
        <article class="markdown-body">
            {html_content}
        </article>
    </body>
    </html>
    """

    return HTMLResponse(content=full_html)


# Mount frontend
frontend_path = Path(__file__).parent.parent / "frontend" / "www"


@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    if not frontend_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Frontend not found. Please build the Ionic app first.",
        )

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
