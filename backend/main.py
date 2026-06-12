from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from io import BytesIO
from PIL import Image
from engine import analyze_food_engine 

# Database Imports
from sqlalchemy.ext.asyncio import AsyncSession
from database.database import engine, Base, get_db
from database.models import ScanHistory
from contextlib import asynccontextmanager

# Automatically create database tables on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="Healthy India Food Analyzer", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# HELPER FUNCTION: To save data into the database
async def save_to_db(db: AsyncSession, query_type: str, goal: str, data: dict):
    try:
        new_scan = ScanHistory(
            query_type=query_type,
            food_name=data.get("query_name", "Unknown"),
            health_goal=goal,
            calories=data.get("macronutrients", {}).get("calories", 0),
            protein_g=data.get("macronutrients", {}).get("protein_g", 0.0),
            health_rating=data.get("health_intelligence", {}).get("rating_out_of_10", 0.0),
            rating_label=data.get("health_intelligence", {}).get("rating_label", "Unknown"),
            primary_warning=data.get("health_intelligence", {}).get("primary_warning", "")
        )
        db.add(new_scan)
        await db.commit()
        print("💾 Success: Data saved to database!")
    except Exception as e:
        print(f"⚠️ Warning: Could not save to database. Error: {e}")

@app.get("/analyze/text/")
async def analyze_text(food_name: str, goal: str = "General Health", mode: str = "food", db: AsyncSession = Depends(get_db)):
    try:
        data = analyze_food_engine(food_query=food_name, user_goal=goal, mode=mode)
        if "error" in data: raise HTTPException(status_code=400, detail=data["error"])
        
        # Save to DB asynchronously
        await save_to_db(db, "text", goal, data)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/image/")
async def analyze_image(file: UploadFile = File(...), goal: str = Form("General Health"), mode: str = Form("food"), db: AsyncSession = Depends(get_db)):
    try:
        print(f"\n--- NEW UPLOAD STARTED ---")
        raw_image_bytes = await file.read()
        
        if not raw_image_bytes:
            raise ValueError("The uploaded image is empty.")

        try:
            img = Image.open(BytesIO(raw_image_bytes))
            if img.mode != 'RGB': 
                img = img.convert('RGB')
            img.thumbnail((512, 512))
            compressed_io = BytesIO()
            img.save(compressed_io, format='JPEG', quality=70)
            safe_image_bytes = compressed_io.getvalue()
        except Exception as img_error:
            raise ValueError("Failed to compress the image. Ensure it's a valid picture format.")

        data = analyze_food_engine(user_goal=goal, image_bytes=safe_image_bytes, mime_type="image/jpeg", mode=mode)
        
        if "error" in data: 
            raise HTTPException(status_code=400, detail=data["error"])
            
        # Save to DB asynchronously
        await save_to_db(db, "image", goal, data)
        return data
        
    except Exception as e:
        print(f"❌ Server Crash: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
from sqlalchemy.future import select

@app.get("/history/")
async def get_history(db: AsyncSession = Depends(get_db)):
    try:
        # Database se latest 10 scans nikalna (descending order mein)
        result = await db.execute(select(ScanHistory).order_by(ScanHistory.id.desc()).limit(10))
        scans = result.scalars().all()
        
        history_list = []
        for scan in scans:
            history_list.append({
                "id": scan.id,
                "food_name": scan.food_name,
                "health_goal": scan.health_goal,
                "health_rating": scan.health_rating,
                "rating_label": scan.rating_label,
                "calories": scan.calories,
                "scanned_at": scan.scanned_at.strftime("%d %b %Y, %H:%M") if scan.scanned_at else "Unknown"
            })
        return {"history": history_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))