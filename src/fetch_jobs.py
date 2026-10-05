"""
Downloads the job-posting dataset used for the labor-market side of the project.

This script connects to the Skillab Tracker API, authenticates with the configured
credentials, and retrieves job postings for the selected ISCO occupation group.
For this project, the IT group (ISCO C25) is used so the collected postings match
the analytical scope of the thesis.

The downloaded jobs are stored locally as JSON and are later processed, cleaned,
deduplicated, and used to build the market-based occupation-skill evidence.
"""
import requests as req
import json
import os
import math
import time
from dotenv import load_dotenv

load_dotenv()
API = os.getenv("TRACKER_API")
USERNAME = os.getenv("TRACKER_USERNAME")
PASSWORD = os.getenv("TRACKER_PASSWORD")

ISCO_CODE_IT = "http://data.europa.eu/esco/isco/C25"

def get_token() -> str:
    """Authenticate with the Skillab API and return the access token."""
    print("Trying to login...")
    try:
        res = req.post(f"{API}/login", json={"username": USERNAME, "password": PASSWORD})
        res.raise_for_status() 
        print("Login Successful!")
        return res.text.replace('"', '')
    except Exception as e:
        print(f"Login Failed: {e}")
        exit()

def fetch_jobs_by_occupation(occupation_code):
    """Download the available job postings for the requested ISCO occupation group."""
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    params = {
        "page": 1,
        "page_size": 100,
    }
    
    request_body = {
        "occupation_ids": [occupation_code] 
    }

    print(f"Fetching jobs for Occupation Code: {occupation_code}...")

    response = req.post(f"{API}/jobs", headers=headers, params=params, data=request_body)
    data = response.json()
    
    total_count = data.get("count", 0)
    print(f"Found {total_count} jobs via API.")
    
    if total_count == 0:
        return []

    number_of_pages = int(math.ceil(total_count / 100))
    all_jobs = []

    MAX_PAGES = 50 
    pages_to_download = min(number_of_pages, MAX_PAGES)

    for i in range(1, pages_to_download + 1):
        print(f"Downloading page {i}/{pages_to_download} (Total available: {number_of_pages})...")
        params["page"] = i
        
        try:
            res = req.post(f"{API}/jobs", headers=headers, params=params, data=request_body)
            page_data = res.json()
            items = page_data.get("items", [])
            all_jobs.extend(items)
            time.sleep(0.5)
        except Exception as e:
            print(f"Error on page {i}: {e}")

    return all_jobs

if __name__ == "__main__":
    jobs = fetch_jobs_by_occupation(ISCO_CODE_IT)
    
    filename = "skillab_jobs_isco25.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=4, ensure_ascii=False)
        
    print(f"Done! Saved {len(jobs)} jobs to {filename}")