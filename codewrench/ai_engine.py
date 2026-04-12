from groq import Groq
from dotenv import load_dotenv
import os

#For single file
def analyse(code, warnings):
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    if not warnings:
        return "No issues found — nothing to analyse."
    
    warnings_text = "\n".join(f"- {w['message']}" for w in warnings)
    
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

#For Folder
def analyse_folder(all_results):
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    if not all_results:
        return "No issues found — nothing to analyse."
    
    combined = ""
    for filepath, warnings in all_results.items():
        warnings_text = "\n".join(f"- {w['message']}" for w in warnings)
        combined += f"\nFile: {filepath}\n{warnings_text}\n"
    
    prompt = f"""
You are a performance analytics expert.

These performance issues were detected across a codebase:

{combined}

For each file, go through each issue and:
1. Explain in plain English why it's a problem
2. Suggest a fix with a short code example
3. Explain why the fix is better

Be concise and practical. Group your response by file.
"""
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

#For testing purpose to differentiate the performance
def get_fixed_code(code, warnings):
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    if not warnings:
        return code
    
    warnings_text = "\n".join(f"- {w['message']}" for w in warnings)
    
    prompt = f"""
You are a performance analytics expert.

Here is the original code:
{code}

These performance issues were detected:
{warnings_text}

Return ONLY the fixed version of the complete code.
No explanations, no comments, no markdown, no code blocks.
Just the raw fixed code that can be executed directly.
"""
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content