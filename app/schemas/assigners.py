from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class AssignerPermissions(BaseModel):
    can_create_grants: bool = False
    can_request_grants: bool = False
    can_manage_credentials: bool = False


class AssignerGrantCreateRequest(BaseModel):
    assigner_user_id: UUID
    permissions: AssignerPermissions
    expires_at: Optional[datetime] = None


class AssignerGrantResponse(BaseModel):
    id: UUID
    user_id: UUID
    assigner_user_id: UUID
    permissions: AssignerPermissions
    created_at: datetime
    expires_at: Optional[datetime]
    revoked_at: Optional[datetime]


class AssignerGrantListResponse(BaseModel):
    items: list[AssignerGrantResponse]
    total: int


class AssignerRequestCreateRequest(BaseModel):
    assigner_user_id: UUID
    permissions: AssignerPermissions
    note: Optional[str] = None


class AssignerRequestRejectPayload(BaseModel):
    reason: Optional[str] = None


class AssignerRequestResponse(BaseModel):
    id: UUID
    user_id: UUID
    assigner_user_id: UUID
    permissions: AssignerPermissions
    status: str
    note: Optional[str]
    rejection_reason: Optional[str]
    created_at: datetime
    responded_at: Optional[datetime]


class AssignerRequestListResponse(BaseModel):
    items: list[AssignerRequestResponse]
    total: int


class AssignerCredentialCreateRequest(BaseModel):
    assigner_user_id: UUID
    label: Optional[str] = None
    token_hint: Optional[str] = None
    expires_at: Optional[datetime] = None


class AssignerCredentialResponse(BaseModel):
    id: UUID
    user_id: UUID
    assigner_user_id: UUID
    label: Optional[str]
    token_hint: Optional[str]
    secret: Optional[str] = None  # Populated only when credential is created
    created_at: datetime
    expires_at: Optional[datetime]
    revoked_at: Optional[datetime]


class AssignerCredentialListResponse(BaseModel):
    items: list[AssignerCredentialResponse]
    total: int