from fastapi import APIRouter, HTTPException, Request, Depends
from models import Recipe
from typing import List
from bson import ObjectId
from pymongo.collection import Collection

def get_recipes_collection(request: Request) -> Collection:
    return request.app.db["recipes"]

router = APIRouter()

def recipe_helper(recipe) -> dict:
    return {
        "_id": str(recipe["_id"]),
        "title": recipe["title"],
        "ingredients": recipe["ingredients"],
        "steps": recipe["steps"],
        "dietary_preference": recipe.get("dietary_preference", None),
        "favorite": recipe.get("favorite", False),
    }


@router.post("/add", response_model=Recipe)
async def add_recipe(recipe: Recipe, recipes: Collection = Depends(get_recipes_collection)):
    new_recipe = recipe.model_dump()
    result = await recipes.insert_one(new_recipe)
    created_recipe = await recipes.find_one({"_id": result.inserted_id})
    return recipe_helper(created_recipe)


@router.get("/list", response_model=List[Recipe])
async def list_recipes(recipes: Collection = Depends(get_recipes_collection)):
    recipes_cursor = recipes.find()
    recipes = await recipes_cursor.to_list(length=100)
    return [recipe_helper(recipe) for recipe in recipes]


@router.get("/{recipe_id}", response_model=Recipe)
async def get_recipe(recipe_id: str, recipes: Collection = Depends(get_recipes_collection)):
    recipe = await recipes.find_one({"_id": ObjectId(recipe_id)})
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe_helper(recipe)


@router.put("/{recipe_id}", response_model=Recipe)
async def update_recipe(recipe_id: str, recipe: Recipe, recipes: Collection = Depends(get_recipes_collection)):
    updated_recipe = await recipes.find_one_and_update(
        {"_id": ObjectId(recipe_id)},
        {"$set": recipe.model_dump(exclude_unset=True)},
        return_document=True,
    )
    if not updated_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe_helper(updated_recipe)


@router.delete("/{recipe_id}")
async def delete_recipe(recipe_id: str, recipes: Collection = Depends(get_recipes_collection)):
    delete_count = await recipes.delete_one({"_id": ObjectId(recipe_id)}).deleted_count
    if delete_count > 0:
        return {"message": "Recipe deleted successfully"}
    raise HTTPException(status_code=404, detail="Recipe not found")
    
