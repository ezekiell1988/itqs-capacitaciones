import json
from pathlib import Path

def load_questions(json_path):
    """Carga las preguntas desde el archivo JSON"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def translate_to_spanish_md(questions, output_path):
    """Genera un archivo Markdown en español con las preguntas"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # Encabezado
        f.write("# Preguntas de Práctica - Microsoft AZ-204\n\n")
        f.write("## Developing Solutions for Microsoft Azure\n\n")
        f.write(f"Total de preguntas: **{len(questions)}**\n\n")
        f.write("---\n\n")
        
        # Generar cada pregunta
        for q in questions:
            # Número de pregunta
            f.write(f"## Pregunta #{q['number']}\n\n")
            
            # Texto de la pregunta
            f.write(f"{q['question']}\n\n")
            
            # Opciones
            if q['options']:
                f.write("### Opciones:\n\n")
                for opt in q['options']:
                    # Marcar la respuesta correcta
                    if opt.get('is_correct', False) or opt['letter'] == q.get('correct_answer', ''):
                        f.write(f"- **{opt['letter']}) {opt['text']}** ✅\n")
                    else:
                        f.write(f"- {opt['letter']}) {opt['text']}\n")
                f.write("\n")
            
            # Respuesta correcta
            if q['correct_answer']:
                f.write(f"### ✅ Respuesta Correcta: **{q['correct_answer']}**\n\n")
            
            # Explicación
            if q['explanation']:
                f.write(f"### 📝 Explicación:\n\n")
                f.write(f"{q['explanation']}\n\n")
            
            f.write("---\n\n")
    
    print(f"✓ Archivo Markdown generado: {output_path.name}")

def main():
    # Rutas de archivos
    json_path = Path(r"C:\Users\EzequielBaltodanoCub\OneDrive - IT Quest Solutions (ITQS)\Documents\ITQS\capacitaciones\extracted\az-204_questions.json")
    output_path = Path(r"C:\Users\EzequielBaltodanoCub\OneDrive - IT Quest Solutions (ITQS)\Documents\ITQS\capacitaciones\az-204.md")
    
    print("="*80)
    print("GENERADOR DE MARKDOWN EN ESPAÑOL - AZ-204")
    print("="*80)
    print()
    
    # Cargar preguntas
    print("→ Cargando preguntas desde JSON...")
    questions = load_questions(json_path)
    print(f"  ✓ {len(questions)} preguntas cargadas")
    
    # Generar Markdown
    print("→ Generando archivo Markdown en español...")
    translate_to_spanish_md(questions, output_path)
    
    print()
    print("="*80)
    print("PROCESO COMPLETADO")
    print("="*80)
    print(f"📄 Archivo generado: {output_path}")
    print()

if __name__ == "__main__":
    main()
