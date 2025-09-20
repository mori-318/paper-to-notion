import os
import sys
from pathlib import Path

# プロジェクトのルートディレクトリをsys.pathに追加
ROOT = Path(__file__).resolve().parents[1]
SRC = os.path.join(str(ROOT), "src")
if SRC not in sys.path:
    sys.path.append(SRC)
