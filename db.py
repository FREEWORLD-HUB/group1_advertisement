from pymongo import MongoClient
import os


from dotenv import load_dotenv

load_dotenv()

# connect to the Mongo Atlas cluster 
mongo_client = MongoClient(os.getenv("MONGO_URI"))

# access the database
advert_manager_db = mongo_client["advert_manager_db"]

# pick a collection to operate on
adverts_collection = advert_manager_db["adverts"]