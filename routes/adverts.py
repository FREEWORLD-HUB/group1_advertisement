from fastapi import Form, File, UploadFile, HTTPException, status, APIRouter, Depends
from db import adverts_collection
from bson.objectid import ObjectId
from utils import replace_mongo_id, genai_client
from google.genai import types
from typing import Annotated
import cloudinary
import cloudinary.uploader
from dependencies.authn import is_authenticated
from dependencies.authz import has_roles


# create an advert router
adverts_router = APIRouter()


# Adverts endpoints
@adverts_router.get("/adverts")
def get_adverts(title="", description="", limit=50, skip=0):
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


@adverts_router.get("/adverts/{advert_id}/similar")
def get_similar_adverts(advert_id, limit=10, skip=0):
    # check if advert is valid
    if not ObjectId.is_valid(advert_id):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "Invalid mongo id received"
        )

    # Get advert from database by id
    advert = adverts_collection.find_one({"_id": ObjectId(advert_id)})
    # Get similar adverts from database
    advert = adverts_collection.find(
        filter={
            "$or": [
                {"title": {"$regex": advert["title"], "$options": "i"}},
                {"description": {"$regex": advert["description"], "$options": "i"}},
            ]
        },
        limit=int(limit),
        skip=int(skip),
    ).to_list()
    # returns response
    return {"data": list(map(replace_mongo_id, advert))}


@adverts_router.post("/adverts", dependencies=[Depends(has_roles(["vendor", "admin"]))])
def post_advert(
    title: Annotated[str, Form()],
    company: Annotated[str, Form()],
    description: Annotated[str, Form()],
    price: Annotated[str, Form()],
    job_type: Annotated[str, Form()],
    user_id: Annotated[str, Depends(is_authenticated)],
    image: Annotated[bytes, File()] = None,
):
    if not image:
        # generate AI image
        response = genai_client.models.generate_images(
            model="imagen-4.0-generate-001",
            prompt=title,
            config=types.GenerateImagesConfig(number_of_images=1),
        )
        image = response.generated_images[0].image.image_bytes
    # Ensure an advert with title and user_id combined does not exist
    advert_count = adverts_collection.count_documents(
        filter={"$and": [{"title": title}, {"owner": user_id}]}
    )
    if advert_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Event with {title} and {user_id} already exist!",
        )

    # upload flyer to cloudinary
    upload_result = cloudinary.uploader.upload(image)
    print(upload_result)
    # Debugging line to check upload result

    # insert the event into the database
    adverts_collection.insert_one(
        {
            "title": title,
            "company": company,
            "price": price,
            "description": description,
            "job_type": job_type,
            "image": upload_result["secure_url"],
            "owner": user_id,
        }
    )
    # adverts_collection.insert_one(event.model_dump())
    return {"message": "Event added successfully"}


@adverts_router.get("/adverts/{advert_id}")
def get_advert_by_id(advert_id):
    # check if advert id is valid
    if not ObjectId.is_valid(advert_id):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid mongo id received!",
        )

    # get advert from database by id
    advert = adverts_collection.find_one({"_id": ObjectId(advert_id)})
    # Return response
    return {"data": replace_mongo_id(advert)}


@adverts_router.put("/adverts/{advert_id}")
def replace_advert(
    advert_id,
    title: Annotated[str, Form()],
    description: Annotated[str, Form()],
    user_id: Annotated[str, Form()],
    image: Annotated[bytes, Form()] = None,
):
    # check if event_id  is valid mongo id
    if not ObjectId.is_valid(advert_id):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invalid mongo id received!"
        )

    if not image:
        # generate AI image
        response = genai_client.models.generate_images(
            model="imagen-4.0-generate-001",
            prompt=title,
            config=types.GenerateImagesConfig(number_of_images=1),
        )
        image = response.generated_images[0].image.image_bytes

    # upload to cloudinary to the a url
    Upload_result = cloudinary.uploader.upload(image)
    # Replace advert in database
    replace_result = adverts_collection.replace_one(
        filter={"_id": ObjectId(advert_id), "owner": user_id},
        replacement={
            "title": title,
            "description": description,
            "image_url": Upload_result.get["secure_url"],
            "owner": user_id,
        },
    )
    if not replace_result.modified_count:
        raise HTTPException(status.HTTP_404_NOT_FOUND, " no event found!")
    # Return response
    return {"message": "Event replaced successfully"}


@adverts_router.delete("/adverts/{advert_id}")
def delete_advert(advert_id, user_id: Annotated[str, Depends(is_authenticated)]):
    # check if event_id is valid mongo id
    if not ObjectId.is_valid(advert_id):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invalid mongo id received"
        )
    # Delete event from database
    delete_result = adverts_collection.delete_one(
        filter={"_id": ObjectId(advert_id), "owner": user_id}
    )
    # Return response
    if not delete_result.deleted_count:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="invalid mongo id received!"
        )
    return {"message": "Event deleted successfully!"}
