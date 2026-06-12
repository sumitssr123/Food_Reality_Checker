import os
import json
import time
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("CRITICAL: GEMINI_API_KEY is missing from the .env file!")

client = genai.Client(api_key=API_KEY)

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
    analyzed_quantity: str = Field(description="EXACT quantity analyzed (e.g., 'Per 100 grams' or '1 Standard Piece').")
    macronutrients: MacroProfile
    health_intelligence: HealthScore
    goal_alignment: str = Field(description="Strictly evaluate if this helps the user's SPECIFIC chosen goal.")
    healthy_alternatives: list[str] = Field(description="Top 3 super-detailed healthy whole-food alternatives with reasons.")
    deep_dive_details: list[str] = Field(description="5 detailed points about ingredients, digestion, and molecular impact.")

def analyze_food_engine(food_query: str = "Unknown", user_goal: str = "General Health", image_bytes: bytes = None, mime_type: str = None, mode: str = "food"):
    print(f"\n🧬 Mode: {mode.upper()} | Goal: {user_goal}")
    
    if mode == "ingredients":
        prompt_text = f"""
        Act as an Elite Clinical Nutritionist, Food Safety Auditor (FSSAI/FDA level), and Toxicologist.
        USER'S CURRENT HEALTH GOAL: "{user_goal}". 
        
        You are analyzing the ingredient label from a packaged food image. Your job is to brutally and accurately analyze these ingredients, leaving no hidden toxin, chemical, or marketing lie unchecked.
        
        CRITICAL INSTRUCTIONS:
        1. DYNAMIC GOAL ALIGNMENT: Strictly evaluate if this helps or hurts the "{user_goal}". If the goal is "Weight Loss" and it has maltodextrin/sugar, destroy it in the goal_alignment section.
        2. DECODE EVERY INS/E-NUMBER: Explicitly state what each code means (e.g., INS 471, INS 319, INS 150c) and its known health risks, side effects, or gut microbiome impact.
        3. RED FLAG OILS & TOXINS: Heavily penalize Palm Oil, Palmolein, Cottonseed Oil, Hydrogenated Fats (Trans Fats), Maltodextrin, High Fructose Corn Syrup, Invert Sugar, Liquid Glucose, and Artificial Sweeteners/Colors. Explain exactly why they are harmful (e.g., "Palm Oil raises LDL cholesterol and causes inflammation").
        4. STRICT RATING: Give a Health Rating out of 10. If it contains Palm Oil, Maida (Refined Wheat Flour), or Maltodextrin, the rating MUST be Poor (below 4). Expose marketing deception (e.g., "Baked not Fried" but uses Palm Oil).
        5. DISEASE-SPECIFIC WARNINGS: The `primary_warning` MUST flag specific medical risks. Use formats like: "⚠️ For Diabetics: [Reason]", "⚠️ For Heart Patients: [Reason]", "⚠️ For PCOS: [Reason]".
        6. Base all macronutrients on "Per 100 grams" default. State this clearly in `analyzed_quantity`.
        7. Suggest 3 whole-food, home-made, or natural alternatives to this packaged junk.
        """
    else:
        prompt_text = f"""
        Act as an Elite Clinical Nutritionist, Sports Dietitian, and Advanced Fitness Coach.
        USER'S CURRENT HEALTH GOAL: "{user_goal}". 
        
        Analyze this food item in extreme clinical detail, evaluating it strictly against the user's specific goal.
        
        CRITICAL INSTRUCTIONS:
        1. DYNAMIC GOAL-BASED SCORING: Your health rating (0.0 to 10.0) MUST adapt strictly to "{user_goal}". 
           - 'Build Muscle': Heavily reward high-quality protein and bioavailable nutrients. Do NOT penalize natural saturated fats (like in Paneer, Whole Milk, Whole Eggs, Ghee) as they support testosterone and muscle recovery. Score high-protein whole foods high (8.0-10.0).
           - 'Weight Loss': Penalize high caloric density and refined carbs. Reward high fiber, protein, and low-calorie volume.
           - 'Clean Eating': Brutally penalize ultra-processed elements; reward single-ingredient organic whole foods.
        2. QUANTITY: Base all macros exactly on "Per 100 grams" unless it's a single clear item (like '1 medium apple'). State this strictly in `analyzed_quantity`.
        3. NUTRITIONAL GOLDMINE & DEEP DIVE: Detail specific biomechanical benefits. Identify specific vitamins, minerals, types of fiber, and healthy fats. Explain digestion time and glycemic index/load.
        4. DISEASE-SPECIFIC WARNINGS: The `primary_warning` MUST be clinical. Use formats like: "⚠️ For Diabetics: [Reason]", "⚠️ For Lactose Intolerant: [Reason]".
        5. Give a Health Rating out of 10 (Poor, Average, Good, Best, Excellent).
        6. Suggest 3 super-detailed healthy alternatives with clinical reasons.
        """

    if image_bytes:
        print("📸 Processing Image Upload...")
        contents = [
            prompt_text + "\nAnalyze the image provided.",
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        ]
    else:
        print(f"📝 Processing Text Query: {food_query}")
        contents = [prompt_text + f"\nAnalyze this food: {food_query}"]

    # Resilience Loop - Upgraded for High Traffic, Network Drops & SSL Hiccups
    max_retries = 5 
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
            error_message = str(e).lower()
            
            # Catching 503, Rate Limits, Disconnects, and SSL errors automatically
            if "503" in error_message or "unavailable" in error_message or "429" in error_message or "disconnected" in error_message or "connection" in error_message or "ssl" in error_message:
                if attempt < max_retries - 1:
                    wait_time = 4 ** attempt
                    print(f"⚠️ Google Network Drop/SSL Hiccup. Retrying in {wait_time} seconds (Attempt {attempt+1}/{max_retries})...")
                    time.sleep(wait_time)
                    continue 
            
            print(f"❌ Fatal Error: {str(e)}")
            return {"error": f"AI Engine Failure: {str(e)}"}