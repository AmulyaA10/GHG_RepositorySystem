"""
GHG App Agent - Orchestrates the GHG data lifecycle
Aligned to GHG Protocol, ISO 14064-1/-3

Workflow Lanes:
1. DATA COLLECTION - Collect, aggregate, quality check
2. DATA TRANSFORMATION - Map, normalize, transform, validate
3. DATA VERIFICATION - Verify, compliance check, approval
4. FINAL REVIEW - Review, approve, archive
5. REPORTING - Dashboard, reports, distribution
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import func
import logging

from models.project import Project
from models.project_data import ProjectData
from models.calculation import Calculation
from models.review import Review
from models.approval import Approval
from core.workflow import WorkflowManager, STATE_TRANSITIONS

logger = logging.getLogger(__name__)


class GHGAgentError(Exception):
    """Base exception for GHG Agent errors."""
    pass


class ProjectNotFoundError(GHGAgentError):
    """Raised when a project is not found."""
    pass


class InvalidStateError(GHGAgentError):
    """Raised when an operation is not allowed in the current state."""
    pass


class ValidationError(GHGAgentError):
    """Raised when validation fails."""
    pass


class DatabaseError(GHGAgentError):
    """Raised when a database operation fails."""
    pass


class GHGAppAgent:
    """
    Orchestrates the GHG data lifecycle:
    1) Data Collection
    2) Data Transformation (Mapping)
    3) Data Verification
    4) Final Review (Validation)
    5) Approval & Reporting

    Aligned to GHG Protocol, ISO 14064-1/-3
    """

    # Valid scopes per GHG Protocol
    VALID_SCOPES = ["Scope 1", "Scope 2", "Scope 3"]

    # States that allow data modification
    EDITABLE_STATES = ["DRAFT", "SUBMITTED", "REJECTED"]

    def __init__(self, db: Session):
        if db is None:
            raise ValueError("Database session cannot be None")
        self.db = db

    def _get_project_or_raise(self, project_id: int) -> Project:
        """
        Retrieve a project by ID or raise ProjectNotFoundError.

        Args:
            project_id: The project ID to look up

        Returns:
            Project: The found project

        Raises:
            ProjectNotFoundError: If project does not exist
        """
        if not isinstance(project_id, int) or project_id <= 0:
            raise ValidationError(f"Invalid project_id: {project_id}")

        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.warning(f"Project not found: {project_id}")
            raise ProjectNotFoundError(f"Project {project_id} not found")
        return project

    def _safe_commit(self, operation: str = "operation") -> None:
        """
        Safely commit database transaction with rollback on failure.

        Args:
            operation: Description of the operation for logging

        Raises:
            DatabaseError: If commit fails
        """
        try:
            self.db.commit()
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error during {operation}: {e}")
            raise DatabaseError(f"Data integrity error during {operation}")
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error during {operation}: {e}")
            raise DatabaseError(f"Database error during {operation}: {str(e)}")

    def _validate_scope(self, scope: str) -> None:
        """Validate that scope is a valid GHG Protocol scope."""
        if scope not in self.VALID_SCOPES:
            raise ValidationError(
                f"Invalid scope '{scope}'. Must be one of: {', '.join(self.VALID_SCOPES)}"
            )

    def _validate_positive_number(self, value: float, field_name: str) -> None:
        """Validate that a number is positive."""
        if not isinstance(value, (int, float)):
            raise ValidationError(f"{field_name} must be a number")
        if value <= 0:
            raise ValidationError(f"{field_name} must be positive, got: {value}")

    # ==================================================================
    # LANE 1: DATA COLLECTION - Persona: Data Collector (L1)
    # ==================================================================

    def collect_raw_data(
        self,
        project_id: int,
        criteria_id: int,
        activity_data: float,
        unit: str,
        notes: Optional[str],
        user_id: int
    ) -> Dict[str, Any]:
        """
        Collect raw activity data for a project.
        Creates a ProjectData record.

        Args:
            project_id: Target project ID
            criteria_id: Emission criteria ID
            activity_data: Activity amount (must be positive)
            unit: Unit of measurement
            notes: Optional notes
            user_id: ID of user collecting data

        Returns:
            Dict with step result

        Raises:
            ProjectNotFoundError: If project doesn't exist
            InvalidStateError: If project is not in editable state
            ValidationError: If input validation fails
            DatabaseError: If database operation fails
        """
        # Input validation
        self._validate_positive_number(activity_data, "activity_data")
        if not unit or not unit.strip():
            raise ValidationError("Unit cannot be empty")
        if not isinstance(criteria_id, int) or criteria_id <= 0:
            raise ValidationError(f"Invalid criteria_id: {criteria_id}")
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValidationError(f"Invalid user_id: {user_id}")

        project = self._get_project_or_raise(project_id)

        if project.status not in self.EDITABLE_STATES:
            raise InvalidStateError(
                f"Cannot add data to project in {project.status} status. "
                f"Allowed states: {', '.join(self.EDITABLE_STATES)}"
            )

        try:
            project_data = ProjectData(
                project_id=project_id,
                criteria_id=criteria_id,
                activity_data=activity_data,
                unit=unit.strip(),
                notes=notes.strip() if notes else None,
                entered_by=user_id,
                entered_at=datetime.utcnow()
            )
            self.db.add(project_data)
            self._safe_commit("collect_raw_data")
            self.db.refresh(project_data)

            logger.info(
                f"Raw data collected: project={project_id}, criteria={criteria_id}, "
                f"activity={activity_data} {unit}, user={user_id}"
            )

            return {
                "step": "Collect Raw Data",
                "project_data_id": project_data.id,
                "project_id": project_id,
                "status": "DONE"
            }
        except (GHGAgentError, DatabaseError):
            raise
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Unexpected error in collect_raw_data: {e}")
            raise DatabaseError(f"Failed to collect raw data: {str(e)}")

    def aggregate_data(self, project_id: int) -> Dict[str, Any]:
        """
        Aggregate all collected data for a project.

        Args:
            project_id: Target project ID

        Returns:
            Dict with aggregation statistics

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        project = self._get_project_or_raise(project_id)

        try:
            data_records = self.db.query(ProjectData).filter(
                ProjectData.project_id == project_id
            ).all()

            total_records = len(data_records)
            total_activity = sum(
                d.activity_data for d in data_records if d.activity_data is not None
            )

            logger.debug(
                f"Aggregated data for project {project_id}: "
                f"{total_records} records, {total_activity} total activity"
            )

            return {
                "step": "Aggregate Data",
                "project_id": project_id,
                "project_name": project.project_name,
                "total_records": total_records,
                "total_activity_data": total_activity,
                "status": "DONE"
            }
        except SQLAlchemyError as e:
            logger.error(f"Database error in aggregate_data: {e}")
            raise DatabaseError(f"Failed to aggregate data: {str(e)}")

    def initial_quality_check(self, project_id: int) -> Dict[str, Any]:
        """
        Run initial quality checks on collected data.

        Checks:
        - No negative activity values (ERROR)
        - Units are specified (WARNING)
        - Evidence is attached (WARNING)

        Args:
            project_id: Target project ID

        Returns:
            Dict with QC results and any issues found

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        self._get_project_or_raise(project_id)

        try:
            data_records = self.db.query(ProjectData).filter(
                ProjectData.project_id == project_id
            ).all()

            if not data_records:
                return {
                    "step": "Initial Quality Check",
                    "project_id": project_id,
                    "passed": False,
                    "total_records": 0,
                    "issues": [{"record_id": None, "issue": "No data records found", "severity": "ERROR"}],
                    "status": "FAILED"
                }

            issues = []
            for record in data_records:
                # Check for negative values
                if record.activity_data is not None and record.activity_data < 0:
                    issues.append({
                        "record_id": record.id,
                        "issue": "Negative activity data",
                        "severity": "ERROR",
                        "value": record.activity_data
                    })
                # Check for missing units
                if not record.unit:
                    issues.append({
                        "record_id": record.id,
                        "issue": "Missing unit of measurement",
                        "severity": "WARNING"
                    })
                # Check for evidence
                if record.has_evidence == 0:
                    issues.append({
                        "record_id": record.id,
                        "issue": "No supporting evidence attached",
                        "severity": "WARNING"
                    })

            error_count = len([i for i in issues if i["severity"] == "ERROR"])
            warning_count = len([i for i in issues if i["severity"] == "WARNING"])
            passed = error_count == 0

            logger.info(
                f"QC for project {project_id}: passed={passed}, "
                f"errors={error_count}, warnings={warning_count}"
            )

            return {
                "step": "Initial Quality Check",
                "project_id": project_id,
                "passed": passed,
                "total_records": len(data_records),
                "error_count": error_count,
                "warning_count": warning_count,
                "issues": issues,
                "status": "DONE" if passed else "FAILED"
            }
        except SQLAlchemyError as e:
            logger.error(f"Database error in initial_quality_check: {e}")
            raise DatabaseError(f"Failed to run quality check: {str(e)}")

    def quality_check_pass(self, qc_result: Dict[str, Any]) -> bool:
        """
        Check if quality check passed.

        Args:
            qc_result: Result dict from initial_quality_check

        Returns:
            bool: True if QC passed (no errors)
        """
        if not isinstance(qc_result, dict):
            return False
        return qc_result.get("passed", False)

    def submit_for_calculation(
        self,
        project_id: int,
        user_id: int,
        user_role: str
    ) -> Dict[str, Any]:
        """
        Submit project for calculation (L1 -> L2 handoff).

        Args:
            project_id: Target project ID
            user_id: ID of user submitting
            user_role: Role of user (must be L1)

        Returns:
            Dict with submission result

        Raises:
            ProjectNotFoundError: If project doesn't exist
            InvalidStateError: If transition is not allowed
        """
        project = self._get_project_or_raise(project_id)

        try:
            WorkflowManager.transition(
                db=self.db,
                project=project,
                new_status="SUBMITTED",
                user_id=user_id,
                user_role=user_role,
                comments="Submitted for calculation"
            )

            logger.info(f"Project {project_id} submitted for calculation by user {user_id}")

            return {
                "step": "Submit for Calculation",
                "project_id": project_id,
                "new_status": "SUBMITTED",
                "status": "DONE"
            }
        except ValueError as e:
            raise InvalidStateError(str(e))

    # ==================================================================
    # LANE 2: DATA TRANSFORMATION - Persona: Data Mapper (L2)
    # ==================================================================

    def map_data_model(
        self,
        project_id: int,
        user_id: int,
        user_role: str
    ) -> Dict[str, Any]:
        """
        Map collected data to GHG emission schema.

        Args:
            project_id: Target project ID
            user_id: ID of user performing mapping
            user_role: Role of user (must be L2)

        Returns:
            Dict with mapped records

        Raises:
            ProjectNotFoundError: If project doesn't exist
            InvalidStateError: If transition is not allowed
        """
        project = self._get_project_or_raise(project_id)

        try:
            # Transition to UNDER_CALCULATION if coming from SUBMITTED
            if project.status == "SUBMITTED":
                WorkflowManager.transition(
                    db=self.db,
                    project=project,
                    new_status="UNDER_CALCULATION",
                    user_id=user_id,
                    user_role=user_role,
                    comments="Started calculation process"
                )

            data_records = self.db.query(ProjectData).filter(
                ProjectData.project_id == project_id
            ).all()

            mapped_records = [
                self._build_emission_record(record) for record in data_records
            ]

            logger.info(f"Mapped {len(mapped_records)} records for project {project_id}")

            return {
                "step": "Map Data Model",
                "project_id": project_id,
                "mapped_count": len(mapped_records),
                "mapped_records": mapped_records,
                "status": "DONE"
            }
        except ValueError as e:
            raise InvalidStateError(str(e))
        except SQLAlchemyError as e:
            logger.error(f"Database error in map_data_model: {e}")
            raise DatabaseError(f"Failed to map data: {str(e)}")

    def normalize_data(self, mapped_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize data - unit conversions, code standardization.

        Args:
            mapped_records: List of mapped records to normalize

        Returns:
            List of normalized records
        """
        if not mapped_records:
            return []

        normalized = []
        for record in mapped_records:
            if not isinstance(record, dict):
                continue

            normalized_record = record.copy()
            # Convert kg to tonnes
            if record.get("unit") == "kg" and "activity_data" in record:
                normalized_record["activity_data"] = record["activity_data"] / 1000
                normalized_record["unit"] = "tonnes"
            normalized.append(normalized_record)

        return normalized

    def transform_data(
        self,
        project_id: int,
        project_data_id: int,
        emission_factor: float,
        emission_factor_source: str,
        scope: str,
        category: str,
        user_id: int,
        gwp: float = 1.0,
        unit_conversion: float = 1.0,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transform activity data into emission calculations.

        Formula: emissions_kg = activity_data × emission_factor × GWP × unit_conversion

        Args:
            project_id: Target project ID
            project_data_id: Source data record ID
            emission_factor: Emission factor value (must be positive)
            emission_factor_source: Source reference (e.g., Ecoinvent ID)
            scope: GHG scope (Scope 1, 2, or 3)
            category: Emission category
            user_id: ID of user performing calculation
            gwp: Global Warming Potential (default 1.0)
            unit_conversion: Unit conversion factor (default 1.0)
            notes: Optional calculation notes

        Returns:
            Dict with calculation result

        Raises:
            ProjectNotFoundError: If project/data doesn't exist
            ValidationError: If input validation fails
            DatabaseError: If database operation fails
        """
        # Input validation
        self._validate_positive_number(emission_factor, "emission_factor")
        self._validate_positive_number(gwp, "gwp")
        self._validate_positive_number(unit_conversion, "unit_conversion")
        self._validate_scope(scope)

        if not emission_factor_source or not emission_factor_source.strip():
            raise ValidationError("emission_factor_source cannot be empty")
        if not category or not category.strip():
            raise ValidationError("category cannot be empty")

        # Verify project exists
        self._get_project_or_raise(project_id)

        # Get source data
        project_data = self.db.query(ProjectData).filter(
            ProjectData.id == project_data_id
        ).first()

        if not project_data:
            raise ProjectNotFoundError(f"ProjectData {project_data_id} not found")

        if project_data.project_id != project_id:
            raise ValidationError(
                f"ProjectData {project_data_id} does not belong to project {project_id}"
            )

        try:
            # Calculate emissions
            emissions_kg = (
                project_data.activity_data *
                emission_factor *
                gwp *
                unit_conversion
            )
            emissions_tco2e = emissions_kg / 1000

            calculation = Calculation(
                project_id=project_id,
                criteria_id=project_data.criteria_id,
                project_data_id=project_data_id,
                activity_data=project_data.activity_data,
                emission_factor=emission_factor,
                emission_factor_source=emission_factor_source.strip(),
                gwp=gwp,
                unit_conversion=unit_conversion,
                emissions_kg=emissions_kg,
                emissions_tco2e=emissions_tco2e,
                scope=scope,
                category=category.strip(),
                formula_used=(
                    f"Activity × EF × GWP × Conversion = "
                    f"{project_data.activity_data} × {emission_factor} × {gwp} × {unit_conversion}"
                ),
                calculation_breakdown={
                    "activity_data": project_data.activity_data,
                    "emission_factor": emission_factor,
                    "gwp": gwp,
                    "unit_conversion": unit_conversion,
                    "emissions_kg": emissions_kg,
                    "emissions_tco2e": emissions_tco2e
                },
                calculated_by=user_id,
                calculated_at=datetime.utcnow(),
                notes=notes.strip() if notes else None
            )

            self.db.add(calculation)
            self._safe_commit("transform_data")
            self.db.refresh(calculation)

            logger.info(
                f"Calculation created: project={project_id}, "
                f"emissions={emissions_tco2e:.4f} tCO2e, scope={scope}"
            )

            return {
                "step": "Transform Data",
                "calculation_id": calculation.id,
                "emissions_kg": emissions_kg,
                "emissions_tco2e": emissions_tco2e,
                "scope": scope,
                "status": "DONE"
            }
        except (GHGAgentError, DatabaseError):
            raise
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Unexpected error in transform_data: {e}")
            raise DatabaseError(f"Failed to create calculation: {str(e)}")

    def validate_data_transformation(self, project_id: int) -> Dict[str, Any]:
        """
        Validate transformed data for internal consistency.

        Checks:
        - Calculation accuracy (recalculates and compares)
        - Valid scope values

        Args:
            project_id: Target project ID

        Returns:
            Dict with validation results

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        self._get_project_or_raise(project_id)

        try:
            calculations = self.db.query(Calculation).filter(
                Calculation.project_id == project_id
            ).all()

            if not calculations:
                return {
                    "step": "Validate Data Transformation",
                    "project_id": project_id,
                    "data_accuracy_compliant": False,
                    "issues": [{"issue": "No calculations found for project"}],
                    "status": "FAILED"
                }

            issues = []
            for calc in calculations:
                # Verify calculation accuracy
                expected = (
                    calc.activity_data *
                    calc.emission_factor *
                    calc.gwp *
                    calc.unit_conversion
                )
                tolerance = 0.01  # Allow 0.01 kg tolerance for floating point
                if abs(calc.emissions_kg - expected) > tolerance:
                    issues.append({
                        "calculation_id": calc.id,
                        "issue": "Calculation mismatch",
                        "expected": round(expected, 4),
                        "actual": round(calc.emissions_kg, 4),
                        "difference": round(abs(calc.emissions_kg - expected), 4)
                    })

                # Check scope validity
                if calc.scope not in self.VALID_SCOPES:
                    issues.append({
                        "calculation_id": calc.id,
                        "issue": f"Invalid scope: {calc.scope}",
                        "valid_scopes": self.VALID_SCOPES
                    })

            is_compliant = len(issues) == 0

            return {
                "step": "Validate Data Transformation",
                "project_id": project_id,
                "calculations_checked": len(calculations),
                "data_accuracy_compliant": is_compliant,
                "issues": issues,
                "status": "DONE" if is_compliant else "ISSUES_FOUND"
            }
        except SQLAlchemyError as e:
            logger.error(f"Database error in validate_data_transformation: {e}")
            raise DatabaseError(f"Failed to validate data: {str(e)}")

    def update_project_totals(self, project_id: int) -> Dict[str, Any]:
        """
        Update project emission totals from calculations.

        Args:
            project_id: Target project ID

        Returns:
            Dict with updated totals

        Raises:
            ProjectNotFoundError: If project doesn't exist
            DatabaseError: If update fails
        """
        project = self._get_project_or_raise(project_id)

        try:
            # Calculate scope totals using aggregation
            scope1 = self.db.query(func.sum(Calculation.emissions_tco2e)).filter(
                Calculation.project_id == project_id,
                Calculation.scope == "Scope 1"
            ).scalar() or 0.0

            scope2 = self.db.query(func.sum(Calculation.emissions_tco2e)).filter(
                Calculation.project_id == project_id,
                Calculation.scope == "Scope 2"
            ).scalar() or 0.0

            scope3 = self.db.query(func.sum(Calculation.emissions_tco2e)).filter(
                Calculation.project_id == project_id,
                Calculation.scope == "Scope 3"
            ).scalar() or 0.0

            total = scope1 + scope2 + scope3

            project.total_scope1 = scope1
            project.total_scope2 = scope2
            project.total_scope3 = scope3
            project.total_emissions = total

            self._safe_commit("update_project_totals")

            logger.info(
                f"Updated totals for project {project_id}: "
                f"S1={scope1:.2f}, S2={scope2:.2f}, S3={scope3:.2f}, Total={total:.2f}"
            )

            return {
                "step": "Update Project Totals",
                "project_id": project_id,
                "scope1": scope1,
                "scope2": scope2,
                "scope3": scope3,
                "total": total,
                "status": "DONE"
            }
        except (GHGAgentError, DatabaseError):
            raise
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Unexpected error in update_project_totals: {e}")
            raise DatabaseError(f"Failed to update totals: {str(e)}")

    def submit_for_review(
        self,
        project_id: int,
        user_id: int,
        user_role: str
    ) -> Dict[str, Any]:
        """
        Submit calculated project for review (L2 -> L3 handoff).

        Args:
            project_id: Target project ID
            user_id: ID of user submitting
            user_role: Role of user (must be L2)

        Returns:
            Dict with submission result

        Raises:
            ProjectNotFoundError: If project doesn't exist
            InvalidStateError: If transition is not allowed
        """
        project = self._get_project_or_raise(project_id)

        # Update totals first
        self.update_project_totals(project_id)

        try:
            WorkflowManager.transition(
                db=self.db,
                project=project,
                new_status="PENDING_REVIEW",
                user_id=user_id,
                user_role=user_role,
                comments="Calculations complete, submitted for review"
            )

            logger.info(f"Project {project_id} submitted for review by user {user_id}")

            return {
                "step": "Submit for Review",
                "project_id": project_id,
                "new_status": "PENDING_REVIEW",
                "status": "DONE"
            }
        except ValueError as e:
            raise InvalidStateError(str(e))

    # ==================================================================
    # LANE 3: DATA VERIFICATION - Persona: Data Verifier (L3)
    # ==================================================================

    def verify_transformed_data(self, project_id: int) -> Dict[str, Any]:
        """
        Verify accuracy and integrity of transformed data.

        Checks:
        - All data records have calculations
        - Valid emission factors (positive values)

        Args:
            project_id: Target project ID

        Returns:
            Dict with verification results

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        self._get_project_or_raise(project_id)

        try:
            calculations = self.db.query(Calculation).filter(
                Calculation.project_id == project_id
            ).all()

            data_records = self.db.query(ProjectData).filter(
                ProjectData.project_id == project_id
            ).all()

            issues = []

            # Check all data has calculations
            calculated_data_ids = {c.project_data_id for c in calculations}
            for data in data_records:
                if data.id not in calculated_data_ids:
                    issues.append({
                        "type": "MISSING_CALCULATION",
                        "project_data_id": data.id,
                        "criteria_id": data.criteria_id,
                        "message": "No calculation found for this data record"
                    })

            # Check for reasonable emission factors
            for calc in calculations:
                if calc.emission_factor <= 0:
                    issues.append({
                        "type": "INVALID_EMISSION_FACTOR",
                        "calculation_id": calc.id,
                        "emission_factor": calc.emission_factor,
                        "message": "Emission factor must be positive"
                    })

            verification_passed = len(issues) == 0

            return {
                "step": "Verify Transformed Data",
                "project_id": project_id,
                "data_records_count": len(data_records),
                "calculations_count": len(calculations),
                "issues": issues,
                "verification_passed": verification_passed,
                "status": "DONE"
            }
        except SQLAlchemyError as e:
            logger.error(f"Database error in verify_transformed_data: {e}")
            raise DatabaseError(f"Failed to verify data: {str(e)}")

    def ghg_protocol_compliance_check(self, project_id: int) -> Dict[str, Any]:
        """
        Check compliance with GHG Protocol standards.

        Checks:
        - At least Scope 1 or Scope 2 is reported (GHG-001)
        - All emission factors have documented sources (GHG-002)

        Args:
            project_id: Target project ID

        Returns:
            Dict with compliance check results

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        self._get_project_or_raise(project_id)

        try:
            calculations = self.db.query(Calculation).filter(
                Calculation.project_id == project_id
            ).all()

            compliance_issues = []

            if not calculations:
                compliance_issues.append({
                    "code": "GHG-000",
                    "severity": "ERROR",
                    "message": "No calculations found - cannot verify compliance"
                })
                return {
                    "step": "GHG Protocol Compliance Check",
                    "project_id": project_id,
                    "compliant": False,
                    "issues": compliance_issues,
                    "protocols_checked": ["GHG Protocol", "ISO 14064-1"],
                    "status": "FAILED"
                }

            # Check scope coverage (GHG Protocol requires Scope 1 and 2 at minimum)
            scopes_present = {c.scope for c in calculations}
            if "Scope 1" not in scopes_present and "Scope 2" not in scopes_present:
                compliance_issues.append({
                    "code": "GHG-001",
                    "severity": "ERROR",
                    "message": "GHG Protocol requires at least Scope 1 or Scope 2 emissions",
                    "scopes_found": list(scopes_present)
                })

            # Check emission factor documentation
            for calc in calculations:
                if not calc.emission_factor_source:
                    compliance_issues.append({
                        "code": "GHG-002",
                        "severity": "WARNING",
                        "calculation_id": calc.id,
                        "message": "Emission factor source not documented (required for audit trail)"
                    })

            is_compliant = not any(
                i.get("severity") == "ERROR" for i in compliance_issues
            )

            return {
                "step": "GHG Protocol Compliance Check",
                "project_id": project_id,
                "compliant": is_compliant,
                "issues": compliance_issues,
                "scopes_reported": list(scopes_present),
                "protocols_checked": ["GHG Protocol", "ISO 14064-1"],
                "status": "DONE"
            }
        except SQLAlchemyError as e:
            logger.error(f"Database error in ghg_protocol_compliance_check: {e}")
            raise DatabaseError(f"Failed compliance check: {str(e)}")

    def create_review(
        self,
        project_id: int,
        reviewer_id: int,
        review_result: str,
        comments: Optional[str] = None,
        reason_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a review record for the project.

        Args:
            project_id: Target project ID
            reviewer_id: ID of reviewer
            review_result: Result (APPROVED or REJECTED)
            comments: Optional review comments
            reason_code: Required for rejections

        Returns:
            Dict with review creation result

        Raises:
            ValidationError: If input validation fails
            DatabaseError: If database operation fails
        """
        if review_result not in ["APPROVED", "REJECTED"]:
            raise ValidationError(
                f"Invalid review_result: {review_result}. Must be APPROVED or REJECTED"
            )

        if review_result == "REJECTED" and not reason_code:
            raise ValidationError("reason_code is required for rejection")

        try:
            review = Review(
                project_id=project_id,
                reviewer_id=reviewer_id,
                review_result=review_result,
                comments=comments.strip() if comments else None,
                reason_code=reason_code,
                reviewed_at=datetime.utcnow()
            )
            self.db.add(review)
            self._safe_commit("create_review")
            self.db.refresh(review)

            logger.info(
                f"Review created: project={project_id}, result={review_result}, "
                f"reviewer={reviewer_id}"
            )

            return {
                "step": "Create Review",
                "review_id": review.id,
                "result": review_result,
                "status": "DONE"
            }
        except (GHGAgentError, DatabaseError):
            raise
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Unexpected error in create_review: {e}")
            raise DatabaseError(f"Failed to create review: {str(e)}")

    def approve_verification(
        self,
        project_id: int,
        verifier_id: int,
        verifier_role: str,
        comments: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Approve verification and transition to APPROVED status.

        Args:
            project_id: Target project ID
            verifier_id: ID of verifier
            verifier_role: Role of verifier (must be L3)
            comments: Optional approval comments

        Returns:
            Dict with approval result

        Raises:
            ProjectNotFoundError: If project doesn't exist
            InvalidStateError: If transition is not allowed
        """
        project = self._get_project_or_raise(project_id)

        # Create review record
        self.create_review(
            project_id=project_id,
            reviewer_id=verifier_id,
            review_result="APPROVED",
            comments=comments
        )

        try:
            WorkflowManager.transition(
                db=self.db,
                project=project,
                new_status="APPROVED",
                user_id=verifier_id,
                user_role=verifier_role,
                comments=comments or "Verification approved"
            )

            logger.info(f"Project {project_id} approved by verifier {verifier_id}")

            return {
                "step": "Approval of Verification",
                "project_id": project_id,
                "verifier": verifier_id,
                "approved": True,
                "new_status": "APPROVED",
                "status": "DONE"
            }
        except ValueError as e:
            raise InvalidStateError(str(e))

    def reject_verification(
        self,
        project_id: int,
        verifier_id: int,
        verifier_role: str,
        reason_code: str,
        comments: str
    ) -> Dict[str, Any]:
        """
        Reject verification and transition to REJECTED status.

        Args:
            project_id: Target project ID
            verifier_id: ID of verifier
            verifier_role: Role of verifier (must be L3)
            reason_code: Reason code for rejection
            comments: Rejection comments (required)

        Returns:
            Dict with rejection result

        Raises:
            ProjectNotFoundError: If project doesn't exist
            ValidationError: If comments are empty
            InvalidStateError: If transition is not allowed
        """
        if not comments or not comments.strip():
            raise ValidationError("Comments are required for rejection")
        if not reason_code or not reason_code.strip():
            raise ValidationError("Reason code is required for rejection")

        project = self._get_project_or_raise(project_id)

        # Create review record
        self.create_review(
            project_id=project_id,
            reviewer_id=verifier_id,
            review_result="REJECTED",
            comments=comments,
            reason_code=reason_code
        )

        try:
            WorkflowManager.transition(
                db=self.db,
                project=project,
                new_status="REJECTED",
                user_id=verifier_id,
                user_role=verifier_role,
                comments=comments,
                reason_code=reason_code
            )

            logger.info(
                f"Project {project_id} rejected by verifier {verifier_id}, "
                f"reason: {reason_code}"
            )

            return {
                "step": "Rejection of Verification",
                "project_id": project_id,
                "verifier": verifier_id,
                "rejected": True,
                "reason_code": reason_code,
                "new_status": "REJECTED",
                "status": "DONE"
            }
        except ValueError as e:
            raise InvalidStateError(str(e))

    def generate_verification_report(self, project_id: int) -> Dict[str, Any]:
        """
        Generate verification report for the project.

        Args:
            project_id: Target project ID

        Returns:
            Dict with report details

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        project = self._get_project_or_raise(project_id)

        try:
            reviews = self.db.query(Review).filter(
                Review.project_id == project_id
            ).order_by(Review.reviewed_at.desc()).all()

            report_id = f"VR-{project_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

            return {
                "step": "Generate Verification Report",
                "report_id": report_id,
                "project_id": project_id,
                "project_name": project.project_name,
                "total_reviews": len(reviews),
                "latest_review": reviews[0].review_result if reviews else None,
                "generated_at": datetime.utcnow().isoformat(),
                "status": "GENERATED"
            }
        except SQLAlchemyError as e:
            logger.error(f"Database error in generate_verification_report: {e}")
            raise DatabaseError(f"Failed to generate report: {str(e)}")

    # ==================================================================
    # LANE 4: FINAL REVIEW - Persona: Sustainability Manager (L4)
    # ==================================================================

    def final_data_review(self, project_id: int) -> Dict[str, Any]:
        """
        Perform final data review before locking.

        Args:
            project_id: Target project ID

        Returns:
            Dict with project summary for review

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        project = self._get_project_or_raise(project_id)

        try:
            calc_count = self.db.query(Calculation).filter(
                Calculation.project_id == project_id
            ).count()

            return {
                "step": "Final Data Review",
                "project_id": project_id,
                "project_name": project.project_name,
                "organization": project.organization_name,
                "reporting_year": project.reporting_year,
                "total_scope1": project.total_scope1 or 0.0,
                "total_scope2": project.total_scope2 or 0.0,
                "total_scope3": project.total_scope3 or 0.0,
                "total_emissions": project.total_emissions or 0.0,
                "calculation_count": calc_count,
                "current_status": project.status,
                "status": "DONE"
            }
        except SQLAlchemyError as e:
            logger.error(f"Database error in final_data_review: {e}")
            raise DatabaseError(f"Failed to retrieve project data: {str(e)}")

    def final_data_approval(
        self,
        project_id: int,
        manager_id: int,
        manager_role: str,
        comments: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Final approval and lock the project.

        Args:
            project_id: Target project ID
            manager_id: ID of manager approving
            manager_role: Role of manager (must be L4)
            comments: Optional approval comments

        Returns:
            Dict with approval result

        Raises:
            ProjectNotFoundError: If project doesn't exist
            InvalidStateError: If transition is not allowed
            DatabaseError: If database operation fails
        """
        project = self._get_project_or_raise(project_id)

        try:
            # Create approval record
            approval = Approval(
                project_id=project_id,
                approver_id=manager_id,
                approval_status="APPROVED",
                comments=comments.strip() if comments else None,
                approved_at=datetime.utcnow()
            )
            self.db.add(approval)

            WorkflowManager.transition(
                db=self.db,
                project=project,
                new_status="LOCKED",
                user_id=manager_id,
                user_role=manager_role,
                comments=comments or "Final approval - project locked"
            )

            logger.info(f"Project {project_id} locked by manager {manager_id}")

            return {
                "step": "Final Data Approval",
                "project_id": project_id,
                "manager": manager_id,
                "approved": True,
                "new_status": "LOCKED",
                "locked_at": project.locked_at.isoformat() if project.locked_at else None,
                "status": "DONE"
            }
        except ValueError as e:
            self.db.rollback()
            raise InvalidStateError(str(e))
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error in final_data_approval: {e}")
            raise DatabaseError(f"Failed to lock project: {str(e)}")

    def generate_approval_docs(self, project_id: int) -> Dict[str, Any]:
        """
        Generate approval documentation.

        Args:
            project_id: Target project ID

        Returns:
            Dict with document details

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        project = self._get_project_or_raise(project_id)

        try:
            approval_count = self.db.query(Approval).filter(
                Approval.project_id == project_id
            ).count()

            doc_id = f"APPR-{project_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

            return {
                "step": "Generate Approval Docs",
                "document_id": doc_id,
                "project_id": project_id,
                "project_name": project.project_name,
                "approval_count": approval_count,
                "generated_at": datetime.utcnow().isoformat(),
                "status": "GENERATED"
            }
        except SQLAlchemyError as e:
            logger.error(f"Database error in generate_approval_docs: {e}")
            raise DatabaseError(f"Failed to generate documents: {str(e)}")

    def archive_approved_data(self, project_id: int) -> Dict[str, Any]:
        """
        Archive approved project data.

        Args:
            project_id: Target project ID

        Returns:
            Dict with archive details

        Raises:
            ProjectNotFoundError: If project doesn't exist
            InvalidStateError: If project is not LOCKED
        """
        project = self._get_project_or_raise(project_id)

        if project.status != "LOCKED":
            raise InvalidStateError(
                f"Only LOCKED projects can be archived. Current status: {project.status}"
            )

        archive_id = f"ARCH-{project_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        logger.info(f"Project {project_id} archived with ID {archive_id}")

        return {
            "step": "Archive Approved Data",
            "archive_id": archive_id,
            "project_id": project_id,
            "project_name": project.project_name,
            "archived_at": datetime.utcnow().isoformat(),
            "status": "ARCHIVED"
        }

    # ==================================================================
    # LANE 5: REPORTING - Dashboard & Reports
    # ==================================================================

    def generate_dashboard_data(self, project_id: int) -> Dict[str, Any]:
        """
        Generate dashboard data for a project.

        Args:
            project_id: Target project ID

        Returns:
            Dict with dashboard data including scope breakdown

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        project = self._get_project_or_raise(project_id)

        try:
            calculations = self.db.query(Calculation).filter(
                Calculation.project_id == project_id
            ).all()

            # Group by scope
            scope_breakdown = {}
            for calc in calculations:
                if calc.scope not in scope_breakdown:
                    scope_breakdown[calc.scope] = {"total": 0.0, "categories": {}}
                scope_breakdown[calc.scope]["total"] += calc.emissions_tco2e or 0.0

                if calc.category not in scope_breakdown[calc.scope]["categories"]:
                    scope_breakdown[calc.scope]["categories"][calc.category] = 0.0
                scope_breakdown[calc.scope]["categories"][calc.category] += calc.emissions_tco2e or 0.0

            return {
                "step": "Generate Dashboard Data",
                "project_id": project_id,
                "project_name": project.project_name,
                "organization": project.organization_name,
                "reporting_year": project.reporting_year,
                "status": project.status,
                "scope_breakdown": scope_breakdown,
                "totals": {
                    "scope1": project.total_scope1 or 0.0,
                    "scope2": project.total_scope2 or 0.0,
                    "scope3": project.total_scope3 or 0.0,
                    "total": project.total_emissions or 0.0
                },
                "dashboard_url": f"/dashboards/ghg/{project_id}"
            }
        except SQLAlchemyError as e:
            logger.error(f"Database error in generate_dashboard_data: {e}")
            raise DatabaseError(f"Failed to generate dashboard: {str(e)}")

    def create_ghg_report(self, project_id: int) -> Dict[str, Any]:
        """
        Create comprehensive GHG inventory report.

        Args:
            project_id: Target project ID

        Returns:
            Dict with report details

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        project = self._get_project_or_raise(project_id)

        try:
            calc_count = self.db.query(Calculation).filter(
                Calculation.project_id == project_id
            ).count()

            report_id = f"GHG-RPT-{project_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

            return {
                "step": "Create GHG Report",
                "report_id": report_id,
                "report_title": f"GHG Inventory Report - {project.project_name}",
                "organization": project.organization_name,
                "reporting_year": project.reporting_year,
                "report_date": datetime.utcnow().isoformat(),
                "scope1_emissions": project.total_scope1 or 0.0,
                "scope2_emissions": project.total_scope2 or 0.0,
                "scope3_emissions": project.total_scope3 or 0.0,
                "total_emissions": project.total_emissions or 0.0,
                "calculation_count": calc_count,
                "verification_status": "VERIFIED" if project.status in ["APPROVED", "LOCKED"] else "PENDING",
                "protocols": ["GHG Protocol", "ISO 14064-1"],
                "status": "GENERATED"
            }
        except SQLAlchemyError as e:
            logger.error(f"Database error in create_ghg_report: {e}")
            raise DatabaseError(f"Failed to create report: {str(e)}")

    def get_reporting_compliance_status(self, project_id: int) -> Dict[str, Any]:
        """
        Get compliance status for reporting requirements.

        Args:
            project_id: Target project ID

        Returns:
            Dict with compliance status

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        project = self._get_project_or_raise(project_id)

        scope1 = project.total_scope1 or 0.0
        scope2 = project.total_scope2 or 0.0
        scope3 = project.total_scope3 or 0.0

        compliance_checks = {
            "scope1_reported": scope1 > 0,
            "scope2_reported": scope2 > 0,
            "scope3_reported": scope3 > 0,
            "verified": project.status in ["APPROVED", "LOCKED"],
            "locked": project.status == "LOCKED"
        }

        # GHG Protocol requires at least Scope 1 or Scope 2
        is_compliant = compliance_checks["scope1_reported"] or compliance_checks["scope2_reported"]

        return {
            "step": "Reporting Compliance",
            "project_id": project_id,
            "project_name": project.project_name,
            "compliance_checks": compliance_checks,
            "overall_compliant": is_compliant,
            "status": "COMPLIANT" if is_compliant else "NON_COMPLIANT"
        }

    # ==================================================================
    # HELPER METHODS
    # ==================================================================

    def _build_emission_record(self, project_data: ProjectData) -> Dict[str, Any]:
        """
        Build emission record from project data.

        Args:
            project_data: ProjectData instance

        Returns:
            Dict with emission record data
        """
        return {
            "project_data_id": project_data.id,
            "criteria_id": project_data.criteria_id,
            "activity_data": project_data.activity_data,
            "unit": project_data.unit,
            "notes": project_data.notes,
            "has_evidence": project_data.has_evidence or 0,
            "entered_at": project_data.entered_at.isoformat() if project_data.entered_at else None
        }

    def get_project_status(self, project_id: int) -> Dict[str, Any]:
        """
        Get comprehensive project status including workflow position.

        Args:
            project_id: Target project ID

        Returns:
            Dict with complete project status

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        project = self._get_project_or_raise(project_id)

        try:
            data_count = self.db.query(ProjectData).filter(
                ProjectData.project_id == project_id
            ).count()

            calc_count = self.db.query(Calculation).filter(
                Calculation.project_id == project_id
            ).count()

            review_count = self.db.query(Review).filter(
                Review.project_id == project_id
            ).count()

            # Determine workflow lane based on status
            status_to_lane = {
                "DRAFT": "DATA_COLLECTION",
                "SUBMITTED": "DATA_COLLECTION",
                "UNDER_CALCULATION": "DATA_TRANSFORMATION",
                "PENDING_REVIEW": "DATA_VERIFICATION",
                "APPROVED": "FINAL_REVIEW",
                "REJECTED": "DATA_COLLECTION",
                "LOCKED": "COMPLETED"
            }
            lane = status_to_lane.get(project.status, "UNKNOWN")

            available_transitions = STATE_TRANSITIONS.get(project.status, [])

            return {
                "project_id": project_id,
                "project_name": project.project_name,
                "organization": project.organization_name,
                "status": project.status,
                "workflow_lane": lane,
                "available_transitions": available_transitions,
                "data_records": data_count,
                "calculations": calc_count,
                "reviews": review_count,
                "totals": {
                    "scope1": project.total_scope1 or 0.0,
                    "scope2": project.total_scope2 or 0.0,
                    "scope3": project.total_scope3 or 0.0,
                    "total": project.total_emissions or 0.0
                },
                "timestamps": {
                    "created_at": project.created_at.isoformat() if project.created_at else None,
                    "submitted_at": project.submitted_at.isoformat() if project.submitted_at else None,
                    "calculated_at": project.calculated_at.isoformat() if project.calculated_at else None,
                    "reviewed_at": project.reviewed_at.isoformat() if project.reviewed_at else None,
                    "approved_at": project.approved_at.isoformat() if project.approved_at else None,
                    "locked_at": project.locked_at.isoformat() if project.locked_at else None
                }
            }
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_project_status: {e}")
            raise DatabaseError(f"Failed to get project status: {str(e)}")
