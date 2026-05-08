from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from io import BytesIO
from PIL import Image
from .engine import analyze_food_engine 

app = FastAPI(title="Healthy India Food Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/analyze/text/")
async def analyze_text(food_name: str, goal: str = "General Health", mode: str = "food"):
    try:
        data = analyze_food_engine(food_query=food_name, user_goal=goal, mode=mode)
        if "error" in data: raise HTTPException(status_code=400, detail=data["error"])
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/image/")
async def analyze_image(file: UploadFile = File(...), goal: str = Form("General Health"), mode: str = Form("food")):
    try:
        print(f"\n--- NEW UPLOAD STARTED ---")
        print(f"📥 Step 1: Receiving file: {file.filename}...")
        raw_image_bytes = await file.read()
        
        if not raw_image_bytes:
            print("❌ Error: Image is completely empty!")
            raise ValueError("The uploaded image is empty.")
            
        print(f"✅ Step 2: Raw Image Size is {len(raw_image_bytes) / 1024:.2f} KB")

        # ULTRA-COMPRESSION
        try:
            print("🗜️ Step 3: Starting Pillow Compression...")
            img = Image.open(BytesIO(raw_image_bytes))
            if img.mode != 'RGB': 
                img = img.convert('RGB')
            
            # Making it even smaller (512x512) so API never disconnects
            img.thumbnail((512, 512))
            compressed_io = BytesIO()
            # Quality 70 makes it extremely lightweight but still visible to AI
            img.save(compressed_io, format='JPEG', quality=70)
            safe_image_bytes = compressed_io.getvalue()
            
            print(f"✅ Step 4: Image compressed down to {len(safe_image_bytes) / 1024:.2f} KB!")
            
        except Exception as img_error:
            print(f"❌ Error during compression: {img_error}")
            raise ValueError("Failed to compress the image. Ensure it's a valid picture format.")

        print("🚀 Step 5: Sending safe image to Gemini Engine...")
        data = analyze_food_engine(user_goal=goal, image_bytes=safe_image_bytes, mime_type="image/jpeg", mode=mode)
        
        if "error" in data: 
            print(f"❌ Gemini API Error: {data['error']}")
            raise HTTPException(status_code=400, detail=data["error"])
            
        print("🎉 Step 6: Success! Sending data to Frontend.")
        return data
        
    except Exception as e:
        print(f"❌ Server Crash: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))