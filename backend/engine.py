import os
import json
import time
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# 1. Configuration & Security
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("CRITICAL: GEMINI_API_KEY is missing from the .env file!")

client = genai.Client(api_key=API_KEY)

# ==========================================
# 2. HEALTHY INDIA DATA SCHEMAS
# ==========================================
class HealthScore(BaseModel):
    rating_out_of_10: float = Field(description="Rate healthiness from 0.0 to 10.0")
    rating_label: str = Field(description="Must be: Poor, Average, Good, Best, or Excellent")
    primary_benefit: str
    primary_warning: str = Field(description="Highlight toxic ingredients like Palm Oil, Maida, Emulsifiers (E471), Maltodextrin, High Sugar if present.")

class MacroProfile(BaseModel):
    calories: int
    protein_g: float
    fats_g: float
    carbs_g: float

class ProFoodAnalysis(BaseModel):
    query_name: str = Field(description="Name of the food or product")
    analyzed_quantity: str
    macronutrients: MacroProfile
    health_intelligence: HealthScore
    goal_alignment: str
    healthy_alternatives: list[str] = Field(description="Top 3 super-detailed healthy whole-food alternatives with reasons.")
    deep_dive_details: list[str] = Field(description="5 detailed points about ingredients, digestion, and molecular impact.")

# ==========================================
# 3. THE DUAL-MODE ENGINE
# ==========================================
def analyze_food_engine(food_query: str = "Unknown", user_goal: str = "General Health", image_bytes: bytes = None, mime_type: str = None, mode: str = "food"):
    print(f"\n🧬 Mode: {mode.upper()} | Goal: {user_goal}")
    
    # AI Prompt changes based on the mode
    if mode == "ingredients":
        prompt_text = f"""
        Act as a strict Food Safety Auditor and Toxicologist for the 'Healthy India' initiative. 
        Analyze the ingredient list from this packaged food image.
        User Goal: {user_goal}
        
        CRITICAL INSTRUCTIONS:
        1. Identify harmful ingredients (Palm Oil, Refined Wheat/Maida, Maltodextrin, Emulsifiers like E471, Hidden Sugars, Preservatives).
        2. Give a strict Health Rating out of 10. If it has Palm Oil, Maida, or Maltodextrin, the rating MUST be Poor (below 4).
        3. Explain the primary warning in detail, naming the exact toxic chemicals.
        4. Suggest 3 whole-food, home-made, or natural alternatives to this packaged junk.
        """
    else:
        prompt_text = f"""
        Act as a Master Clinical Nutritionist. Analyze this food item in extreme detail.
        User Goal: {user_goal}
        
        Instructions:
        1. Provide deep molecular details, digestion impact, and history.
        2. Give a Health Rating out of 10 (Poor, Average, Good, Best, Excellent).
        3. Suggest 3 detailed healthy alternatives.
        """

    # Build Payload
    if image_bytes:
        print("📸 Processing Image Upload...")
        contents = [
            prompt_text + "\nAnalyze the image provided.",
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        ]
    else:
        print(f"📝 Processing Text Query: {food_query}")
        contents = [prompt_text + f"\nAnalyze this food: {food_query} (Assume standard portion)."]

    # Resilience Loop
    max_retries = 3 
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash', 
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ProFoodAnalysis,
                    temperature=0.1, 
                ),
            )
            print("✅ Analysis Complete!")
            return json.loads(response.text)
        except Exception as e:
            error_message = str(e)
            if "503" in error_message or "UNAVAILABLE" in error_message or "429" in error_message:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"⚠️ Server busy. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue 
            print(f"❌ Fatal Error: {error_message}")
            return {"error": f"AI Engine Failure: {error_message}"}