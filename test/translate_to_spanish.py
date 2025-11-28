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

def load_questions(json_path):
    """Carga las preguntas desde el archivo JSON"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_spanish_md(questions, output_path):
    """Genera un archivo Markdown completamente en español"""

    with open(output_path, 'w', encoding='utf-8') as f:
        # Encabezado
        f.write("# Preguntas de Práctica - Microsoft AZ-204\n\n")
        f.write("## Desarrollo de Soluciones para Microsoft Azure\n\n")
        f.write(f"Total de preguntas: **{len(questions)}**\n\n")
        f.write("---\n\n")

        # Generar cada pregunta
        total = len(questions)
        for idx, q in enumerate(questions, 1):
            print(f"  Traduciendo pregunta {idx}/{total}...", end='\r')

            # Número de pregunta
            f.write(f"## Pregunta #{q['number']}\n\n")

            # Traducir texto de la pregunta
            question_text = translate_text(q['question'])
            f.write(f"{question_text}\n\n")

            # Opciones
            if q['options']:
                f.write("### Opciones:\n\n")
                for opt in q['options']:
                    # Traducir texto de la opción
                    option_text = translate_text(opt['text'])

                    # Marcar la respuesta correcta
                    if opt.get('is_correct', False) or opt['letter'] == q.get('correct_answer', ''):
                        f.write(f"- **{opt['letter']}) {option_text}** ✅\n")
                    else:
                        f.write(f"- {opt['letter']}) {option_text}\n")
                f.write("\n")

            # Respuesta correcta
            if q['correct_answer']:
                f.write(f"### ✅ Respuesta Correcta: **{q['correct_answer']}**\n\n")

            # Explicación
            if q['explanation']:
                f.write(f"### 📝 Explicación:\n\n")
                explanation_text = translate_text(q['explanation'])
                f.write(f"{explanation_text}\n\n")

            f.write("---\n\n")

        print()  # Nueva línea después de las traducciones

    print(f"✓ Archivo Markdown en español generado: {output_path.name}")

def main():
    # Rutas de archivos
    json_path = Path(r"C:\Users\EzequielBaltodanoCub\OneDrive - IT Quest Solutions (ITQS)\Documents\ITQS\capacitaciones\extracted\az-204_questions.json")
    output_path = Path(r"C:\Users\EzequielBaltodanoCub\OneDrive - IT Quest Solutions (ITQS)\Documents\ITQS\capacitaciones\az-204.md")

    print("="*80)
    print("TRADUCTOR DE PREGUNTAS AZ-204 AL ESPAÑOL")
    print("="*80)
    print()

    # Verificar si deep-translator está instalado
    try:
        from deep_translator import GoogleTranslator
    except ImportError:
        print("⚠ Instalando librería de traducción...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'deep-translator'])
        print("✓ Librería instalada\n")

    # Cargar preguntas
    print("→ Cargando preguntas desde JSON...")
    questions = load_questions(json_path)
    print(f"  ✓ {len(questions)} preguntas cargadas\n")

    # Generar Markdown traducido
    print("→ Traduciendo preguntas al español...")
    print("  (Esto puede tomar varios minutos...)\n")
    generate_spanish_md(questions, output_path)

    print()
    print("="*80)
    print("PROCESO COMPLETADO")
    print("="*80)
    print(f"📄 Archivo generado: {output_path}")
    print()

if __name__ == "__main__":
    main()
