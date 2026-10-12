import os

from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("LLM_MODEL", "minimax/minimax-m3:free")
MAX_STEPS = 15

FINAL_ANSWER = (
    "Your search budget is used up. Do not call any more tools. "
    "Write your final answer now, using only the results you have found so far."
)