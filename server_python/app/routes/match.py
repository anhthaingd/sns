from fastapi import APIRouter, Body, Depends, Query

from app.controllers.admin_etl import etl_status, start_etl
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
