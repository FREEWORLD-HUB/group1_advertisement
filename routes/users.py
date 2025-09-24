from fastapi import APIRouter, Form,HTTPException,status
from typing import Annotated
from pydantic import EmailStr
from db import users_collection
import bcrypt 
import jwt 
import os
from datetime import datetime,timezone, timedelta
from enum import Enum

# define a user role
class UserRole(str, Enum):
    ADMIN ="admin"
    HOST = "vendor"
    GUEST = "guest"



# Create users router
users_router = APIRouter()


# define endpoints here
@users_router.post("/users/register", tags= ["Users Sign up"])
def register_user(
    username: Annotated[str, Form()],
    email: Annotated[EmailStr, Form()],
    password: Annotated[str, Form(min_length=8)],
    role: Annotated[UserRole,Form()] = UserRole.GUEST,

):
    # Ensure user does not exist
    user_count = users_collection.count_documents(filter={"email": email})
    if user_count > 0:
        raise HTTPException(status.HTTP_409_CONFLICT,"user already exist!")
    # hash your password
    hasded_password = bcrypt.hashpw(password.encode,bcrypt.gensalt())
    # save user into the database
    users_collection.insert_one(
        {"username": username,
         "email": email,
         "password": hasded_password,
         "role": role,}
    )
    # return response
    return {"message": "User registerd successfully"}

# login a user
@users_router.post("/users/login", tags= ["User Login"])
def login_user(
    email: Annotated[str, Form()],
    password: Annotated[str, Form(min_length=8)]
):
    # Ensure user exist
    user = users_collection.find_one(filter={"email": email})
    if not user: 
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user does not exist!")
    # compare their password
    correct_password = bcrypt.checkpw(password.encode(), user["password"])
    if not correct_password:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials!")
    # Generate an acces token for the user
    encoded_jwt = jwt.encode(
        {"id": str (user["_id"]),
         "exp": datetime.now(tz=timezone.utc) + timedelta(seconds=3000)
         }, os.getenv("JWT_SECRET_KEY"),
         "HS256")
    # Return response
    return{"message": "user logged in successsfully!", "access_token": encoded_jwt}