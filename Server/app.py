import os
import git
import shutil
from flask import Flask, request, send_file, render_template, jsonify

app = Flask(__name__)

REPO_PATH = "/tmp/repo"
GIT_URL = "https://github.com/NAdaM02/Iskola.git"
BASE_PATH = os.path.join(REPO_PATH, "2024-25")
EXCLUDED_SUBJECTS = {"Németh", "Zeneirodalom"}  # Subjects to exclude

# Simulated conversion function (replace with real conversion logic)
def one_to_pdf(input_file, output_file, pages=None):
    """Simulated OneNote to PDF conversion."""
    with open(output_file, "w") as f:
        f.write(f"Converted: {input_file}\nPages: {pages if pages else 'ALL'}")

def clone_repo():
    """Clone GitHub repository to get the latest OneNote files."""
    if os.path.exists(REPO_PATH):
        shutil.rmtree(REPO_PATH)
    git.Repo.clone_from(GIT_URL, REPO_PATH)

@app.route("/")
def index():
    """Serve the main webpage."""
    return render_template("index.html")

@app.route("/subjects")
def list_subjects():
    """Return a list of available subjects, excluding unwanted ones."""
    subjects = [d for d in os.listdir(BASE_PATH) if os.path.isdir(os.path.join(BASE_PATH, d)) and d not in EXCLUDED_SUBJECTS]
    return jsonify(subjects)

@app.route("/files")
def list_files():
    """Return available OneNote files in a subject folder."""
    subject = request.args.get("subject")
    subject_path = os.path.join(BASE_PATH, subject)
    if os.path.exists(subject_path):
        files = [f for f in os.listdir(subject_path) if f.endswith(".one")]
        return jsonify(files)
    return jsonify([])

@app.route("/convert")
def convert_file():
    """Convert OneNote file based on requested mode."""
    subject = request.args.get("subject")
    file_name = request.args.get("file")
    mode = request.args.get("mode")  # 'full', 'last_x', 'date'
    x = int(request.args.get("x", 1))  # Default last 1 note
    date = request.args.get("date", None)  # Date format: YYYY-MM-DD

    file_path = os.path.join(BASE_PATH, subject, file_name)
    output_pdf = file_path.replace(".one", ".pdf")

    # Simulate reading pages from the OneNote file
    pages = sorted([f"{year}-{month:02d}-{day:02d} Topic" for year in range(2023, 2025) for month in range(1, 13) for day in range(1, 29)])

    if mode == "last_x":
        selected_pages = pages[-x:]
    elif mode == "date" and date:
        selected_pages = [p for p in pages if date in p]
    else:
        selected_pages = None

    one_to_pdf(file_path, output_pdf, selected_pages)
    return send_file(output_pdf, as_attachment=True)

if __name__ == "__main__":
    clone_repo()
    app.run(host="0.0.0.0", port=5000)
