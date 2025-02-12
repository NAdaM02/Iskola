app = Flask(__name__)

# Ensure BASE_DIR is correctly set
BASE_DIR = Path.cwd().parent / "2024-25"  # Moves one directory up
print("Current working directory:", Path.cwd())
print("Expected BASE_DIR:", BASE_DIR)

if not BASE_DIR.exists():
    print("Warning: BASE_DIR does not exist. Check the folder structure!")

EXCLUDED_SUBJECTS = {"Németh", "Zeneirodalom", "Matek", "Fizika"}
TEMP_DIR = Path("data")
TEMP_DIR.mkdir(exist_ok=True)

@app.route("/")
def index():
    if not BASE_DIR.exists():
        return "Error: Base directory does not exist!", 500

    subjects = [
        s.name for s in BASE_DIR.iterdir() 
        if s.is_dir() and s.name not in EXCLUDED_SUBJECTS
    ]
    return render_template("index.html", subjects=subjects)
