from fastapi import FastAPI

app = FastAPI(
    title="Agno Agentic Service",
    version="0.1.0",
    description="A unified service for managing Agno AI agents and swarms.",
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Agno Agentic Service"}

@app.get("/health")
def health_check():
    return {"status": "ok"}