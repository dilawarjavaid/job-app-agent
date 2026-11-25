from rich.console import Console
from rich.markdown import Markdown
from job_agent.agent import run_agent

console = Console()

task = (
    "My resume is at data/resume.txt. "
    "The job posting is at data/job.txt. "
    "Analyze my fit and write a cover letter."
)

result = run_agent(task)
console.print(Markdown(result))