import { useState, useRef, useEffect } from 'react'
import { Search, Upload, Camera, Zap, ShieldAlert, Activity, Leaf, Target, X, Focus, Flame, CheckCircle, AlertTriangle, History, ChevronRight, Loader2, Image as ImageIcon } from 'lucide-react'

// 🌟 THE MAGIC FIX: Auto-detects Localhost vs Live Server automatically!
const API_BASE_URL = import.meta.env.DEV 
  ? "http://127.0.0.1:8000" 
  : (import.meta.env.VITE_API_URL || "https://healthyindiatracker.onrender.com");

function App() {
  // --- States ---
  const [userGoal, setUserGoal] = useState('General Health')
  const [foodQuery, setFoodQuery] = useState('')
  const [activeMode, setActiveMode] = useState('food') // 'food' or 'ingredients'
  
  // UI States
  const [isCameraOpen, setIsCameraOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [showHistory, setShowHistory] = useState(false)
  const [historyData, setHistoryData] = useState([])
  const [analysisResult, setAnalysisResult] = useState(null)

  // NEW: Image Preview States
  const [selectedFile, setSelectedFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)

  // NEW: Creative Loading Messages State
  const loadingMessages = [
    "Consulting the Digital Dietitian 🧑‍⚕️...",
    "Scanning for hidden sugars & toxins 🔍...",
    "Calculating macros & micronutrients 🧬...",
    "Evaluating goal alignment 🎯...",
    "Extracting biological benefits 🌿..."
  ]
  const [loadingText, setLoadingText] = useState(loadingMessages[0])

  // Refs
  const videoRef = useRef(null)
  const streamRef = useRef(null)
  const canvasRef = useRef(null)
  const fileInputRef = useRef(null)

  // --- Dynamic Loading Text Effect ---
  useEffect(() => {
    let interval;
    if (isLoading) {
      let i = 0;
      setLoadingText(loadingMessages[0]);
      interval = setInterval(() => {
        i = (i + 1) % loadingMessages.length;
        setLoadingText(loadingMessages[i]);
      }, 2500); // Har 2.5 second mein message change hoga
    }
    return () => clearInterval(interval);
  }, [isLoading])

  // --- API Functions ---

  // 1. Text Search (Bina photo ke)
  const handleTextSearch = async () => {
    if (!foodQuery) return alert("Please enter a food name first!")
    setIsLoading(true)
    setAnalysisResult(null)
    setPreviewUrl(null) // Hide preview if text search is used
    
    try {
      const formData = new FormData()
      formData.append("food_query", foodQuery)
      formData.append("user_goal", userGoal)
      formData.append("mode", "food")

      const response = await fetch(`${API_BASE_URL}/analyze/image/`, {
        method: "POST",
        body: formData
      })
      const data = await response.json()
      if (data.error) throw new Error(data.error)
      setAnalysisResult(data)
    } catch (error) {
      alert("❌ " + error.message)
    }
    setIsLoading(false)
  }

  // 2. File Upload Handler (Hold in State, don't send to API yet)
  const handleFileUpload = (event) => {
    const file = event.target.files[0]
    if (!file) return

    setSelectedFile(file)
    setPreviewUrl(URL.createObjectURL(file))
    setAnalysisResult(null) // Clear old result
    event.target.value = null // reset input
  }

  // 3. Camera Snapshot (Hold in State, don't send to API yet)
  const takeSnapshot = () => {
    if (videoRef.current && canvasRef.current) {
      const context = canvasRef.current.getContext('2d')
      canvasRef.current.width = videoRef.current.videoWidth
      canvasRef.current.height = videoRef.current.videoHeight
      context.drawImage(videoRef.current, 0, 0)
      
      // Convert Canvas to Blob (File format)
      canvasRef.current.toBlob((blob) => {
        setSelectedFile(blob)
        setPreviewUrl(URL.createObjectURL(blob))
        setAnalysisResult(null)
        closeCamera()
      }, 'image/jpeg', 0.8)
    }
  }

  // 4. MANUAL ANALYZE SUBMIT BUTTON FUNCTION
  const submitImageForAnalysis = async () => {
    if (!selectedFile) return
    setIsLoading(true)
    setAnalysisResult(null)

    try {
      const formData = new FormData()
      formData.append("file", selectedFile, "captured_image.jpg")
      formData.append("food_query", "Unknown (Image Upload)")
      formData.append("user_goal", userGoal)
      formData.append("mode", activeMode)

      const response = await fetch(`${API_BASE_URL}/analyze/image/`, {
        method: "POST",
        body: formData
      })
      const data = await response.json()
      
      // Handle the strict validation error from Backend
      if (data.error) throw new Error(data.error)
      
      setAnalysisResult(data)
      
      // Clear preview after successful analysis
      setPreviewUrl(null)
      setSelectedFile(null)
    } catch (error) {
      // Backend se reject aayega toh yahan alert banega
      alert("⚠️ " + error.message) 
    }
    setIsLoading(false)
  }

  // Clear Preview
  const cancelPreview = () => {
    setPreviewUrl(null)
    setSelectedFile(null)
  }

  // 5. Fetch History
  const loadHistory = async () => {
    if (showHistory) {
      setShowHistory(false)
      return
    }
    try {
      const response = await fetch(`${API_BASE_URL}/history/`)
      const data = await response.json()
      setHistoryData(data.history || [])
      setShowHistory(true)
    } catch (error) {
      alert("Could not load history. Is backend running?")
    }
  }

  // --- Camera UI Logic ---
  const triggerUpload = (mode) => {
    setActiveMode(mode)
    fileInputRef.current.click()
  }

  const openCamera = async (mode) => {
    setActiveMode(mode)
    setIsCameraOpen(true)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
      streamRef.current = stream
      if (videoRef.current) videoRef.current.srcObject = stream
    } catch (err) {
      alert("⚠️ Camera permission denied!")
      setIsCameraOpen(false)
    }
  }

  const closeCamera = () => {
    if (streamRef.current) streamRef.current.getTracks().forEach(track => track.stop())
    setIsCameraOpen(false)
  }

  return (
    <div className="min-h-screen bg-slate-50 py-10 px-4 font-sans text-slate-800 selection:bg-blue-200 pb-24">
      {/* Hidden File Input for Uploads */}
      <input type="file" ref={fileInputRef} onChange={handleFileUpload} accept="image/*" className="hidden" />

      <div className="max-w-3xl mx-auto space-y-8">
        
        {/* --- Header Section --- */}
        <header className="text-center mb-10 relative">
          
          <div className="absolute left-0 top-1 z-10 animate-in fade-in slide-in-from-left-4 duration-500 scale-75 origin-top-left sm:scale-100">
            <div className="bg-white/80 backdrop-blur-sm px-4 py-1.5 rounded-full shadow-sm border border-slate-200 hover:shadow-md transition-all cursor-default">
              <p className="text-xs font-extrabold text-slate-500 tracking-wide">
                Created by <span className="text-blue-600">Sumit Singh</span> <span className="text-slate-400 font-medium">(IIITL)</span>
              </p>
            </div>
          </div>

          <div className="absolute right-0 top-0">
            <button 
              onClick={loadHistory}
              className="flex items-center gap-2 bg-white text-slate-600 px-4 py-2 rounded-full shadow-sm border border-slate-200 hover:bg-slate-100 transition-colors text-sm font-bold"
            >
              <History className="w-4 h-4" /> {showHistory ? "Hide History" : "My Scans"}
            </button>
          </div>
          
          <div className="inline-flex items-center justify-center p-3 bg-blue-100 rounded-full mb-4 mt-8 md:mt-0">
            <Activity className="w-8 h-8 text-blue-600" />
          </div>
          <h1 className="text-4xl md:text-6xl font-extrabold mb-3 tracking-tight bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            Healthy India Tracker
          </h1>
          <p className="text-slate-500 font-medium text-lg">AI-Powered Food & Ingredient Auditor</p>
          
          {/* Goal Selector */}
          <div className="mt-8 text-left bg-white/60 backdrop-blur-md p-6 rounded-2xl border border-white/80 shadow-[0_8px_30px_rgb(0,0,0,0.04)]">
            <label className="flex items-center gap-2 text-slate-800 font-bold mb-3">
              <Target className="w-5 h-5 text-blue-500" /> Select Your Core Health Goal:
            </label>
            <select 
              value={userGoal}
              onChange={(e) => setUserGoal(e.target.value)}
              className="w-full p-4 border border-slate-200 rounded-xl bg-slate-50 hover:bg-white focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all font-medium text-slate-700 cursor-pointer"
            >
              <option value="General Health">Overall Health & Longevity</option>
              <option value="Weight Loss">Weight Loss (Fat Burning)</option>
              <option value="Build Muscle">Build Muscle (High Protein)</option>
              <option value="Clean Eating">Clean Eating (Zero Toxins)</option>
            </select>
          </div>
        </header>
         
        {/* --- History Dashboard --- */}
        {showHistory && (
          <div className="bg-slate-800 text-white p-6 rounded-3xl shadow-xl animate-in fade-in slide-in-from-top-4">
            <h2 className="text-xl font-bold flex items-center gap-2 mb-4"><History className="w-5 h-5 text-blue-400"/> Recent Scans</h2>
            <div className="space-y-3">
              {historyData.length === 0 ? <p className="text-slate-400">No scans found in database.</p> : null}
              {historyData.map((item, idx) => (
                <div key={idx} className="bg-slate-700/50 p-4 rounded-xl flex justify-between items-center border border-slate-600">
                  <div>
                    <h4 className="font-bold text-lg capitalize">{item.food_name}</h4>
                    <p className="text-xs text-slate-400">Target: {item.health_goal}</p>
                  </div>
                  <div className="text-right">
                    <span className={`px-3 py-1 rounded-full text-sm font-bold text-white ${item.health_rating >= 8 ? 'bg-green-500' : item.health_rating >= 5 ? 'bg-yellow-500' : 'bg-red-500'}`}>
                      {item.health_rating} / 10
                    </span>
                    <p className="text-sm font-bold mt-1 text-slate-300 flex items-center gap-1 justify-end"><Flame className="w-3 h-3 text-yellow-500"/> {item.calories} kcal</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* --- Inputs Panels --- */}
        <div className="grid md:grid-cols-2 gap-6 relative">
          
          {/* THE NEW HEALTHY LOADING OVERLAY */}
          {isLoading && (
            <div className="absolute inset-0 z-10 bg-white/70 backdrop-blur-md rounded-3xl flex flex-col items-center justify-center border border-green-100 shadow-2xl">
              <div className="relative mb-6">
                <div className="absolute inset-0 bg-green-200 rounded-full blur-xl animate-pulse"></div>
                <Leaf className="w-14 h-14 text-green-600 relative animate-bounce" />
              </div>
              <h3 className="text-xl font-extrabold text-slate-800 tracking-tight text-center px-4 transition-all duration-500">
                {loadingText}
              </h3>
              <p className="text-slate-500 font-medium mt-2 text-sm animate-pulse">Running health diagnostics...</p>
            </div>
          )}

          {/* Universal Food Analyzer */}
          <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200 hover:shadow-lg transition-all">
            <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2"><Leaf className="w-5 h-5 text-green-600" /> Food Analyzer</h2>
            <div className="flex gap-2 mb-4">
              <input 
                type="text" 
                placeholder="Food name (e.g. Curd)..." 
                value={foodQuery}
                onChange={(e) => setFoodQuery(e.target.value)}
                className="w-full p-3 border border-slate-200 rounded-xl bg-slate-50 focus:ring-2 focus:ring-blue-500/20 focus:outline-none"
              />
              <button onClick={handleTextSearch} className="bg-blue-600 hover:bg-blue-700 text-white p-3 rounded-xl shadow-sm"><Search className="w-5 h-5" /></button>
            </div>
            <div className="flex gap-2">
              <button onClick={() => triggerUpload('food')} className="flex-1 flex justify-center items-center gap-2 border border-slate-200 hover:bg-slate-50 p-3 rounded-xl font-semibold text-slate-600 text-sm"><Upload className="w-4 h-4"/> Upload</button>
              <button onClick={() => openCamera('food')} className="flex-1 flex justify-center items-center gap-2 border border-slate-200 hover:bg-slate-50 p-3 rounded-xl font-semibold text-slate-600 text-sm"><Camera className="w-4 h-4"/> Snap</button>
            </div>
          </div>

          {/* Packaged Food Auditor */}
          <div className="bg-red-50/50 p-6 rounded-3xl shadow-sm border border-red-100 hover:shadow-lg transition-all flex flex-col justify-between">
            <h2 className="text-xl font-bold text-red-700 mb-4 flex items-center gap-2"><ShieldAlert className="w-5 h-5 text-red-600" /> Ingredient Auditor</h2>
            <div className="flex gap-2">
              <button onClick={() => triggerUpload('ingredients')} className="flex-1 flex justify-center items-center gap-2 border border-red-200 hover:bg-red-50 p-3 rounded-xl font-semibold text-red-600 text-sm"><Upload className="w-4 h-4"/> Upload Label</button>
              <button onClick={() => openCamera('ingredients')} className="flex-1 flex justify-center items-center gap-2 border border-red-200 hover:bg-red-50 p-3 rounded-xl font-semibold text-red-600 text-sm"><Camera className="w-4 h-4"/> Snap Label</button>
            </div>
          </div>
        </div>

        {/* --- IMAGE PREVIEW BLOCK --- */}
        {previewUrl && (
          <div className="bg-white p-6 rounded-3xl shadow-lg border-2 border-blue-400 animate-in fade-in slide-in-from-top-4 relative mt-6 text-center">
            <button onClick={cancelPreview} className="absolute top-4 right-4 p-2 bg-slate-100 rounded-full hover:bg-red-100 hover:text-red-600 transition-colors">
              <X className="w-5 h-5"/>
            </button>
            <h3 className="text-xl font-bold text-slate-800 mb-4 flex items-center justify-center gap-2">
              <ImageIcon className="w-5 h-5 text-blue-500" /> Ready to Analyze {activeMode === 'food' ? 'Food' : 'Label'}
            </h3>
            <div className="bg-slate-100 rounded-2xl p-2 mb-6 inline-block max-w-full">
              <img src={previewUrl} alt="Selected Preview" className="max-h-64 md:max-h-80 mx-auto rounded-xl object-contain shadow-sm" />
            </div>
            <button 
              onClick={submitImageForAnalysis} 
              className="w-full md:w-2/3 lg:w-1/2 bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 px-8 rounded-xl shadow-lg hover:shadow-blue-500/30 transition-all active:scale-95 flex items-center justify-center gap-2 mx-auto"
            >
              <Zap className="w-6 h-6 text-yellow-400"/> START AI ANALYSIS
            </button>
          </div>
        )}

        {/* --- AI RESULT DASHBOARD --- */}
        {analysisResult && analysisResult.health_intelligence && !previewUrl && (
          <div className="mt-12 bg-white rounded-[2rem] shadow-xl border border-slate-200 overflow-hidden animate-in fade-in slide-in-from-bottom-8">
            <div className={`p-8 text-center text-white ${analysisResult.health_intelligence.rating_out_of_10 >= 8 ? 'bg-gradient-to-br from-green-500 to-emerald-700' : analysisResult.health_intelligence.rating_out_of_10 >= 5 ? 'bg-gradient-to-br from-yellow-400 to-orange-500' : 'bg-gradient-to-br from-red-500 to-rose-700'}`}>
              <h2 className="text-3xl md:text-4xl font-extrabold capitalize mb-4">{analysisResult.query_name}</h2>
              <p className="text-white/80 font-medium tracking-widest uppercase text-sm mb-6">Health Score</p>
              <div className="inline-flex items-baseline justify-center px-6 py-2 bg-white/20 backdrop-blur-md rounded-full border border-white/30 shadow-inner">
                <span className="text-5xl font-black">{analysisResult.health_intelligence.rating_out_of_10}</span>
                <span className="text-2xl font-bold text-white/70 ml-1">/10</span>
              </div>
              <p className="mt-4 font-bold text-lg bg-white/10 inline-block px-4 py-1 rounded-full">{analysisResult.health_intelligence.rating_label}</p>
            </div>

            <div className="p-6 md:p-8 space-y-8">
              <div>
                <p className="text-center font-bold text-slate-400 uppercase tracking-widest text-xs mb-4">⚖️ Analyzed: {analysisResult.analyzed_quantity}</p>
                <div className="grid grid-cols-4 gap-2 md:gap-4 text-center">
                  <div className="bg-orange-50 p-3 rounded-2xl border border-orange-100">
                    <p className="text-xs md:text-sm text-orange-600 font-bold mb-1">Calories</p>
                    <p className="text-lg md:text-xl font-black text-slate-800">{analysisResult.macronutrients.calories}</p>
                  </div>
                  <div className="bg-blue-50 p-3 rounded-2xl border border-blue-100">
                    <p className="text-xs md:text-sm text-blue-600 font-bold mb-1">Protein</p>
                    <p className="text-lg md:text-xl font-black text-slate-800">{analysisResult.macronutrients.protein_g}g</p>
                  </div>
                  <div className="bg-yellow-50 p-3 rounded-2xl border border-yellow-100">
                    <p className="text-xs md:text-sm text-yellow-600 font-bold mb-1">Fat</p>
                    <p className="text-lg md:text-xl font-black text-slate-800">{analysisResult.macronutrients.fats_g}g</p>
                  </div>
                  <div className="bg-purple-50 p-3 rounded-2xl border border-purple-100">
                    <p className="text-xs md:text-sm text-purple-600 font-bold mb-1">Carbs</p>
                    <p className="text-lg md:text-xl font-black text-slate-800">{analysisResult.macronutrients.carbs_g}g</p>
                  </div>
                </div>
              </div>

              <div className="bg-indigo-50 border border-indigo-100 rounded-2xl p-6">
                <h3 className="text-indigo-800 font-bold text-lg mb-2">🎯 Goal Alignment: {userGoal}</h3>
                <p className="text-indigo-900 font-medium leading-relaxed">{analysisResult.goal_alignment}</p>
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                <div className="bg-green-50 border border-green-100 rounded-2xl p-5">
                  <h4 className="text-green-800 font-bold flex items-center gap-2 mb-2"><CheckCircle className="w-5 h-5"/> Benefit</h4>
                  <p className="text-green-700 text-sm leading-relaxed">{analysisResult.health_intelligence.primary_benefit}</p>
                </div>
                <div className="bg-red-50 border border-red-100 rounded-2xl p-5">
                  <h4 className="text-red-800 font-bold flex items-center gap-2 mb-2"><AlertTriangle className="w-5 h-5"/> Warning</h4>
                  <p className="text-red-700 text-sm leading-relaxed">{analysisResult.health_intelligence.primary_warning}</p>
                </div>
              </div>

              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-bold text-slate-800 mb-3 border-b border-slate-200 pb-2">🔬 Deep Dive Insights</h3>
                  <ul className="space-y-2">
                    {analysisResult.deep_dive_details.map((item, index) => (
                      <li key={index} className="flex items-start gap-2 text-slate-600 text-sm"><ChevronRight className="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5"/> {item}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h3 className="text-lg font-bold text-slate-800 mb-3 border-b border-slate-200 pb-2 text-green-700">✅ Healthy Alternatives</h3>
                  <ul className="space-y-2">
                    {analysisResult.healthy_alternatives.map((item, index) => (
                      <li key={index} className="flex items-start gap-2 text-slate-700 font-medium text-sm"><Leaf className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5"/> {item}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

      </div>

      {/* --- LIVE CAMERA MODAL --- */}
      {isCameraOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/95 backdrop-blur-sm flex flex-col justify-center items-center p-4">
          <div className="w-full max-w-md bg-black rounded-3xl overflow-hidden shadow-2xl relative border border-slate-700">
            <button onClick={closeCamera} className="absolute top-4 right-4 z-10 p-2 bg-black/50 text-white rounded-full hover:bg-red-500 transition-colors"><X className="w-6 h-6" /></button>
            <div className="relative aspect-[3/4] bg-slate-800 flex items-center justify-center">
              <video ref={videoRef} autoPlay playsInline className="absolute inset-0 w-full h-full object-cover"/>
              <div className="absolute inset-0 border-2 border-white/20 m-8 rounded-xl flex items-center justify-center"><Focus className="w-12 h-12 text-white/50" /></div>
            </div>
            <canvas ref={canvasRef} className="hidden" />
            <div className="p-6 bg-slate-900 text-center">
              <button onClick={takeSnapshot} className="w-full bg-white text-slate-900 font-bold py-4 rounded-xl hover:bg-slate-200 flex items-center justify-center gap-2"><Camera className="w-6 h-6" /> Capture Image</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App