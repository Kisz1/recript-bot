# ฟังก์ชันเรียก OCR, LLM, Google Sheets
from ocr_llm.validation import validate_receipt
from sheets.sheets import save_receipt, get_summary_sheet
from ocr_llm.ocr import run_ocr
from ocr_llm.llm import structure_text

#tan edit
def process_receipt(image_file):
    text = run_ocr(image_file)
    data = structure_text(text)
    return data

def save_to_sheet(data):
    save_receipt(data)

def get_summary(period="daily"):
    return get_summary_sheet(period)

