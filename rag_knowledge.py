"""Small, local document ingestion and vector retrieval helpers for RAG.

The project already uses Groq for answer generation. To keep retrieval usable
without another API key or a large model download, this module creates sparse
hashed text vectors locally and ranks them with cosine similarity. These
vectors are lexical (word and phrase overlap), not a neural semantic model.
"""

from collections import Counter
from hashlib import blake2b, sha256
from io import BytesIO
import json
import math
from pathlib import PurePath
import re
import unicodedata


MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_EXTRACTED_CHARACTERS = 300_000
MAX_PDF_PAGES = 80
MAX_CHUNKS_PER_DOCUMENT = 300
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 180
VECTOR_DIMENSIONS = 4096
SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}


class KnowledgeFileError(ValueError):
    """Raised when a user-uploaded knowledge file cannot be safely read."""


def sha256_hex(payload):
    return sha256(payload).hexdigest()


def extract_document_text(filename, payload):
    """Extract bounded text from PDF, TXT, or Markdown bytes."""
    suffix = PurePath(filename or "").suffix.casefold()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise KnowledgeFileError("Use a PDF, TXT, or Markdown file.")
    if not payload:
        raise KnowledgeFileError("The selected file is empty.")
    if len(payload) > MAX_UPLOAD_BYTES:
        raise KnowledgeFileError("Files must be 5 MB or smaller.")

    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise KnowledgeFileError(
                "PDF support is not installed yet. Install the project requirements and try again."
            ) from exc

        try:
            reader = PdfReader(BytesIO(payload), strict=False)
            if reader.is_encrypted:
                try:
                    reader.decrypt("")
                except Exception as exc:
                    raise KnowledgeFileError(
                        "This PDF is password-protected. Remove its password before uploading."
                    ) from exc
                if reader.is_encrypted:
                    raise KnowledgeFileError(
                        "This PDF is password-protected. Remove its password before uploading."
                    )

            if len(reader.pages) > MAX_PDF_PAGES:
                raise KnowledgeFileError(
                    f"PDFs can contain up to {MAX_PDF_PAGES} pages. Split this file and upload the relevant part."
                )

            page_text = []
            total_characters = 0
            for page_number, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                text = _clean_extracted_text(text)
                if text:
                    total_characters += len(text)
                    if total_characters > MAX_EXTRACTED_CHARACTERS:
                        raise KnowledgeFileError(
                            "This PDF contains too much extractable text. Split it into smaller files."
                        )
                    page_text.append(f"[Page {page_number}]\n{text}")
            extracted = "\n\n".join(page_text)
        except KnowledgeFileError:
            raise
        except Exception as exc:
            raise KnowledgeFileError(
                "The PDF could not be read. Check that it is a valid, text-based PDF."
            ) from exc

        if not extracted.strip():
            raise KnowledgeFileError(
                "No selectable text was found in this PDF. Scanned-image OCR is not supported yet."
            )
        return extracted

    try:
        extracted = payload.decode("utf-8-sig")
    except UnicodeDecodeError:
        extracted = payload.decode("utf-8", errors="replace")

    extracted = _clean_extracted_text(extracted)
    if len(extracted) > MAX_EXTRACTED_CHARACTERS:
        raise KnowledgeFileError(
            "Text files can contain up to 300,000 characters. Split this file and upload the relevant part."
        )
    if not extracted:
        raise KnowledgeFileError("No readable text was found in this file.")
    return extracted


def _clean_extracted_text(text):
    normalized = unicodedata.normalize("NFKC", str(text or ""))
    normalized = normalized.replace("\x00", " ")
    normalized = re.sub(r"[^\S\n]+", " ", normalized)
    normalized = re.sub(r"\n[ \t]+", "\n", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split extracted text into readable, overlapping chunks."""
    text = _clean_extracted_text(text)
    if not text:
        return []

    chunks = []
    start = 0
    text_length = len(text)
    while start < text_length:
        hard_end = min(start + chunk_size, text_length)
        end = hard_end

        if hard_end < text_length:
            minimum_break = start + int(chunk_size * 0.65)
            candidates = [
                text.rfind("\n", minimum_break, hard_end),
                text.rfind(". ", minimum_break, hard_end),
                text.rfind("? ", minimum_break, hard_end),
                text.rfind("! ", minimum_break, hard_end),
                text.rfind(" ", minimum_break, hard_end),
            ]
            best_break = max(candidates)
            if best_break >= minimum_break:
                end = best_break + (1 if text[best_break] == "\n" else 2)

        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= text_length:
            break
        start = max(start + 1, end - overlap)
        if len(chunks) > MAX_CHUNKS_PER_DOCUMENT:
            raise KnowledgeFileError(
                f"This file is too long to index at once. Keep it under {MAX_CHUNKS_PER_DOCUMENT} text sections."
            )
    return chunks


_STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "but", "by",
    "can", "could", "did", "do", "does", "for", "from", "had", "has",
    "have", "how", "i", "in", "into", "is", "it", "its", "me", "my",
    "of", "on", "or", "our", "please", "should", "so", "tell", "that",
    "the", "their", "them", "there", "these", "this", "to", "use", "was",
    "we", "what", "when", "where", "which", "who", "why", "will", "with",
    "would", "you", "your",
}


def _features(text):
    normalized = unicodedata.normalize("NFKC", str(text or "")).casefold()
    tokens = re.findall(r"[\w+#.-]+", normalized, flags=re.UNICODE)
    tokens = [
        token.strip("._-#")
        for token in tokens
        if len(token.strip("._-#")) > 1
        and token.strip("._-#") not in _STOP_WORDS
    ]
    features = [f"w:{token}" for token in tokens]
    features.extend(
        f"b:{left}_{right}"
        for left, right in zip(tokens, tokens[1:])
    )
    return features


def embed_text(text):
    """Return a normalized sparse hashed vector for lexical retrieval."""
    counts = Counter(_features(text))
    if not counts:
        return {}

    vector = {}
    for feature, count in counts.items():
        index = str(
            int.from_bytes(blake2b(feature.encode("utf-8"), digest_size=8).digest(), "big")
            % VECTOR_DIMENSIONS
        )
        vector[index] = vector.get(index, 0.0) + 1.0 + math.log(count)

    norm = math.sqrt(sum(value * value for value in vector.values()))
    if not norm:
        return {}
    return {index: round(value / norm, 7) for index, value in vector.items()}


def rank_chunks(query, rows, limit=4, minimum_score=0.08):
    """Rank rows shaped as (chunk_id, document_id, filename, chunk_index,
    page_number, content, embedding_json) against a user query.
    """
    query_vector = embed_text(query)
    if not query_vector:
        return []

    ranked = []
    for row in rows:
        try:
            stored_vector = json.loads(row[6] or "{}")
            if not isinstance(stored_vector, dict):
                continue
            score = sum(
                query_weight * float(stored_vector.get(index, 0.0))
                for index, query_weight in query_vector.items()
            )
        except (TypeError, ValueError, json.JSONDecodeError):
            continue

        if score < minimum_score:
            continue
        ranked.append({
            "chunk_id": row[0],
            "document_id": row[1],
            "filename": row[2],
            "chunk_index": row[3],
            "page_number": row[4],
            "content": row[5],
            "score": round(score, 4),
        })

    ranked.sort(key=lambda item: (-item["score"], item["document_id"], item["chunk_index"]))
    return ranked[:max(1, int(limit))]
