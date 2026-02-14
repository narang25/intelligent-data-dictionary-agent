from fastapi import FastAPI

from app.api.chat import router as chat_router
from app.api.health import router as health_router # type: ignore


app = FastAPI(title="Intelligent Data Dictionary Agent")

app.include_router(chat_router)
app.include_router(health_router)

@app.get("/")
def root():
    return {"message": "JARVIS Data Dictionary is running"}
