import os
import json
import time
import io
from PIL import Image, ImageEnhance
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("CRITICAL: GEMINI_API_KEY is missing from the .env file!")

client = genai.Client(api_key=API_KEY)

# --- 1. ULTRA-ACCURATE IMAGE PROCESSING (Zero Text Blur) ---
def compress_image_bytes(image_bytes: bytes, mode: str) -> tuple[bytes, str]:
    try:
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        
        # Max resolution set to 1080p (Perfect for fast upload but retains detail)
        img.thumbnail((1280, 1280))
        
        # CRITICAL FOR INGREDIENTS: Boost sharpness & contrast to make tiny text 100% legible for AI
        if mode == "ingredients":
            img = ImageEnhance.Sharpness(img).enhance(2.5)
            img = ImageEnhance.Contrast(img).enhance(1.2)
            print("🔬 Image enhanced with High-Contrast Sharpness for perfect OCR parsing.")
            
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=85, optimize=True)
        
        size_kb = len(output.getvalue()) / 1024
        print(f"✅ Image Optimized: {size_kb:.1f} KB (Network-Safe & Crystal Clear)")
        return output.getvalue(), "image/jpeg"
    except Exception as e:
        print(f"⚠️ Compression Failed: {e}. Sending original image.")
        return image_bytes, "image/jpeg"

# --- 2. THE ULTRA-STRICT MEDICAL DATA SCHEMAS ---
class HealthScore(BaseModel):
    rating_out_of_10: float = Field(description="EXACT ALGORITHMIC SCORING. Never round off to 5.0. Output precise decimals (e.g., 9.5, 9.2, 8.9, 2.1) strictly based on the user's goal and biochemical markers. Bad food MUST be below 4.0. Nutrient-dense whole foods MUST be above 8.5.")
    rating_label: str = Field(description="Must be exactly one of: Terrible, Poor, Average, Good, Best, or Excellent.")
    primary_benefit: str = Field(description="Highly specialized medical analysis of benefits. CRITICAL RULE: You MUST state any actual benefits present (e.g., 'Contains 5g of protein and calcium for bone health'). Even if it is a bad/junk product, acknowledge these nutrients FIRST, but then clearly state: 'However, despite these trace benefits, the overall product is unhealthy/not recommended because...'.")
    primary_warning: str = Field(description="MANDATORY CLINICAL FORMAT: '⚠️ If you have [Condition like Diabetes, High BP, PCOS, Fatty Liver, IBS], then you MUST avoid this because [Exact scientific mechanism of harm].'")

class MacroProfile(BaseModel):
    calories: int
    protein_g: float
    fats_g: float
    carbs_g: float

class ProFoodAnalysis(BaseModel):
    is_recognized_target: bool = Field(description="Set False ONLY if the image does not contain text/label (in ingredients mode) or recognizable food (in food mode).")
    recognition_error: str = Field(description="If is_recognized_target is False, state the exact reason here. Else 'None'.")
    query_name: str = Field(description="Scientific or commercial name. CRITICAL RULE: In 'ingredients' mode, if you only see an ingredient list and NO brand packaging, DO NOT GUESS the product name (e.g., do not guess 'Tomato Ketchup'). Just output 'Analyzed Ingredient Label' or 'Packaged Food List'.")
    analyzed_quantity: str = Field(description="Exact reference frame analyzed (e.g., 'Per 100 grams'). ALL MACROS MUST BE BASED ON THIS QUANTITY.")
    macronutrients: MacroProfile
    health_intelligence: HealthScore
    goal_alignment: str = Field(description="A deep, critical explanation of how this food biologically aligns with or completely contradicts the chosen health goal. Expose marketing deception here.")
    healthy_alternatives: list[str] = Field(description="Top 3 clean, bioavailable whole-food alternatives with exact clinical justifications for the user's goal.")
    deep_dive_details: list[str] = Field(description="5 highly advanced, extensive bullet points. Break down exact molecular impacts of INS codes/preservatives, digestion kinetics, blood sugar impact, and gut microbiome health.")

# --- 3. THE MASTER RE-ENGINEERED PROMPTS ---
def analyze_food_engine(food_query: str = "Unknown", user_goal: str = "General Health", image_bytes: bytes = None, mime_type: str = None, mode: str = "food"):
    print(f"\n🧬 Mode: {mode.upper()} | Goal: {user_goal}")
    
    if mode == "ingredients":
        prompt_text = f"""
        ROLE: Supreme FSSAI/FDA Toxicologist, Clinical Biochemist, and Medical Auditor.
        CURRENT USER HEALTH GOAL: "{user_goal}".
        
        🔴 IMAGE VALIDATION (CRITICAL RULE):
        You are strictly an INGREDIENT AUDITOR. If the image provided is NOT a nutritional label, ingredient list, or food packaging with text, YOU MUST set `is_recognized_target` to false and set `recognition_error` to "Please upload a clear ingredient label or packaging text."
        
        CRITICAL MANDATE: Scan EVERY single character on the label image with 100% precision. 

        🔴 DETAILED INGREDIENT JUDGMENT PROTOCOL:
        1. NO GUESSING RULE: If you are only looking at an ingredient list or nutritional table, DO NOT assume or guess what the actual product is (like 'Ketchup' or 'Oat Milk'). Just analyze the chemicals and ingredients present.
        2. ACKNOWLEDGE TRACE BENEFITS: Even if the product is toxic, if it has protein, calcium, or vitamins, mention them in the 'primary_benefit' section before stating it's not worth the health trade-off.
        3. CRITICAL RED FLAGS: Search aggressively for Palm Oil, Palmolein, Hydrogenated Vegetable Oils, Maltodextrin, High Fructose Corn Syrup (HFCS), Maida, Liquid Glucose, and Artificial Sweeteners/Colors.
        4. AUTOMATIC PENALTY RULE: If ANY of the above red flags are detected, the absolute MAXIMUM health rating allowed is 3.5/10. It is a toxic corporate product.
        5. DECODE ALL ADDICTIVE INS/E-CODES: Identify and list chemical risks in `deep_dive_details`.
        """
    else:
        prompt_text = f"""
        ROLE: Master Chief Sports Dietitian, Clinical Endocrinologist, and Human Performance Bio-Architect.
        CURRENT USER HEALTH GOAL: "{user_goal}".

        🔴 IMAGE VALIDATION (CRITICAL RULE):
        You are strictly a FOOD ANALYZER. If the image is NOT a recognizable food item, meal, or beverage, YOU MUST set `is_recognized_target` to false and set `recognition_error` to "Please upload a valid image of a food item."

        CRITICAL MANDATE: Evaluate this food item with absolute biochemical precision. Bad food must be called out as garbage; pristine fuel must be highly rewarded.

        🔴 THE MATHEMATICAL SCORING PROTOCOL:
        1. ACKNOWLEDGE TRACE BENEFITS: Even if it is a junk food (like pizza/burger), if it contains protein (cheese/meat) or calcium, you MUST highlight that benefit first in the 'primary_benefit' field before concluding that the overall caloric/fat trade-off is bad.
        2. Evaluate the nutritional profile out of 10.0 based on these exact biological multipliers:
           - HIGH BIOAVAILABILITY FACTORS (+): High-quality Protein, Bioavailable Calcium, Magnesium, Zinc, High Dietary Fiber, and Clean Fats.
           - HIGH INFLAMMATION FACTORS (-): High glycemic refined sugars, trans-fats, processed sodium levels.

        🔴 GOAL-SPECIFIC DECIMALS MATRIX (MANDATORY ADJUSTMENT):
        Shift the score strictly depending on the current active goal "{user_goal}". 
        - Example Case (Nutrient-dense whole foods like Paneer or Eggs):
          * Goal 'Build Muscle' -> Score 9.5/10.
          * Goal 'Clean Eating' -> Score 9.2/10.
          * Goal 'Weight Loss' -> Score 6.8/10 to 7.2/10.
        - Example Case (Junk Food like a Burger/Pizza):
          * Goal 'Weight Loss' -> Score 1.5/10 to 2.5/10.
          * Goal 'Build Muscle' -> Score 2.5/10 to 3.7/10 (dirty bulk).
        
        Apply this rigorous scaling algorithm. Output precise decimals (e.g., 9.2, 8.9, 2.1).
        """

    if image_bytes:
        print("📸 Processing Image Upload...")
        compressed_bytes, new_mime = compress_image_bytes(image_bytes, mode)
        contents = [prompt_text + "\nPerform a granular analysis on this image.", types.Part.from_bytes(data=compressed_bytes, mime_type=new_mime)]
    else:
        print(f"📝 Processing Raw Text Query: {food_query}")
        contents = [prompt_text + f"\nAnalyze this food entry: {food_query}"]

    # --- 4. SMART NETWORK RESILIENCE LOOP ---
    max_retries = 4
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
            
            data = json.loads(response.text)
            
            # 🟢 PROPER REJECTION LOGIC
            if not data.get("is_recognized_target", True):
                print(f"🚫 Validation Failed: {data.get('recognition_error')}")
                return {"error": data.get("recognition_error", "Invalid image uploaded.")}
                
            print("✅ Granular Analysis Complete!")
            return data
            
        except Exception as e:
            error_message = str(e).lower()
            print(f"🔍 DEBUG EXACT ERROR: {error_message}")
            
            # 🛑 1. QUOTA LIMIT FIX
            if "429" in error_message or "quota" in error_message or "exhausted" in error_message:
                print("❌ API Limit Reached. Stopping retries to prevent permanent block.")
                return {"error": "Google API free limit reached. Please wait 1 minute before scanning again."}
            
            # 🔄 2. NETWORK FIX
            if "503" in error_message or "unavailable" in error_message or "disconnected" in error_message or "ssl" in error_message:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + 2 
                    print(f"⚠️ Network Fluctuation. Smart Retry in {wait_time} seconds (Attempt {attempt+1}/{max_retries})...")
                    time.sleep(wait_time)
                    continue 
            
            print(f"❌ Fatal Error: {str(e)}")
            return {"error": "AI Engine Failure: Network issue. Please try again."}