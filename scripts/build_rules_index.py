"""
Construye (o reconstruye) el índice del reglamento de pádel a partir de un PDF.

Uso:
    export GEMINI_API_KEY="tu_api_key_gratuita"
    python scripts/build_rules_index.py ruta/al/reglamento.pdf

Vuelve a ejecutarlo cada vez que cambies el PDF del reglamento.
"""
import sys
from pathlib import Path

# Permite ejecutar el script desde la raíz del proyecto
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.infrastructure.ai.padel_rules_rag import PadelRulesRAG

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scripts/build_rules_index.py ruta/al/reglamento.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]
    if not Path(pdf_path).exists():
        print(f"No se encuentra el fichero: {pdf_path}")
        sys.exit(1)

    rag = PadelRulesRAG()
    rag.build_index_from_pdf(pdf_path)
