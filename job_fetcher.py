import json

import requests
from utils import load_config
config = load_config()
jsearch = config["jsearch"]
adzuna = config["adzuna"]

location = config["search_defaults"]["location"]
results = config["search_defaults"]["results"]



def fetch_adzuna_jobs(title, location=location, total_results=results):
    params = {
        "app_id": adzuna["app_id"],
        "app_key": adzuna["app_key"],
        "results_per_page": total_results,
        "what": title,
        "where": location,
        "content-type": "application/json"
    }

    response = requests.get(adzuna["api_url"], params=params)

    if response.status_code != 200:
        print("❌ Adzuna API returned error:")
        print("Status code:", response.status_code)
        print("Response:", response.text[:200])
        return []

    data = response.json()

    jobs = []
    for job in data.get("results", []):
        #print(json.dumps(job, indent=2))
        #print()
        #print()
        jobs.append({
            "title": job.get("title"),
            "company": job.get("company", {}).get("display_name"),
            "location": job.get("location", {}).get("display_name", "N/A"),
            "description": job.get("description"),
            "url": job.get("redirect_url"),
            "min_salary": job.get("salary_min"),
            "max_salary": job.get("salary_max"),
            "posted_date": job.get("created"),
            "job_type": job.get("contract_time") or job.get("category", {}).get("label"),
            "latitude": job.get("latitude"),
            "longitude": job.get("longitude"),
            "benefits": None,
            "highlights": None,
            "source": "adzuna"
        })

    return jobs

def fetch_jsearch_jobs(title, location=location, total_results=results):
    headers = {
        "X-RapidAPI-Key": jsearch["api_key"],
        "X-RapidAPI-Host": jsearch["api_host"]
    }
    jobs = []
    results_per_page = 10  # Assuming the API returns 10 results per page
    pages = (total_results + results_per_page - 1) // results_per_page  # Calculate the number of pages needed

    for page in range(1, pages + 1):
        querystring = {
            "query": f"{title} in {location}",
            "page": str(page),
            "num_pages": "1"
        }
        response = requests.get(jsearch["api_url"], headers=headers, params=querystring)
        if response.status_code != 200:
            print("Status code:", response.status_code)
            print("Response:", response.text)
            raise Exception("JSearch API call failed.")
        data = response.json()
        for job in data.get("data", []):
            #print(json.dumps(job, indent=2))
            jobs.append({
                "title": job.get("job_title"),
                "company": job.get("employer_name"),
                "location": job.get("job_location") or job.get("job_city", "N/A"),
                "description": job.get("job_description"),
                "url": job.get("job_apply_link"),
                "min_salary": job.get("job_min_salary"),
                "max_salary": job.get("job_max_salary"),
                "posted_date": job.get("job_posted_at_datetime_utc"),
                "job_type": job.get("job_employment_type"),
                "latitude": job.get("job_latitude"),
                "longitude": job.get("job_longitude"),
                "benefits": job.get("job_benefits"),
                "highlights": job.get("job_highlights"),
                "source": "jsearch"
            })
            if len(jobs) >= total_results:
                return jobs[:total_results]
    return jobs
