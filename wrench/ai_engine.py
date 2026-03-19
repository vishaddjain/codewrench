from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def analyse(code, warnings):
    if not warnings:
        return "No issues found — nothing to analyse."
    
    warnings_text = "\n".join(f"- {w}" for w in warnings)
    
    prompt = f"""
You are a performance analytics expert.

Here is the code:
{code}

These performance issues were detected:
{warnings_text}

For each issue:
1. Explain in plain English why it's a problem
2. Show a fixed version of that specific code
3. Explain why the fix is better

Be concise and practical.
"""
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content