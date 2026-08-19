import argparse
import sys
import os
from dotenv import load_dotenv

load_dotenv()


def main():
    parser = argparse.ArgumentParser(
        description="AutoVideo — Render-only mode: YAML scene spec → MP4",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python render.py --scene scenes/script_a.yaml --out output/script_a.mp4
"""
    )
    parser.add_argument("--scene", required=True, help="Path to scene specification YAML file")
    parser.add_argument("--out", required=True, help="Path to output MP4 video file")
    parser.add_argument("--config", default=None, help="Path to custom config.yaml")

    args = parser.parse_args()

    if not os.path.exists(args.scene):
        print(f"ERROR: Scene specification file does not exist: {args.scene}")
        sys.exit(1)

    try:
        from src.pipeline import Pipeline
        pipeline = Pipeline(config_path=args.config)
        pipeline.run_render_only(args.scene, args.out)
    except Exception as e:
        print(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
