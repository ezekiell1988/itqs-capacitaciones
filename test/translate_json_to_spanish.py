import json
from pathlib import Path
from deep_translator import GoogleTranslator

def translate_text(text, max_length=4500):
    """Traduce texto al español dividiendo en chunks si es necesario"""
    if not text or len(text.strip()) == 0:
        return text
    
    translator = GoogleTranslator(source='en', target='es')
    
    # Si el texto es corto, traducir directamente
    if len(text) <= max_length:
        try:
            return translator.translate(text)
        except Exception as e:
            print(f"  ⚠ Error traduciendo: {e}")
            return text
    
    # Si es largo, dividir en párrafos y traducir
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

def translate_json_to_spanish(input_path, output_path):
    """Traduce el archivo JSON completo al español"""
    
    # Cargar JSON original
    with open(input_path, 'r', encoding='utf-8') as f:
        questions = json.load(f)
    
    translated_questions = []
    total = len(questions)
    
    for idx, q in enumerate(questions, 1):
        print(f"  Traduciendo pregunta {idx}/{total}...", end='\r')
        
        translated_q = {
            "numero": q["number"],
            "pregunta": translate_text(q["question"]),
            "opciones": [],
            "respuesta_correcta": q["correct_answer"],
            "explicacion": translate_text(q["explanation"]) if q["explanation"] else ""
        }
        
        # Traducir opciones
        for opt in q["options"]:
            translated_opt = {
                "letra": opt["letter"],
                "texto": translate_text(opt["text"]),
                "es_correcta": opt["is_correct"]
            }
            translated_q["opciones"].append(translated_opt)
        
        translated_questions.append(translated_q)
    
    print()  # Nueva línea después de las traducciones
    
    # Guardar JSON traducido
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(translated_questions, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Archivo JSON traducido guardado: {output_path.name}")

def main():
    # Rutas de archivos
    input_path = Path(r"C:\Users\EzequielBaltodanoCub\OneDrive - IT Quest Solutions (ITQS)\Documents\ITQS\capacitaciones\extracted\az-204_questions.json")
    output_path = Path(r"C:\Users\EzequielBaltodanoCub\OneDrive - IT Quest Solutions (ITQS)\Documents\ITQS\capacitaciones\extracted\az-204_questions_es.json")
    
    print("="*80)
    print("TRADUCTOR JSON AZ-204 AL ESPAÑOL")
    print("="*80)
    print()
    
    # Traducir JSON
    print("→ Traduciendo archivo JSON al español...")
    print("  (Esto puede tomar varios minutos...)\n")
    translate_json_to_spanish(input_path, output_path)
    
    print()
    print("="*80)
    print("PROCESO COMPLETADO")
    print("="*80)
    print(f"📄 Archivo JSON en español: {output_path}")
    print()

if __name__ == "__main__":
    main()
