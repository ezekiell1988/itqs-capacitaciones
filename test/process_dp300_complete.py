import pdfplumber
import re
import json
from pathlib import Path
from docx import Document
from deep_translator import GoogleTranslator

# ==================== FUNCIONES DE EXTRACCIÓN ====================

def extract_text_from_pdf(pdf_path):
    """Extrae texto de un archivo PDF"""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error al leer PDF: {e}")
    return text

def save_to_txt(text, output_path):
    """Guarda el texto en un archivo .txt"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"  ✓ Texto guardado: {output_path.name}")

def save_to_docx(text, output_path):
    """Guarda el texto en un archivo .docx"""
    doc = Document()
    doc.add_paragraph(text)
    doc.save(output_path)
    print(f"  ✓ Documento Word guardado: {output_path.name}")

def extract_questions_and_answers(text):
    """Extrae preguntas con sus respuestas del texto"""
    questions = []
    
    # Encontrar donde empiezan las preguntas reales (después del índice)
    start_marker = re.search(r'(Question\s+#1\s+[^\d].*?)(?=Question\s+#2)', text, re.DOTALL | re.IGNORECASE)
    
    if start_marker:
        start_pos = start_marker.start()
        text = text[start_pos:]
    
    # Patrón para el formato del PDF
    pattern = r'Question\s+#(\d+)\s+(.*?)(?=Question\s+#\d+|$)'
    
    matches = re.finditer(pattern, text, re.DOTALL | re.IGNORECASE)
    
    for match in matches:
        question_num = match.group(1)
        full_content = match.group(2).strip()
        
        # Filtrar preguntas que son solo parte del índice
        if len(full_content) < 50 or re.match(r'^\d+\s*•?\s*$', full_content):
            continue
        
        question_text = ""
        options = []
        correct_answer = ""
        explanation = ""
        
        # Buscar donde empiezan las opciones (A), B), C), D))
        options_start = re.search(r'\n[A-D]\)', full_content)
        if options_start:
            question_text = full_content[:options_start.start()].strip()
            remaining_text = full_content[options_start.start():]
            
            # Extraer opciones (A), B), C), D))
            option_pattern = r'([A-D])\)\s+(.*?)(?=\n[A-D]\)|Explanation|Correct Answer:|Community Discussion|$)'
            option_matches = re.finditer(option_pattern, remaining_text, re.DOTALL)
            
            for opt_match in option_matches:
                letter = opt_match.group(1)
                text = opt_match.group(2).strip()
                
                is_correct = "(Correct Answer)" in text
                text = text.replace("(Correct Answer)", "").strip()
                
                options.append({
                    'letter': letter,
                    'text': text,
                    'is_correct': is_correct
                })
            
            # Extraer respuesta correcta
            answer_match = re.search(r'Correct Answer:\s*([A-D])', remaining_text, re.IGNORECASE)
            if answer_match:
                correct_answer = answer_match.group(1)
            
            # Extraer explicación
            explanation_match = re.search(r'Explanation\s*Correct Answer:\s*([A-D])\s*(.*?)(?=Community Discussion|Page \d+|$)', remaining_text, re.DOTALL | re.IGNORECASE)
            if explanation_match:
                explanation = explanation_match.group(2).strip()
        else:
            question_text = full_content
        
        # Limpiar texto de la pregunta
        question_text = re.sub(r'Page \d+ of \d+', '', question_text)
        question_text = re.sub(r'\d+ Microsoft - DP-\d+ Practice Questions - SecExams\.com', '', question_text)
        question_text = re.sub(r'SecExams - Focus Only.*?secexams\.com', '', question_text, flags=re.DOTALL)
        question_text = question_text.strip()
        
        if question_text and len(question_text) > 50:
            questions.append({
                'number': question_num,
                'question': question_text,
                'options': options,
                'correct_answer': correct_answer,
                'explanation': explanation
            })
    
    return questions

def save_questions_to_json(questions, output_path):
    """Guarda las preguntas extraídas en formato JSON"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    print(f"  ✓ Preguntas guardadas en JSON: {output_path.name}")

# ==================== FUNCIONES DE TRADUCCIÓN ====================

def translate_text(text, max_length=4500):
    """Traduce texto al español dividiendo en chunks si es necesario"""
    if not text or len(text.strip()) == 0:
        return text
    
    translator = GoogleTranslator(source='en', target='es')
    
    if len(text) <= max_length:
        try:
            return translator.translate(text)
        except Exception as e:
            return text
    
    paragraphs = text.split('\n')
    translated_paragraphs = []
    
    current_chunk = ""
    for para in paragraphs:
        if len(current_chunk) + len(para) + 1 <= max_length:
            current_chunk += para + "\n"
        else:
            if current_chunk:
                try:
                    translated_paragraphs.append(translator.translate(current_chunk.strip()))
                except:
                    translated_paragraphs.append(current_chunk.strip())
            current_chunk = para + "\n"
    
    if current_chunk:
        try:
            translated_paragraphs.append(translator.translate(current_chunk.strip()))
        except:
            translated_paragraphs.append(current_chunk.strip())
    
    return "\n".join(translated_paragraphs)

def translate_json_to_spanish(questions):
    """Traduce las preguntas al español"""
    translated_questions = []
    total = len(questions)
    
    print("→ Traduciendo preguntas al español...")
    for idx, q in enumerate(questions, 1):
        print(f"  Traduciendo pregunta {idx}/{total}...", end='\r')
        
        translated_q = {
            "numero": q["number"],
            "pregunta": translate_text(q["question"]),
            "opciones": [],
            "respuesta_correcta": q["correct_answer"],
            "explicacion": translate_text(q["explanation"]) if q["explanation"] else ""
        }
        
        for opt in q["options"]:
            translated_opt = {
                "letra": opt["letter"],
                "texto": translate_text(opt["text"]),
                "es_correcta": opt["is_correct"]
            }
            translated_q["opciones"].append(translated_opt)
        
        translated_questions.append(translated_q)
    
    print()
    return translated_questions

def save_spanish_json(questions, output_path):
    """Guarda JSON en español"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    print(f"  ✓ JSON en español guardado: {output_path.name}")

# ==================== FUNCIONES DE MARKDOWN ====================

def generate_spanish_md(questions, output_path, exam_name):
    """Genera un archivo Markdown en español"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# Preguntas de Práctica - Microsoft {exam_name}\n\n")
        
        if exam_name == "DP-300":
            f.write("## Administering Microsoft Azure SQL Solutions\n\n")
        
        f.write(f"Total de preguntas: **{len(questions)}**\n\n")
        f.write("---\n\n")
        
        for q in questions:
            f.write(f"## Pregunta #{q['numero']}\n\n")
            f.write(f"{q['pregunta']}\n\n")
            
            if q['opciones']:
                f.write("### Opciones:\n\n")
                for opt in q['opciones']:
                    if opt.get('es_correcta', False) or opt['letra'] == q.get('respuesta_correcta', ''):
                        f.write(f"- **{opt['letra']}) {opt['texto']}** ✅\n")
                    else:
                        f.write(f"- {opt['letra']}) {opt['texto']}\n")
                f.write("\n")
            
            if q['respuesta_correcta']:
                f.write(f"### ✅ Respuesta Correcta: **{q['respuesta_correcta']}**\n\n")
            
            if q['explicacion']:
                f.write(f"### 📝 Explicación:\n\n")
                f.write(f"{q['explicacion']}\n\n")
            
            f.write("---\n\n")
    
    print(f"  ✓ Markdown en español generado: {output_path.name}")

# ==================== FUNCIÓN PRINCIPAL ====================

def main():
    # Configuración de rutas
    pdf_path = Path(r"C:\Users\EzequielBaltodanoCub\OneDrive - IT Quest Solutions (ITQS)\Documents\ITQS\capacitaciones\docs\dp-300.pdf")
    output_dir = Path(r"C:\Users\EzequielBaltodanoCub\OneDrive - IT Quest Solutions (ITQS)\Documents\ITQS\capacitaciones\extracted")
    
    exam_code = "dp-300"
    
    print("="*80)
    print(f"PROCESAMIENTO COMPLETO: {exam_code.upper()}")
    print("="*80)
    print()
    
    # PASO 1: Extraer texto del PDF
    print("📄 PASO 1: Extrayendo texto del PDF...")
    text = extract_text_from_pdf(pdf_path)
    
    if not text:
        print("✗ No se pudo extraer texto del PDF.")
        return
    
    txt_output = output_dir / f"{exam_code}_full_text.txt"
    save_to_txt(text, txt_output)
    
    docx_output = output_dir / f"{exam_code}_full_text.docx"
    save_to_docx(text, docx_output)
    
    # PASO 2: Extraer preguntas
    print("\n📝 PASO 2: Extrayendo preguntas y respuestas...")
    questions = extract_questions_and_answers(text)
    print(f"  ✓ Total de preguntas encontradas: {len(questions)}")
    
    if not questions:
        print("✗ No se encontraron preguntas.")
        return
    
    json_output = output_dir / f"{exam_code}_questions.json"
    save_questions_to_json(questions, json_output)
    
    # PASO 3: Traducir al español
    print("\n🌐 PASO 3: Traduciendo al español...")
    print("  (Esto puede tomar varios minutos...)")
    questions_es = translate_json_to_spanish(questions)
    
    json_es_output = output_dir / f"{exam_code}_questions_es.json"
    save_spanish_json(questions_es, json_es_output)
    
    # PASO 4: Generar Markdown en español
    print("\n📋 PASO 4: Generando Markdown en español...")
    md_output = output_dir.parent / f"{exam_code}.md"
    generate_spanish_md(questions_es, md_output, exam_code.upper())
    
    # Resumen final
    print("\n" + "="*80)
    print("✅ PROCESO COMPLETADO EXITOSAMENTE")
    print("="*80)
    print(f"\n📁 Archivos generados:")
    print(f"  • {txt_output.name}")
    print(f"  • {docx_output.name}")
    print(f"  • {json_output.name}")
    print(f"  • {json_es_output.name}")
    print(f"  • {md_output.name}")
    print(f"\n📊 Total de preguntas procesadas: {len(questions)}")
    print(f"📂 Ubicación: {output_dir}")
    print()

if __name__ == "__main__":
    main()
