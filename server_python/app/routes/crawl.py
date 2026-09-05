from fastapi import APIRouter, Query

from app.controllers.crawl import crawl_dai_job, crawl_gaijinpot, crawl_linked, crawl_nihongo
from app.schemas.responses import ERROR_RESPONSES, CrawlResponse

router = APIRouter(tags=["crawl"], responses=ERROR_RESPONSES)


@router.get("/crawl/linked_jp_jobs", response_model=CrawlResponse)
async def route_crawl_linked(curPage: int | None = Query(1, ge=1)):
    return await crawl_linked(curPage or 1)


@router.get("/crawl/dai_job", response_model=CrawlResponse)
async def route_crawl_dai_job(curPage: int | None = Query(1, ge=1)):
    return await crawl_dai_job(curPage or 1)


@router.get("/crawl/nihongo", response_model=CrawlResponse)
async def route_crawl_nihongo(curPage: int | None = Query(1, ge=1)):
    return await crawl_nihongo(curPage or 1)


@router.get("/crawl/gaijinpot", response_model=CrawlResponse)
async def route_crawl_gaijinpot(curPage: int | None = Query(1, ge=1)):
    return await crawl_gaijinpot(curPage or 1)
