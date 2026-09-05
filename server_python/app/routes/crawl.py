from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.controllers.crawl import crawl_dai_job, crawl_gaijinpot, crawl_linked, crawl_nihongo

router = APIRouter()


@router.get("/crawl/linked_jp_jobs")
async def route_crawl_linked(curPage: int | None = Query(1)):
    result = await crawl_linked(curPage or 1)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.get("/crawl/dai_job")
async def route_crawl_dai_job(curPage: int | None = Query(1)):
    result = await crawl_dai_job(curPage or 1)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.get("/crawl/nihongo")
async def route_crawl_nihongo(curPage: int | None = Query(1)):
    result = await crawl_nihongo(curPage or 1)
    return JSONResponse(status_code=result["status"], content=result["body"])


@router.get("/crawl/gaijinpot")
async def route_crawl_gaijinpot(curPage: int | None = Query(1)):
    result = await crawl_gaijinpot(curPage or 1)
    return JSONResponse(status_code=result["status"], content=result["body"])
