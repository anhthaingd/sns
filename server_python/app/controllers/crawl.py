from bs4 import BeautifulSoup
from playwright.async_api import async_playwright


async def _get_page_content_and_css(url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--no-sandbox", "--disable-setuid-sandbox"])
        page = await browser.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)

        css_content = await page.evaluate("""
            () => {
                return Array.from(document.styleSheets)
                    .map(styleSheet => {
                        try {
                            return Array.from(styleSheet.cssRules)
                                .map(cssRule => cssRule.cssText)
                                .join('\\n');
                        } catch (error) {
                            return '';
                        }
                    })
                    .join('\\n');
            }
        """)

        html_content = await page.content()
        await browser.close()
        return html_content, css_content


async def crawl_dai_job(cur_page: int = 1):
    try:
        url = f"https://www.daijob.com/jobs/search_result?job_post_language=2&job_search_form_hidden=1&page={cur_page}"
        html_content, css_content = await _get_page_content_and_css(url)

        soup = BeautifulSoup(html_content, "html.parser")
        data = []
        for element in soup.select(".job-card-wrap"):
            el_html = str(element)
            el_html = el_html.replace('href="/jobs', 'href="https://www.daijob.com/jobs')
            el_html = el_html.replace("data-src=", "src=")
            data.append(el_html)

        return {"status": 200, "body": {"html": data, "css": css_content}}
    except Exception as e:
        print(f"Error crawling: {e}")
        return {"status": 500, "body": {"error": "Có lỗi xảy ra khi crawl dữ liệu"}}


async def crawl_linked(cur_page: int = 1):
    try:
        offset = (cur_page - 1) * 25
        url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?currentJobId=3942468982&keywords=information%2Btechnology&location=japan&start={offset}"
        html_content, css_content = await _get_page_content_and_css(url)

        soup = BeautifulSoup(html_content, "html.parser")
        data = []
        for element in soup.select(
            ".base-card.relative.w-full.hover\\:no-underline.focus\\:no-underline.base-card--link.base-search-card.base-search-card--link.job-search-card"
        ):
            el_html = "".join(str(child) for child in element.children)
            el_html = el_html.replace("data-delayed-url", "src")
            el_html = el_html.replace(
                "base-card__full-link absolute top-0 right-0 bottom-0 left-0 p-0 z-[2]",
                "base-card__full-link",
            )
            data.append(el_html)

        return {"status": 200, "body": {"html": data, "css": css_content}}
    except Exception as e:
        print(f"Error crawling: {e}")
        return {"status": 500, "body": {"error": "Có lỗi xảy ra khi crawl dữ liệu"}}


async def crawl_nihongo(cur_page: int = 1):
    try:
        url = f"https://nihongo-engineer.com/?page={cur_page}"
        html_content, css_content = await _get_page_content_and_css(url)

        soup = BeautifulSoup(html_content, "html.parser")
        data = []
        for element in soup.select(".job-item"):
            el_html = "".join(str(child) for child in element.children)
            el_html = el_html.replace(
                "/upload/image_job",
                "https://nihongo-engineer.com/upload/image_job",
            )
            data.append(el_html)

        return {"status": 200, "body": {"html": data, "css": css_content}}
    except Exception as e:
        print(f"Error crawling: {e}")
        return {"status": 500, "body": {"error": "Có lỗi xảy ra khi crawl dữ liệu"}}


async def crawl_gaijinpot(cur_page: int = 1):
    try:
        url = f"https://jobs.gaijinpot.com/job/index/page/{cur_page}"
        html_content, css_content = await _get_page_content_and_css(url)

        soup = BeautifulSoup(html_content, "html.parser")
        data = []
        for element in soup.select(".card.card--premium.gpjs-open-link"):
            el_html = "".join(str(child) for child in element.children)
            el_html = el_html.replace("/job/view", "https://jobs.gaijinpot.com/job/view")
            data.append(el_html)

        return {"status": 200, "body": {"html": data, "css": css_content}}
    except Exception as e:
        print(f"Error crawling: {e}")
        return {"status": 500, "body": {"error": "Có lỗi xảy ra khi crawl dữ liệu"}}
