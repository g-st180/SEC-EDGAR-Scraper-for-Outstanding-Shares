# 📊 SEC Outstanding Shares Scraper

A Python tool to extract the Outstanding Shares value from a U.S. public company's 10-Q or 10-K filing using the SEC EDGAR system.

---

## 🚀 What It Does

- Navigates to a company's SEC filing index page (10-Q / 10-K)
- Opens the Interactive XBRL viewer
- Dynamically locates the “Common Stock, Shares Outstanding” value in the table.
- Accurately retrieves the number of shares outstanding for a specific stock on a given date

---

## ✅ No API keys required — uses publicly available SEC.gov resources

---

## 🛠️ Tech Stack

- Python
- Selenium
- webdriver-manager
- ChromeDriver
- requests
