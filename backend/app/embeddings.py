
from google import genai
from google.genai import types
from .config import GEMINI_API_KEY, GEMINI_EMBEDDING_MODEL

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing.")

client = genai.Client(api_key=GEMINI_API_KEY)

def embed_text(text: str) -> list[float]:
    result = client.models.embed_content(
        model=GEMINI_EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(output_dimensionality=768),
    )
    return list(result.embeddings[0].values)
