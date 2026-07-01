import sys
sys.stdout.reconfigure(line_buffering=True)
print("step 1")

import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
print("step 2")

from dotenv import load_dotenv
load_dotenv()
print("step 3")

from agent.graph import ask
print("step 4")

result = ask("Which driver was most aggressive?")
print("step 5")
print(result)