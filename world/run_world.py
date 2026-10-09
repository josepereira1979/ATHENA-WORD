from __future__ import annotations

import argparse
import json

from world.orchestration.world_runtime import WorldRuntime


def main() -> int:
    parser = argparse.ArgumentParser(description="ATHENA WORLD control CLI")
    parser.add_argument("command", choices=("status", "integrity", "preview", "readiness", "prepare", "finalize", "cycle", "sync-sec"))
    parser.add_argument("--cycles", type=int, default=1)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument(
        "--user-agent",
        default=None,
        help="Identificação descritiva exigida pelo SEC, incluindo contacto real do operador.",
    )
    parser.add_argument(
        "--max-new",
        type=int,
        default=None,
        help="Limita o número de registos SEC processados; não atribui famílias automaticamente.",
    )
    args = parser.parse_args()

    runtime = WorldRuntime()
    if args.command == "status":
        result = runtime.world_snapshot()
    elif args.command == "integrity":
        result = runtime.world_integrity()
    elif args.command == "preview":
        result = runtime.preview_global_world(limit=args.limit)
    elif args.command == "readiness":
        result = runtime.launch_readiness()
    elif args.command == "prepare":
        result = runtime.prepare_world(allocate=False, cycles=0)
    elif args.command == "finalize":
        result = runtime.finalize_global_world()
    elif args.command == "sync-sec":
        if not args.user_agent:
            parser.error("sync-sec exige --user-agent com uma identificação e contacto válidos.")
        if args.max_new is not None and args.max_new < 0:
            parser.error("--max-new não pode ser negativo.")
        result = runtime.sync_sec_global_companies(
            user_agent=args.user_agent,
            max_new=args.max_new,
            allocate=False,
        )
    else:
        result = runtime.run_cycles(max(1, args.cycles))

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
