import logging
from fastapi import FastAPI
from app.api.endpoints import router as api_router
from app.api.telegram import router as telegram_router

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI()

@app.get('/')
def root():
    return {'message': 'Forex Trading Bot API'}

app.include_router(api_router, prefix='/api')
app.include_router(telegram_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}


