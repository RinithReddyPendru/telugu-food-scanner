"""
Annapurna Telugu Food Scanner & ICMR-NIN Nutrition Engine Runner.
Usage:
    python run.py                     # Start Web UI + REST API server on http://localhost:8005
    python run.py --port 8000         # Custom port
    python run.py --image dish.jpg    # Scan image from CLI
"""

import argparse
import json
import pathlib
import sys
import webbrowser

SCANNER_DIR = pathlib.Path(__file__).resolve().parent
if str(SCANNER_DIR) not in sys.path:
    sys.path.insert(0, str(SCANNER_DIR))


def main():
    parser = argparse.ArgumentParser(description="Annapurna Telugu Food Scanner & ICMR-NIN Nutrition Engine")
    parser.add_argument("--image", type=str, help="Path to a Telugu dish image to analyze in CLI mode")
    parser.add_argument("--hint", type=str, default=None, help="Optional meal hint (e.g. 'Lunch thali')")
    parser.add_argument("--port", type=int, default=8005, help="Port to run the FastAPI Web UI & REST server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host binding")
    parser.add_argument("--no-browser", action="store_true", help="Do not auto-open browser on startup")
    args = parser.parse_args()

    if args.image:
        from scanner_engine import scan_telugu_food_image
        img_path = pathlib.Path(args.image)
        if not img_path.exists():
            print(f"Error: Image file not found: {img_path}")
            sys.exit(1)
        print(f"Scanning {img_path.name} with Annapurna Vision Engine...")
        res = scan_telugu_food_image(img_path.read_bytes(), meal_hint=args.hint)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        import uvicorn
        url = f"http://localhost:{args.port}"
        print(f"================================================================")
        print(f"  Annapurna Telugu Food Scanner & ICMR-NIN Nutrition Engine")
        print(f"  Web UI:    {url}")
        print(f"  REST Docs: {url}/docs")
        print(f"================================================================")
        if not args.no_browser:
            webbrowser.open(url)
        uvicorn.run("app:app", host=args.host, port=args.port, app_dir=str(SCANNER_DIR), reload=False)


if __name__ == "__main__":
    main()
