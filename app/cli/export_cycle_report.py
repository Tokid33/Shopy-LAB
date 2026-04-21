import argparse

from app.db.session import SessionLocal
from app.services.cycle_report import HypothesisNotFoundError, export_cycle_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Export Shopify Lab cycle report")
    parser.add_argument("--hypothesis-id", type=int, required=True, help="Hypothesis ID to export")
    parser.add_argument("--output-dir", type=str, default="artifacts/reports", help="Output directory")
    args = parser.parse_args()

    with SessionLocal() as db:
        try:
            json_path, md_path = export_cycle_report(db, args.hypothesis_id, output_dir=args.output_dir)
        except HypothesisNotFoundError as exc:
            raise SystemExit(f"Error: {exc}") from exc

    print(f"Cycle report exported:\n- JSON: {json_path}\n- Markdown: {md_path}")


if __name__ == "__main__":
    main()
