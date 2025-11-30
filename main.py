import json
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from utils import download_file, process_document
from extractor import analyze_page

app = FastAPI()

@app.get("/")
def home():
    return {"status": "FastAPI running successfully!", "message": "Webhook Ready 🚀"}

class ExtractionRequest(BaseModel):
    document: str  # URL

@app.post("/extract-bill-data")
async def extract_bill_data(request: ExtractionRequest):
    
    total_tokens_used = {"input": 0, "output": 0}
    all_pages_data = []
    total_items_count = 0

    try:
        # 1) Download
        file_path = download_file(request.document)
        print("Downloaded:", file_path)

        # 2) Convert → returns list of image file paths
        pages = process_document(file_path)

        # 3) Process Page-wise
        for idx, img_path in enumerate(pages, start=1):
            print(f"Extracting Page {idx}")
            json_text, in_tok, out_tok = analyze_page(img_path, idx)

            page = json.loads(json_text)
            page["page_no"] = str(idx)

            total_tokens_used["input"] += in_tok
            total_tokens_used["output"] += out_tok
            total_items_count += len(page.get("bill_items", []))

            all_pages_data.append(page)

        return {
            "is_success": True,
            "token_usage": {
                "input_tokens": total_tokens_used["input"],
                "output_tokens": total_tokens_used["output"],
                "total_tokens": sum(total_tokens_used.values())
            },
            "data": {
                "pagewise_line_items": all_pages_data,
                "total_item_count": total_items_count
            }
        }

    except Exception as e:
        return {"is_success": False, "error": str(e), "data": None}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
