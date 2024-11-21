# arXiv Search Script

This is a small Python script to query the arXiv API for academic
papers based on keywords, categories, and date ranges. It retrieves
metadata like the title, authors, abstract snippets, and links.

You can use this script for your own purpose. It is written with the help of ChatGPT.

## Features
- Query by keywords (e.g., "Bayesian optimization").
- Restrict results to specific categories (e.g., `stat.ML`, `stat.TH`).
- Filter by submission date range (e.g., 2021 to 2024).
- Handles large datasets with pagination.

## How to Use
1. Modify the `parameters` dictionary in the script to fit your search:
   ```python
   parameters = {
       "subject": "Bayesian optimization",
       "max_results": 5000,
       "categories": ["stat.ML", "stat.TH"],
       "year_start": 2021,
       "year_end": 2024
   }
