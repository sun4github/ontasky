from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.assigners import (
    AssignerCredentialCreateRequest,
    AssignerCredentialListResponse,
    AssignerCredentialResponse,
    AssignerGrantCreateRequest,
    AssignerGrantListResponse,
    AssignerGrantResponse,
    AssignerRequestCreateRequest,
    AssignerRequestListResponse,
    AssignerRequestRejectPayload,
    AssignerRequestResponse,
)
from app.schemas.common import MessageResponse, get_user_id

router = APIRouter(prefix="/api/v1", tags=["assigners"])


@router.post("/assigners/grants", response_model=AssignerGrantResponse, status_code=201)
async def create_assigner_grant(
    req: AssignerGrantCreateRequest,
    user_id: UUID = Depends(get_user_id),
):
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/assigners/grants", response_model=AssignerGrantListResponse)
async def list_assigner_grants(user_id: UUID = Depends(get_user_id)):
    raise HTTPException(status_code=501, detail="Not implemented")


@router.delete("/assigners/grants/{assigner_user_id}", response_model=MessageResponse)
async def delete_assigner_grant(
    assigner_user_id: UUID,
    user_id: UUID = Depends(get_user_id),
):
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/assigners/requests", response_model=AssignerRequestResponse, status_code=201)
async def create_assigner_request(
    req: AssignerRequestCreateRequest,
    user_id: UUID = Depends(get_user_id),
):
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/assigners/requests", response_model=AssignerRequestListResponse)
async def list_assigner_requests(user_id: UUID = Depends(get_user_id)):
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/assigners/requests/{request_id}/approve", response_model=AssignerRequestResponse)
async def approve_assigner_request(
    request_id: UUID,
    user_id: UUID = Depends(get_user_id),
):
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/assigners/requests/{request_id}/reject", response_model=AssignerRequestResponse)
async def reject_assigner_request(
    request_id: UUID,
    req: AssignerRequestRejectPayload,
    user_id: UUID = Depends(get_user_id),
):
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post(
    "/assigners/credentials",
    response_model=AssignerCredentialResponse,
    status_code=201,
)
async def create_assigner_credential(
    req: AssignerCredentialCreateRequest,
    user_id: UUID = Depends(get_user_id),
):
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/assigners/credentials", response_model=AssignerCredentialListResponse)
async def list_assigner_credentials(user_id: UUID = Depends(get_user_id)):
    raise HTTPException(status_code=501, detail="Not implemented")


@router.delete("/assigners/credentials/{credential_id}", response_model=MessageResponse)
async def delete_assigner_credential(
    credential_id: UUID,
    user_id: UUID = Depends(get_user_id),
):
    raise HTTPException(status_code=501, detail="Not implemented")