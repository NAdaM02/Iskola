from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, send_file, abort
import pdfkit
from pyOneNote.OneDocument import OneDocment
from werkzeug.utils import secure_filename
import json
import tempfile
import os

app = Flask(__name__)

EXCLUDED_SUBJECTS = {"Németh", "Zeneirodalom", "Matek", "Fizika"}

BASE_DIR = Path.cwd().parent / "2024-25"
TEMP_DIR = Path.cwd().parent / "Server" / "data"

print("\n\n\nCurrent working directory:", Path.cwd())
print("Expected BASE_DIR:", BASE_DIR)
try:
    print(Path.cwd().parent.parent)
except:
    pass
print(Path.cwd().parents)
print("Expected TEMP_DIR:", TEMP_DIR,"\n\n\n")

def get_one_file_path(subject):
    subject = secure_filename(subject)
    subject_path = BASE_DIR / subject / f".{subject}.one"
    return subject_path if subject_path.exists() else None

def extract_content(subject, mode, count=5, date=None):
    file_path = get_one_file_path(subject)
    if not file_path:
        return None

    with open(file_path, "rb") as file:
        # Check if it's a valid OneNote file
        file.seek(0)
        if not OneDocment.check_valid(file):
            return None
        
        # Reset file pointer and process the file
        file.seek(0)
        document = OneDocment(file)
        content = document.get_json()
        
        # Extract embedded files and their properties
        files_data = []
        for file_guid, file_info in content['files'].items():
            # Get associated properties
            file_properties = next(
                (prop for prop in content['properties'] 
                 if prop['identity'] == file_info['identity']),
                None
            )
            
            if file_properties:
                files_data.append({
                    'content': bytes.fromhex(file_info['content']),
                    'extension': file_info['extension'],
                    'properties': file_properties['val']
                })
        
        # Sort and filter based on mode
        if mode == "last_x":
            files_data = sorted(
                files_data,
                key=lambda x: x['properties'].get('LastModifiedTime', ''),
                reverse=True
            )[:count]
        elif mode == "by_date" and date:
            files_data = [
                f for f in files_data
                if date in str(f['properties'].get('LastModifiedTime', ''))
            ]
            
        return files_data

def convert_content_to_pdf(files_data, output_file):
    html_content = "<h1>OneNote Export</h1>"
    
    for file_data in files_data:
        # Add metadata if available
        if 'properties' in file_data:
            title = file_data['properties'].get('DisplayName', 'Untitled')
            modified_time = file_data['properties'].get('LastModifiedTime', '')
            html_content += f"<h2>{title}</h2>"
            html_content += f"<p>Last Modified: {modified_time}</p>"
        
        # Handle different types of content based on extension
        if file_data['extension'].lower() in {'.png', '.jpg', '.jpeg', '.gif'}:
            # Create a temporary file for the image
            with tempfile.NamedTemporaryFile(suffix=file_data['extension'], delete=False) as temp_file:
                temp_file.write(file_data['content'])
                html_content += f'<img src="{temp_file.name}" style="max-width: 100%"><br>'
        else:
            try:
                text_content = file_data['content'].decode('utf-8', errors='ignore')
                html_content += f"<pre>{text_content}</pre><br>"
            except Exception:
                html_content += "<p>Binary content not displayed</p><br>"

    pdfkit.from_string(html_content, str(output_file))
    
    # Cleanup temporary files
    for filename in os.listdir():
        if filename.startswith('tmp') and any(filename.endswith(ext) 
            for ext in ['.png', '.jpg', '.jpeg', '.gif']):
            try:
                os.remove(filename)
            except:
                pass

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
    mode = request.form["mode"]
    count = int(request.form.get("count", 5))
    date = request.form.get("date")

    files_data = extract_content(subject, mode, count, date)
    if not files_data:
        abort(404, description="No content found")

    pdf_path = TEMP_DIR / f"{secure_filename(subject)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    convert_content_to_pdf(files_data, pdf_path)
    
    @app.after_request
    def cleanup(response):
        pdf_path.unlink(missing_ok=True)
        return response

    return send_file(pdf_path, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)