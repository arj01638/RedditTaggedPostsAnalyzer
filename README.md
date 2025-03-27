# Reddit Tagged Posts Analyzer (RTPA)

This project is a tool for scraping, analyzing, and graphing data from Reddit (and GWASI). It supports both command‐line (deprecated) and GUI interfaces. The project includes functions for:
 
- Scraping data from Reddit and GWASI.
- Loading and filtering CSV datasets.
- Performing statistical analyses (T-tests and confidence intervals) on upvotes, comments, etc.
- Generating various graphs with Matplotlib.
- Running a DearPyGui–based GUI for interactive analysis.

When scraping from Reddit, any subreddit where posts follow a "[Tag1] Title [Tag2] [etc.]", "Title [Tag1] [etc.]", or "[Tag1] [etc.] Title" format can be scraped. The scraper will extract the title, tags, upvotes, comments, and other metadata. The data can then be analyzed and graphed using the provided GUI.

## Requirements

Install the required dependencies via:

```bash
pip install -r requirements.txt
```

## Running the Project

- **GUI:**  
  Run the GUI with:
  ```bash
  python -m rtpa.gui
  ```

Alternatively, you can run this project via CLI, but I haven't updated it in a while, so it may be outdated.

- **CLI:**  
  Run the main script from the command line:
  ```bash
  python main.py
  ```

## Project Structure

```
RTPA/
├── README.md
├── requirements.txt
├── setup.py
├── main.py
└── rtpa
    ├── __init__.py
    ├── exceptions.py         # Custom exceptions
    ├── stats.py              # Statistical functions and analysis
    ├── loader.py             # Data loading and processing routines
    ├── analysis.py           # Analysis routines (grouping and T-tests)
    ├── gui.py                # GUI interface (Dear PyGui)
    ├── graphing
    │   ├── __init__.py
    │   ├── utils.py          # Utility functions for plotting
    │   └── generation.py     # Functions to generate graphs
    └── scraping
        ├── __init__.py
        ├── gwasi.py          # GWASI scraper
        └── old_reddit.py     # Old Reddit scraper
```