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


def strip_version(arxiv_id):
    """
    Strip the version suffix from an arXiv ID.

    Args:
        arxiv_id (str): Full arXiv ID, e.g., '2405.01304v1'.

    Returns:
        str: Version-less arXiv ID, e.g., '2405.01304'.
    """
    return arxiv_id.split("v")[0]


def query_semantic_scholar(arxiv_id):
    """
    Query Semantic Scholar for all available data on a paper.

    Args:
        arxiv_id (str): The arXiv ID of the paper.

    Returns:
        dict: A dictionary containing the paper's citation count, references,
              and citing papers.
    """
    url = f"https://api.semanticscholar.org/v1/paper/arXiv:{arxiv_id}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        return {
            "citation_count": len(data.get("citations", [])),
            "influential_citation_count": data.get("influentialCitationCount", 0),
            "references": [
                {
                    "title": ref.get("title", "Unknown Title"),
                    "authors": [
                        author.get("name", "Unknown")
                        for author in ref.get("authors", [])
                    ],
                }
                for ref in data.get("references", [])
            ],
            "citing_papers": [
                {
                    "title": citation.get("title", "Unknown Title"),
                    "authors": [
                        author.get("name", "Unknown")
                        for author in citation.get("authors", [])
                    ],
                }
                for citation in data.get("citations", [])
            ],
        }
    else:
        print(f"Failed to fetch data for arXiv ID {arxiv_id}.")
        return {
            "citation_count": None,
            "influential_citation_count": None,
            "references": None,
            "citing_papers": None,
        }


if __name__ == "__main__":
    # Predefined parameters
    parameters = {
        "subject": "Bayesian optimization",
        "max_results": 2,  # Max number of articles to retrieve
        "categories": ["stat.ML", "stat.TH"],
        "year_start": 2020,
        "year_end": 2021,
    }

    results = search_arxiv(parameters)

    if results:
        print(f"\nFound {len(results)} articles:\n")
        for i, article in enumerate(results, start=1):
            print(f"{i}. {article['title']}")
            print(f"   Author(s): {', '.join(article['authors'])}")
            print(f"   Summary: {article['summary'][:300]}...")
            print(f"   Link: {article['link']}\n")

        # Example: Get all data for the first result
        first_result = results[0]
        arxiv_id = strip_version(first_result["link"].split("/")[-1])
        paper_data = query_semantic_scholar(arxiv_id)

        print(f"\nSemantic Scholar Data for '{first_result['title']}':")
        print(f"  Citation Count: {paper_data['citation_count']}")
        print(f"  Influential Citations: {paper_data['influential_citation_count']}")

        print("\nReferences:")
        if paper_data["references"]:
            for ref in paper_data["references"]:
                print(f"   - {ref['title']} by {', '.join(ref['authors'])}")

        print("\nCiting Papers:")
        if paper_data["citing_papers"]:
            for citing in paper_data["citing_papers"]:
                print(f"   - {citing['title']} by {', '.join(citing['authors'])}")

    else:
        print(
            "No articles found for the given subject in the specified categories and date range."
        )
