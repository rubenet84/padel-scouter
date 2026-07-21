"""
Servicio RAG (Retrieval-Augmented Generation) para el chatbot del reglamento de pádel.

Usa exclusivamente la API de Google Gemini:
  - Embeddings: text-embedding-004
  - Generación: gemini-2.5-flash

El chatbot SOLO responde con información extraída del PDF indexado, nunca
inventa reglas ni usa conocimiento externo del modelo.
"""
import json
import pickle
import re
from pathlib import Path
from typing import List
from urllib import request as urllib_request

import numpy as np
from google import genai
from google.genai import types as genai_types
from pypdf import PdfReader

from app.core.config import settings

# --- Configuración ---
GOOGLE_API_KEY = settings.google_api_key.get_secret_value()
if not GOOGLE_API_KEY:
    raise RuntimeError(
        "Falta la variable de entorno GOOGLE_API_KEY. "
        "Consíguela gratis en https://aistudio.google.com/apikey"
    )

_client = genai.Client(api_key=GOOGLE_API_KEY)
EMBEDDING_MODEL = "gemini-embedding-2"
GENERATION_MODEL = "gemini-2.5-flash"
PROJECT_ROOT = Path(__file__).resolve().parents[3]
INDEX_PATH = PROJECT_ROOT / "data" / "padel_rules_index.pkl"

SYSTEM_PROMPT = (
    "Eres el asistente de reglamento del sistema Padel Scouter. "
    "SOLO puedes responder usando la información del CONTEXTO proporcionado, "
    "que proviene literalmente del reglamento oficial de pádel. "
    "Si la respuesta no está en el contexto, responde exactamente: "
    "'No he encontrado esa información en el reglamento. ¿Puedes reformular la pregunta?' "
    "No inventes reglas, no completes con conocimiento general de pádel que no esté "
    "en el contexto. Responde en español, de forma clara, breve y con un tono "
    "cercano al estilo 'scouter' del sistema (directo y preciso)."
)


class PadelRulesRAG:
    def __init__(self):
        self.chunks: List[str] = []
        self.embeddings: np.ndarray | None = None
        if INDEX_PATH.exists():
            self._load_index()

    # ---------------- Construcción del índice (offline, una vez) ----------------

    def build_index_from_pdf(self, pdf_path: str, max_chunk_chars: int = 1200):
        text = self._extract_text(pdf_path)
        self.chunks = self._chunk_by_structure(text, max_chunk_chars)
        self.embeddings = self._embed_chunks(self.chunks)
        self._save_index()

    def _extract_text(self, pdf_path: str) -> str:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += (page.extract_text() or "") + "\n"
        return text

    # Cabeceras conocidas del reglamento FIP (fuera de las "REGLA N."), tomadas
    # del propio índice del documento. Si la FIP publica una nueva revisión con
    # apartados adicionales, basta con añadirlos aquí.
    _KNOWN_HEADERS = [
        "PRÓLOGO", "LA PISTA", "DIMENSIONES", "RED", "CERRAMIENTOS", "FONDOS", "LATERALES",
        "SUELO", "ACCESOS", "ZONA DE SEGURIDAD Y JUEGO EXTERIOR", "ILUMINACIÓN", "ORIENTACIÓN",
        "LA PELOTA", "LA PALA",
        "NORMAS DE ETIQUETA Y DE CONDUCTA", "PUNTUALIDAD", "INDUMENTARIA", "IDENTIDAD",
        "CONDUCTA Y DISCIPLINA", "ÁREA DE JUEGO", "CONSEJOS E INSTRUCCIONES", "ENTREGA DE PREMIOS",
        "JUEGO CONTINUO Y/O DEMORA EN EL JUEGO", "OBSCENIDADES AUDIBLES Y VISIBLES", "ABUSO DE PELOTA",
        "ABUSO DE PALA O EQUIPO", "ABUSO VERBAL Y ABUSO FÍSICO O AGRESIÓN", "MEJORES ESFUERZOS",
        "CONDUCTA ANTIDEPORTIVA", "PENALIZACIONES/ TABLA DE PENALIZACIONES", "DESCALIFICACIÓN DIRECTA",
    ]

    def _chunk_by_structure(self, text: str, max_chunk_chars: int) -> List[str]:
        """Trocea el reglamento respetando su estructura real: detecta las
        cabeceras ("REGLA N. ...", "LA PISTA", "DIMENSIONES", etc.) y genera
        un fragmento por sección, dividiendo las secciones largas por sus
        puntos numerados/lettered (1., 2., a), b)...) para no pasarnos del
        tamaño máximo, siempre conservando el título como contexto."""
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n+", "\n", text)

        # Quita el índice (ÍNDICE ... hasta la 2ª aparición de "PRÓLOGO",
        # la 1ª es solo la entrada del propio índice) y números de página sueltos
        idx_start = text.find("ÍNDICE")
        first_prologo = text.find("PRÓLOGO")
        second_prologo = text.find("PRÓLOGO", first_prologo + 1) if first_prologo != -1 else -1
        if idx_start != -1 and second_prologo != -1:
            text = text[:idx_start] + text[second_prologo:]
        text = re.sub(r"\n\d{1,3}\s*\n", "\n", text)

        headers_sorted = sorted(self._KNOWN_HEADERS, key=len, reverse=True)
        header_alt = "|".join(re.escape(h) for h in headers_sorted)
        pattern = re.compile(
            rf"(?:{header_alt}|REGLA\s+\d+\.\s+[^\n]*?(?=\s\d{{1,2}}\.\s|\n|$))"
        )

        matches = list(pattern.finditer(text))
        if not matches:
            return self._chunk_plain(text, max_chunk_chars)

        chunks: List[str] = []
        pending_title = None
        for i, m in enumerate(matches):
            title = m.group().strip()
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            content = text[start:end].strip()

            if pending_title:
                title = f"{pending_title} / {title}"
                pending_title = None

            if len(content) < 25:
                pending_title = title
                continue

            if len(content) <= max_chunk_chars:
                chunks.append(f"{title}\n{content}")
            else:
                chunks.extend(self._split_long_section(title, content, max_chunk_chars))

        return chunks

    def _split_long_section(self, title: str, content: str, max_chunk_chars: int) -> List[str]:
        item_pattern = re.compile(r"(?=\s\d{1,2}\.\s|\s[a-z]\)\s)")
        parts = [p.strip() for p in item_pattern.split(content) if p.strip()]
        if len(parts) <= 1:
            return self._chunk_plain(content, max_chunk_chars, title=title)

        chunks, current = [], ""
        for part in parts:
            if len(current) + len(part) + 1 <= max_chunk_chars or not current:
                current = f"{current} {part}".strip()
            else:
                chunks.append(f"{title}\n{current}")
                current = part
        if current:
            chunks.append(f"{title}\n{current}")
        return chunks

    def _chunk_plain(self, text: str, max_chunk_chars: int, title: str | None = None) -> List[str]:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        chunks, current = [], ""
        for s in sentences:
            if len(current) + len(s) + 1 <= max_chunk_chars or not current:
                current = f"{current} {s}".strip()
            else:
                chunks.append(f"{title}\n{current}" if title else current)
                current = s
        if current:
            chunks.append(f"{title}\n{current}" if title else current)
        return chunks

    def _embed_chunks(self, chunks: List[str]) -> np.ndarray:
        vectors = []
        for chunk in chunks:
            vectors.append(self._call_embed_api(chunk))
        return np.array(vectors)

    def _save_index(self):
        INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(INDEX_PATH, "wb") as f:
            pickle.dump({"chunks": self.chunks, "embeddings": self.embeddings}, f)

    def _load_index(self):
        with open(INDEX_PATH, "rb") as f:
            data = pickle.load(f)
        self.chunks = data["chunks"]
        self.embeddings = data["embeddings"]

    # ---------------- Consulta (online, en cada pregunta) ----------------

    def _call_embed_api(self, text: str) -> list[float]:
        """Llama a la API de embeddings v1 directamente (evita v1beta)."""
        url = f"https://generativelanguage.googleapis.com/v1/models/{EMBEDDING_MODEL}:embedContent?key={GOOGLE_API_KEY}"
        body = json.dumps({"model": f"models/{EMBEDDING_MODEL}", "content": {"parts": [{"text": text}]}}).encode()
        req = urllib_request.Request(url, data=body, headers={"Content-Type": "application/json"})
        resp = urllib_request.urlopen(req)
        data = json.loads(resp.read())
        return data["embedding"]["values"]

    def _embed_query(self, query: str) -> np.ndarray:
        return np.array(self._call_embed_api(query))

    def _top_k_chunks(self, query_vec: np.ndarray, k: int = 4) -> List[str]:
        sims = self.embeddings @ query_vec / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_vec) + 1e-10
        )
        top_idx = np.argsort(sims)[::-1][:k]
        return [self.chunks[i] for i in top_idx]

    def answer(self, question: str, k: int = 4) -> str:
        if self.embeddings is None:
            raise RuntimeError(
                "El índice del reglamento no existe todavía. "
                "Ejecuta scripts/build_rules_index.py primero."
            )
        query_vec = self._embed_query(question)
        context = "\n\n---\n\n".join(self._top_k_chunks(query_vec, k))

        response = _client.models.generate_content(
            model=GENERATION_MODEL,
            contents=f"CONTEXTO DEL REGLAMENTO:\n{context}\n\nPREGUNTA DEL USUARIO: {question}",
            config=genai_types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
            ),
        )
        return response.text
