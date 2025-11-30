import os, base64, json
from typing import List, Literal
from pydantic import BaseModel, Field
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ---------------- Schema ----------------
class BillItem(BaseModel):
    item_name: str
    item_amount: float
    item_rate: float
    item_quantity: float

    class Config:
        extra = "ignore"  # <== This fixes schema crash


class PageData(BaseModel):
    page_no: str
    page_type: Literal["Bill Detail", "Final Bill", "Pharmacy"]
    bill_items: List[BillItem]

    class Config:
        extra = "ignore"  # <== extremely important

# ------------ Convert Image Path → base64 before sending ------------
def encode_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


# ------------ Main Extraction Function ------------
def analyze_page(image_path: str, page_number: int):
    """
    Sends an image file path to Gemini, returns structured JSON result.
    """
    encoded_img = encode_image(image_path)

    prompt = f"""
    Extract detailed bill items from hospital bill image - Page {page_number}.
    Output must strictly follow the JSON schema.

    Rules:
    - Extract ONLY item rows (not totals/subtotals/discount/summary).
    - Convert numbers to float.
    - If qty missing → default to 1.0
    - "Final Bill" page should return empty bill_items unless new items exist.
    """

    model = genai.GenerativeModel("gemini-2.5-flash")

    try:
        result = model.generate_content(
            [
                {"mime_type": "image/png", "data": encoded_img},
                prompt
            ],
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=PageData
            )
        )

        usage = result.usage_metadata
        return result.text, usage.prompt_token_count, usage.candidates_token_count

    except Exception as e:
        print("\n 🔻 Extraction failed on page", page_number, ":", e)
        return json.dumps({
            "page_no": str(page_number),
            "page_type": "Bill Detail",
            "bill_items": []
        }), 0, 0
