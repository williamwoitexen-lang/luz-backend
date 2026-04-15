import uuid
import json
import numpy as np
from typing import List, Dict, Any
# from app.core.db import get_connection  # Legacy: not used anymore, using SQL Server directly


def insert_document(document_id: str, title: str, created_by: str, allowed_countries, allowed_cities, min_role_level, collar, plant_code):
    con = get_connection()
    con.execute(
        "INSERT INTO documents (document_id, title, created_by, allowed_countries, allowed_cities, min_role_level, collar, plant_code) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [document_id, title, created_by, json.dumps(allowed_countries) if allowed_countries else None, json.dumps(allowed_cities) if allowed_cities else None, min_role_level, collar, plant_code]
    )


def insert_version(version_id: str, document_id: str, version_number: int, file_path: str = None):
    con = get_connection()
    con.execute(
        "INSERT INTO versions (version_id, document_id, version_number, file_path) VALUES (?, ?, ?, ?)",
        [version_id, document_id, version_number, file_path]
    )


def insert_chunk(chunk_id: str, document_id: str, version_id: str, chunk_index: int, content: str, emb_bytes: bytes, min_role_level: int, allowed_countries, allowed_cities, created_by: str, collar: str, plant_code: int):
    con = get_connection()
    con.execute(
        "INSERT INTO chunks (chunk_id, document_id, version_id, chunk_index, content, embedding, min_role_level, allowed_countries, allowed_cities, created_by, collar, plant_code) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [chunk_id, document_id, version_id, chunk_index, content, emb_bytes, min_role_level, json.dumps(allowed_countries) if allowed_countries else None, json.dumps(allowed_cities) if allowed_cities else None, created_by, collar, plant_code]
    )


def delete_document(document_id: str):
    con = get_connection()
    con.execute("DELETE FROM chunks WHERE document_id = ?", [document_id])
    con.execute("DELETE FROM versions WHERE document_id = ?", [document_id])
    con.execute("DELETE FROM documents WHERE document_id = ?", [document_id])
    return True


def delete_document_version_by_number(document_id: str, version_number: int):
    con = get_connection()
    row = con.execute("SELECT version_id FROM versions WHERE document_id = ? AND version_number = ?", [document_id, version_number]).fetchone()
    if not row:
        raise ValueError(f"Versão {version_number} não existe para este documento")
    version_id = row[0]
    con.execute("DELETE FROM chunks WHERE version_id = ?", [version_id])
    con.execute("DELETE FROM versions WHERE version_id = ?", [version_id])
    return True


def get_version_file_path(document_id: str, version_number: int = None, version_id: str = None) -> str:
    """
    Get file path for a specific version.
    
    Args:
        document_id: ID do documento
        version_number: Número da versão (inteiro)
        version_id: ID da versão (UUID/string)
    
    If both are None, returns latest version.
    """
    con = get_connection()
    
    if version_id:
        # Search by version_id (UUID)
        row = con.execute(
            "SELECT file_path FROM versions WHERE document_id = ? AND version_id = ?",
            [document_id, version_id]
        ).fetchone()
    elif version_number is None:
        # Get latest version
        row = con.execute(
            "SELECT TOP 1 file_path FROM versions WHERE document_id = ? ORDER BY version_number DESC",
            [document_id]
        ).fetchone()
    else:
        # Search by version_number
        row = con.execute(
            "SELECT file_path FROM versions WHERE document_id = ? AND version_number = ?",
            [document_id, version_number]
        ).fetchone()
    
    if not row or not row[0]:
        raise FileNotFoundError(f"Arquivo não encontrado para documento {document_id}")
    return row[0]


def search_similar(q_emb: List[float], limit: int = 5) -> List[Dict[str, Any]]:
    # naive search: load all embeddings and compute cosine similarity
    con = get_connection()
    rows = con.execute(
        "SELECT d.title, v.version_number, c.chunk_index, c.content, c.embedding FROM chunks c JOIN versions v ON v.version_id = c.version_id JOIN documents d ON d.document_id = c.document_id"
    ).fetchall()

    results = []
    q_vec = np.array(q_emb, dtype=np.float32)

    for title, version_number, chunk_index, content, emb_blob in rows:
        emb_vec = np.frombuffer(emb_blob, dtype=np.float32)
        # guard against zero norms
        denom = (np.linalg.norm(q_vec) * np.linalg.norm(emb_vec))
        score = float(np.dot(q_vec, emb_vec) / denom) if denom != 0 else 0.0
        results.append({
            "title": title,
            "version_number": version_number,
            "chunk_index": chunk_index,
            "content": content,
            "score": score,
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]
