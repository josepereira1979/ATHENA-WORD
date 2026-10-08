from __future__ import annotations

import argparse
import json

from world.orchestration.world_runtime import WorldRuntime


def main() -> int:
    parser = argparse.ArgumentParser(description="ATHENA WORLD control CLI")
    parser.add_argument("command", choices=("status", "integrity", "preview", "cycle"))
    parser.add_argument("--cycles", type=int, default=1)
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    runtime = WorldRuntime()
    if args.command == "status":
        result = runtime.world_snapshot()
    elif args.command == "integrity":
        result = runtime.world_integrity()
    elif args.command == "preview":
        result = runtime.preview_global_world(limit=args.limit)
    else:
        result = runtime.run_cycles(max(1, args.cycles))

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
