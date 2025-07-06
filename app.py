from flask import Flask, request, jsonify
import pdfplumber
from docx import Document
import google.generativeai as genai
import os
from flask_cors import CORS
import json

from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize Gemini API
genai.configure(api_key="AIzaSyBAm3FwW4KadjuUnZ_H-hO6ZQO2wWA6E0Y")
model = genai.GenerativeModel("gemini-1.5-flash")

def extract_text_from_file(filepath):
    if filepath.endswith('.pdf'):
        with pdfplumber.open(filepath) as pdf:
            return "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
    elif filepath.endswith('.docx'):
        doc = Document(filepath)
        return "\n".join([para.text for para in doc.paragraphs])
    else:
        return ""

@app.route("/analyze", methods=["POST"])
def analyze():
    cv_file = request.files.get("cv")
    job_description = request.form.get("job_description")

    if not cv_file or not job_description:
        return jsonify({"error": "CV file and job description are required"}), 400

    filename = secure_filename(cv_file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    cv_file.save(filepath)

    cv_text = extract_text_from_file(filepath)

    prompt = f"""
    You are an expert career assistant. Compare the user's CV with the provided job description and provide:

    1. A list of matched qualifications from the CV.
    2. A list of missing qualifications or experience.
    3. Suggestions to improve the CV to better fit the job.

    Respond in JSON format like:
    {{
      "matched": ["Python", "GPA above 2.5"],
      "missing": ["Excel proficiency", "Internship experience"],
      "suggestions": [
        "Mention Excel or data analysis tools",
        "Add internship or project experience",
        "Include teamwork or communication skills"
      ]
    }}

    CV:
    {cv_text}

    Job Description:
    {job_description}
    """

    response = model.generate_content(prompt)
    
    try:
        result = json.loads(response.text)
        return jsonify(result)
    except:
        return jsonify({"raw_output": response.text}), 200

if __name__ == "__main__":
    app.run(debug=True)
