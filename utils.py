import os
import requests
import tempfile
from pdf2image import convert_from_path
from PIL import Image

# -----------------------------------------------------------
# 1) Download file (PDF / PNG / JPG) and keep it on disk
# -----------------------------------------------------------
def download_file(url: str) -> str:
    response = requests.get(url, stream=True)
    response.raise_for_status()

    ctype = response.headers.get("content-type", "")
    ext = ".pdf"
    if "png" in ctype: ext = ".png"
    if "jpeg" in ctype or "jpg" in ctype: ext = ".jpg"

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    for chunk in response.iter_content(8192):
        tmp.write(chunk)
    tmp.close()

    return tmp.name   # return file path safely


# -----------------------------------------------------------
# 2) Convert PDF to images → return actual image FILE PATHS
# -----------------------------------------------------------
def process_document(file_path: str) -> list[str]:
    output_files = []

    if file_path.lower().endswith(".pdf"):
        pages = convert_from_path(file_path)
        for i, page in enumerate(pages):
            out_path = f"{file_path}_page{i+1}.png"  # save pages separately
            page.save(out_path)
            output_files.append(out_path)

    else:
        output_files.append(file_path)   # PNG/JPG comes directly

    return output_files  # RETURN PATHS ONLY (very important!)
