from pathlib import Path
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

OUTPUT_DIR = Path("outputs")


def read_file(path: str) -> str:
    """Read a resume or saved job posting (.pdf or .txt)."""
    p = Path(path)
    if not p.exists():
        return f"Error: file not found: {path}"
    if p.suffix.lower() == ".pdf":
        reader = PdfReader(p)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return p.read_text(encoding="utf-8")


def fetch_job_posting(url: str) -> str:
    """Download a job posting page and return its plain text."""
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        return f"Error fetching {url}: {e}"
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = " ".join(soup.get_text(separator=" ").split())
    return text[:15000]  # keep the prompt small


def save_output(filename: str, content: str) -> str:
    """Save a cover letter or report to the outputs folder."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    path = OUTPUT_DIR / Path(filename).name  # blocks paths like ../../
    path.write_text(content, encoding="utf-8")
    return f"Saved to {path}"