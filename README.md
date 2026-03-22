# BEU Result Engine 🎓

A high-speed, automated batch downloader for **Bihar Engineering University (BEU)** results. This tool allows users to enter a range of registration numbers and a sample URL to generate a single, merged PDF containing all marksheets instantly.

![Version](https://img.shields.io/badge/version-2.0-black)
![Python](https://img.shields.io/badge/python-3.9+-blue)
![Playwright](https://img.shields.io/badge/engine-playwright-green)

## 🚀 Features

* **Batch Processing:** Download up to 60 marksheets in a single request.
* **High Speed:** Uses asynchronous programming (`asyncio`) and parallel browser instances (`Playwright`) to process multiple results simultaneously.
* **Automatic Merging:** Combines all individual marksheets into one clean, high-quality PDF document.
* **Clean Layout:** Injected CSS automatically hides UI elements like buttons, navbars, and footers for a professional PDF look.
* **Self-Cleaning:** Server-side logic using Flask's `after_this_request` automatically deletes temporary files after the download is complete to save storage.
* **Modern UI:** Clean, responsive interface built with Bootstrap 5 and the Plus Jakarta Sans typeface.

## 🛠️ Tech Stack

* **Backend:** Flask (Python)
* **Automation:** Playwright (Chromium)
* **PDF Manipulation:** PyPDF2
* **Frontend:** HTML5, CSS3 (Bootstrap 5)

## 📦 Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/gooolu-git/beu-result-engine.git
    cd beu-result-engine
    ```

2.  **Install dependencies:**
    ```bash
    pip install flask playwright pypdf2
    ```

3.  **Install Browser Engines:**
    ```bash
    playwright install chromium
    ```

4.  **Run the App:**
    ```bash
    python app.py
    ```
## 🚀 Deployment

You can pull and run the latest version of the BEU Result Engine directly from Docker Hub:

```bash
docker pull gooolu/beu-result-engine:latest

## 📂 Project Structure

```text
/beu-result-engine
│
├── app.py              # Main Flask application logic & PDF generation
├── .gitignore          # Prevents temp PDFs and cache from being tracked
├── README.md           # Project documentation
├── templates/          # HTML templates folder
│   ├── index.html      # Professional landing page & input form
│   └── thankyou.html   # Success page with auto-download trigger
└── static/
    └── results/        # Temporary storage for generated PDFs (auto-cleaned)
