import os
import asyncio
import io
import uuid
from flask import Flask, render_template, request, send_file, redirect, url_for, after_this_request ,send_from_directory
from playwright.async_api import async_playwright
from PyPDF2 import PdfMerger
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

app = Flask(__name__)

# Render uses /tmp for temporary writable storage
STATIC_DIR = os.path.join('/tmp', 'results')
os.makedirs(STATIC_DIR, exist_ok=True)

CONCURRENCY_LIMIT = 15 # Reduced slightly for Render Free Tier stability
MAX_TOTAL_SEARCHES = 60

async def capture_single_pdf(semaphore, browser, target_url, reg_no):
    async with semaphore:
        context = await browser.new_context()
        page = await context.new_page()
        try:
            print(f"--> Fetching: {reg_no}")
            await page.goto(target_url, wait_until="networkidle", timeout=60000)
            await page.wait_for_selector("table tr", timeout=20000)
            await page.add_style_tag(content=".no-print, button, .btn, nav, footer { display: none !important; }")
            await asyncio.sleep(1)

            pdf_bytes = await page.pdf(
                format="A4", 
                print_background=True,
                margin={"top": "0.4in", "right": "0.4in", "bottom": "0.4in", "left": "0.4in"}
            )
            await context.close()
            return pdf_bytes
        except Exception as e:
            print(f" [!] Skip {reg_no}: {e}")
            await context.close()
            return None

async def run_batch(raw_url, start_num, end_num):
    parsed_url = urlparse(raw_url)
    query_params = parse_qs(parsed_url.query)
    async with async_playwright() as p:
        # Essential flags for running in Docker/Render
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
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
        start_num = int(request.form.get('start_reg', 0))
        end_num = int(request.form.get('end_reg', 0))
        
        if (end_num - start_num) >= MAX_TOTAL_SEARCHES:
            return f"Error: Maximum range is {MAX_TOTAL_SEARCHES}", 400

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

        return "No results found or server timeout.", 404
    return render_template('index.html')

@app.route('/thankyou')
def thankyou():
    file_name = request.args.get('file')
    return render_template('thankyou.html', file_name=file_name)

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(STATIC_DIR, filename)
    
    if not os.path.exists(file_path):
        return "File already downloaded or expired.", 410

    return_data = send_file(file_path, as_attachment=True)

    @after_this_request
    def remove_file(response):
        try:
            os.remove(file_path)
        except Exception as error:
            app.logger.error(f"Error deleting file: {error}")
        return response

    return return_data
@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'sitemap.xml')


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)