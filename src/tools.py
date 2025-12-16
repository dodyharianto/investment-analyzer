from typing import Annotated
import wikipedia
from langchain_core.tools import tool
import pandas as pd
import os
import requests
from datetime import datetime
from markdown_pdf import MarkdownPdf, Section
from yahooquery import Ticker
from matplotlib import pyplot as plt
import seaborn as sns
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
CSV_DIR = OUTPUTS_DIR / "csv"
VIS_DIR = OUTPUTS_DIR / "visualizations"
CSV_DIR.mkdir(parents=True, exist_ok=True)
VIS_DIR.mkdir(parents=True, exist_ok=True)

@tool
def wikipedia_tool(query: Annotated[str, "The Wikipedia search to execute to find key summary information."]):
    """Use this to search Wikipedia for factual information."""
    try:
        results = wikipedia.search(query)
        if not results:
            return "No results found on Wikipedia."
        
        # Retrieve page title
        title = results[0]

        # Fetch summary
        summary = wikipedia.summary(title, sentences=8, auto_suggest=False, redirect=True)
    except BaseException as e:
        return f"Failed to execute. Error: {repr(e)}"
    return f"Successfully executed:\nWikipedia summary: {summary}"

@tool
def fetch_latest_headlines(category: str = None, country: str = 'sg', page_size: int = 10):
    """
    Use this to fetch latest news headlines using NewsAPI.
    Args:
        - category (str, optional): News category (e.g., 'business', 'technology', 'sports')
        - country (str, optional): 2-letter ISO 3166-1 country code. Defaults to 'us'
        - page_size (int, optional): Number of headlines to return. Defaults to 10
    Returns:
        List[Dict]: List of news articles with title, description, source, and URL
    """
    api_key = os.getenv('NEWS_API_KEY')
    base_url = "https://newsapi.org/v2/top-headlines"
    params = {
        'country': country,
        'pageSize': page_size,
        'apiKey': api_key
    }
    if category:
        params['category'] = category
    try:
        response = requests.get(base_url, params=params)
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching news: {e}")
        return []

@tool
def get_financial_statement(file_name: str, symbols: str = ['fb', 'aapl', 'amzn', 'nflx', 'goog']):
    """
    Use this to retrieve financial data from Yahoo Finance, such as accessing balance sheets, income statements, and cash flow statements based on the ticker symbol for the company for analysis.
    """
    stock_data = Ticker(symbols)

    balance_df = stock_data.balance_sheet().set_index('asOfDate')
    balance_df['CurrentRatio'] = balance_df['CurrentAssets'] / balance_df['CurrentLiabilities']
    balance_df['QuickRatio'] = balance_df['CurrentAssets'] / balance_df['Inventory'] / balance_df['CurrentLiabilities']
    balance_df['DebtToEquityRatio'] = balance_df['TotalDebt'] / balance_df['StockholdersEquity']

    csv_path = CSV_DIR / 'balance_sheet.csv'
    balance_df.to_csv(csv_path, index=False)

    return {'csv_filename': csv_path.name, 'csv_columns': balance_df.columns.tolist()}

@tool
def visualize_financial_data(file_name: str, column: str, title: str):
    """
    Use this to create a matplotlib figure to visualize the value of a financial metric over time.
    """
    csv_path = CSV_DIR / "balance_sheet.csv"
    df = pd.read_csv(csv_path)

    plt.figure(figsize=(8, 5))
    df.plot(y=column, legend=True, marker='o')
    plt.xlabel('Date')
    plt.ylabel('Value')
    plt.grid(True)
    img_path = VIS_DIR / f"{title}.png"
    plt.savefig(img_path)
    plt.show()

    return {'figure_file_name': f'{title}.png'}

@tool
def convert_text_to_pdf(text: str, file_name: str):
    """
    Use this to write plain or markdown text to PDF file and generate the PDF document.
    Call this only when the user asks for PDF document generation.
    """
    pdf = MarkdownPdf()
    pdf.add_section(Section(text))
    pdf.save(file_name)

    return {'pdf_file_name': file_name}