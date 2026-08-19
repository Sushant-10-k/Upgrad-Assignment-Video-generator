import argparse
import sys
import os
from dotenv import load_dotenv

load_dotenv()


def main():
    parser = argparse.ArgumentParser(
        description="AutoVideo — Deterministic Script-to-Explainer Video Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py --script scripts/script_a.txt --out output/script_a.mp4
  python run.py --script scripts/script_b.txt --out output/script_b.mp4 --config config/config.yaml
"""
    )
    parser.add_argument("--script", required=True, help="Path to input UTF-8 plain-text narration script")
    parser.add_argument("--out", required=True, help="Path to output MP4 video file")
    parser.add_argument("--config", default=None, help="Path to custom config.yaml (default: config/config.yaml)")
    parser.add_argument("--save-spec", default=None, dest="save_spec",
                        help="Path to save intermediate scene specification YAML (default: scenes/<script>.yaml)")

    args = parser.parse_args()

    if not os.path.exists(args.script):
        print(f"ERROR: Script file does not exist: {args.script}")
        sys.exit(1)

    try:
        from src.pipeline import Pipeline
        pipeline = Pipeline(config_path=args.config)
        pipeline.run_full(args.script, args.out, scene_save_path=args.save_spec)
    except Exception as e:
        print(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
