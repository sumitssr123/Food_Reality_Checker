const API_BASE_URL = "http://127.0.0.1:8000";

// Jab file select ho, toh status text update karein
function updateLabel(inputId, statusId) {
    const file = document.getElementById(inputId).files[0];
    const statusEl = document.getElementById(statusId);
    
    // Agar user ne Camera se photo li, toh dusra Upload wala box khali kar do, taaki confusion na ho
    const isCamera = inputId.includes("Camera");
    const siblingId = isCamera ? inputId.replace("Camera", "Upload") : inputId.replace("Upload", "Camera");
    document.getElementById(siblingId).value = ""; 

    if (file) {
        statusEl.innerText = "✅ Ready: " + file.name;
        statusEl.style.display = "block";
    } else {
        statusEl.style.display = "none";
    }
}

// Alert with dynamic input selection
function triggerIngredientAlert(inputId) {
    alert("IMPORTANT: Please capture the INGREDIENTS LIST on the back of the packet, not the front cover!");
    document.getElementById(inputId).click();
}

// Helper: Find which input actually has the file
function getSelectedFile(uploadId, cameraId) {
    const uploadFile = document.getElementById(uploadId).files[0];
    const cameraFile = document.getElementById(cameraId).files[0];
    return uploadFile || cameraFile; // Returns whichever one has a file
}

async function startFoodText() {
    const goal = document.getElementById("userGoal").value;
    const textQuery = document.getElementById("foodInput").value.trim();
    if (!textQuery) return alert("Please type a food name to search!");

    const url = `${API_BASE_URL}/analyze/text/?food_name=${encodeURIComponent(textQuery)}&goal=${encodeURIComponent(goal)}&mode=food`;
    await executeAnalysis(url, { method: "GET" });
}

async function startFoodImage() {
    const goal = document.getElementById("userGoal").value;
    const file = getSelectedFile("foodImgUpload", "foodImgCamera");
    
    if (!file) return alert("Please select a photo from Gallery or use the Camera first!");

    const formData = new FormData();
    formData.append("file", file);
    formData.append("goal", goal);
    formData.append("mode", "food"); 

    const url = `${API_BASE_URL}/analyze/image/`;
    await executeAnalysis(url, { method: "POST", body: formData });
}

async function startIngredientsImage() {
    const goal = document.getElementById("userGoal").value;
    const file = getSelectedFile("ingImgUpload", "ingImgCamera");
    
    if (!file) return alert("Please upload or snap an image of the ingredients label!");

    const formData = new FormData();
    formData.append("file", file);
    formData.append("goal", goal);
    formData.append("mode", "ingredients"); 

    const url = `${API_BASE_URL}/analyze/image/`;
    await executeAnalysis(url, { method: "POST", body: formData });
}

async function executeAnalysis(url, options) {
    const resultArea = document.getElementById("resultArea");
    resultArea.style.display = "none";
    document.body.style.cursor = "wait";
    
    try {
        const response = await fetch(url, options);
        const data = await response.json();
        
        if (!response.ok || data.error) throw new Error(data.detail || data.error);
        renderResults(data);

    } catch (error) {
        console.error("Error:", error);
        alert(`Analysis Error: ${error.message}`);
    } finally {
        document.body.style.cursor = "default";
    }
}

function renderResults(data) {
    document.getElementById("resName").innerText = data.query_name;
    
    const rating = data.health_intelligence?.rating_out_of_10 ?? 0;
    const label = data.health_intelligence?.rating_label ?? "Unknown";
    document.getElementById("resRatingNum").innerText = rating;
    
    const labelEl = document.getElementById("resRatingLabel");
    const resultCard = document.getElementById("resultCard");
    labelEl.innerText = label;
    
    if (rating >= 8) {
        labelEl.style.background = "#16a34a"; resultCard.style.borderTopColor = "#16a34a";
    } else if (rating >= 5) {
        labelEl.style.background = "#eab308"; resultCard.style.borderTopColor = "#eab308";
    } else {
        labelEl.style.background = "#dc2626"; resultCard.style.borderTopColor = "#dc2626";
    }

    document.getElementById("cal").innerText = data.macronutrients?.calories ?? 0;
    document.getElementById("pro").innerText = (data.macronutrients?.protein_g ?? 0) + "g";
    document.getElementById("fat").innerText = (data.macronutrients?.fats_g ?? 0) + "g";
    document.getElementById("carb").innerText = (data.macronutrients?.carbs_g ?? 0) + "g";

    document.getElementById("resBenefit").innerText = data.health_intelligence?.primary_benefit ?? "N/A";
    document.getElementById("resWarning").innerText = data.health_intelligence?.primary_warning ?? "N/A";
    document.getElementById("goalAlignmentText").innerText = data.goal_alignment || "N/A";

    const detailsList = document.getElementById("resDetails");
    detailsList.innerHTML = "";
    (data.deep_dive_details || []).forEach(item => {
        let li = document.createElement("li"); li.innerText = item; li.style.marginBottom = "8px"; detailsList.appendChild(li);
    });

    const altList = document.getElementById("resAlternatives");
    altList.innerHTML = "";
    (data.healthy_alternatives || []).forEach(item => {
        let li = document.createElement("li"); li.innerText = item; li.style.marginBottom = "8px"; altList.appendChild(li);
    });

    document.getElementById("resultArea").style.display = "block";
    document.getElementById("resultArea").scrollIntoView({ behavior: 'smooth' });
}