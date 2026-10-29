
from sqlalchemy import select
from sqlalchemy.orm import Session
from .config import RAG_MIN_SIMILARITY, RAG_TOP_K
from .embeddings import embed_text
from .models import KnowledgeChunk

def retrieve_knowledge(db: Session, query: str) -> list[dict]:
    query_vector = embed_text(query)
    distance = KnowledgeChunk.embedding.cosine_distance(query_vector)
    rows = db.execute(
        select(KnowledgeChunk, distance.label("distance"))
        .order_by(distance)
        .limit(RAG_TOP_K)
    ).all()

    results = []
    for chunk, distance_value in rows:
        similarity = 1 - float(distance_value)
        if similarity >= RAG_MIN_SIMILARITY:
            results.append({
                "id": chunk.id,
                "source": chunk.source,
                "title": chunk.title,
                "content": chunk.content,
                "similarity": round(similarity, 4),
            })
    return results

def format_context(results: list[dict]) -> str:
    if not results:
        return "NO RELEVANT KNOWLEDGE BASE CONTEXT WAS FOUND."
    return "\n\n".join(
        f"[KB-{x['id']}] {x['title']} (source: {x['source']})\n{x['content']}"
        for x in results
    )
