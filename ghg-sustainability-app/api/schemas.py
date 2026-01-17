"""
Pydantic Schemas for FastAPI Endpoints
Request/Response models for GHG workflow API
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ==================================================================
# ENUMS
# ==================================================================

class ProjectStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_CALCULATION = "UNDER_CALCULATION"
    PENDING_REVIEW = "PENDING_REVIEW"
    REJECTED = "REJECTED"
    APPROVED = "APPROVED"
    LOCKED = "LOCKED"


class UserRole(str, Enum):
    L1 = "L1"  # Data Entry Specialist
    L2 = "L2"  # Calculation Specialist
    L3 = "L3"  # QA Reviewer
    L4 = "L4"  # Approver/Manager


class Scope(str, Enum):
    SCOPE_1 = "Scope 1"
    SCOPE_2 = "Scope 2"
    SCOPE_3 = "Scope 3"


class ReviewResult(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


# ==================================================================
# AUTH SCHEMAS
# ==================================================================

class TokenRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"


class TokenData(BaseModel):
    user_id: int
    username: str
    role: UserRole


# ==================================================================
# USER SCHEMAS
# ==================================================================

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    role: UserRole


class UserCreate(UserBase):
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ==================================================================
# PROJECT SCHEMAS
# ==================================================================

class ProjectBase(BaseModel):
    project_name: str = Field(..., min_length=1, max_length=255)
    organization_name: str = Field(..., min_length=1, max_length=255)
    reporting_year: int = Field(..., ge=2000, le=2100)
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    project_name: Optional[str] = Field(None, min_length=1, max_length=255)
    organization_name: Optional[str] = Field(None, min_length=1, max_length=255)
    reporting_year: Optional[int] = Field(None, ge=2000, le=2100)
    description: Optional[str] = None


class ProjectResponse(ProjectBase):
    id: int
    status: ProjectStatus
    created_by: int
    created_by_email: Optional[str]
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime]
    calculated_at: Optional[datetime]
    reviewed_at: Optional[datetime]
    approved_at: Optional[datetime]
    locked_at: Optional[datetime]
    total_scope1: float
    total_scope2: float
    total_scope3: float
    total_emissions: float

    class Config:
        from_attributes = True


class ProjectStatusResponse(BaseModel):
    project_id: int
    project_name: str
    status: str
    workflow_lane: str
    available_transitions: List[str]
    data_records: int
    calculations: int
    reviews: int
    totals: Dict[str, float]
    timestamps: Dict[str, Optional[str]]


# ==================================================================
# DATA COLLECTION SCHEMAS (Lane 1)
# ==================================================================

class RawDataCollect(BaseModel):
    criteria_id: int
    activity_data: float = Field(..., gt=0)
    unit: str = Field(..., min_length=1, max_length=50)
    notes: Optional[str] = None


class RawDataCollectResponse(BaseModel):
    step: str
    project_data_id: int
    project_id: int
    status: str


class AggregateDataResponse(BaseModel):
    step: str
    project_id: int
    total_records: int
    total_activity_data: float
    status: str


class QualityCheckIssue(BaseModel):
    record_id: int
    issue: str
    severity: str


class QualityCheckResponse(BaseModel):
    step: str
    project_id: int
    passed: bool
    total_records: int
    issues: List[QualityCheckIssue]
    status: str


class SubmitForCalculationResponse(BaseModel):
    step: str
    project_id: int
    new_status: str
    status: str


# ==================================================================
# DATA TRANSFORMATION SCHEMAS (Lane 2)
# ==================================================================

class MappedRecord(BaseModel):
    project_data_id: int
    criteria_id: int
    activity_data: float
    unit: Optional[str]
    notes: Optional[str]
    has_evidence: int
    entered_at: Optional[str]


class MapDataResponse(BaseModel):
    step: str
    project_id: int
    mapped_count: int
    mapped_records: List[MappedRecord]
    status: str


class TransformDataRequest(BaseModel):
    project_data_id: int
    emission_factor: float = Field(..., gt=0)
    emission_factor_source: str = Field(..., min_length=1)
    scope: Scope
    category: str = Field(..., min_length=1)
    gwp: float = Field(default=1.0, ge=0)
    unit_conversion: float = Field(default=1.0, ge=0)
    notes: Optional[str] = None


class TransformDataResponse(BaseModel):
    step: str
    calculation_id: int
    emissions_tco2e: float
    scope: str
    status: str


class ValidationIssue(BaseModel):
    calculation_id: Optional[int] = None
    issue: str
    expected: Optional[float] = None
    actual: Optional[float] = None


class ValidateTransformationResponse(BaseModel):
    step: str
    project_id: int
    data_accuracy_compliant: bool
    issues: List[Dict[str, Any]]
    status: str


class UpdateTotalsResponse(BaseModel):
    step: str
    project_id: int
    scope1: float
    scope2: float
    scope3: float
    total: float
    status: str


class SubmitForReviewResponse(BaseModel):
    step: str
    project_id: int
    new_status: str
    status: str


# ==================================================================
# DATA VERIFICATION SCHEMAS (Lane 3)
# ==================================================================

class VerificationIssue(BaseModel):
    type: str
    project_data_id: Optional[int] = None
    calculation_id: Optional[int] = None
    message: str


class VerifyDataResponse(BaseModel):
    step: str
    project_id: int
    issues: List[Dict[str, Any]]
    verification_passed: bool
    status: str


class ComplianceIssue(BaseModel):
    code: str
    calculation_id: Optional[int] = None
    message: str


class ComplianceCheckResponse(BaseModel):
    step: str
    project_id: int
    compliant: bool
    issues: List[Dict[str, Any]]
    protocols_checked: List[str]
    status: str


class ApproveVerificationRequest(BaseModel):
    comments: Optional[str] = None


class ApproveVerificationResponse(BaseModel):
    step: str
    project_id: int
    verifier: int
    approved: bool
    new_status: str
    status: str


class RejectVerificationRequest(BaseModel):
    reason_code: str = Field(..., min_length=1)
    comments: str = Field(..., min_length=1)


class RejectVerificationResponse(BaseModel):
    step: str
    project_id: int
    verifier: int
    rejected: bool
    reason_code: str
    new_status: str
    status: str


class VerificationReportResponse(BaseModel):
    step: str
    report_id: str
    project_id: int
    project_name: str
    total_reviews: int
    latest_review: Optional[str]
    generated_at: str
    status: str


# ==================================================================
# FINAL REVIEW SCHEMAS (Lane 4)
# ==================================================================

class FinalReviewResponse(BaseModel):
    step: str
    project_id: int
    project_name: str
    organization: str
    reporting_year: int
    total_scope1: float
    total_scope2: float
    total_scope3: float
    total_emissions: float
    calculation_count: int
    current_status: str
    status: str


class FinalApprovalRequest(BaseModel):
    comments: Optional[str] = None


class FinalApprovalResponse(BaseModel):
    step: str
    project_id: int
    manager: int
    approved: bool
    new_status: str
    locked_at: Optional[str]
    status: str


class ApprovalDocsResponse(BaseModel):
    step: str
    document_id: str
    project_id: int
    approval_count: int
    generated_at: str
    status: str


class ArchiveDataResponse(BaseModel):
    step: str
    archive_id: str
    project_id: int
    archived_at: str
    status: str


# ==================================================================
# REPORTING SCHEMAS (Lane 5)
# ==================================================================

class ScopeBreakdown(BaseModel):
    total: float
    categories: Dict[str, float]


class DashboardDataResponse(BaseModel):
    step: str
    project_id: int
    project_name: str
    organization: str
    reporting_year: int
    status: str
    scope_breakdown: Dict[str, ScopeBreakdown]
    totals: Dict[str, float]
    dashboard_url: str


class GHGReportResponse(BaseModel):
    step: str
    report_id: str
    report_title: str
    organization: str
    reporting_year: int
    report_date: str
    scope1_emissions: float
    scope2_emissions: float
    scope3_emissions: float
    total_emissions: float
    calculation_count: int
    verification_status: str
    protocols: List[str]
    status: str


class ComplianceStatusResponse(BaseModel):
    step: str
    project_id: int
    compliance_checks: Dict[str, bool]
    overall_compliant: bool
    status: str


# ==================================================================
# GENERIC RESPONSES
# ==================================================================

class WorkflowStepResponse(BaseModel):
    step: str
    project_id: int
    status: str
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None


class SuccessResponse(BaseModel):
    message: str
    data: Optional[Dict[str, Any]] = None


# ==================================================================
# LIST RESPONSES
# ==================================================================

class ProjectListResponse(BaseModel):
    projects: List[ProjectResponse]
    total: int
    page: int
    page_size: int


# Update forward references
Token.model_rebuild()
