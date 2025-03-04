import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import APIRouter
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../../.env"))

DATABASE_NAME = "recipe-manager"

@asynccontextmanager
async def lifespan(app):
    mongo_uri = os.getenv("MONGO_DB")
    app.mongodb_client = AsyncIOMotorClient(mongo_uri)
    app.db = app.mongodb_client[DATABASE_NAME]

    app.recipes = app.db['recipes']
    app.users = app.db['users']
    
    print("MongoDB connection established")
    yield
    
    app.mongodb_client.close()
    print("MongoDB connection closed")
