from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from db.database import create_tables
from routers import player_routes, roster_routes

app = FastAPI(title="NBA Roster Analytics API",
              version="0.1.0",
              docs_url="/docs",
              redoc_url="/redoc")

create_tables()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]

)

app.include_router(player_routes.router)
app.include_router(roster_routes.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    