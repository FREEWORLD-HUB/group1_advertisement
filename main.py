from fastapi import FastAPI
import cloudinary
from routes.adverts import adverts_router
from routes.users import users_router
from routes.genai import genai_router
import os
from dotenv import load_dotenv

load_dotenv()

# configuring cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

app = FastAPI(title= "kol kit Advertisement app", version= "1.0.0")

@app.get("/")
def get_home():
    return{"message": "Welcome to the Advertisement API"}

# include the adverts router
app.include_router (adverts_router)
app.include_router(users_router)
app.include_router(genai_router)