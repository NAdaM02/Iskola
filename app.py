from pathlib import Path
from datetime import datetime, timezone
import tempfile
import subprocess

from flask import Flask, render_template, request, send_file, abort
from werkzeug.utils import secure_filename

app = Flask(__name__)

EXCLUDED_SUBJECTS = {"Németh", "Zeneirodalom", "Matek", "Fizika"}
BASE_DIR = Path(__file__).resolve().parent / "2024-25"

print()
print()
print("########################################")
print("Excluded sublecjts:", EXCLUDED_SUBJECTS)
print("Current working directory:", Path.cwd())
print("Expected BASE_DIR:", BASE_DIR)
print("########################################")
print()
print()

def get_one_file_path(subject):
    subject_path = BASE_DIR / subject / f".{subject}.one"
    return subject_path if subject_path.exists() else None

def extract_onenote_content(notebook_name, output_dir):
    command = [
        "python", "onenote_dump/main.py", notebook_name, output_dir
    ]
    
    try:
        process = subprocess.run(command, capture_output=True, text=True, check=True)
        print("Extraction successful.")
        return output_dir
    except subprocess.CalledProcessError as e:
        print(f"Error during extraction:\nReturn Code: {e.returncode}\nStdout: {e.stdout}\nStderr: {e.stderr}")
        return None
    except FileNotFoundError:
        print("Error: onenote-dump script not found.")
        return None

@app.route("/")
def index():
    subjects = [
        s.name for s in BASE_DIR.iterdir()
        if s.is_dir() and s.name not in EXCLUDED_SUBJECTS
    ]
    return render_template("index.html", subjects=subjects)

@app.route("/download", methods=["POST"])
def download():
    subject = request.form["subject"]
    notebook_path = get_one_file_path(subject)

    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = extract_onenote_content(notebook_path, temp_dir)
        if not output_dir:
            abort(500, description="Extraction failed.")
        
        zip_path = Path(temp_dir) / f"{secure_filename(subject)}.zip"
        subprocess.run(["zip", "-r", str(zip_path), str(output_dir)], check=True)
        return send_file(zip_path, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
