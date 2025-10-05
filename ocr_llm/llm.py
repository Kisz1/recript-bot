import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def structure_text(text: str) -> dict:
    prompt = f"""
    Extract the following fields from the receipt text:
    - date (in YYYY-MM-DD format)
    - shop (name of the store)
    - items (list of items with name, quantity, and price)
    - total (total amount)

    Receipt Text:
    {text}

    Return the result as a JSON object with keys: date, shop, items, total.
    Example:
    {{
        "date": "2025-09-30",
        "shop": "7-Eleven",
        "items": [
            {{"name": "Coke", "qty": 1, "price": 20}},
            {{"name": "Bread", "qty": 2, "price": 15}}
        ],
        "total": 50
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that extracts structured data from receipt text."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500,
        temperature=0
    )
    result_text = response.choices[0].message.content

    try:
        result_json = json.loads(result_text)
        return result_json
    except json.JSONDecodeError:
        raise ValueError(f"Failed to parse JSON from LLM response: {result_text}")



