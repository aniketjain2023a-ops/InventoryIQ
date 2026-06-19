

import os
import google.generativeai as genai


GEMINI_MODEL = "gemini-2.5-flash"



def configure_gemini(api_key=None):
    api_key = api_key or os.getenv("GEMINI_API_KEY", "")

    if not api_key:
        return False

    genai.configure(api_key=api_key)
    return True



def get_inventory_summary(products, purchase_orders=None):
    prompt = f"""
    You are an inventory management expert.

    Products:
    {products}

    Purchase Orders:
    {purchase_orders or []}

    Provide:
    1. Inventory health summary
    2. Reorder risks
    3. Supplier risks
    4. Recommended actions
    """

    model = genai.GenerativeModel(GEMINI_MODEL)
    response = model.generate_content(prompt)
    return response.text



def get_reorder_advice(product_data):
    prompt = f"""
    Analyze the following inventory data and recommend reorder quantities.

    {product_data}

    Include:
    - Priority level
    - Recommended order quantity
    - Explanation
    """

    model = genai.GenerativeModel(GEMINI_MODEL)
    response = model.generate_content(prompt)
    return response.text



def chat_with_inventory(question, inventory_context):
    prompt = f"""
    Inventory Context:
    {inventory_context}

    User Question:
    {question}

    Answer as an inventory management assistant.
    """

    model = genai.GenerativeModel(GEMINI_MODEL)
    response = model.generate_content(prompt)
    return response.text