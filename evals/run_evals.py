import json
import sys
import time
from pathlib import Path
from rich.console import Console
from rich.table import Table
from job_agent.agent import run_agent, MODEL

OUTPUTS = Path("outputs")
console = Console()


def newest_assessment(since: float):
    files = [f for f in OUTPUTS.glob("assessment_*.json") if f.stat().st_mtime >= since]
    return max(files, key=lambda f: f.stat().st_mtime) if files else None


def missing_keywords(items: list, keywords: list) -> list:
    text = " ".join(items).lower()
    return [k for k in keywords if k.lower() not in text]


def main():
    model = sys.argv[1] if len(sys.argv) > 1 else MODEL
    cases = json.loads(Path("evals/cases.json").read_text())

    table = Table(title=f"Eval results: {model}")
    for col in ["Case", "Score", "Expected", "Result", "Steps", "Tokens", "Time"]:
        table.add_column(col)

    results, passed = [], 0
    for case in cases:
        console.print(f"\n[bold]Running {case['name']}...[/bold]")
        start = time.time()
        task = (
            f"My resume is at {case['resume']}. "
            f"The job posting is at: {case['job']}. "
            "Analyze my fit, save the assessment, and write a cover letter."
        )
        run = run_agent(task, model=model)

        problems, score = [], None
        path = newest_assessment(start)
        if path is None:
            problems.append("no assessment saved")
        else:
            a = json.loads(path.read_text())
            score = a["score"]
            if not case["min_score"] <= score <= case["max_score"]:
                problems.append("score out of range")
            if m := missing_keywords(a["matched_skills"], case["expected_matches"]):
                problems.append(f"unmatched: {m}")
            if m := missing_keywords(a["missing_skills"], case["expected_gaps"]):
                problems.append(f"gaps not flagged: {m}")

        ok = not problems
        passed += ok
        tokens = run["input_tokens"] + run["output_tokens"]
        table.add_row(
            case["name"], str(score), f"{case['min_score']}-{case['max_score']}",
            "[green]PASS[/green]" if ok else "[red]FAIL[/red] " + "; ".join(problems),
            str(run["steps"]), str(tokens), f"{run['seconds']}s",
        )
        results.append({"case": case["name"], "score": score, "passed": ok,
                        "problems": problems, "steps": run["steps"],
                        "tokens": tokens, "seconds": run["seconds"]})

    console.print(table)
    console.print(f"\n[bold]Passed {passed}/{len(cases)}[/bold]")
    out = Path(f"evals/results_{model}.json")
    out.write_text(json.dumps(results, indent=2))
    console.print(f"Saved to {out}")


if __name__ == "__main__":
    main()