import os
import json
import openai
from dotenv import load_dotenv
from typing import List
from fastapi import APIRouter, HTTPException
from models import GenerateItem

router = APIRouter()

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../../.env"))

openai_client = openai.OpenAI(api_key = os.getenv("OPENAI_API_KEY"))

@router.post("/generate-recipe", response_model = GenerateItem)
async def generate_ai_recipe(ingredients: List[str], dietary_preference: str = None):
    try:
        prompt = f"Create a unique recipe using {', '.join(ingredients)}."
        if dietary_preference:
            prompt += f" Ensure it follows {dietary_preference} dietary guidelines."
        
        prompt += "\n\nPlease also create a creative title for the recipe."

        prompt += "\nPlease create the response in the following format: \n" \
                  "{\n" \
                  " 'title': '<recipe-title>', \n" \
                  " 'ingredients': [<list of ingredients>], \n" \
                  " 'steps': [<list of recipe steps>] \n" \
                  "}"

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional helpful chef."},
                {"role": "user", "content": prompt}
            ]
        )

        recipe_text = response["choices"][0]["message"]["content"]

        try:
            recipe_dict = json.loads(recipe_text)
            title = recipe_dict.get('title')
            ingredients = recipe_dict.get('ingredients', [])
            steps = recipe_dict.get('steps', [])

            recipe = GenerateItem(
                title=title,
                ingredients=ingredients,
                steps=steps,
                dietary_preference=dietary_preference
            )
            return recipe

        except Exception as e:
            raise HTTPException(status_code=500, detail="Error parsing response from GPT")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
