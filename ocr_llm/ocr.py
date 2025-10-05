from PIL import Image
import pytesseract
import io
import os

# def run_ocr(image_file):
#     """แปลงรูปภาพเป็นข้อความด้วย Tesseract OCR """
    
#     # mock function: สมมติว่า OCR คืนข้อความมา
#     return "7-Eleven\nCoke x1 20\nBread x2 15\nTotal 50"
def run_ocr(uploaded_file):
    try:
        from google.cloud import vision
        client = vision.ImageAnnotatorClient()
        content = uploaded_file.getvalue()
        image = vision.Image(content=content)
        response = client.text_detection(image=image)
        
        if response.error.message:
            raise Exception(response.error.message)
        texts = response.text_annotations
        if texts and len(texts[0].description.strip()) > 10:
            return texts[0].description, "Google Vision"
        else:
            raise Exception("Vision returned too little text")
    except Exception as e:
        img = Image.open(uploaded_file)
        text = pytesseract.image_to_string(img, lang="tha+eng")
        return text, f"Tesseract (fallback: {e})"