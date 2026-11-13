import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common.runner import run_dataset

if __name__ == "__main__":
    run_dataset("test2", "oslom")
