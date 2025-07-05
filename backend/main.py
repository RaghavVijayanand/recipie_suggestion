from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import requests
import base64
import json
import os
from typing import List, Dict, Any
import uvicorn

app = FastAPI(
    title="Free Food Recipe AI",
    description="A completely free food recipe generator using Qwen AI",
    version="1.0.0"
)

# Serve the frontend
frontend_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../frontend')
)
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenRouter configuration for Qwen
OPENROUTER_API_KEY = "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"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "qwen/qwen-2.5-72b-instruct"  # Free Qwen model

def call_qwen_api(messages: List[Dict[str, str]], max_tokens: int = 1500) -> str:
    """Call Qwen API through OpenRouter"""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",  # Required for OpenRouter
        "X-Title": "Free Food Recipe AI"
    }
    
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.7,
        "top_p": 0.9
    }
    
    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content']
        else:
            raise HTTPException(status_code=500, detail="Invalid response from AI model")
            
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"API request failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

def analyze_image_with_qwen(image_base64: str) -> List[str]:
    """Analyze image to detect ingredients using Qwen vision model"""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Analyze this image and identify all the food ingredients you can see. List them as a comma-separated list. Focus on identifying specific ingredients like vegetables, fruits, meats, spices, etc. Be specific but concise."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}"
                    }
                }
            ]
        }
    ]
    
    try:
        # For vision tasks, we'll use a vision-capable model
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Free Food Recipe AI"
        }
        
        payload = {
            "model": "qwen/qwen-2-vl-72b-instruct",  # Vision model
            "messages": messages,
            "max_tokens": 500,
            "temperature": 0.3
        }
        
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        if 'choices' in result and len(result['choices']) > 0:
            ingredients_text = result['choices'][0]['message']['content']
            # Parse the comma-separated ingredients
            ingredients = [ingredient.strip() for ingredient in ingredients_text.split(',')]
            return [ingredient for ingredient in ingredients if ingredient]
        else:
            return []
            
    except Exception as e:
        print(f"Vision analysis failed: {e}")
        # Fallback: return empty list if vision fails
        return []

@app.get("/")
async def root():
    """Serve the main page"""
    frontend_file = os.path.join(frontend_dir, "index.html")
    return FileResponse(frontend_file)

@app.post("/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    """Analyze uploaded image to detect ingredients"""
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read and encode image
        content = await file.read()
        image_base64 = base64.b64encode(content).decode('utf-8')
        
        # Analyze image with Qwen
        ingredients = analyze_image_with_qwen(image_base64)
        
        return {
            "success": True,
            "ingredients": ingredients,
            "message": f"Detected {len(ingredients)} ingredients"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")

@app.post("/generate-recipes")
async def generate_recipes(request: Dict[str, Any]):
    """Generate recipes based on ingredients"""
    try:
        ingredients = request.get("ingredients", [])
        dietary_preferences = request.get("dietary_preferences", [])
        cuisine_type = request.get("cuisine_type", "any")
        servings = request.get("servings", 2)
        
        if not ingredients:
            raise HTTPException(status_code=400, detail="No ingredients provided")
        
        # Create prompt for recipe generation
        ingredients_text = ", ".join(ingredients)
        dietary_text = ", ".join(dietary_preferences) if dietary_preferences else "none"
        
        prompt = f"""
        I have these ingredients: {ingredients_text}

        Please generate 3 different recipes that I can make with these ingredients. For each recipe, provide:
        1. Recipe name
        2. Estimated cooking time
        3. Difficulty level (Easy/Medium/Hard)
        4. Complete ingredient list (including any common pantry items needed)
        5. Step-by-step cooking instructions
        6. Serving size for {servings} people
        
        Additional preferences:
        - Dietary restrictions: {dietary_text}
        - Cuisine preference: {cuisine_type}
        
        IMPORTANT: Respond ONLY with a valid JSON array. Do not include any other text, explanations, or markdown code blocks.
        
        Format:
        [
          {{
            "name": "Recipe Name",
            "cooking_time": "X minutes",
            "difficulty": "Easy",
            "servings": {servings},
            "ingredients": ["ingredient 1", "ingredient 2"],
            "instructions": ["Step 1", "Step 2"],
            "cuisine_type": "cuisine name"
          }}
        ]
        """
        
        messages = [
            {
                "role": "system",
                "content": "You are a professional chef and recipe expert. You MUST respond with valid JSON format only. Do not include any markdown code blocks, explanations, or other text. Only return the raw JSON array."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        # Call Qwen API
        response = call_qwen_api(messages, max_tokens=2000)
        
        # Try to parse JSON response
        try:
            # Clean the response - remove markdown code blocks if present
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response.replace('```json', '', 1)
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response.rsplit('```', 1)[0]
            cleaned_response = cleaned_response.strip()
            
            recipes = json.loads(cleaned_response)
            if not isinstance(recipes, list):
                raise ValueError("Response is not a list")
        except (json.JSONDecodeError, ValueError) as e:
            # If JSON parsing fails, create a structured response
            print(f"JSON parsing failed: {e}")
            print(f"Raw response: {response}")
            recipes = [
                {
                    "name": "AI-Generated Recipe",
                    "cooking_time": "30 minutes",
                    "difficulty": "Medium",
                    "servings": servings,
                    "ingredients": ingredients,
                    "instructions": [response],
                    "cuisine_type": cuisine_type
                }
            ]
        
        return {
            "success": True,
            "recipes": recipes,
            "total_recipes": len(recipes)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recipe generation failed: {str(e)}")

@app.post("/ingredients-to-recipes")
async def ingredients_to_recipes(request: Dict[str, Any]):
    """Direct ingredient list to recipe conversion"""
    try:
        ingredients_text = request.get("ingredients", "")
        
        if not ingredients_text.strip():
            raise HTTPException(status_code=400, detail="No ingredients provided")
        
        # Parse ingredients from text
        ingredients = [ingredient.strip() for ingredient in ingredients_text.split(',')]
        
        # Generate recipes
        recipe_request = {
            "ingredients": ingredients,
            "dietary_preferences": request.get("dietary_preferences", []),
            "cuisine_type": request.get("cuisine_type", "any"),
            "servings": request.get("servings", 2)
        }
        
        return await generate_recipes(recipe_request)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "model": MODEL_NAME, "api": "OpenRouter"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
