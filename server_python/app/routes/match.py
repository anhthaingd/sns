from fastapi import APIRouter, Body, Depends, Query

from app.controllers.admin_etl import etl_status, start_etl
from app.controllers.advice import (
    company_advice,
    job_advice,
    overview_advice,
    whatif_advice,
)
from app.controllers.match import (
    company_gap,
    job_gap,
    match_companies,
    match_jobs,
    whatif_simulate,
    whatif_suggestions,
)
from app.middleware.auth import get_current_user
from app.schemas.responses import (
    ERROR_RESPONSES,
    AdviceResponse,
    CompanyGapResponse,
    CompanyMatchResponse,
    EtlStatusResponse,
    GapResponse,
    JobMatchResponse,
    MessageResponse,
    WhatIfSimulateResponse,
    WhatIfSuggestionsResponse,
)

router = APIRouter(tags=["match"], responses=ERROR_RESPONSES)


@router.get("/api/match/companies", response_model=CompanyMatchResponse)
async def route_match_companies(
    page: int | None = Query(1, ge=1),
    qualifiedOnly: bool = Query(False),
    decoded=Depends(get_current_user),
):
    return await match_companies(decoded, page or 1, qualifiedOnly)


@router.get("/api/match/jobs", response_model=JobMatchResponse)
async def route_match_jobs(page: int | None = Query(1, ge=1), decoded=Depends(get_current_user)):
    return await match_jobs(decoded, page or 1)


@router.get("/api/match/jobs/{job_id}/gap", response_model=GapResponse)
async def route_job_gap(job_id: str, decoded=Depends(get_current_user)):
    return await job_gap(decoded, job_id)


@router.get("/api/match/companies/{company_id}/gap", response_model=CompanyGapResponse)
async def route_company_gap(company_id: str, decoded=Depends(get_current_user)):
    return await company_gap(decoded, company_id)


@router.get("/api/match/whatif", response_model=WhatIfSuggestionsResponse)
async def route_whatif(decoded=Depends(get_current_user)):
    return await whatif_suggestions(decoded)


@router.post("/api/match/whatif", response_model=WhatIfSimulateResponse)
async def route_whatif_simulate(
    actions: list[dict] | None = Body(default=None, embed=True),
    decoded=Depends(get_current_user),
):
    return await whatif_simulate(decoded, actions)


# --- Lời khuyên bằng LLM ----------------------------------------------------
# Endpoint RIÊNG, không gộp vào /gap: /gap trả về trong ~15ms, gộp lời gọi LLM
# vào đó thì màn hình phải đợi 2-5 giây mới hiện được cả những thứ đã tính xong
# từ lâu. Xem docs/12-loi-khuyen-bang-llm.md muc 12.11.


@router.get("/api/match/advice/overview", response_model=AdviceResponse)
async def route_overview_advice(
    page: int | None = Query(1, ge=1),
    # Phải nhận đúng bộ lọc mà trang danh sách đang dùng, nếu không lời khuyên
    # sẽ mô tả một tập công ty khác với tập đang hiện trên màn hình.
    qualifiedOnly: bool = Query(False),
    lang: str | None = Query(None, description="ja | vi | en"),
    decoded=Depends(get_current_user),
):
    return await overview_advice(decoded, page or 1, lang, qualifiedOnly)


@router.get("/api/match/jobs/{job_id}/advice", response_model=AdviceResponse)
async def route_job_advice(
    job_id: str,
    lang: str | None = Query(None, description="ja | vi | en"),
    decoded=Depends(get_current_user),
):
    return await job_advice(decoded, job_id, lang)


@router.get("/api/match/companies/{company_id}/advice", response_model=AdviceResponse)
async def route_company_advice(
    company_id: str,
    lang: str | None = Query(None, description="ja | vi | en"),
    decoded=Depends(get_current_user),
):
    return await company_advice(decoded, company_id, lang)


@router.get("/api/match/whatif/advice", response_model=AdviceResponse)
async def route_whatif_advice(
    lang: str | None = Query(None, description="ja | vi | en"),
    decoded=Depends(get_current_user),
):
    return await whatif_advice(decoded, lang)


# --- Quản trị dữ liệu -------------------------------------------------------


@router.post("/api/admin/etl/run", response_model=MessageResponse)
async def route_start_etl(
    sources: list[str] | None = Body(default=None, embed=True),
    pages: int = Body(default=3, embed=True),
    detail: int = Body(default=0, embed=True),
    decoded=Depends(get_current_user),
):
    return await start_etl(decoded, sources, pages, detail)


@router.get("/api/admin/etl/status", response_model=EtlStatusResponse)
async def route_etl_status(decoded=Depends(get_current_user)):
    return await etl_status(decoded)
