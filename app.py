from pathlib import Path
from datetime import datetime
import tempfile
import os
import shutil

from flask import Flask, render_template, request, send_file, abort
from werkzeug.utils import secure_filename
import comtypes.client

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

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        pdf_path = temp_dir_path / f"{secure_filename(subject)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        try:
            # Get the OneNote application object
            one_note = comtypes.client.CreateObject("OneNote.Application")

            # Open the OneNote file (you might need to adjust flags)
            # one_note.OpenHierarchy(str(file_path), "", comtypes.client.CreateObject("OneNote.HierarchyType.htNotebooks")) #This is optional

            # --- Filtering (COM-based) ---
            # This is the trickiest part.  The OneNote COM API is *extensive* and
            # not very well documented from a Python perspective.  This example
            # demonstrates a *basic* approach to getting the XML representation of
            # the notebook, which you can then parse to implement filtering.
            # You'll *definitely* need to adapt this.

            notebook_xml = one_note.GetHierarchy(None, 3) #htSectionsInNotebook 3, htPages 4
            # print(notebook_xml) # Uncomment to see the XML structure

            # **Important:**  The filtering logic using the OneNote COM API
            # will be significantly different from the Aspose.Note approach.
            # You'll need to work with the XML representation of the notebook
            # and potentially use the OneNote API to navigate and select
            # specific sections/pages based on your criteria (date, etc.).
            # This is beyond the scope of a simple example, but I'll provide
            # some guidance below.

            # --- Basic Filtering Example (by date - VERY rudimentary) ---
            if mode == "by_date" and date:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(notebook_xml)
                
                # VERY IMPORTANT:  OneNote's XML uses namespaces.  You *must*
                # include the namespace when searching for elements.
                ns = {'one': 'http://schemas.microsoft.com/office/onenote/2013/onenote'}

                for section in root.findall('.//one:Section', ns):
                    section_path = section.get('path')
                    
                    page_xml = one_note.GetHierarchy(section.get('ID'), 4) #4 = htPages
                    page_root = ET.fromstring(page_xml)

                    for page in page_root.findall('.//one:Page', ns):
                        last_modified_str = page.get('lastModifiedTime')
                        if last_modified_str and date in last_modified_str:
                            
                            one_note.Publish(page.get('ID'), str(pdf_path)) #page id, path
                            return pdf_path
                return None #No page matches

            # Publish the entire notebook to PDF (if no filtering or no matches)
            one_note.Publish(one_note.Windows.CurrentWindow.CurrentNotebookId, str(pdf_path))

            return pdf_path

        except Exception as e:
            print(f"Error during conversion: {e}")
            return None
        finally:
            # No need to explicitly close OneNote; comtypes handles that
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

    pdf_path = convert_one_to_pdf(subject, mode, count, date)
    if not pdf_path:
        abort(404, description="No content found or conversion failed.")

    try:
        return send_file(pdf_path, as_attachment=True)
    finally:
        pass

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)