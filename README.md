Healthy India Tracker 🍃
AI-Powered Food & Ingredient Auditor

Healthy India Tracker is an intelligent, full-stack application designed to provide users with transparent, clinical-grade nutritional analysis. Whether you are tracking daily meals or decoding complex ingredient labels on packaged foods, this tool provides brutal, scientifically-backed honesty about what you are consuming.

🚀 Key Features
Dynamic Scoring Matrix: Evaluates food items based on specific health goals (Weight Loss, Muscle Building, Clean Eating) using precise biochemical markers.

Smart Ingredient Decoding: Detects hidden toxins, emulsifiers (INS codes), and marketing deceptions on food labels with high-precision OCR.

Clinical-Grade Analysis: Provides medical reasoning for every health rating, explaining the impact of specific nutrients on hormones, blood sugar, and gut health.

Network Resilience: Features a custom asynchronous retry engine to handle API rate limits and network drops gracefully.

Image Optimization Pipeline: Implements on-the-fly image enhancement (sharpness/contrast boosting) to ensure perfect text parsing even from low-quality photos.

🛠 Tech Stack
AI Engine: Google Gemini 2.5 Flash (via google-genai SDK)

Backend: FastAPI (Asynchronous Python)

Frontend: React.js, Tailwind CSS, Lucide Icons

Data Validation: Pydantic (for structured JSON parsing)

Database: SQLite with SQLAlchemy (Async)

Image Processing: PIL (Pillow) & ImageEnhance

🏗 System Architecture
Preprocessing: Uploaded images undergo adaptive sharpening to optimize OCR legibility before transmission.

Inference: The prompt engine acts as a "Medical Auditor," applying dynamic scoring rules based on user-selected health goals.

Validation: AI output is strictly enforced via Pydantic schemas to prevent hallucinations and ensure consistent data structure.

Persistence: Analysis results are stored asynchronously in a relational database for history tracking.

⚙️ Installation & Setup
Prerequisites
Python 3.10+

Node.js 18+

A valid GEMINI_API_KEY from Google AI Studio

Backend Setup
Bash
# Clone the repo
git clone https://github.com/sumitssr123/Food_Reality_Checker.git


# Install dependencies
pip install -r requirements.txt

# Set up environment
echo "GEMINI_API_KEY=your_key_here" > .env

# Run the server
uvicorn main:app --reload
Frontend Setup
Bash
cd frontend-react
npm install
npm run dev
🔬 Scoring Philosophy
Unlike generic fitness apps, Healthy India Tracker is opinionated:

Brutal Honesty: If a product contains refined sugars, palm oil, or harmful additives, the rating is aggressively penalized (1.0–3.5/10).

Goal-Centric: A food item is scored differently based on your objective. For example, a high-calorie whole food is rewarded for "Muscle Building" but analyzed critically for "Weight Loss."

🛡 License
This project is for educational and clinical-nutritional analysis purposes. Always consult a certified medical professional for personalized health advice.

Built with precision, candor, and a commitment to better public health.
