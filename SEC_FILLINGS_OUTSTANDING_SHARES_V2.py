import requests
from datetime import datetime
from bs4 import BeautifulSoup
from constant import get_sp500_tickers
from concurrent.futures import ThreadPoolExecutor, as_completed

def is_share_label(text):
    """
    Normalize and check if the label likely refers to shares outstanding.
    """
    text = text.lower().replace(",", "").replace("\xa0", " ").strip()
    if not ("share" in text and "outstanding" in text):
        return False
    optional_keywords = ['common', 'stock', 'entity', 'ordinary', 'class']
    return any(word in text for word in optional_keywords)

def get_company_shares(ticker, filing_date):
    cookies = {
        'bm_mi': '369E6E4488D760FBE0631097DC2448D9~YAAQBXUsMeKLWAmWAQAA4XCYCRv1mb5ZrfJd8EcfmMeedCVeApjGnWcoJZdrQbvWaUVgKZM2fxwVmNu+6Ardt7zOmGcGaOIfLRZgtXp0j/2cLJb3LsZn2YCevhUwjtFLZegQvbxbFnB1dvICjFugGeA/HptahB+1fmy9Lgf54e7qDKnknu6viPUgOZR8kLcQXW+/92QncLzZOI9t7lW62+/AOVtFc03HWO6aoBMzBybpy2FvsnRIIkFOzhvOYDiMdSA5hYkZ0sq9uqNwJuIPV8TnrlkuQEeVodpcvxZ03dcWCkft7h/nlnD1~1',
        'ak_bmsc': '491AB94E8EB86ADF73E56D7C777B9481~000000000000000000000000000000~YAAQBXUsMRWMWAmWAQAAZ4GYCRsQqHwEI/whKsK2NY34go4k4DbLUOVSYtEeusPmatLM85PA2E6QcBWKUDBZOvf48vhTBV3mQJ+5aWk9/qm9bAOc73sUCjlo9nLQn6crRiQZR1yH1vjdfXzhG0GiSBYvlEMVeLFLOCn+BRsQdWIvy+9v6kI1vh+ARVasptd2C5lTSO2vOY4JR6yBZE/gO65SisN/bLz2PQc2CtSuBFOM6QVA26AciUTrNfxnFl0iEopyKfjYfvpG9K7GLKdpLfjjV3ROBSmoE5liqjQqGumfnQ4x7tKyqOb6y+EKkafuLeGKIu9B7KZoqzWBRA+JRtb2DtrnVCCsygWmUL4go3RCX39Ln4cMju7XL67p4b1XkGjfVFepY0/ru2xiSrorj+lT+T7v+/kLDUSR+TZ0ELpa30zP2cyN2VU3daTocaiKrqskTjF9+N8TIKQlom348Dys5J7ZBHw0XIs=',
        'bm_sv': '669A0D0FB8263E82C6A4BD37D137A148~YAAQBXUsMR+QWAmWAQAAQ3+ZCRuz3I1IBhcqHa6BM6rIqDZwOTRdnRr1+9fZ5Tbpu0Yf8+bXtCYTZJFZz2EzCvuYrCxsB15fH6WXLvQYGuF3X8pjtFRQaqwAXXHjbE2QZSnpNCslYmMba+XTkH4vkXw1t1C27+9RTTujZKPcLeEkyHMzkjiaTf3KOBaIUDwWkD35K3hj3XtHmsFb0RTYibeXBVVCWZyDculZ7WeR6Up/ubXXsXHaPB0g9RX8g==~1',
    }

    def get_cik(ticker):
        headers = {
            'accept-language': 'en-US,en;q=0.5',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
        }
        res = requests.get('https://www.sec.gov/files/company_tickers.json', cookies=cookies, headers=headers).json()
        for k, v in res.items():
            if v['ticker'].lower() == ticker.lower():
                return str(v['cik_str']).zfill(10)
        return None

    cik = get_cik(ticker)
    if not cik:
        return ticker, None

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
    })

    def get_filing_url(cik, form_type, before_date):
        url = f'https://data.sec.gov/submissions/CIK{int(cik):010d}.json'
        try:
            res = session.get(url)
            res.raise_for_status()
            data = res.json()
        except Exception:
            return None

        filings = data.get("filings", {}).get("recent", {})
        dates = filings.get("filingDate", [])
        forms = filings.get("form", [])
        accession_nums = filings.get("accessionNumber", [])

        before = datetime.strptime(before_date, "%Y-%m-%d")

        for form, date_str, acc_num in zip(forms, dates, accession_nums):
            if form == form_type:
                filing_date = datetime.strptime(date_str, "%Y-%m-%d")
                if filing_date <= before:
                    acc_num_fmt = acc_num.replace("-", "")
                    doc_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_num_fmt}/{acc_num}-index.htm"
                    return doc_url
        return None

    url = get_filing_url(cik, "10-Q", filing_date)
    if not url:
        return ticker, None

    base = url.rsplit('/', 1)[0]
    r1_url = f"{base}/R1.htm"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.sec.gov/',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    response = requests.get(r1_url, headers=headers)
    if response.status_code != 200:
        return ticker, None

    soup = BeautifulSoup(response.text, 'html.parser')
    rows = soup.find_all('tr')

    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 2:
            label = cells[0].get_text(strip=True)
            if is_share_label(label):
                for i in range(1, len(cells)):
                    value = cells[i].get_text(strip=True).replace(",", "").replace("\u00a0", "")
                    if value.replace('.', '', 1).isdigit():
                        shares = float(value)
                        return ticker, shares
    return ticker, None

def process_tickers(tickers, filing_date, max_workers=10):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit tasks for each ticker
        future_to_ticker = {executor.submit(get_company_shares, ticker, filing_date): ticker for ticker in tickers}
        for future in as_completed(future_to_ticker):
            ticker, shares = future.result()
            if shares:
                print(f"{ticker}: {shares}")
            else:
                print(f"Shares Outstanding Not found for {ticker}")

if __name__ == "__main__":
    tickers = get_sp500_tickers
    process_tickers(tickers, '2024-11-03')
