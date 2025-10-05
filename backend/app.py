from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# import your RAG pipeline pieces
from .query_rag_interactive_updated import run_rag_query, TOP_N
from fastapi.staticfiles import StaticFiles
import os
import re
from fastapi.responses import JSONResponse


# Serve static files (charts, images, etc.)



# ---------------------------
# Setup FastAPI
# ---------------------------
app = FastAPI()

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Allow frontend (React) to call backend (CORS fix)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # change to ["http://localhost:3000"] for stricter setup
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# Input schema
# ---------------------------
class Query(BaseModel):
    question: str

# ---------------------------
# Route for RAG pipeline
# ---------------------------


@app.post("/ask")
def ask_rag(query: Query):
    print("Received query:", query.question)
    try:
        # Run the RAG pipeline
        answer, chart_path, docs_with_scores = run_rag_query(query.question)

        # === Text Cleanup ===
        def clean_text(text: str) -> str:
            # Remove bullet markers (* or •)
            text = re.sub(r"[\*\•]\s*", "", text)
            # Convert **bold** markdown to <b>
            text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
            # Convert *italic* markdown to <i>
            text = re.sub(r"\*(.*?)\*", r"<i>\1</i>", text)
            # Remove any double spaces and trim
            return re.sub(r"\s{2,}", " ", text).strip()

        cleaned_answer = clean_text(answer)

        # === Build Document Payload ===
        docs_payload = []
        NASA_REPO_BASE = "https://github.com/jgalazka/SB_publications/blob/main/SB_publication_PMC.csv"  # base link to repository

        for i, (doc, score) in enumerate(docs_with_scores[:TOP_N]):
            # Try to get the original source file or fallback
            source_file = doc.metadata.get("source", "")
            if source_file:
                # If the source is a filename, make it look like a real repository file
                # e.g., "study_42.pdf" -> https://nasa-openscience-data-repository.gov/space-biology/study_42.pdf
                source_url = f"{NASA_REPO_BASE}"
                # /{source_file.replace(' ', '%20')}"
            elif "url" in doc.metadata:
                source_url = doc.metadata["url"]
            else:
                # fallback to repository main dataset with a unique anchor
                source_url = f"{NASA_REPO_BASE}#doc={i+1}"

            docs_payload.append({
                "id": str(i + 1),
                "title": doc.metadata.get("title", f"Study {i+1}"),
                "score": round(score, 2),
                "snippet": clean_text(doc.page_content[:200]) + "...",
                "url": source_url
            })

        # === Chart URL ===
        chart_url = f"http://127.0.0.1:8000/{chart_path}" if chart_path else None

        return JSONResponse(content={
            "answer": cleaned_answer,
            "docs": docs_payload,
            "chart": chart_url
        })

    except Exception as e:
        print("❌ Error in /ask:", e)
        return JSONResponse(content={"error": str(e)}, status_code=500)





# @app.post("/ask")
# def ask_rag(query: Query):
#     """
#     Receive a question from frontend and return RAG pipeline answer.
#     """
#     try:
#         answer, chart_path = run_rag_query(query.question)
#         return {
#             "answer": answer,
#             "chart": chart_path if chart_path else None
#         }
#     except Exception as e:
#         return {"error": str(e)}

# ---------------------------
# Run if executed directly
# ---------------------------
if __name__ == "__main__":
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=True)
