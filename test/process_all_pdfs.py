import pdfplumber
import re
import json
from pathlib import Path
from docx import Document

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
    print(f"  ✓ Texto guardado en: {output_path.name}")

def save_to_docx(text, output_path):
    """Guarda el texto en un archivo .docx"""
    doc = Document()
    doc.add_paragraph(text)
    doc.save(output_path)
    print(f"  ✓ Documento Word guardado en: {output_path.name}")

def extract_questions_and_answers(text):
    """Extrae preguntas con sus respuestas del texto"""
    questions = []
    
    # Encontrar donde empiezan las preguntas reales (después del índice)
    # Buscar el primer "Question #" seguido de contenido real (no solo números)
    start_marker = re.search(r'(Question\s+#1\s+[^\d].*?)(?=Question\s+#2)', text, re.DOTALL | re.IGNORECASE)
    
    if start_marker:
        # Encontrar el inicio del contenido real
        start_pos = start_marker.start()
        text = text[start_pos:]
    
    # Patrón mejorado para el formato del PDF de AZ-204
    # Busca "Question #X" seguido del contenido hasta el siguiente "Question #"
    pattern = r'Question\s+#(\d+)\s+(.*?)(?=Question\s+#\d+|$)'
    
    matches = re.finditer(pattern, text, re.DOTALL | re.IGNORECASE)
    
    for match in matches:
        question_num = match.group(1)
        full_content = match.group(2).strip()
        
        # Filtrar preguntas que son solo parte del índice (muy cortas, solo números)
        if len(full_content) < 50 or re.match(r'^\d+\s*•?\s*$', full_content):
            continue
        
        # Extraer el texto de la pregunta (antes de las opciones)
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
                
                # Verificar si esta opción es marcada como correcta
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
            # Si no hay opciones con formato A), B), etc., tomar todo el contenido
            question_text = full_content
        
        # Limpiar texto de la pregunta (remover líneas con "SecExams.com", "Page X of Y", etc.)
        question_text = re.sub(r'Page \d+ of \d+', '', question_text)
        question_text = re.sub(r'\d+ Microsoft - AZ-\d+ Practice Questions - SecExams\.com', '', question_text)
        question_text = re.sub(r'SecExams - Focus Only.*?secexams\.com', '', question_text, flags=re.DOTALL)
        question_text = question_text.strip()
        
        if question_text and len(question_text) > 50:  # Solo agregar si hay contenido válido y suficientemente largo
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

def save_questions_to_txt(questions, output_path):
    """Guarda las preguntas extraídas en formato de texto legible"""
    with open(output_path, 'w', encoding='utf-8') as f:
        for q in questions:
            f.write(f"{'='*80}\n")
            f.write(f"PREGUNTA #{q['number']}\n")
            f.write(f"{'='*80}\n\n")
            f.write(f"{q['question']}\n\n")
            
            if q['options']:
                f.write("OPCIONES:\n")
                for opt in q['options']:
                    marker = " ✓" if opt.get('is_correct', False) else ""
                    f.write(f"  {opt['letter']}) {opt['text']}{marker}\n")
                f.write("\n")
            
            if q['correct_answer']:
                f.write(f"RESPUESTA CORRECTA: {q['correct_answer']}\n\n")
            
            if q['explanation']:
                f.write(f"EXPLICACIÓN:\n{q['explanation']}\n")
            
            f.write("\n" + "="*80 + "\n\n")
    
    print(f"  ✓ Preguntas guardadas en TXT: {output_path.name}")

def process_pdf(pdf_path, output_dir):
    """Procesa un único archivo PDF"""
    pdf_name = pdf_path.stem
    
    print(f"\n{'='*80}")
    print(f"PROCESANDO: {pdf_path.name}")
    print(f"{'='*80}")
    
    # 1. Extraer texto del PDF
    print("→ Extrayendo texto del PDF...")
    text = extract_text_from_pdf(pdf_path)
    
    if not text:
        print("  ✗ No se pudo extraer texto del PDF.")
        return False
    
    # 2. Guardar texto completo
    txt_output = output_dir / f"{pdf_name}_full_text.txt"
    save_to_txt(text, txt_output)
    
    docx_output = output_dir / f"{pdf_name}_full_text.docx"
    save_to_docx(text, docx_output)
    
    # 3. Extraer preguntas y respuestas
    print("→ Extrayendo preguntas y respuestas...")
    questions = extract_questions_and_answers(text)
    
    print(f"  ✓ Total de preguntas encontradas: {len(questions)}")
    
    # 4. Guardar preguntas
    if questions:
        json_output = output_dir / f"{pdf_name}_questions.json"
        save_questions_to_json(questions, json_output)
        
        questions_txt_output = output_dir / f"{pdf_name}_questions.txt"
        save_questions_to_txt(questions, questions_txt_output)
    else:
        print("  ⚠ No se encontraron preguntas con el formato esperado.")
    
    return True

def main():
    # Directorio con los PDFs
    docs_dir = Path(r"C:\Users\EzequielBaltodanoCub\OneDrive - IT Quest Solutions (ITQS)\Documents\ITQS\capacitaciones\docs")
    
    # Crear carpeta de salida si no existe
    output_dir = Path(r"C:\Users\EzequielBaltodanoCub\OneDrive - IT Quest Solutions (ITQS)\Documents\ITQS\capacitaciones\extracted")
    output_dir.mkdir(exist_ok=True)
    
    # Buscar todos los archivos PDF
    pdf_files = list(docs_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No se encontraron archivos PDF en el directorio 'docs'.")
        return
    
    print(f"\n{'#'*80}")
    print(f"EXTRACTOR DE PREGUNTAS DE EXÁMENES - AZURE CERTIFICATIONS")
    print(f"{'#'*80}")
    print(f"\nEncontrados {len(pdf_files)} archivo(s) PDF:")
    for pdf in pdf_files:
        print(f"  • {pdf.name}")
    
    # Procesar cada PDF
    successful = 0
    failed = 0
    
    for pdf_path in pdf_files:
        try:
            if process_pdf(pdf_path, output_dir):
                successful += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ✗ Error procesando {pdf_path.name}: {e}")
            failed += 1
    
    # Resumen final
    print(f"\n{'#'*80}")
    print(f"RESUMEN FINAL")
    print(f"{'#'*80}")
    print(f"  ✓ Archivos procesados exitosamente: {successful}")
    if failed > 0:
        print(f"  ✗ Archivos con errores: {failed}")
    print(f"\n  📁 Archivos guardados en: {output_dir}")
    print(f"{'#'*80}\n")

if __name__ == "__main__":
    main()
