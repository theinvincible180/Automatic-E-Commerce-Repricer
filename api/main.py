from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import products, prices, pipeline

app = FastAPI(
    title="Repricer Agent API",
    description="Backend API for the Autonomous E-Commerce Repricer",
    version="1.0.0"
)

# CORS middleware — browsers block JavaScript from calling APIs
# on a different origin (domain/port) by default. Since React
# runs on localhost:5173 and our API on localhost:8000, they're
# different origins, so we must explicitly allow it here.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",   # fallback
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router)
app.include_router(prices.router)
app.include_router(pipeline.router)


@app.get("/")
def root():
    return {"status": "Repricer Agent API is running."}