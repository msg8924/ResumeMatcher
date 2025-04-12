from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer, util

# Initialize semantic model (lightweight + fast)
model = SentenceTransformer('all-MiniLM-L6-v2')

def score_keyword_overlap(resume, job_description):
    tokens = [resume, job_description]
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(tokens)
    score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    return round(score, 4)

def score_semantic_similarity(resume, job_description):
    resume_embed = model.encode(resume, convert_to_tensor=True)
    job_embed = model.encode(job_description, convert_to_tensor=True)
    score = util.cos_sim(resume_embed, job_embed).item()
    return round(score, 4)

def match_jobs(jobs, resume_text):
    scored_jobs = []
    for job in jobs:
        desc = job['description']
        keyword_score = score_keyword_overlap(resume_text, desc)
        semantic_score = score_semantic_similarity(resume_text, desc)
        combined_score = round((keyword_score + semantic_score) / 2, 4)
        job['keyword_score'] = keyword_score
        job['semantic_score'] = semantic_score
        job['match_score'] = combined_score
        scored_jobs.append(job)
    return sorted(scored_jobs, key=lambda x: x['match_score'], reverse=True)
