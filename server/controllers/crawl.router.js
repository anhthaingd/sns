import cheerio from 'cheerio';
import puppeteer from 'puppeteer';
export const crawlDaiJob = async (req, res) => {
  const { curPage } = req.query;
  try {
    const url = `https://www.daijob.com/jobs/search_result?job_post_language=2&job_search_form_hidden=1&page=${
      curPage ? curPage : 1
    }`;

    // Sử dụng Puppeteer để mở trang web và lấy CSS của trang
    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    await page.goto(url);
    const cssContent = await page.evaluate(() => {
      return Array.from(document.styleSheets)
        .map((styleSheet) => {
          try {
            return Array.from(styleSheet.cssRules)
              .map((cssRule) => cssRule.cssText)
              .join('\n');
          } catch (error) {
            console.error('Error processing CSS rule:', error);
            return '';
          }
        })
        .join('\n');
    });

    // Sử dụng Cheerio để phân tích HTML và lấy dữ liệu cần thiết
    const htmlContent = await page.content();
    const $ = cheerio.load(htmlContent);

    const data = [];
    $('.jobs_box.mb16').each((index, element) => {
      const el = $(element)
        .html()
        .replace(/\/jobs/g, 'https://www.daijob.com/jobs')
        .replace('src="/images/.png?"', '')
        .replace('data-src', 'src');
      data.push(el);
    });

    await browser.close();

    res.json({ html: data, css: cssContent });
  } catch (error) {
    console.error(`Có lỗi xảy ra: ${error}`);
    res.status(500).json({ error: 'Có lỗi xảy ra khi crawl dữ liệu' });
  }
};

export const crawlLinked = async (req, res) => {
  const { curPage } = req.query;
  const offset = curPage ? Number(curPage - 1) * 25 : 0;
  try {
    const url = `https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?currentJobId=3942468982&keywords=information%2Btechnology&location=japan&start=${offset}`;

    // Sử dụng Puppeteer để mở trang web và lấy CSS của trang
    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    await page.goto(url);
    const cssContent = await page.evaluate(() => {
      return Array.from(document.styleSheets)
        .map((styleSheet) => {
          try {
            return Array.from(styleSheet.cssRules)
              .map((cssRule) => cssRule.cssText)
              .join('\n');
          } catch (error) {
            console.error('Error processing CSS rule:', error);
            return '';
          }
        })
        .join('\n');
    });

    // Sử dụng Cheerio để phân tích HTML và lấy dữ liệu cần thiết
    const htmlContent = await page.content();
    const $ = cheerio.load(htmlContent);
    const data = [];
    $(
      '.base-card.relative.w-full.hover\\:no-underline.focus\\:no-underline.base-card--link.base-search-card.base-search-card--link.job-search-card'
    ).each((index, element) => {
      const el = $(element)
        .html()
        .replace('data-delayed-url', 'src')
        .replace(
          'base-card__full-link absolute top-0 right-0 bottom-0 left-0 p-0 z-[2]',
          'base-card__full-link'
        );
      data.push(el);
    });
    await browser.close();

    return res.json({ html: data, css: cssContent });
  } catch (error) {
    console.error(`Có lỗi xảy ra: ${error}`);
    return res.status(500).json({ error: 'Có lỗi xảy ra khi crawl dữ liệu' });
  }
};

export const crawlNihongo = async (req, res) => {
  const { curPage } = req.query;
  try {
    const url = `https://nihongo-engineer.com/?page=${curPage ? curPage : 1}`;

    // Sử dụng Puppeteer để mở trang web và lấy CSS của trang
    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    await page.goto(url);
    const cssContent = await page.evaluate(() => {
      return Array.from(document.styleSheets)
        .map((styleSheet) => {
          try {
            return Array.from(styleSheet.cssRules)
              .map((cssRule) => cssRule.cssText)
              .join('\n');
          } catch (error) {
            console.error('Error processing CSS rule:', error);
            return '';
          }
        })
        .join('\n');
    });
    // Sử dụng Cheerio để phân tích HTML và lấy dữ liệu cần thiết
    const htmlContent = await page.content();
    const $ = cheerio.load(htmlContent);
    const data = [];
    $('.job-item').each((index, element) => {
      const el = $(element)
        .html()
        .replace(
          '/upload/image_job',
          'https://nihongo-engineer.com/upload/image_job'
        );
      data.push(el);
    });
    await browser.close();

    return res.json({ html: data, css: cssContent });
  } catch (error) {
    console.error(`Có lỗi xảy ra: ${error}`);
    return res.status(500).json({ error: 'Có lỗi xảy ra khi crawl dữ liệu' });
  }
};
export const crawlGaijinpot = async (req, res) => {
  const { curPage } = req.query;
  try {
    const url = `https://jobs.gaijinpot.com/job/index/page/${
      curPage ? curPage : 1
    }`;

    // Sử dụng Puppeteer để mở trang web và lấy CSS của trang
    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    await page.goto(url);
    const cssContent = await page.evaluate(() => {
      return Array.from(document.styleSheets)
        .map((styleSheet) => {
          try {
            return Array.from(styleSheet.cssRules)
              .map((cssRule) => cssRule.cssText)
              .join('\n');
          } catch (error) {
            console.error('Error processing CSS rule:', error);
            return '';
          }
        })
        .join('\n');
    });
    // Sử dụng Cheerio để phân tích HTML và lấy dữ liệu cần thiết
    const htmlContent = await page.content();
    const $ = cheerio.load(htmlContent);
    const data = [];
    $('.card.card--premium.gpjs-open-link').each((index, element) => {
      const el = $(element)
        .html()
        .replace('/job/view', 'https://jobs.gaijinpot.com/job/view');
      data.push(el);
    });
    await browser.close();

    return res.json({ html: data, css: cssContent });
  } catch (error) {
    console.error(`Có lỗi xảy ra: ${error}`);
    return res.status(500).json({ error: 'Có lỗi xảy ra khi crawl dữ liệu' });
  }
};
export const crawlJobsinjapan = async (req, res) => {
  const { curPage } = req.query;
  try {
    const url = `https://jobsinjapan.com/job-category/information-technology-telecommunications/page/${
      curPage ? curPage : 1
    }`;

    // Sử dụng Puppeteer để mở trang web và lấy CSS của trang
    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    await page.goto(url);
    const cssContent = await page.evaluate(() => {
      return Array.from(document.styleSheets)
        .map((styleSheet) => {
          try {
            return Array.from(styleSheet.cssRules)
              .map((cssRule) => cssRule.cssText)
              .join('\n');
          } catch (error) {
            console.error('Error processing CSS rule:', error);
            return '';
          }
        })
        .join('\n');
    });
    // Sử dụng Cheerio để phân tích HTML và lấy dữ liệu cần thiết
    const htmlContent = await page.content();
    const $ = cheerio.load(htmlContent);
    const data = [];
    $(
      '.loadmore-item.noo_job.style-1.type-noo_job.status-publish.hentry.job_category-information-technology-telecommunications.job_type-full-time.job_location-tokyo.no-featured'
    ).each((index, element) => {
      const el = $(element).html().split('<div class="job-tools">')[0];
      data.push(el);
    });
    await browser.close();

    return res.json({ html: data, css: cssContent });
  } catch (error) {
    console.error(`Có lỗi xảy ra: ${error}`);
    return res.status(500).json({ error: 'Có lỗi xảy ra khi crawl dữ liệu' });
  }
};
