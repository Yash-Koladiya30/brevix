"""Brevix CLI entrypoint."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from brevix import (
    Compressor,
    CompressionMode,
    AccuracyGuard,
    Stats,
    pick_mode,
    count_tokens,
    count_tokens_method,
    install as install_target,
    list_targets,
    TARGETS,
    __version__,
)
from brevix.file_compress import compress_file


def _cmd_compress(args: argparse.Namespace) -> int:
    text = args.text
    if text == "-" or not text:
        text = sys.stdin.read()

    if args.mode == "auto":
        adaptive = pick_mode(text, threshold=args.threshold)
        result = adaptive.compression
        guard_result = adaptive.guard
        chosen = adaptive.chosen_mode
        if not guard_result.passed and args.strict:
            sys.stderr.write(
                f"[brevix] auto: no mode passed guard ({guard_result.similarity:.2f} < {args.threshold:.2f}). "
                f"Emitting original.\n"
            )
            print(text)
            return 2
        if args.verbose:
            sys.stderr.write(f"[brevix] auto picked mode={chosen.value}\n")
    else:
        chosen = CompressionMode(args.mode)
        result = Compressor(mode=chosen).compress(text)
        guard_result = None
        if args.guard:
            guard = AccuracyGuard(threshold=args.threshold)
            guard_result = guard.check(result.original, result.compressed)
            if not guard_result.passed:
                sys.stderr.write(guard_result.warning + "\n")
                if args.strict:
                    sys.stderr.write("Strict mode: emitting original instead.\n")
                    print(result.original)
                    return 2

    if not args.no_stats:
        Stats().record(
            mode=chosen.value,
            chars_saved=result.char_savings,
            tokens_saved=result.token_savings_estimate,
        )

    print(result.compressed)
    if args.verbose:
        orig_tok = count_tokens(result.original)
        comp_tok = count_tokens(result.compressed)
        method = count_tokens_method()
        sys.stderr.write(
            f"\n[brevix] mode={chosen.value} "
            f"chars: {len(result.original)}→{len(result.compressed)} "
            f"({result.char_savings_pct}% saved) "
            f"tokens ({method}): {orig_tok}→{comp_tok}\n"
        )
        if guard_result:
            sys.stderr.write(
                f"[brevix] guard: sim={guard_result.similarity:.3f} "
                f"({guard_result.method}) pass={guard_result.passed}\n"
            )
    return 0


def _cmd_compress_file(args: argparse.Namespace) -> int:
    mode = CompressionMode(args.mode)
    try:
        result = compress_file(
            args.path,
            mode=mode,
            guard=not args.no_guard,
            threshold=args.threshold,
            dry_run=args.dry_run,
            force=args.force,
        )
    except (FileNotFoundError, IsADirectoryError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2

    if result.skipped:
        sys.stderr.write(f"Skipped: {result.reason}\n")
        return 1

    suffix = " (dry-run)" if args.dry_run else ""
    print(
        f"Compressed {result.path}{suffix}: "
        f"{result.compression.char_savings} chars saved "
        f"({result.compression.char_savings_pct}%)"
    )
    if result.backup:
        print(f"Backup: {result.backup}")
    if result.guard:
        print(
            f"Guard: sim={result.guard.similarity:.3f} "
            f"({result.guard.method}) pass={result.guard.passed}"
        )
    return 0


def _cmd_stats(args: argparse.Namespace) -> int:
    if args.routing:
        from brevix.route.route_stats import render_summary, reset_log, summarize
        if args.reset:
            reset_log()
            print("Routing log cleared.")
            return 0
        try:
            summary = summarize(since=args.since)
        except ValueError as e:
            sys.stderr.write(f"Error: {e}\n")
            return 2
        print(render_summary(summary, since=args.since))
        return 0

    stats = Stats()
    if args.reset:
        stats.reset()
        print("Stats reset.")
        return 0
    try:
        print(stats.summary(since=args.since, real=args.real, share=args.share))
    except ValueError as e:
        sys.stderr.write(f"Error: {e}\n")
        return 2
    return 0


def _cmd_check(args: argparse.Namespace) -> int:
    guard = AccuracyGuard(threshold=args.threshold)
    result = guard.check(args.original, args.compressed)
    print(
        f"Similarity: {result.similarity:.4f}  "
        f"Threshold: {result.threshold:.2f}  "
        f"Passed: {result.passed}  "
        f"Method: {result.method}"
    )
    return 0 if result.passed else 1


def _cmd_count(args: argparse.Namespace) -> int:
    text = args.text
    if text == "-" or not text:
        text = sys.stdin.read()
    print(f"{count_tokens(text)} tokens ({count_tokens_method()}, {len(text)} chars)")
    return 0


def _cmd_route(args: argparse.Namespace) -> int:
    from brevix.route import (
        BudgetExceededError,
        BudgetTracker,
        Router,
        write_default_config,
    )

    if args.init:
        path = write_default_config()
        print(f"Wrote default config: {path}")
        return 0

    if args.budget_reset:
        BudgetTracker().reset()
        print("Budget reset.")
        return 0

    if args.budget_show:
        print(BudgetTracker().summary())
        return 0

    if args.learn_suggest or args.learn_apply:
        from brevix.route.learn import (
            apply_suggestions,
            render_suggestions,
            suggest_overrides,
        )
        suggestions = suggest_overrides(
            min_samples=args.learn_min_samples,
            escalation_threshold=args.learn_threshold,
        )
        print(render_suggestions(suggestions))
        if args.learn_apply and suggestions:
            path = apply_suggestions(suggestions)
            print(f"\nApplied {len(suggestions)} suggestion(s) to {path}")
        return 0

    prompt = args.prompt
    if prompt == "-" or prompt is None:
        prompt = sys.stdin.read()
    if not prompt.strip():
        sys.stderr.write("Error: empty prompt.\n")
        return 2

    router = Router()
    if args.budget_tokens:
        router.budget.state.limit_tokens = args.budget_tokens
    if args.budget_cost:
        router.budget.state.limit_cost_usd = args.budget_cost

    if args.call:
        # Real API call. Lazy-import RoutedClient + SDKs.
        from brevix.route import RoutedClient
        client = RoutedClient(router=router, log_enabled=True)
        try:
            result = client.call(
                prompt,
                override_model=args.model,
                max_tokens=args.max_tokens,
                confidence_check=args.confidence,
            )
        except BudgetExceededError as e:
            sys.stderr.write(f"Budget exceeded: {e}\n")
            return 2
        except ImportError as e:
            sys.stderr.write(
                f"SDK not installed: {e}\n"
                f"Install with: pip install anthropic   (or: pip install openai)\n"
            )
            return 2
        if args.explain:
            sys.stderr.write(
                f"[brevix] task={result.task} model={result.model} "
                f"tokens={result.input_tokens}/{result.output_tokens} "
                f"cost=${result.cost_usd:.6f} "
                f"conf={result.confidence:.2f} escalations={result.escalations}\n"
            )
            for i, a in enumerate(result.attempts):
                sys.stderr.write(
                    f"  [attempt {i+1}] model={a.model} conf={a.confidence:.2f} "
                    f"tokens={a.input_tokens}/{a.output_tokens} cost=${a.cost_usd:.6f}\n"
                )
        print(result.text)
        return 0

    try:
        decision = router.route(prompt, override_model=args.model)
    except BudgetExceededError as e:
        sys.stderr.write(f"Budget exceeded: {e}\n")
        return 2

    if args.explain:
        preview = prompt[:80].replace("\n", " ")
        if len(prompt) > 80:
            preview += "..."
        print(f"Prompt:           {preview}")
        print(f"Detected task:    {decision.task}")
        print(f"Selected model:   {decision.model}")
        print(f"Est. tokens:      {decision.estimated_input_tokens} in / "
              f"{decision.estimated_output_tokens} out")
        print(f"Estimated cost:   ${decision.estimated_cost_usd:.6f}")
        print(f"Reason:           {decision.reason}")
        print(f"Escalation chain: {' -> '.join(decision.escalation_chain)}")
    else:
        print(decision.model)
    return 0


def _cmd_install(args: argparse.Namespace) -> int:
    if args.list:
        print(list_targets())
        return 0
    target = args.target
    if target is None:
        sys.stderr.write("Error: target required (or use --list).\n")
        return 2
    if target != "all" and target not in TARGETS:
        sys.stderr.write(f"Error: unknown target '{target}'. Run `brevix install --list`.\n")
        return 2
    root = Path(args.path).resolve()

    if args.dry_run:
        print(f"[dry-run] Would install '{target}' into {root}.")
        return 0

    files = install_target(target, root)
    print(f"Brevix installed for target '{target}' in {root}:")
    for f in files:
        try:
            print(f"  + {f.relative_to(root)}")
        except ValueError:
            print(f"  + {f}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="brevix",
        description="Compress LLM output safely. Save tokens without breaking your code.",
    )
    parser.add_argument("--version", action="version", version=f"brevix {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_compress = sub.add_parser("compress", help="Compress text")
    p_compress.add_argument("text", nargs="?", default="-", help="Text to compress, or '-' for stdin")
    p_compress.add_argument("--mode", choices=["lite", "full", "ultra", "auto"], default="full")
    p_compress.add_argument("--guard", action="store_true", help="Enable Accuracy Guard")
    p_compress.add_argument("--strict", action="store_true", help="Fall back to original if guard fails")
    p_compress.add_argument("--threshold", type=float, default=0.85)
    p_compress.add_argument("--no-stats", action="store_true", help="Don't record to local stats")
    p_compress.add_argument("-v", "--verbose", action="store_true")
    p_compress.set_defaults(func=_cmd_compress)

    p_cf = sub.add_parser("compress-file", help="Compress a file in place (with .original backup)")
    p_cf.add_argument("path")
    p_cf.add_argument("--mode", choices=["lite", "full", "ultra"], default="full")
    p_cf.add_argument("--threshold", type=float, default=0.85)
    p_cf.add_argument("--no-guard", action="store_true")
    p_cf.add_argument("--dry-run", action="store_true")
    p_cf.add_argument("--force", action="store_true", help="Overwrite even if guard fails")
    p_cf.set_defaults(func=_cmd_compress_file)

    p_stats = sub.add_parser("stats", help="Show local stats")
    p_stats.add_argument("--reset", action="store_true")
    p_stats.add_argument("--since", default="all", help="Time window: 7d, 24h, 30m, all")
    p_stats.add_argument("--real", action="store_true", help="Parse real Claude Code session logs")
    p_stats.add_argument("--share", action="store_true", help="One-line tweet-ready output")
    p_stats.add_argument("--routing", action="store_true",
                         help="Show routing stats (cost saved, escalations, by model/task)")
    p_stats.set_defaults(func=_cmd_stats)

    p_check = sub.add_parser("check", help="Check similarity between two texts")
    p_check.add_argument("original")
    p_check.add_argument("compressed")
    p_check.add_argument("--threshold", type=float, default=0.85)
    p_check.set_defaults(func=_cmd_check)

    p_count = sub.add_parser("count", help="Count tokens in text")
    p_count.add_argument("text", nargs="?", default="-")
    p_count.set_defaults(func=_cmd_count)

    p_route = sub.add_parser(
        "route",
        help="Pick a model for a prompt and manage cost/token budgets",
    )
    p_route.add_argument("prompt", nargs="?", default="-",
                         help="Prompt text or '-' for stdin")
    p_route.add_argument("--model", help="Override model selection")
    p_route.add_argument("--explain", action="store_true",
                         help="Show task, model, est cost, reason")
    p_route.add_argument("--init", action="store_true",
                         help="Write default config to ~/.brevix/route.json")
    p_route.add_argument("--budget-show", action="store_true",
                         help="Show current budget usage")
    p_route.add_argument("--budget-reset", action="store_true",
                         help="Reset budget counters (limits preserved)")
    p_route.add_argument("--budget-tokens", type=int,
                         help="Token budget for this run")
    p_route.add_argument("--budget-cost", type=float,
                         help="Cost budget USD for this run")
    p_route.add_argument("--call", action="store_true",
                         help="Actually call the chosen model (requires SDK + API key)")
    p_route.add_argument("--max-tokens", type=int, default=2000,
                         help="Max output tokens for --call (default: 2000)")
    p_route.add_argument("--confidence", action="store_true",
                         help="Score response and escalate to next tier on low confidence")
    p_route.add_argument("--learn-suggest", action="store_true",
                         help="Print suggested rule changes from observed escalations")
    p_route.add_argument("--learn-apply", action="store_true",
                         help="Apply learn suggestions to ~/.brevix/route.json (implies --learn-suggest)")
    p_route.add_argument("--learn-min-samples", type=int, default=20,
                         help="Min calls per task before a suggestion is offered (default: 20)")
    p_route.add_argument("--learn-threshold", type=float, default=0.5,
                         help="Escalation rate threshold for a suggestion (default: 0.5)")
    p_route.set_defaults(func=_cmd_route)

    p_install = sub.add_parser(
        "install",
        help="Install Brevix rules into a project for a specific LLM coding tool",
    )
    p_install.add_argument(
        "target",
        nargs="?",
        help="Target tool. Use --list to see all options.",
    )
    p_install.add_argument("--path", default=".", help="Project root (default: cwd)")
    p_install.add_argument("--list", action="store_true", help="List available targets")
    p_install.add_argument("--dry-run", action="store_true", help="Preview without writing")
    p_install.set_defaults(func=_cmd_install)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
