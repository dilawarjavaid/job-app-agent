from job_agent.tools import read_file, fetch_job_posting

print(read_file("data/resume.txt")[:500])
print(fetch_job_posting("https://example.com")[:300])