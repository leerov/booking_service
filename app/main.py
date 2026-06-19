from fastapi import FastAPI
from app.api import router

app = FastAPI(title="Booking Service API")
app.include_router(router)

@app.get("/")
def root():
    return {"message": "Booking Service is running"}
