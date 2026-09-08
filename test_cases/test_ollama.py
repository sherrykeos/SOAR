import requests


prompt = """
You are the planning component of SOAR.

Create a simple step-by-step plan for this task:

TASK:
Read an inspection report and create an approval note

Rules:
- Return only numbered steps.
- Each step must describe one concrete action.
- Use 2 to 6 steps.
- Do not execute the task.
"""

print("[TEST] Sending request...", flush=True)

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "qwen3:4b",
        "prompt": prompt,
        "stream": False,
        "think": False,
    },
    timeout=180,
)

print("[TEST] Response received", flush=True)

response.raise_for_status()

data = response.json()

print("\n===== RESPONSE =====")
print(data["response"])
print("====================")