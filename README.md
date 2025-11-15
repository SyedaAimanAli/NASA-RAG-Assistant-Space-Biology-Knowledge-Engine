# NASA RAG Assistant — Space Biology Knowledge Engine

**Team:** GalactiDevs  
**Author:** Aiman Ali  

---

## Project Overview

NASA RAG Assistant is an AI-powered knowledge engine built to make NASA’s space biology research and data more accessible and interactive. The system combines **retrieval** (searching through NASA’s open science data) with **generation** (summarizing and explaining results) to let users ask questions and instantly get data-backed insights.

- Uses **RAG (Retrieval-Augmented Generation)** workflows  
- Backend: Python, FastAPI, LangChain, Chroma, Gemini  
- Frontend: React + Vite  
- Visual component: relevance charts to show similarity and importance  
- Documents panel: clickable study links and snippets  

---

## Features

- Ask natural language questions (e.g. “How does microgravity affect human cells?”)  
- AI generates a concise, context-aware answer  
- Sidebar “Documents” panel shows top retrieved studies with title, snippet, and URL  
- Sidebar “Studies / Chart” panel visualizes a relevance chart  
- Click on the chart to enlarge for better viewing  
- Clean formatting: bold/italic styling instead of raw markdown  
- Fallback to NASA’s central data repository link if no direct URL for a study  

---

