import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
PROMPTS_DIR = BASE_DIR / "prompts"

def load_json(filename):
    with open(PROMPTS_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)

FINAL_SOLUTIONS = load_json("final_solutions.json")

# Convert keys to int here so hintCounter works correctly
INSTRUCTIONAL_PROMPTS = {
    int(k): v for k, v in load_json("instructional_prompts.json").items()
}

WORKED_EXAMPLE_PROMPTS = {
    int(k): v for k, v in load_json("worked_example_prompts.json").items()
}
