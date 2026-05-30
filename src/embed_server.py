import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

app = FastAPI(title="PraxisIQ Embedding Server")

# Load model once at startup
model = SentenceTransformer("all-MiniLM-L6-v2")


class EmbedRequest(BaseModel):
    text: str


@app.post("/embed")
def embed_text(request: EmbedRequest) -> dict[str, list[float]]:
    try:
        # Ensure input is not empty
        if not request.text or not request.text.strip():
            raise ValueError("Text must not be empty")
        vector = model.encode(request.text).tolist()
        return {"embedding": vector}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)
