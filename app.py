# import streamlit as st
# # backend/services.py
# from sheets.sheets import save_receipt, get_summary_sheet
# from backend.services import process_receipt, save_to_sheet, get_summary

# st.title("📸 Receipt Bot")
# st.write("อัพโหลดใบเสร็จ → ระบบจะ OCR + LLM + ส่งเข้า Google Sheets")

# uploaded_file = st.file_uploader("Upload Receipt", type=["jpg", "jpeg", "png"]) # ให้ผู้ใช้เลือกอัปโหลดรูปใบเสร็จ

# if uploaded_file:
#     st.image(uploaded_file, caption="Uploaded Receipt", use_column_width=True)

#     if st.button("Process Receipt"):
#         with st.spinner("Processing..."):
#             data = process_receipt(uploaded_file) # เรียกใช้ฟังก์ชัน OCR + LLM เพื่อดึงข้อมูลจากใบเสร็จ

#         st.subheader("📑 Extracted Data")
#         st.json(data)

#         if st.button("Save to Google Sheets"): # ส่งข้อมูลไปบันทึกใน Google Sheets
#             save_to_sheet(data)
#             st.success("✅ Saved to Google Sheets")

# st.subheader("📊 Summary")
# period = st.selectbox("เลือกช่วงเวลา", ["daily", "weekly", "monthly"])
# if st.button("Get Summary"):
#     summary = get_summary(period)  # ดึงข้อมูลสรุปจาก Google Sheets (เช่น รายวัน/สัปดาห์/เดือน)
#     st.write(summary)
# app.py — Streamlit + OpenAI Vision + Supabase (แทน Google Sheets)





import os, base64, json
from datetime import datetime, timedelta
from dateutil import parser as dparse
import pandas as pd
import streamlit as st
from supabase import create_client
from openai import OpenAI   # << ใช้ไวยากรณ์ SDK v1

# 1) ต้องเรียก set_page_config ให้เร็วที่สุด (ก่อนมี output ใด ๆ)
st.set_page_config(page_title="📸 Receipt Bot", page_icon="🧾", layout="centered")

# 2) โหลด secrets/ENV แบบ fallback (รันได้ทั้ง local และ Streamlit Cloud)
def S(key, default=None):
    return (st.secrets.get(key) if key in st.secrets else os.getenv(key, default))

OPENAI_API_KEY = S("OPENAI_API_KEY")
SUPABASE_URL = S("SUPABASE_URL")
SUPABASE_SERVICE_KEY = S("SUPABASE_SERVICE_KEY")

if not (OPENAI_API_KEY and SUPABASE_URL and SUPABASE_SERVICE_KEY):
    st.error("Missing secrets: ต้องตั้งค่า OPENAI_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY")
    st.stop()

# 3) สร้าง clients
client = OpenAI(api_key=OPENAI_API_KEY)
sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

st.title("📸 Receipt Bot")
st.write("อัปโหลดใบเสร็จ → LLM Extract → บันทึกที่ Supabase → ดูสรุป")

# 4) ฟังก์ชัน Vision → JSON (อัปเดตให้เข้ากับ openai==1.44.0)
def vision_extract_json(file_bytes: bytes, mime: str) -> dict:
    """ให้ GPT-4o อ่านรูปใบเสร็จและคืน JSON ตามสคีมา"""
    if not mime:
        mime = "image/png"
    b64 = base64.b64encode(file_bytes).decode()
    data_url = f"data:{mime};base64,{b64}"

    prompt = (
        "You are a receipt parser for Thai receipts. "
        "Extract STRICT JSON with keys: vendor, date (YYYY-MM-DD), "
        "items[{name, qty, unit_price}], subtotal, tax, total, currency. "
        "Return ONLY JSON (no markdown/prose)."
    )

    resp = client.chat.completions.create(   # << new SDK call
        model="gpt-4o-mini",
        temperature=0,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": data_url}}
            ]
        }]
    )

    raw = resp.choices[0].message.content
    # บางรุ่นอาจส่งเป็นชิ้น ๆ; ที่นี่คาดหวังเป็นสตริงเดียว
    try:
        data = json.loads(raw)
    except Exception:
        # ถ้าตอบไม่ใช่ JSON ล้วน แสดงผลดิบไว้ช่วยดีบั๊ก
        raise ValueError(f"Model did not return pure JSON:\n{raw}")

    # normalize วันที่
    try:
        data["date"] = dparse.parse(str(data.get("date"))).date().isoformat()
    except Exception:
        pass
    return data

def save_to_supabase(rec: dict) -> bool:  # save at supabase
    payload = {                           # จัดรูป payload ให้ตรง schema ของตาราง receipt ใน supabase
        "date": rec.get("date"),          # ตอนนี้ยังไม่ได้จัด ลุ้นจัดเด้อ
        "vendor": rec.get("vendor"),
        "total": rec.get("total"),
        "subtotal": rec.get("subtotal"),
        "tax": rec.get("tax"),
        "currency": rec.get("currency", "THB"),
        "items_json": rec.get("items", []),       # items_json เก็บ items ทั้ง array ลงคอลัมน์ JSONB
        "user_id": rec.get("user_id", ""),
        "raw_text": "",  # ไม่จำเป็นเพราะส่งรูปให้ LLM ตรง ๆ
    }
    try:
        res = sb.table("receipts").insert(payload).execute()
        # แสดงผลลัพธ์เพื่อวินิจฉัย
        st.write("Insert result:", res.data)
        return bool(res.data)
    except Exception as e:
        st.error("Insert failed:")
        st.exception(e)  # โชว์ stacktrace/ข้อความจาก Supabase
        return False        # เพื่อบอกว่าบันทึกสำเร็จไหม

def get_period_range(kind: str):          # สร้างกรอบช่วงเวลา
    today = datetime.utcnow().date()
    if kind == "daily":
        start, end = today, today
    elif kind == "weekly":
        start = today - timedelta(days=6)
        end = today
    else:  # monthly
        start = today.replace(day=1)
        end = today
    return start, end

def query_summary(kind: str, user_id: str | None = None) -> pd.DataFrame:   # ดึงสรุปจาก Supabase
    start, end = get_period_range(kind)
    q = sb.table("receipts").select("*").gte("date", str(start)).lte("date", str(end)).order("date", desc=False)
    if user_id:
        q = q.eq("user_id", user_id)
    rows = q.execute().data or []
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for col in ["total","subtotal","tax"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

# ---------- UI: Upload ----------
st.subheader("📥 Upload")
col1, col2 = st.columns([2,1])
with col1:
    uploaded = st.file_uploader("อัปโหลดรูปใบเสร็จ", type=["jpg","jpeg","png","webp"])
with col2:
    user_id = st.text_input("User ID (optional)", value="")

if uploaded:
    st.image(uploaded, caption="Uploaded Receipt", use_column_width=True)
    if st.button("Process Receipt"):
        try:
            with st.spinner("Extracting with GPT-4o..."):
                data = vision_extract_json(uploaded.getvalue(), uploaded.type)
                data["user_id"] = user_id
            st.session_state["pending_receipt"] = data
            st.success("✅ Extracted")
            st.subheader("📑 Extracted Data")
            st.json(data)
        except Exception as e:
            st.error(f"ไม่สามารถสกัด JSON ได้: {e}")

            """
ให้ผู้ใช้อัปโหลดรูป + ใส่ user_id (ถ้าต้องการ)

แสดงรูป preview

เมื่อกด Process:

เรียก vision_extract_json(...)

เก็บผลลัพธ์ไว้ใน st.session_state["pending_receipt"] (จำค่าข้าม interaction ได้)

โชว์ JSON ให้ตรวจสอบ
            """

# ---------- UI: Confirm & Save ----------
st.subheader("✅ Confirm & Save")
pending = st.session_state.get("pending_receipt")
if not pending:
    st.info("ยังไม่มีข้อมูลรอยืนยัน (กด Process ก่อน)")
else:
    # ให้แก้ไขได้เล็กน้อยก่อนบันทึก
    edited_total = st.number_input("total", value=float(pending.get("total", 0) or 0.0))
    pending["total"] = edited_total
    if st.button("Save to Supabase"):
        ok = save_to_supabase(pending)
        if ok:
            st.success("บันทึกสำเร็จที่ Supabase")
            st.session_state.pop("pending_receipt", None)
        else:
            st.error("บันทึกล้มเหลว ตรวจตาราง/สิทธิ์ใน Supabase")

# ---------- UI: Summary ----------
st.subheader("📊 Summary")
period = st.selectbox("เลือกช่วงเวลา", ["daily", "weekly", "monthly"], index=2)
filter_user = st.text_input("Filter user_id (optional)", value="")
if st.button("Get Summary"):
    df = query_summary(period, filter_user or None)
    if df.empty:
        st.info("ไม่มีข้อมูลในช่วงนี้")
    else:
        total = float(df["total"].sum()) if "total" in df.columns else 0.0
        start, end = get_period_range(period)
        st.write(f"ช่วง: {start} – {end} | รายการ: {len(df)}")
        st.metric("รวมทั้งหมด (THB)", f"{total:,.2f}")
        if "date" in df.columns and "total" in df.columns:
            daily = df.groupby(df["date"].dt.date)["total"].sum()
            st.line_chart(daily)
        st.dataframe(df)
"""
ถ้ามี pending_receipt ใน session → ให้แก้ไข total ได้เล็กน้อยก่อนเซฟ

กด Save → เรียก save_to_supabase → แจ้งผล และล้าง state เมื่อสำเร็จ
"""