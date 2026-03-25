"""Export FastAPI's OpenAPI spec to a JSON file.

Usage:
    python -m scripts.export_openapi          # writes to ../openapi.json (project root)
    python -m scripts.export_openapi out.json  # writes to specified path
"""

import json
import sys
from pathlib import Path

from app.main import app

OUTPUT_DEFAULT = Path(__file__).resolve().parent.parent / "openapi.json"


def main() -> None:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else OUTPUT_DEFAULT
    spec = app.openapi()
    output.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n")
    print(f"OpenAPI spec written to {output}")


if __name__ == "__main__":
    main()
