"""Check your Gemini key: lists the models it can use and makes one tiny test call. Never prints the key.

Run from the backend folder:  pipenv run python scripts/check_gemini.py
Then put the model you want in .env as GEMINI_MODEL=...
"""
import os
import sys

from dotenv import load_dotenv

here = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(here, "..", "..", ".env"))
load_dotenv(os.path.join(here, "..", ".env"))
key = os.getenv("GOOGLE_API_KEY")
if not key:
    sys.exit("GOOGLE_API_KEY is not set (check the .env file in the repo root).")
print(f"GOOGLE_API_KEY found (length {len(key)}).")

from app import llm  # noqa: E402

try:
    names = llm.list_models(key)
except Exception as e:
    sys.exit(f"Could not list models: {type(e).__name__}: {str(e)[:200]}")

flash = [n for n in names if "flash" in n and not any(x in n for x in llm._EXCLUDE)]
print("\nModels your key can call (flash family):")
for n in flash:
    print("  ", n)
chosen = llm.pick_model(names)
print(f"\nThe app will auto-pick: {chosen}")
print("(To force a different one, add GEMINI_MODEL=<name> to .env)")

model = os.getenv("GEMINI_MODEL") or chosen
print(f"\nTest call with {model} ...")
try:
    print("Reply:", llm.text_of(llm.gemini(model).invoke("Reply with the single word: ready")).strip())
except Exception as e:
    print(f"Test call failed: {type(e).__name__}: {str(e)[:300]}\nTry another name from the list and set GEMINI_MODEL in .env.")
