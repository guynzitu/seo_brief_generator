"""
DataForSEO SERP API integration.
Fetches top organic results for a keyword.
"""
import requests
import base64
import json


def get_top_results(
    keyword: str,
    login: str,
    password: str,
    se_domain: str = "google.fr",
    language_code: str = "fr",
    location_code: int = 2250,
    top_n: int = 5,
) -> dict:
    """
    Query DataForSEO to get top organic SERP results.

    Returns:
        dict with keys:
            - urls: list of top organic URLs
            - error: error message if any
    """
    try:
        cred = base64.b64encode(f"{login}:{password}".encode()).decode()
        headers = {
            "Authorization": f"Basic {cred}",
            "Content-Type": "application/json",
        }

        # Use the Google Organic SERP Live/Advanced endpoint
        url = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"

        payload = [
            {
                "keyword": keyword,
                "location_code": location_code,
                "language_code": language_code,
                "se_domain": se_domain,
                "depth": 10,
                "calculate_rectangles": False,
            }
        ]

        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()

        if data.get("status_code") != 20000:
            return {"urls": [], "error": f"API error: {data.get('status_message', 'Unknown')}"}

        tasks = data.get("tasks", [])
        if not tasks:
            return {"urls": [], "error": "No tasks returned"}

        task = tasks[0]
        if task.get("status_code") != 20000:
            return {"urls": [], "error": f"Task error: {task.get('status_message', 'Unknown')}"}

        result = task.get("result", [])
        if not result:
            return {"urls": [], "error": "No results"}

        items = result[0].get("items", [])

        # Extract organic results
        organic_urls = []
        for item in items:
            if item.get("type") == "organic" and item.get("url"):
                organic_urls.append(item["url"])
                if len(organic_urls) >= top_n:
                    break

        return {"urls": organic_urls, "error": None}

    except requests.exceptions.RequestException as e:
        return {"urls": [], "error": f"Network error: {str(e)}"}
    except Exception as e:
        return {"urls": [], "error": f"Unexpected error: {str(e)}"}
