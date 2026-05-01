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
OUTPUT_FILE = "github_resumes.txt"

async def copilot_scraper():
    pdf_links = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        query = urllib.parse.quote(DORK)
        url = f"https://duckduckgo.com/?q={query}&ia=web"
        
        print(f"\n[*] GOAL: {DORK}")
        print("[!] INSTRUCTIONS:")
        print("    1. Look at the browser window.")
        print("    2. When you want more results, CLICK 'More Results' manually.")
        print("    3. The script will detect the click and scrape the new links automatically.")
        print("    4. Close the browser window when you are finished.\n")

        await page.goto(url, wait_until="domcontentloaded")

        last_count = 0
        try:
            while True:
                # 1. Scrape all currently visible links
                all_hrefs = await page.evaluate("() => Array.from(document.querySelectorAll('a')).map(a => a.href)")
                
                new_finds = 0
                for href in all_hrefs:
                    clean_url = href
                    if "uddg=" in href:
                        try:
                            clean_url = urllib.parse.unquote(href.split("uddg=")[1].split("&")[0])
                        except: continue

                    if "github.io" in clean_url and clean_url.lower().endswith(".pdf"):
                        if clean_url not in pdf_links:
                            pdf_links.add(clean_url)
                            new_finds += 1
                            print(f"  [+] Scraped: {clean_url}")

                if new_finds > 0:
                    print(f"[*] Added {new_finds} new links. Total unique: {len(pdf_links)}")
                
                # 2. Wait for the user to click the button
                print("[>] Waiting for you to click 'More Results' in the browser...")
                
                # This waits for the network to become active (meaning you clicked) 
                # and then silent again (meaning the results loaded)
                try:
                    await page.wait_for_load_state("networkidle", timeout=0) # 0 means wait forever
                except Exception:
                    # If the browser is closed manually, break the loop
                    break
                    
                # Small pause to let the DOM settle after the click
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
    asyncio.run(copilot_scraper())