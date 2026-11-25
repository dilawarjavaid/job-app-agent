import os
from dotenv import load_dotenv
import anthropic
from rich.console import Console

from job_agent.tools import read_file, fetch_job_posting, save_output, save_assessment

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
console = Console()

MODEL = os.getenv("MODEL", "claude-haiku-5-5")

SYSTEM_PROMPT = """You are a job application assistant.

Your workflow:
1. Read the candidate's resume with read_file.
2. Get the job posting: use fetch_job_posting for a URL, or read_file for a local file.
3. Extract the key requirements (skills, experience, qualifications).
4. Compare them to the resume. Give a match score from 0 to 100,
   list matched skills, and list missing or weak areas.
   Then call save_assessment with these results.
5. Write a tailored cover letter (under 350 words) that highlights the
   strongest matches.
6. Save the cover letter with save_output as a .txt file.
7. Finish with a short summary: score, top matches, gaps, and the saved file name.

Rules:
- Never invent experience, skills, or numbers that are not in the resume.
- If a tool returns an error, explain it or try another approach."""

# What Claude sees: each tool's name, purpose, and inputs
TOOLS = [
    {
        "name": "read_file",
        "description": "Read a local .txt or .pdf file, such as a resume or a saved job posting.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "File path, e.g. data/resume.txt"}},
            "required": ["path"],
        },
    },
    {
        "name": "fetch_job_posting",
        "description": "Download a job posting web page and return its text.",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string", "description": "Full URL of the job posting"}},
            "required": ["url"],
        },
    },
    {
        "name": "save_output",
        "description": "Save text (like a cover letter) to the outputs folder.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "e.g. cover_letter_acme.txt"},
                "content": {"type": "string", "description": "The text to save"},
            },
            "required": ["filename", "content"],
        },
    },

        {
        "name": "save_assessment",
        "description": "Save the structured fit assessment as JSON. Call once after comparing the resume to the job.",
        "input_schema": {
            "type": "object",
            "properties": {
                "company": {"type": "string"},
                "score": {"type": "integer", "minimum": 0, "maximum": 100},
                "matched_skills": {"type": "array", "items": {"type": "string"}},
                "missing_skills": {"type": "array", "items": {"type": "string"}},
                "summary": {"type": "string", "description": "2-3 sentence overall assessment"},
            },
            "required": ["company", "score", "matched_skills", "missing_skills", "summary"],
        },
    },
]

# What actually runs: tool name -> Python function
TOOL_FUNCTIONS = {
    "read_file": read_file,
    "fetch_job_posting": fetch_job_posting,
    "save_output": save_output,
    "save_assessment": save_assessment,
}


def run_tool(name: str, tool_input: dict) -> str:
    func = TOOL_FUNCTIONS.get(name)
    if func is None:
        return f"Error: unknown tool '{name}'"
    try:
        return func(**tool_input)
    except Exception as e:
        return f"Error running {name}: {e}"


def run_agent(task: str, model: str = MODEL, max_steps: int = 10) -> str:
    messages = [{"role": "user", "content": task}]

    for step in range(1, max_steps + 1):
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        # No more tool calls: Claude is done
        if response.stop_reason != "tool_use":
            return "".join(b.text for b in response.content if b.type == "text")

        # Run every tool Claude asked for and send the results back
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                console.print(f"[cyan]Step {step}:[/cyan] {block.name}({list(block.input.keys())})")
                result = run_tool(block.name, block.input)
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": result}
                )
        messages.append({"role": "user", "content": tool_results})

    return "Stopped: reached the maximum number of steps."