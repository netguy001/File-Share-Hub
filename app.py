import os
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_from_directory,
    flash,
    session,
)
from werkzeug.utils import secure_filename
import datetime

app = Flask(__name__)
app.secret_key = "your-secret-key-change-this-in-production"

# Admin Credentials - Change these values
ADMIN_USERNAME = "pcboy"
ADMIN_PASSWORD = "cant_findit#@boys"

# Configuration
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {
    # Documents
    "txt",
    "pdf",
    "doc",
    "docx",
    "xlsx",
    "xls",
    "ppt",
    "pptx",
    "odt",
    "ods",
    "odp",
    "rtf",
    "csv",
    "md",
    "epub",
    # Images
    "png",
    "jpg",
    "jpeg",
    "gif",
    "webp",
    "svg",
    "bmp",
    "tiff",
    "tif",
    "ico",
    "psd",
    "ai",
    "eps",
    # Audio
    "mp3",
    "wav",
    "flac",
    "aac",
    "ogg",
    "wma",
    "m4a",
    "mid",
    "midi",
    # Video
    "mp4",
    "avi",
    "mov",
    "wmv",
    "flv",
    "webm",
    "mkv",
    "m4v",
    "3gp",
    # Programming
    "js",
    "jsx",
    "ts",
    "tsx",
    "py",
    "java",
    "cpp",
    "c",
    "cs",
    "php",
    "rb",
    "go",
    "rs",
    "html",
    "css",
    "scss",
    "sass",
    "json",
    "xml",
    "yaml",
    "yml",
    "sql",
    "sh",
    "bat",
    "vue",
    "svelte",
    # Archives
    "zip",
    "rar",
    "7z",
    "tar",
    "gz",
    "bz2",
    # Other
    "log",
    "cfg",
    "ini",
    "conf",
}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

# Create upload directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def allowed_file(filename):
    """Check if file extension is allowed"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_info(filepath):
    """Get file information including size and upload date"""
    stat = os.stat(filepath)
    size = stat.st_size
    modified_time = datetime.datetime.fromtimestamp(stat.st_mtime)

    # Convert size to human readable format
    if size < 1024:
        size_str = f"{size} B"
    elif size < 1024 * 1024:
        size_str = f"{size / 1024:.1f} KB"
    else:
        size_str = f"{size / (1024 * 1024):.1f} MB"

    return {"size": size_str, "modified": modified_time.strftime("%Y-%m-%d %H:%M:%S")}


def require_admin():
    """Check if user is logged in as admin"""
    if "admin_logged_in" not in session:
        return redirect(url_for("admin_login"))
    return None


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Admin login page"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            flash("Login successful! Welcome to admin panel.", "success")
            return redirect(url_for("admin_manage"))
        else:
            flash("Invalid username or password", "error")

    return render_template("login.html")


@app.route("/admin/logout")
def admin_logout():
    """Admin logout"""
    session.pop("admin_logged_in", None)
    flash("Logged out successfully", "success")
    return redirect(url_for("index"))


@app.route("/")
def index():
    """Landing page"""
    return render_template("index.html")


@app.route("/admin/upload", methods=["GET", "POST"])
def upload_file():
    """Admin upload page"""
    auth_check = require_admin()
    if auth_check:
        return auth_check

    if request.method == "POST":
        # Check if file was uploaded
        if "file" not in request.files:
            flash("No file selected", "error")
            return redirect(request.url)

        file = request.files["file"]

        # Check if file is selected
        if file.filename == "":
            flash("No file selected", "error")
            return redirect(request.url)

        # Check if file is allowed and save it
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            # Handle duplicate filenames
            counter = 1
            original_filename = filename
            while os.path.exists(os.path.join(app.config["UPLOAD_FOLDER"], filename)):
                name, ext = os.path.splitext(original_filename)
                filename = f"{name}_{counter}{ext}"
                counter += 1

            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            flash(f'File "{filename}" uploaded successfully!', "success")
            return redirect(url_for("upload_file"))
        else:
            flash(
                "File type not allowed. Allowed types: "
                + ", ".join(ALLOWED_EXTENSIONS),
                "error",
            )

    return render_template("upload.html")


@app.route("/dashboard")
def dashboard():
    """User dashboard showing all uploaded files"""
    files = []
    image_count = 0
    document_count = 0
    upload_path = app.config["UPLOAD_FOLDER"]

    # Define file type categories
    image_extensions = {
        "jpg",
        "jpeg",
        "png",
        "gif",
        "webp",
        "svg",
        "bmp",
        "tiff",
        "tif",
        "ico",
    }
    document_extensions = {
        "pdf",
        "doc",
        "docx",
        "txt",
        "xlsx",
        "xls",
        "ppt",
        "pptx",
        "odt",
        "rtf",
        "csv",
        "md",
        "epub",
    }

    if os.path.exists(upload_path):
        for filename in os.listdir(upload_path):
            if os.path.isfile(os.path.join(upload_path, filename)):
                file_path = os.path.join(upload_path, filename)
                file_info = get_file_info(file_path)
                files.append(
                    {
                        "name": filename,
                        "size": file_info["size"],
                        "modified": file_info["modified"],
                    }
                )

                # Count file types
                if "." in filename:
                    ext = filename.rsplit(".", 1)[1].lower()
                    if ext in image_extensions:
                        image_count += 1
                    elif ext in document_extensions:
                        document_count += 1

    # Sort files by modification time (newest first)
    files.sort(key=lambda x: x["modified"], reverse=True)

    return render_template(
        "dashboard.html",
        files=files,
        image_count=image_count,
        document_count=document_count,
    )


@app.route("/download/<filename>")
def download_file(filename):
    """Download file from uploads directory"""
    try:
        return send_from_directory(
            app.config["UPLOAD_FOLDER"], filename, as_attachment=True
        )
    except FileNotFoundError:
        flash("File not found", "error")
        return redirect(url_for("dashboard"))


@app.route("/admin/delete/<filename>", methods=["POST"])
def delete_file(filename):
    """Admin delete file"""
    auth_check = require_admin()
    if auth_check:
        return auth_check

    try:
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            flash(f'File "{filename}" deleted successfully!', "success")
        else:
            flash("File not found", "error")
    except Exception as e:
        flash(f"Error deleting file: {str(e)}", "error")

    return redirect(url_for("admin_manage"))


@app.route("/admin/manage")
def admin_manage():
    """Admin file management page"""
    auth_check = require_admin()
    if auth_check:
        return auth_check

    files = []
    upload_path = app.config["UPLOAD_FOLDER"]

    if os.path.exists(upload_path):
        for filename in os.listdir(upload_path):
            if os.path.isfile(os.path.join(upload_path, filename)):
                file_path = os.path.join(upload_path, filename)
                file_info = get_file_info(file_path)
                files.append(
                    {
                        "name": filename,
                        "size": file_info["size"],
                        "modified": file_info["modified"],
                    }
                )

    # Sort files by modification time (newest first)
    files.sort(key=lambda x: x["modified"], reverse=True)

    return render_template("admin_manage.html", files=files)


@app.route("/admin/rename/<filename>", methods=["POST"])
def rename_file(filename):
    """Admin rename file"""
    auth_check = require_admin()
    if auth_check:
        return auth_check

    new_name = request.form.get("new_name")
    if not new_name:
        flash("New filename cannot be empty", "error")
        return redirect(url_for("admin_manage"))

    try:
        old_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        new_filename = secure_filename(new_name)
        new_path = os.path.join(app.config["UPLOAD_FOLDER"], new_filename)

        if os.path.exists(new_path):
            flash("A file with that name already exists", "error")
            return redirect(url_for("admin_manage"))

        if os.path.exists(old_path):
            os.rename(old_path, new_path)
            flash(
                f'File renamed from "{filename}" to "{new_filename}" successfully!',
                "success",
            )
        else:
            flash("Original file not found", "error")
    except Exception as e:
        flash(f"Error renaming file: {str(e)}", "error")

    return redirect(url_for("admin_manage"))


@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    flash("File is too large. Maximum size is 16MB.", "error")
    return redirect(url_for("upload_file"))


if __name__ == "__main__":
    print("Starting Flask File Sharing Application...")
    print("Access the application at: http://localhost:5000")
    print("Admin upload page: http://localhost:5000/admin/upload")
    print("Dashboard: http://localhost:5000/dashboard")
    app.run(debug=True, host="0.0.0.0", port=5000)
