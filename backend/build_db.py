# build_db.py
import pandas as pd
import requests
from bs4 import BeautifulSoup
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# --- Load CSV ---
df = pd.read_csv("backend/SB_publication_PMC.csv")

docs_csv = []
for _, row in df.iterrows():
    try:
        # Try fetching the linked page for abstract/description
        r = requests.get(row['Link'], timeout=10, verify=False)
        soup = BeautifulSoup(r.text, "html.parser")
        text = " ".join([p.get_text() for p in soup.find_all("p")])
        if not text.strip():
            text = row['Title']  # fallback if no <p> found
    except Exception:
        text = row['Title']  # fallback if request fails

    docs_csv.append(
        Document(
            page_content=f"{row['Title']}. {text}",
            metadata={"url": row['Link'], "source": "CSV"}
        )
    )

# --- Scrape Webpages ---
urls = {
    "OSDR": "https://osdr.nasa.gov/bio/repo/search?q=&data_source=cgene,alsda,esa&data_type=study",
    "NSLSL": "https://public.ksc.nasa.gov/nslsl/",
    "Taskbook": "https://taskbook.nasaprs.com/tbp/welcome.cfm"
}

docs_web = []
for name, url in urls.items():
    try:
        r = requests.get(url, timeout=15, verify=False)
        soup = BeautifulSoup(r.text, "html.parser")
        text = " ".join([p.get_text() for p in soup.find_all("p")])
        docs_web.append(
            Document(page_content=text, metadata={"source": name, "url": url})
        )
    except Exception as e:
        print(f"❌ Failed to fetch {url}: {e}")

# --- Combine ---
all_docs = docs_csv + docs_web

# --- Chunk ---
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
docs_chunks = splitter.split_documents(all_docs)

# --- Store in Chroma ---
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vector_db = Chroma.from_documents(
    docs_chunks,
    embedding=embeddings,
    persist_directory="spacebio_chroma"
)
vector_db.persist()

print("✅ Vector DB built and saved in spacebio_chroma/")
