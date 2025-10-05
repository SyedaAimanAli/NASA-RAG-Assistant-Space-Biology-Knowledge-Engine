# -------------------- Imports --------------------
import re
import time
import requests
from bs4 import BeautifulSoup
import difflib
import matplotlib.pyplot as plt
import urllib3
from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
# -------------------- FastAPI Wrapper --------------------
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# -------------------- Config --------------------
FETCH_K = 12
MMR_K = 10
TOP_N = 5
SIMILARITY_DEDUPE = 0.80
MODEL_NAME = "gemini-2.5-flash"

# -------------------- Utilities --------------------
def clean_text_simple(text: str) -> str:
    if not text:
        return ""
    t = re.sub(r"[^\x00-\x7F]+", " ", text)  # remove non-ASCII
    t = re.sub(r"\s+", " ", t).strip()
    return t.strip(" .")

def retrieve_docs(vector_db, query: str, fetch_k=FETCH_K, mmr_k=MMR_K):
    try:
        return vector_db.max_marginal_relevance_search_with_score(query, k=mmr_k, fetch_k=fetch_k)
    except Exception:
        try:
            docs = vector_db.similarity_search(query, k=fetch_k)
            return [(doc, float(i+1)) for i, doc in enumerate(docs)]

        except Exception:
            return []

def normalize_and_plot(results_with_scores, top_n=TOP_N, min_sim_thresh=0.1):
    """Generate a horizontal bar chart of relevance scores."""
    if not results_with_scores:
        print("No documents to plot.")
        return None

    docs_raw = [clean_text_simple(doc.page_content) for doc, _ in results_with_scores]

    # Deduplicate using cosine similarity
    vectorizer = TfidfVectorizer().fit_transform(docs_raw)
    sims_matrix = cosine_similarity(vectorizer)

    seen = set()
    unique_docs = []
    for i, doc in enumerate(docs_raw):
        if any(sims_matrix[i, j] > SIMILARITY_DEDUPE for j in seen):
            continue
        seen.add(i)
        unique_docs.append((results_with_scores[i][0], results_with_scores[i][1]))

    if not unique_docs:
        print("No relevant documents after deduplication.")
        return None

    # Compute simple relevance scores
    sims = [1.0 / (1.0 + float(dist)) for _, dist in unique_docs]
    titles = [clean_text_simple(d.page_content[:80]) for d, _ in unique_docs]

    # Sort and pick top_n
    selected = sorted(list(zip(titles, sims)), key=lambda x: x[1], reverse=True)[:top_n]
    titles_short = [t[:80] + "..." if len(t) > 80 else t for t, _ in selected]
    sims = [s for _, s in selected]

    # Plot
    plt.figure(figsize=(10, 5))
    bars = plt.barh(range(len(sims)), sims, color="#60a5fa")
    plt.yticks(range(len(titles_short)), titles_short, fontsize=8)
    plt.xlabel("Relevance Score", fontsize=11)
    plt.title("Top Related Experiments / Studies", fontsize=13, weight="bold")
    plt.gca().invert_yaxis()

    for bar, val in zip(bars, sims):
        plt.text(val + 0.01, bar.get_y() + bar.get_height() / 2, f"{val:.2f}", va="center", fontsize=8)

    plt.tight_layout()

    os.makedirs("static", exist_ok=True)
    chart_path = "static/relevance_chart.png"
    plt.savefig(chart_path, bbox_inches="tight")
    plt.close()
    return chart_path




# -------------------- LLM --------------------
def build_llm_pipeline(model_name=MODEL_NAME):
    return ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0.3,
        max_output_tokens=6144
    )

def answer_with_context(llm, query: str, docs, top_n=TOP_N) -> str:
    # ✅ Limit context to top_n docs and keep only first ~1200 chars to avoid overflow
    context_parts = []
    for d, _ in docs[:top_n]:
        chunk = clean_text_simple(d.page_content)
        context_parts.append(chunk[:800])  # trim long docs
    context = "\n\n".join(context_parts)

    prompt = (f"""
        You are a NASA space biology research assistant.
        Your task is to read the research studies in the provided context and produce
        a short, well-organized summary answering the user’s question.

        For each relevant study:
        - Include the study title (in bold if available)
        - Write 1–2 concise sentences describing its purpose or focus
        - Briefly mention the main result or discovery

        At the end, include a short concluding line summarizing how these studies collectively address the question.

        Question: {query}

        Context:
        {context}

        Now write the response as a professional yet clear summary.
        Use bullet points and scientific tone, not just a list of facts.
        """

    )

    try:
        out = llm.invoke(prompt)
        print("DEBUG RAW GEMINI OUTPUT:", out)

        # ✅ Extract Gemini output robustly
        if hasattr(out, "content") and out.content:
            if isinstance(out.content, str):
                return out.content.strip()
            if isinstance(out.content, list):
                texts = []
                for item in out.content:
                    if isinstance(item, dict) and "text" in item:
                        texts.append(item["text"])
                    elif isinstance(item, str):
                        texts.append(item)
                if texts:
                    return "\n".join(texts).strip()

        if hasattr(out, "text") and isinstance(out.text, str):
            return out.text.strip()

        # Fallback: stringify the whole object
        return str(out)

    except Exception as e:
        return f"[Error from Gemini: {e}]"
    


def run_rag_query(user_question: str):
    """Runs the retrieval-augmented generation pipeline."""
    embedding_fn = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vector_db = Chroma(persist_directory="spacebio_chroma", embedding_function=embedding_fn)
    llm = build_llm_pipeline(MODEL_NAME)

    # Retrieve docs
    docs_with_scores = retrieve_docs(vector_db, user_question, fetch_k=FETCH_K, mmr_k=MMR_K)
    answer = answer_with_context(llm, user_question, docs_with_scores, top_n=TOP_N)

    # Generate chart
    chart_path = normalize_and_plot(docs_with_scores, top_n=TOP_N)
    return answer, chart_path, docs_with_scores


 

# -------------------- Interactive Loop --------------------
def interactive_loop():
    print("Loading Chroma DB (spacebio_chroma)...")
    embedding_fn = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vector_db = Chroma(persist_directory="spacebio_chroma", embedding_function=embedding_fn)

    print(f"Loading LLM pipeline ({MODEL_NAME})...")
    llm = build_llm_pipeline(MODEL_NAME)

    while True:
        query = input("\n🛰️ Enter your query (or type 'exit' to quit): ").strip()
        if query.lower() in ["exit", "quit"]:
            print("Exiting interactive RAG.")
            break
        if not query:
            print("Please enter a valid query.")
            continue

        start = time.time()
        docs_and_scores = retrieve_docs(vector_db, query, fetch_k=FETCH_K, mmr_k=MMR_K)
        print(f"Retrieved {len(docs_and_scores)} candidate documents in {time.time() - start:.1f}s")
        if not docs_and_scores:
            print("No relevant docs found.")
            continue

        # Get LLM answer
        answer = answer_with_context(llm, query, docs_and_scores)
        print("\n💡 Answer:\n", answer)

        # Show chart
        print("\nGenerating relevance chart for the top results...")
        normalize_and_plot(docs_and_scores, top_n=TOP_N)
        

# -------------------- Entry --------------------
if __name__ == "__main__":
    interactive_loop()

