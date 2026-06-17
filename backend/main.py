from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from io import BytesIO
from PIL import Image
from backend.engine import analyze_food_engine 

# Database Imports (✅ FIXED PATHS HERE)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.database.database import engine, Base, get_db
from backend.database.models import ScanHistory
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
async def save_to_db(db: AsyncSession, query_type: str, user_goal: str, data: dict):
    try:
        new_scan = ScanHistory(
            query_type=query_type,
            food_name=data.get("query_name", "Unknown"),
            health_goal=user_goal,
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
async def analyze_text(food_name: str, user_goal: str = "General Health", mode: str = "food", db: AsyncSession = Depends(get_db)):
    try:
        data = analyze_food_engine(food_query=food_name, user_goal=user_goal, mode=mode)
        
        if "error" in data: 
            return JSONResponse(status_code=400, content={"error": data["error"]})
        
        await save_to_db(db, "text", user_goal, data)
        return data
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Server Error: {str(e)}"})

@app.post("/analyze/image/")
async def analyze_image(
    file: UploadFile = File(None), 
    food_query: str = Form("Unknown Image Upload"),
    user_goal: str = Form("General Health"), # 🟢 FIX: Exactly matches React's formData.append("user_goal")
    mode: str = Form("food"), 
    db: AsyncSession = Depends(get_db)
):
    try:
        safe_image_bytes = None
        mime_type = None

        if file is not None and file.filename != "":
            print(f"\n--- NEW IMAGE UPLOAD STARTED ---")
            raw_image_bytes = await file.read()
            
            if raw_image_bytes:
                try:
                    img = Image.open(BytesIO(raw_image_bytes))
                    if img.mode != 'RGB': 
                        img = img.convert('RGB')
                    img.thumbnail((512, 512))
                    compressed_io = BytesIO()
                    img.save(compressed_io, format='JPEG', quality=70)
                    safe_image_bytes = compressed_io.getvalue()
                    mime_type = "image/jpeg"
                except Exception as img_error:
                    return JSONResponse(status_code=400, content={"error": "Failed to compress the image. Ensure it's a valid picture format."})
        else:
            print(f"\n--- NEW TEXT SEARCH STARTED: {food_query} ---")

        # Pass data to the engine
        data = analyze_food_engine(
            food_query=food_query, 
            user_goal=user_goal, 
            image_bytes=safe_image_bytes, 
            mime_type=mime_type, 
            mode=mode
        )
        
        if "error" in data: 
            return JSONResponse(status_code=400, content={"error": data["error"]})
            
        query_type = "image" if safe_image_bytes else "text"
        await save_to_db(db, query_type, user_goal, data)
        return data
        
    except Exception as e:
        print(f"❌ Server Crash: {str(e)}")
        return JSONResponse(status_code=500, content={"error": f"Internal Server Error: {str(e)}"})
    
@app.get("/history/")
async def get_history(db: AsyncSession = Depends(get_db)):
    try:
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
        return JSONResponse(status_code=500, content={"error": str(e)})