
from google import genai
from google.genai import types
from sqlalchemy import select

from app.config import GEMINI_API_KEY, GEMINI_EMBEDDING_MODEL
from app.db import Base, SessionLocal, engine
from app.models import KnowledgeChunk, User

Base.metadata.create_all(bind=engine)

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing.")

client = genai.Client(api_key=GEMINI_API_KEY)

USERS = [
    dict(name="Demo User 1", email="demo1@example.com", phone="+1-202-555-0101",
         department="Engineering", job_title="Senior Software Engineer", location="Delhi"),
    dict(name="Demo User 2", email="demo2@example.com", phone="+1-202-555-0102",
         department="Human Resources", job_title="HR Manager", location="Bengaluru"),
]

KNOWLEDGE = [
    ("employee-handbook.md", "Annual Leave Policy",
     "Full-time employees receive 24 days of annual paid leave per calendar year. Leave requests should normally be submitted at least 3 working days before the first day of leave."),
    ("employee-handbook.md", "Work From Home Policy",
     "Employees may work from home up to 2 days per week with manager approval. Teams with on-site operational requirements may have different schedules documented by their department."),
    ("security-policy.md", "Password Policy",
     "Company passwords must be at least 14 characters long. Employees must not reuse their company password on personal services."),
    ("engineering-handbook.md", "Production Deployment",
     "Production deployments require a reviewed pull request, passing automated tests, and approval from the service owner. Emergency changes must be documented after deployment."),
    ("engineering-handbook.md", "Code Review Policy",
     "Every production code change must have at least one reviewer. Changes affecting authentication, authorization, or payment logic require two reviewers."),
]

def embed(text):
    result = client.models.embed_content(
        model=GEMINI_EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(output_dimensionality=768),
    )
    return list(result.embeddings[0].values)

with SessionLocal() as db:
    for data in USERS:
        if not db.scalar(select(User).where(User.email == data["email"])):
            db.add(User(**data))
    db.commit()

    if db.scalar(select(KnowledgeChunk).limit(1)) is None:
        for source, title, content in KNOWLEDGE:
            db.add(KnowledgeChunk(
                source=source,
                title=title,
                content=content,
                embedding=embed(title + "\n" + content),
            ))
        db.commit()

print("Seed complete. Demo users: 1=Demo User 1, 2=Demo User 2. Knowledge chunks: 5.")
