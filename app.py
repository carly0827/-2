from flask import Flask, render_template, request, send_file
import os

app = Flask(__name__)

UPLOAD_DIR = "uploads"
RESULT_DIR = "results"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/process", methods=["POST"])
def process():
    pdf_file = request.files.get("pdf_file")
    script_file = request.files.get("script_file")

    if not pdf_file or not script_file:
        return "파일이 누락되었습니다.", 400

    pdf_path = os.path.join(UPLOAD_DIR, pdf_file.filename)
    script_path = os.path.join(UPLOAD_DIR, script_file.filename)

    pdf_file.save(pdf_path)
    script_file.save(script_path)

    result_path = os.path.join(RESULT_DIR, "result.txt")
    with open(result_path, "w", encoding="utf-8") as f:
        f.write("업로드 성공!\n")
        f.write(f"PDF: {pdf_file.filename}\n")
        f.write(f"전사본: {script_file.filename}\n")

    return send_file(result_path, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
