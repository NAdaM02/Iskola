from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, send_file
import pdfkit
from pyonenote import OneNoteFile
from werkzeug.utils import secure_filename

app = Flask(__name__)

BASE_DIR = Path.cwd() / ".." / "2024-25"
EXCLUDED_SUBJECTS = {"Németh", "Zeneirodalom", "Matek", "Fizika"}
TEMP_DIR = Path("data")
TEMP_DIR.mkdir(exist_ok=True)

def get_one_file_path(subject):
    subject = secure_filename(subject)
    subject_path = BASE_DIR / subject / f".{subject}.one"
    return subject_path if subject_path.exists() else None

def extract_pages(subject, mode, count=5, date=None):
    file_path = get_one_file_path(subject)
    if not file_path:
        return None

    with open(file_path, 'rb') as f:
        one = OneNoteFile(f)
        pages = list(one.iter_pages())

    if mode == "last_x":
        pages = sorted(pages, key=lambda p: p.title)[-count:]
    elif mode == "by_date" and date:
        pages = [p for p in pages if date in p.title]

    return pages

def convert_pages_to_pdf(pages, output_file):
    html_content = "<h1>OneNote Export</h1>"
    for page in pages:
        html_content += f"<h2>{page.title}</h2>{page.get_html()}<br>"

    pdfkit.from_string(html_content, str(output_file))

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

    pages = extract_pages(subject, mode, count, date)
    if not pages:
        return "No pages found", 404

    pdf_path = TEMP_DIR / f"{secure_filename(subject)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    convert_pages_to_pdf(pages, pdf_path)
    
    @app.after_request
    def cleanup(response):
        pdf_path.unlink()
        return response

    return send_file(pdf_path, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)