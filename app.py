"""Entry point: `streamlit run app.py`.

Only puts `src/` on the import path and hands over to the frontend.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from frontend.main import main  # noqa: E402  (import after the path setup on purpose)

main()
