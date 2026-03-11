import sys
from pathlib import Path

project_root = Path(__file__).parent

# Ensure imports like `from src...` work regardless of where this is launched from.
sys.path.insert(0, str(project_root))

# Run the app
if __name__ == "__main__":
    import streamlit.web.cli as stcli

    # Prefer the old location if present; otherwise use the root app entrypoint.
    ui_app = project_root / "src" / "ui" / "main_app.py"
    root_app = project_root / "main_app.py"
    app_path = ui_app if ui_app.exists() else root_app

    sys.argv = ["streamlit", "run", str(app_path)]
    sys.exit(stcli.main())
