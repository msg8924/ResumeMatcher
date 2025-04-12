from docx import Document
import csv
from rapidfuzz import fuzz
import yaml
from collections import Counter
import re
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
import yake

KNOWN_SKILLS = {"communication", "collaboration", "problem solving", "leadership", "strategy", "planning"}
KNOWN_TOOLS = {"jira", "tableau", "figma", "excel", "confluence", "git", "notion"}
KNOWN_TECH = {"python", "sql", "aws", "api", "react", "hadoop", "tensorflow", "spark", "docker", "java", "r"}

def extract_phrases(text, top_n=15, phrase_len=1):
    """
    Extract key phrases from a given text using YAKE.
    """
    kw_extractor = yake.KeywordExtractor(n=phrase_len, top=top_n)
    keywords = kw_extractor.extract_keywords(text)
    return [kw for kw, score in keywords]


def classify_keywords(keywords):
    """
    Classify extracted phrases into skills, tools, and technologies.
    """
    skills, tools, tech = [], [], []
    for phrase in keywords:
        words = phrase.lower().split()
        for word in words:
            if word in KNOWN_TECH:
                tech.append(word)
            elif word in KNOWN_TOOLS:
                tools.append(word)
            elif word in KNOWN_SKILLS:
                skills.append(word)
    return list(set(skills)), list(set(tools)), list(set(tech))

def load_config(path="config.yaml"):
    with open(path, "r") as f:
        config = yaml.safe_load(f)
    return config

config = load_config()
fuzzy_match_threshold = config["search_defaults"]["fuzzy_match_threshold"]
filter_jobs_threshold = config["search_defaults"]["filter_jobs_threshold"]


def extract_keywords_from_text(text, top_n=15):
    # Lowercase, remove punctuation
    clean = re.sub(r"[^a-zA-Z0-9\s]", "", text.lower())
    tokens = clean.split()

    # Remove stopwords
    tokens = [word for word in tokens if word not in ENGLISH_STOP_WORDS and len(word) > 2]

    # Count word frequency
    freq = Counter(tokens)
    common = freq.most_common(top_n)

    return [word for word, count in common]

def deduplicate_jobs(jobs, threshold=fuzzy_match_threshold):
    seen = []
    unique_jobs = []
    for job in jobs:
        title = job.get("title", "") or ""
        company = job.get("company", "") or ""

        title = title.strip().lower()
        company = company.strip().lower()

        is_duplicate = False
        for s in seen:
            title_sim = fuzz.token_sort_ratio(title, s['title'])
            if (
                title_sim >= threshold and
                company == s['company']
            ):
                is_duplicate = True
                break

        if not is_duplicate:
            seen.append({"title": title, "company": company})
            unique_jobs.append(job)

    return unique_jobs

def parse_docx_resume(file_path):
    doc = Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            full_text.append(text)
    return "\n".join(full_text)


def generate_resume_addition_suggestions(skills, tools, tech):
    suggestions = []
    if skills:
        skills_list = ", ".join(sorted(skills))
        suggestions.append(
            f"You may want to highlight your strengths in areas such as {skills_list} to align with key soft skill expectations."
        )
    if tools:
        tools_list = ", ".join(tool.upper() for tool in sorted(tools))
        suggestions.append(
            f"Demonstrating hands-on experience with tools like {tools_list} can help reflect modern project or product management capabilities."
        )
    if tech:
        tech_list = ", ".join(tech.upper() for tech in sorted(tech))
        suggestions.append(
            f"Consider adding technical contributions or results involving {tech_list} to showcase your engineering and system-level impact."
        )
    return " ".join(suggestions) if suggestions else "No additional suggestions.""No additional suggestions."


def filter_jobs(jobs, min_score=filter_jobs_threshold):
    return [job for job in jobs if float(job.get("match_score", 0)) >= min_score]

def export_to_csv(jobs, filename="matched_jobs.csv", phrase_count=10, resume_text=None):
    """
    Export the matched jobs along with extracted keyword fields and comparison
    against resume to a CSV file.
    """
    all_fields = set()
    for job in jobs:
        all_fields.update(job.keys())

    all_fields.update([
        "phrases", "skills", "tools", "technologies",
        "missing_skills", "missing_tools", "missing_tech"
    ])

    fieldnames = sorted(all_fields)

    # Extract and classify resume keywords
    resume_keywords = extract_phrases(resume_text) if resume_text else []
    resume_skills, resume_tools, resume_tech = classify_keywords(resume_keywords)

    with open(filename, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        keyword_counter = Counter()
        for job in jobs:
            desc = job.get("description", "")
            phrases = extract_phrases(desc, top_n=phrase_count)
            skills, tools, tech = classify_keywords(phrases)

            job["phrases"] = ", ".join(phrases)
            job["skills"] = ", ".join(skills)
            job["tools"] = ", ".join(tools)
            job["technologies"] = ", ".join(tech)
            job["missing_skills"] = ", ".join(set(skills) - set(resume_skills))
            job["missing_tools"] = ", ".join(set(tools) - set(resume_tools))
            job["missing_tech"] = ", ".join(set(tech) - set(resume_tech))

            keyword_counter.update(set(skills) - set(resume_skills))
            keyword_counter.update(set(tools) - set(resume_tools))
            keyword_counter.update(set(tech) - set(resume_tech))
            job["top_missing_keywords"] = ", ".join([kw for kw, _ in keyword_counter.most_common(10)])
            keyword_counter.update(set(skills) - set(resume_skills))
            keyword_counter.update(set(tools) - set(resume_tools))
            keyword_counter.update(set(tech) - set(resume_tech))

            job["top_missing_keywords"] = ", ".join([kw for kw, _ in keyword_counter.most_common(10)])

            # Generate suggestion for each job
            suggestion = generate_resume_addition_suggestions(
                set(skills) - set(resume_skills),
                set(tools) - set(resume_tools),
                set(tech) - set(resume_tech)
            )
            job["resume_addition_suggestions"] = suggestion

            writer.writerow(job)

    print(f"✅ Exported {len(jobs)} jobs with keyword classification, resume comparison, and suggestions.")



def visualize_resume_gaps(jobs, top_n=10):
    all_missing = []
    for job in jobs:
        all_missing += job.get("missing_skills", "").split(", ")
        all_missing += job.get("missing_tools", "").split(", ")
        all_missing += job.get("missing_tech", "").split(", ")

    all_missing = [kw.strip().lower() for kw in all_missing if kw.strip()]
    counter = Counter(all_missing)
    most_common = counter.most_common(top_n)

    if not most_common:
        print("\n✅ No missing keywords to visualize.")
        return

    labels, values = zip(*most_common)
    plt.figure(figsize=(10, 6))
    plt.barh(labels, values, color="salmon")
    plt.xlabel("Frequency")
    plt.title("Top Missing Resume Keywords Across Job Matches")
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.show()

