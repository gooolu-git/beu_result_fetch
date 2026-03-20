import os
import asyncio
import io
import uuid
from flask import Flask, render_template, request, send_file, redirect, url_for, after_this_request
from playwright.async_api import async_playwright
from PyPDF2 import PdfMerger
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

app = Flask(__name__)

STATIC_DIR = os.path.join('static', 'results')
os.makedirs(STATIC_DIR, exist_ok=True)

# Dropped concurrency slightly to 7 to prevent university server from blocking/timing out
CONCURRENCY_LIMIT = 7 
MAX_TOTAL_SEARCHES = 60

async def capture_single_pdf(semaphore, browser, target_url, reg_no):
    async with semaphore:
        # Using a fresh context for each to avoid cache/session bleed
        context = await browser.new_context()
        page = await context.new_page()
        try:
            print(f"--> Fetching: {reg_no}")
            # CHANGED: 'networkidle' ensures the data has actually loaded from the backend
            await page.goto(target_url, wait_until="networkidle", timeout=45000)
            
            # CHANGED: Explicitly wait for the table to have content (rows)
            await page.wait_for_selector("table tr", timeout=20000)
            
            # Hide UI elements
            await page.add_style_tag(content=".no-print, button, .btn, nav, footer { display: none !important; }")
            
            # Small delay to ensure any JS-based styling finishes
            await asyncio.sleep(0.5)

            pdf_bytes = await page.pdf(
                format="A4", 
                print_background=True,
                margin={"top": "0.4in", "right": "0.4in", "bottom": "0.4in", "left": "0.4in"}
            )
            await context.close()
            return pdf_bytes
        except Exception as e:
            print(f" [!] Skip {reg_no} due to timeout/empty: {e}")
            await context.close()
            return None

async def run_batch(raw_url, start_num, end_num):
    parsed_url = urlparse(raw_url)
    query_params = parse_qs(parsed_url.query)
    async with async_playwright() as p:
        # Added a small slowMo to simulate human behavior and avoid blocking
        browser = await p.chromium.launch(headless=True)
        semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
        tasks = []
        for reg in range(start_num, end_num + 1):
            query_params['regNo'] = [str(reg)]
            target_url = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, '', urlencode(query_params, doseq=True), ''))
            tasks.append(capture_single_pdf(semaphore, browser, target_url, reg))
        
        results = await asyncio.gather(*tasks)
        await browser.close()
        return results

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        raw_url = request.form.get('url', '').strip()
        start_reg = request.form.get('start_reg', '').strip()
        end_reg = request.form.get('end_reg', '').strip()
        try:
            start_num, end_num = int(start_reg), int(end_reg)
            
            # Handle the async loop correctly within Flask
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            pdf_list = loop.run_until_complete(run_batch(raw_url, start_num, end_num))
            loop.close()

            valid_pdfs = [pdf for pdf in pdf_list if pdf is not None]
            if valid_pdfs:
                unique_filename = f"Batch_{uuid.uuid4().hex[:8]}.pdf"
                file_path = os.path.join(STATIC_DIR, unique_filename)
                
                merger = PdfMerger()
                for pdf_data in valid_pdfs:
                    merger.append(io.BytesIO(pdf_data))
                merger.write(file_path)
                merger.close()

                return redirect(url_for('thankyou', file=unique_filename))

            return "No valid marksheets were captured. The server might be busy.", 404
        except Exception as e:
            return f"Error: {str(e)}", 500
    return render_template('index.html')

@app.route('/thankyou')
def thankyou():
    file_name = request.args.get('file')
    return render_template('thankyou.html', file_name=file_name)

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(STATIC_DIR, filename)
    
    @after_this_request
    def remove_file(response):
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass
        return response
        
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)