from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configure CORS: Cannot read it from sveltekit unless this is set.
origins = [
    "https://eftk.vercel.app",
    "http://eftk.vercel.app",
    "http://localhost",
    "https://localhost",
    "http://localhost:5173",
    "http://localhost:5174",
    "https://eftokyo5-5nae106id-ohmaye.vercel.app",
    # Add more allowed origins as needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
