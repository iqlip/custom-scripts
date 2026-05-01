import asyncio
import urllib.parse
from playwright.async_api import async_playwright

# Use nest_asyncio only if running in Jupyter/Colab
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass

DORK = 'site:github.io "resume" filetype:pdf'
OUTPUT_FILE = "github_resumes_google.txt"

async def get_google_page_number(page):
    """Helper to find the active page number on Google's UI"""
    try:
        # Google marks the current page in a <td> with a specific class or lack of <a> tag
        # This selector targets the 'active' page number in the footer
        page_num = await page.evaluate('''() => {
            const activePage = document.querySelector('td.YyVfkd');
            return activePage ? activePage.innerText : "1";
        }''')
        return page_num
    except:
        return "1"

async def google_scraper():
    pdf_links = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        query = urllib.parse.quote(DORK)
        url = f"https://www.google.com/search?q={query}"
        
        await page.goto(url)

        try:
            while True:
                current_url = page.url
                current_page_no = await get_google_page_number(page)

                print(f"\n--- [ CURRENTLY ON GOOGLE PAGE: {current_page_no} ] ---")
                print("[*] Scanning for PDF links...")
                
                try:
                    all_hrefs = await page.evaluate("() => Array.from(document.querySelectorAll('a')).map(a => a.href)")
                    
                    new_finds = 0
                    for href in all_hrefs:
                        clean_url = href
                        if "/url?q=" in href:
                            try:
                                clean_url = href.split("/url?q=")[1].split("&")[0]
                                clean_url = urllib.parse.unquote(clean_url)
                            except: continue

                        if "github.io" in clean_url and clean_url.lower().endswith(".pdf"):
                            if clean_url not in pdf_links:
                                pdf_links.add(clean_url)
                                new_finds += 1
                                print(f"  [+] Found: {clean_url}")

                    print(f"[*] Done with Page {current_page_no}. Total unique links: {len(pdf_links)}")
                except Exception as e:
                    print(f"[!] Error during scan: {e}")

                print(f"\n[>] PLEASE CLICK NEXT PAGE (e.g., Page {int(current_page_no)+1 if current_page_no.isdigit() else '??'}) IN BROWSER...")

                # Wait for the URL to change
                while page.url == current_url:
                    await asyncio.sleep(0.5)
                    if page.is_closed():
                        break
                
                if page.is_closed():
                    break

                # Wait for the new page to actually load its content
                await asyncio.sleep(2) 

        except Exception as e:
            print(f"\n[!] Browser closed or session ended.")

        # Final Save
        if pdf_links:
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                for link in sorted(pdf_links):
                    f.write(link + "\n")
            print(f"\n--- SUCCESS ---")
            print(f"Saved {len(pdf_links)} unique resumes to {OUTPUT_FILE}")

if __name__ == "__main__":
    try:
        asyncio.run(google_scraper())
    except KeyboardInterrupt:
        print("\n[!] Script stopped by user.")