import { Router, json } from 'express';
import {
  crawlDaiJob,
  crawlGaijinpot,
  crawlJobsinjapan,
  crawlLinked,
  crawlNihongo,
} from '../controllers/crawl.router.js';
export const router_crawl = Router();
router_crawl.use(json());
router_crawl.route('/crawl/linked_jp_jobs').get(crawlLinked);
router_crawl.route('/crawl/dai_job').get(crawlDaiJob);
router_crawl.route('/crawl/nihongo').get(crawlNihongo);
router_crawl.route('/crawl/gaijinpot').get(crawlGaijinpot);
// router_crawl.route('/crawl/jobsinjapan').get(crawlJobsinjapan);
