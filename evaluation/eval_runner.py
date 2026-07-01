import sys
import os
sys.stdout.reconfigure(line_buffering=True)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import json
import time
from pathlib import Path
from datetime import datetime

from agent.graph import ask

QUESTIONS_FILE = Path(__file__).parent / "test_questions.json"
RESULTS_FILE   = Path(__file__).parent / "eval_results.json"


def run_evaluation():
    with open(QUESTIONS_FILE) as f:
        questions = json.load(f)

    results = []
    correct = 0
    total = len(questions)

    print(f"Running evaluation on {total} questions...\n")

    for q in questions:
        print(f"[Q{q['id']:02d}] {q['question'][:60]}...")
        start = time.time()

        try:
            result = ask(q['question'])
            actual = result['route']
            elapsed = round(time.time() - start, 2)
            is_correct = actual == q['expected_route']

            if is_correct:
                correct += 1
                print(f"  ✅ Expected: {q['expected_route']} | Got: {actual} | {elapsed}s")
            else:
                print(f"  ❌ Expected: {q['expected_route']} | Got: {actual} | {elapsed}s")

            results.append({
                "id": q['id'],
                "question": q['question'],
                "expected": q['expected_route'],
                "actual": actual,
                "correct": is_correct,
                "elapsed_s": elapsed,
            })

        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            results.append({
                "id": q['id'], "question": q['question'],
                "expected": q['expected_route'], "actual": "error",
                "correct": False, "elapsed_s": 0,
            })

        time.sleep(13)

    accuracy = round(correct / total * 100, 1)
    avg_latency = round(sum(r['elapsed_s'] for r in results) / total, 2)
    
    
    
    
if __name__ == "__main__":
    run_evaluation()