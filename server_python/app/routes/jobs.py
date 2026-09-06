from fastapi import APIRouter, Depends, Query

from app.controllers.jobs import (
    get_companies,
    get_company_details,
    get_job_details,
    get_job_filters,
    get_jobs,
    job_market,
)
from app.middleware.auth import get_current_user
from app.schemas.responses import (
    ERROR_RESPONSES,
    CompanyDetailsResponse,
    CompanyListResponse,
    JobDetailsResponse,
    JobFiltersResponse,
    JobListResponse,
    MarketResponse,
)

router = APIRouter(tags=["jobs"], responses=ERROR_RESPONSES)


@router.get("/api/jobs", response_model=JobListResponse)
async def route_get_jobs(
    page: int | None = Query(1, ge=1),
    search: str | None = Query(None),
    prefecture: str | None = Query(None),
    japanese: str | None = Query(None),
    salaryMin: int | None = Query(None, ge=0),
    skills: list[str] | None = Query(None),
    remote: bool | None = Query(None),
    company: str | None = Query(None),
    decoded=Depends(get_current_user),
):
    return await get_jobs(
        page=page or 1,
        search=search,
        prefecture=prefecture,
        japanese=japanese,
        salary_min=salaryMin,
        skills=skills,
        remote=remote,
        company_id=company,
    )


@router.get("/api/jobs/filters", response_model=JobFiltersResponse)
async def route_get_job_filters(decoded=Depends(get_current_user)):
    return await get_job_filters()


@router.get("/api/jobs/market", response_model=MarketResponse)
async def route_job_market(decoded=Depends(get_current_user)):
    return await job_market(decoded)


@router.get("/api/jobs/{job_id}", response_model=JobDetailsResponse)
async def route_get_job_details(job_id: str, decoded=Depends(get_current_user)):
    return await get_job_details(job_id)


@router.get("/api/companies", response_model=CompanyListResponse)
async def route_get_companies(
    page: int | None = Query(1, ge=1),
    search: str | None = Query(None),
    withProfile: bool = Query(False),
    decoded=Depends(get_current_user),
):
    return await get_companies(page or 1, search, withProfile)


@router.get("/api/companies/{company_id}", response_model=CompanyDetailsResponse)
async def route_get_company_details(company_id: str, decoded=Depends(get_current_user)):
    return await get_company_details(company_id)
