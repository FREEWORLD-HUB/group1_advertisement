from fastapi import FastAPI
import cloudinary
from routes.adverts import adverts_router
from routes.users import users_router
import os
from dotenv import load_dotenv

load_dotenv

# configuring cloudinary
cloudinary.config(
    cloud_name=os.getenv("dhqwkwo8e"),
    api_key=os.getenv("544878511352217"),
    api_secret=os.getenv("DB2whHclPE2tpDECsKPQNRq7G0Y")
)

app = FastAPI(title= "kool kit Advertisement app", version= "1.0.0")

@app.get("/")
def get_home():
    return{"message": "Welcome to the Advertisement API"}

# include the adverts router
app.include_router (adverts_router)
app.include_router(users_router)