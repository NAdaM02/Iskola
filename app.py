from pathlib import Path
from datetime import datetime, timezone
import tempfile
import os
import base64

from flask import Flask, render_template, request, send_file, abort
from werkzeug.utils import secure_filename
import pdfkit
from one_extract import OneNoteExtractor

app = Flask(__name__)

EXCLUDED_SUBJECTS = {"Németh", "Zeneirodalom", "Matek", "Fizika"}
BASE_DIR = Path(__file__).resolve().parent / "2024-25"

print("\n\n\nCurrent working directory:", Path.cwd())
print("Expected BASE_DIR:", BASE_DIR)


def get_one_file_path(subject):
    subject_path = BASE_DIR / subject / f".{subject}.one"
    return subject_path if subject_path.exists() else None


def extract_content(subject, mode, count=5, date=None, password=None):
    file_path = get_one_file_path(subject)
    if not file_path:
        print("Error: File path not found.", file_path)
        return None

    print(f"Attempting to open file: {file_path}")

    if not file_path.exists():
        print(f"Error: File does not exist: {file_path}")
        return None
    if not os.access(file_path, os.R_OK):
        print(f"Error: File is not readable: {file_path}")
        return None

    try:
        with open(file_path, "rb") as f:
            file_data = f.read()

        extractor = OneNoteExtractor(data=file_data, password=password)
        extracted_data = []

        # Extract metadata
        for meta in extractor.extract_meta():
            extracted_data.append({
                'type': 'meta',
                'title': meta.title,
                'last_modified_time': meta.last_modification_date or datetime.min.replace(tzinfo=timezone.utc),
                'creation_date': meta.creation_date,
                'content': meta.title,
            })

        # Extract embedded files
        for file_index, file_content in enumerate(extractor.extract_files()):
            extracted_data.append({
                'type': 'file',
                'index': file_index,
                'file_name': f"embedded_file_{file_index}",
                'content': file_content,
            })

        # Extract images (if available)
        if hasattr(extractor, 'extract_images'):
            for image_index, (image_name, image_data) in enumerate(extractor.extract_images()):
                extracted_data.append({
                    'type': 'image',
                    'index': image_index,
                    'file_name': image_name,
                    'content': image_data,
                })

        print(f"Extracted {len(extracted_data)} items BEFORE filtering.")

    except Exception as e:
        print(f"Error during extraction: {e}")
        return None

    # --- Filtering ---
    filtered_data = []
    if mode == "last_x":
        sorted_data = sorted(
            extracted_data,
            key=lambda x: x.get('last_modified_time', datetime.min.replace(tzinfo=timezone.utc)),
            reverse=True
        )
        filtered_data = sorted_data[:count]

    elif mode == "by_date" and date:
        target_date = datetime.strptime(date, '%Y-%m-%d').date()
        filtered_data = [
            item for item in extracted_data
            if isinstance(item.get('last_modified_time'), datetime)
            and item['last_modified_time'].date() == target_date
        ]

    else:
        filtered_data = extracted_data

    print(f"Extracted {len(filtered_data)} items AFTER filtering.")
    return filtered_data


def convert_content_to_pdf(files_data, output_file):
    html_content = "<h1>OneNote Export</h1>"

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)

        for item in files_data:
            title = item.get('title', 'Untitled')
            last_modified = item.get('last_modified_time', '')
            html_content += f"<h2>{title}</h2>"
            html_content += f"<p>Last Modified: {last_modified}</p>"

            if item['type'] in {'text', 'meta'}:
                html_content += f"<pre>{item['content']}</pre><br>"

            elif item['type'] == 'image':
                encoded_image = base64.b64encode(item['content']).decode('utf-8')
                html_content += f'<img src="data:image/png;base64,{encoded_image}" style="max-width: 100%"><br>'

            elif item['type'] == 'file':
                html_content += f"<p>Embedded File: {item['file_name']}</p><br>"

            else:
                html_content += f"<p>Unknown content type: {item['type']}</p><br>"

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
    password = request.form.get("password")

    files_data = extract_content(subject, mode, count, date, password)
    if not files_data:
        abort(404, description="No content found or extraction failed.")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        pdf_path = temp_dir_path / f"{secure_filename(subject)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        convert_content_to_pdf(files_data, pdf_path)

        return send_file(pdf_path, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
