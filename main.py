import argparse
from rich.console import Console
from rich.markdown import Markdown
from job_agent.agent import run_agent, MODEL


def main():
    parser = argparse.ArgumentParser(description="Job application assistant agent")
    parser.add_argument("--resume", default="data/resume.txt", help="Path to resume (.txt or .pdf)")
    parser.add_argument("--job", required=True, help="Job posting URL or path to a .txt file")
    parser.add_argument("--model", default=MODEL, help="Claude model to use")
    parser.add_argument("--max-steps", type=int, default=10)
    args = parser.parse_args()

    task = (
        f"My resume is at {args.resume}. "
        f"The job posting is at: {args.job}. "
        "Analyze my fit, save the assessment, and write a cover letter."
    )


    console = Console()
    run = run_agent(task, model=args.model, max_steps=args.max_steps)
    console.print(Markdown(run["text"]))
    console.print(
        f"\n[dim]{run['steps']} steps | "
        f"{run['input_tokens']} in / {run['output_tokens']} out tokens | "
        f"{run['seconds']}s[/dim]"
    )


if __name__ == "__main__":
    main()