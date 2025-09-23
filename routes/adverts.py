from fastapi import Form, File, UploadFile, HTTPException, status, APIRouter, Depends
from db import adverts_collection
from bson.objectid import ObjectId
from utils import replace_mongo_id
from typing import Annotated
import cloudinary
import cloudinary.uploader
from dependencies.authn import is_authenticated
from dependencies.authz import has_roles



# create an advert router
adverts_router = APIRouter()


# Adverts endpoints
@adverts_router.get("/adverts")
def get_adverts(title="", description="", limit=10, skip=0):
    # get all adverts from the database
    adverts = adverts_collection.find(
        filter={
            "$or": [
                {"title": {"$regex": title, "$options": "i"}},
                {"description": {"$regex": description, "$options": "i"}},
            ]
        },
        limit=int(limit),
        skip=int(skip),
    ).to_list()
    # Return response
    return {"data": list(map(replace_mongo_id, adverts))}

@adverts_router.post("/adverts",dependencies=[Depends(has_roles(["host", "admin"]))])
def post_advert(
    title: Annotated[str, Form()],
    description: Annotated[str, Form()],
    flyer: Annotated[str, File ()],
    user_id: Annotated[str, Depends(is_authenticated)],
):
    # Ensure an advert with title and user_id combined does not exist
    advert_count = adverts_collection.count_documents(
        filter={"$and": [{"title": title}, {"owner": user_id}]}
    )
    if advert_count > 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Event with {title} and {user_id} already exist!",)
    
    # upload flyer to cloudinary
    upload_result = cloudinary.uploader.upload(flyer.file)
    print(upload_result) 
    # Debugging line to check upload result 

    # insert the event into the database
    adverts_collection.insert_one(
       { "title": title,
        "description": description,
        "flyer_url":upload_result.get("secure_url"),
        "owner": user_id
       }
    )
    # adverts_collection.insert_one(event.model_dump())
    return {"message": "Event added successfully"}

