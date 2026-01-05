import os
import json
import re
from flask import Flask, render_template, request, jsonify
from google import genai
import PyPDF2
from werkzeug.utils import secure_filename

app = Flask(__name__)

# --- CONFIG ---
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Correct Model Name: gemini-1.5-flash
client = genai.Client(api_key="AIzaSyDDSlU4VQ_Z3v0spDYMmSya8eXqoavalpE") 

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() or ""
    except Exception as e:
        print(f"Extraction Error: {e}")
    return text

@app.route('/')
def home():
    return render_template('resume.html')

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        if "resume" not in request.files:
            return jsonify({"error": "No resume file uploaded"}), 400

        resume_file = request.files["resume"]
        if resume_file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        # Save and Extract
        filename = secure_filename(resume_file.filename)
        pdf_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        resume_file.save(pdf_path)
        resume_text = extract_text_from_pdf(pdf_path)

        if not resume_text.strip():
            return jsonify({"error": "PDF is empty or scanned image"}), 400

        # Updated General Audit Prompt
        prompt = f"""
        Act as an expert Resume Auditor. Analyze the following resume text for:
        1. Professional impact and action verbs.
        2. Clarity and formatting.
        3. Skills present vs missing industry standards.
        
        Resume Text: {resume_text}
        
        Return ONLY a JSON object:
        {{
            "score": 85,
            "strengths": ["Strong use of metrics", "Clear technical stack"],
            "weaknesses": ["Vague summary", "Lack of soft skills"],
            "skills_detected": ["Python", "SQL", "Project Management"],
            "suggestions": "Add a dedicated certifications section and quantify results in your latest role."
        }}
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt
        )
        
        # Robust JSON cleaning
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            return jsonify(json.loads(json_match.group(0)))
        
        return jsonify({"error": "AI failed to return JSON"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)