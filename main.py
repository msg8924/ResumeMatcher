from job_fetcher import fetch_jsearch_jobs, fetch_adzuna_jobs
from utils import deduplicate_jobs, export_to_csv, parse_docx_resume, visualize_resume_gaps, filter_jobs, load_config
from matcher import match_jobs
config = load_config()
job_titles = config["search_defaults"]["job_titles"]
resume_path = config["resume"]["path"]

def main():
    # === Step 1: Parse Resume ===
    resume_text = parse_docx_resume(resume_path)

    # === Step 2: Fetch Jobs ===
    jobs_jsearch = []
    jobs_adzuna = []

    for title in job_titles:
        jobs_jsearch += fetch_jsearch_jobs(title)
        jobs_adzuna += fetch_adzuna_jobs(title)

    jobs = jobs_jsearch + jobs_adzuna
    jobs = deduplicate_jobs(jobs)
    # === Step 3: Score Matches ===
    matched_jobs = match_jobs(jobs, resume_text)
    matched_jobs = filter_jobs(matched_jobs)

    # === Step 4: Display Results ===
    print("\n📄 Top Job Matches:\n")
    for i, job in enumerate(matched_jobs, 1):
        print(f"{i}. {job['title']} at {job['company']}")
        print(f"   Location: {job['location']}")
        print(
            f"   Match Score: {job['match_score']} (Keyword: {job['keyword_score']}, Semantic: {job['semantic_score']})")

        min_salary = job.get("min_salary")
        max_salary = job.get("max_salary")
        if min_salary or max_salary:
            print(
                f"   \U0001F4B0 Salary Range: ${int(min_salary):,} - ${int(max_salary):,}" if min_salary and max_salary else
                f"   \U0001F4B0 Salary Estimate: ${int(min_salary or max_salary):,}")

        print(f"   URL: {job['url']}\n")
    # === Step 5: Export to CSV ===
    export_to_csv(matched_jobs, filename="matched_jobs.csv",resume_text=resume_text)

    # === Step 6: Visualize Resume Gaps ===
    visualize_resume_gaps(matched_jobs)


if __name__ == "__main__":
    main()
