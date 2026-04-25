from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints.pipeline import router as pipeline_router
from app.api.endpoints.users import router as users_router

app = FastAPI(title="Virtual Try-On API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pipeline_router)
app.include_router(users_router)

@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}

@app.get("/")
async def root():
    return {"message": "Virtual Try-On API"}