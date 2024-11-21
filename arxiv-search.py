"""
Author: Emmanuel Vazquez <emmanuel.vazquez@centralesupelec.fr>
License: MIT License (see LICENSE)
"""

import requests
import xml.etree.ElementTree as ET


def search_arxiv(parameters, batch_size=2000):
    """
    Search for arXiv articles in specific categories, date range, and abstracts
    mentioning a given subject. Handles pagination for large result sets.

    Args:
        parameters (dict): Dictionary of parameters including:
            - subject (str): Subject to search for in abstracts.
            - max_results (int): Total maximum number of articles to retrieve.
            - categories (list): List of arXiv categories to restrict the search to.
            - year_start (int): Start year for filtering articles.
            - year_end (int): End year for filtering articles.
        batch_size (int): Number of articles to fetch per API request (max 2000).

    Returns:
        list: List of articles with title, author(s), abstract, and link.
    """
    base_url = "http://export.arxiv.org/api/query?"

    subject = parameters.get("subject", "")
    max_results = parameters.get("max_results", 50)
    categories = parameters.get("categories", [])
    year_start = parameters.get("year_start", None)
    year_end = parameters.get("year_end", None)

    # Build the category filter
    category_filter = (
        " OR ".join([f"cat:{cat}" for cat in categories]) if categories else ""
    )
    if category_filter:
        category_filter = f"({category_filter}) AND "

    # Build the date filter
    date_filter = ""
    if year_start:
        date_filter += f"submittedDate:[{year_start}0000 TO "
        date_filter += f"{year_end}1231]" if year_end else "*]"

    # Combine query parts
    query = f"{category_filter}{date_filter} AND all:{subject}"

    all_results = []
    start = 0

    while len(all_results) < max_results:
        batch_query = f"{base_url}search_query={query}&start={start}&max_results={min(batch_size, max_results - len(all_results))}"
        response = requests.get(batch_query)

        if response.status_code != 200:
            print(f"HTTP error {response.status_code} when accessing the arXiv API.")
            break

        # Parse the XML response
        root = ET.fromstring(response.content)
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        batch_results = []
        for entry in root.findall("atom:entry", ns):
            title = entry.find("atom:title", ns).text.strip()
            authors = [
                author.find("atom:name", ns).text
                for author in entry.findall("atom:author", ns)
            ]
            summary = entry.find("atom:summary", ns).text.strip()
            link = entry.find('atom:link[@rel="alternate"]', ns).attrib["href"]

            batch_results.append(
                {"title": title, "authors": authors, "summary": summary, "link": link}
            )

        if not batch_results:
            break  # No more results available

        all_results.extend(batch_results)
        start += batch_size

    return all_results[:max_results]


if __name__ == "__main__":
    # Predefined parameters
    parameters = {
        "subject": "Bayesian optimization",
        "max_results": 5000,  # Max number of articles to retrieve
        "categories": ["stat.ML", "stat.TH"],
        "year_start": 2021,
        "year_end": 2024,
    }

    results = search_arxiv(parameters)

    if results:
        print(f"\nFound {len(results)} articles:\n")
        for i, article in enumerate(results, start=1):
            print(f"{i}. {article['title']}")
            print(f"   Author(s): {', '.join(article['authors'])}")
            # Limit to 300 characters
            print(f"   Summary: {article['summary'][:300]}...")
            print(f"   Link: {article['link']}\n")
    else:
        print(
            "No articles found for the given subject in the specified categories and date range."
        )
