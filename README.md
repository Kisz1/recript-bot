# recript-bot
# Receipt Bot

โปรเจ็คนี้คือ **Streamlit chatbot** ที่ช่วยอัพโหลดใบเสร็จ → OCR + LLM แปลงข้อมูล → บันทึกลง Google Sheets → สรุปยอดรายวัน/สัปดาห์/เดือน

---
##
💚 Frontend (Streamlit UI) → frontend/ , app.py
💚  OCR & LLM Parser → ocr_llm/
💚 Google Sheets Integration & Analytics → sheets/
💚 Backend / Integration / Deployment → backend/ + root app.py
💚 Shared utilities → utils/ (schema, common helpers)

## 🔥 งานแต่ละคน

1. **Frontend / Chatbot UI (Streamlit)**  
   - คนรับผิดชอบ: **ฟ้า**  
   - งาน:  
     - ทำหน้าเว็บ Streamlit ให้ผู้ใช้ interact กับบอท  
     - อัพโหลดไฟล์ภาพ/ข้อความ  
     - แสดง preview ของข้อมูลหลัง OCR/LLM  
     - ปุ่มยืนยัน → ส่งข้อมูลไป backend  
     - แสดงสรุปยอดรายวัน/สัปดาห์/เดือน  

2. **OCR & LLM Parser**  
   - คนรับผิดชอบ: **ตาล**  
   - งาน:  
     - OCR ใบเสร็จ (Tesseract / Google Vision)  
     - ใช้ LLM parse เป็น JSON schema `{date, total, items:[{name, price}]}`  
     - Clean / normalize (วันที่ → `YYYY-MM-DD`, เงินเป็นทศนิยม 2 ตำแหน่ง)  
     - Validate ว่า `sum(items) ≈ total`  

3. **Google Sheets Integration & Analytics**  
   - คนรับผิดชอบ: **ลุ้น**  
   - งาน:  
     - ออกแบบ schema → `Sheet1 = Receipts`, `Sheet2 = Items`  
     - เขียนฟังก์ชันบันทึกข้อมูลด้วย Google Sheets API  
     - Query / aggregation: รายวัน / สัปดาห์ / เดือน  
     - ทำ pivot / helper สำหรับ summary  

4. **Backend / Integration / Deployment**  
   - คนรับผิดชอบ: **ตูน**  
   - งาน:  
     - ทำ API ( backend ใน Streamlit)  
     - Routes:  
       - `/upload` → OCR + LLM → JSON  
       - `/confirm` → Save to Google Sheets  
       - `/summary?period=xxx`  
     - จัดการ secrets (API keys, service account)  
     - Deploy บอทบน streamlit

---

## ⚙️ วิธีใช้งาน Git
### 1. clone เริ่มทำครั้งแรก (ยังไม่มีโค้ดในเครื่อง)
```bash
   git clone git@github.com:YOUR-USERNAME/receipt-bot.git
   cd receipt-bot
   ```

### 2. Setup ครั้งแรก
```bash
cd recipt-bot
git init
git remote add origin git@github.com:YOUR-USERNAME/receipt-bot.git
git remote -v
```

### Push ครั้งแรก (ทำแค่ครั้งเดียว)
```bash
git add .
git commit -m "example message" #
git branch -M main
git push -u origin main
```

### Workflow ประจำวัน (เคย clone มาแล้ว)
```bash
    # 1. ดึงโค้ดล่าสุดก่อนเริ่มทำ
        git pull origin main
    # 2. สร้าง branch ของตัวเอง
        git checkout -b feature/frontend-ui

        #Convention:
            #feature/frontend-ui
            #feature/ocr-parser
            #feature/sheets-storage
            #feature/backend-api
            #fix/... → แก้บั๊ก
            #chore/... → config, doc
    # 3. Commit & Push
        git add path/to/your/file.py
        git commit -m "feat: Add basic Streamlit chatbot UI"
        git push origin feature/frontend-ui
```
