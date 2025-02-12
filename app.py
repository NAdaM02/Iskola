from pathlib import Path
from datetime import datetime
import tempfile
from flask import Flask, render_template, request, send_file, abort
from werkzeug.utils import secure_filename
import aspose.note as an

app = Flask(__name__)

EXCLUDED_SUBJECTS = {"Németh", "Zeneirodalom", "Matek", "Fizika"}

BASE_DIR = Path(__file__).resolve().parent / "2024-25"

print("\n\n\nCurrent working directory:", Path.cwd())
print("Expected BASE_DIR:", BASE_DIR)

def get_one_file_path(subject):
    subject = secure_filename(subject)
    subject_path = BASE_DIR / subject / f".{subject}.one"
    return subject_path if subject_path.exists() else None

def convert_one_to_pdf(subject, mode, count=5, date=None):
    file_path = get_one_file_path(subject)
    if not file_path:
        return None

    # Create a temporary directory that will be automatically cleaned up
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        pdf_path = temp_dir_path / f"{secure_filename(subject)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        # Load the OneNote document
        document = an.Document(str(file_path))

        if mode == "last_x":
            #  Aspose.Note has page-level last modified time
            pages = sorted(document.get_child_nodes(an.Page), key=lambda p: p.last_modified_time, reverse=True)[:count]
            new_doc = an.Document()
            for page in pages:
                new_doc.append_child_last(page.clone())  # Append clones to avoid modifying the original
            document = new_doc

        elif mode == "by_date" and date:
            new_doc = an.Document()
            for page in document.get_child_nodes(an.Page):
                if date in str(page.last_modified_time.date()):
                    new_doc.append_child_last(page.clone())
            document = new_doc

        # Save the document as PDF
        document.save(str(pdf_path))

        return pdf_path

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

    pdf_path = convert_one_to_pdf(subject, mode, count, date)
    if not pdf_path:
        abort(404, description="No content found or conversion failed.")

    try:
        return send_file(pdf_path, as_attachment=True)
    
    finally:
        pass

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)