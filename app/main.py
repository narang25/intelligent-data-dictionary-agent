from fastapi import FastAPI

app = FastAPI(title="Intelligent Data Dictionary Agent")

@app.get("/")
def root():
    return {"message": "JARVIS Data Dictionary is running"}
