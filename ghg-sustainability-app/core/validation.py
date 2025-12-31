"""
Data Validation Rules
"""
from typing import Dict, List, Any, Optional
import re
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom validation error"""
    pass

class DataValidator:
    """Data validation utilities"""

    @staticmethod
    def validate_positive_number(value: Any, field_name: str) -> float:
        """
        Validate that a value is a positive number

        Args:
            value: Value to validate
            field_name: Name of field for error messages

        Returns:
            float: Validated value

        Raises:
            ValidationError: If validation fails
        """
        try:
            num_value = float(value)
            if num_value < 0:
                raise ValidationError(f"{field_name} must be a positive number")
            return num_value
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} must be a valid number")

    @staticmethod
    def validate_required(value: Any, field_name: str) -> Any:
        """
        Validate that a required field has a value

        Args:
            value: Value to validate
            field_name: Name of field for error messages

        Returns:
            Any: Validated value

        Raises:
            ValidationError: If validation fails
        """
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValidationError(f"{field_name} is required")
        return value

    @staticmethod
    def validate_email(email: str) -> str:
        """
        Validate email format

        Args:
            email: Email address to validate

        Returns:
            str: Validated email

        Raises:
            ValidationError: If validation fails
        """
        email = email.strip().lower()
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not re.match(pattern, email):
            raise ValidationError("Invalid email format")

        return email

    @staticmethod
    def validate_year(year: int) -> int:
        """
        Validate reporting year

        Args:
            year: Year to validate

        Returns:
            int: Validated year

        Raises:
            ValidationError: If validation fails
        """
        if year < 1990 or year > 2100:
            raise ValidationError("Year must be between 1990 and 2100")
        return year

    @staticmethod
    def validate_scope(scope: str) -> str:
        """
        Validate GHG Protocol scope

        Args:
            scope: Scope to validate

        Returns:
            str: Validated scope

        Raises:
            ValidationError: If validation fails
        """
        valid_scopes = ["Scope 1", "Scope 2", "Scope 3", "Scope-1", "Scope-2", "Scope-3"]

        if scope not in valid_scopes:
            raise ValidationError(f"Invalid scope. Must be one of: {', '.join(valid_scopes)}")

        return scope

    @staticmethod
    def validate_project_data(data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Validate complete project data entry

        Args:
            data: Dictionary of project data

        Returns:
            Dict containing validation errors (empty if valid)
        """
        errors = {}

        # Validate organization name
        try:
            DataValidator.validate_required(data.get('organization_name'), 'Organization Name')
        except ValidationError as e:
            errors['organization_name'] = str(e)

        # Validate reporting year
        try:
            year = data.get('reporting_year')
            if year:
                DataValidator.validate_year(int(year))
        except ValidationError as e:
            errors['reporting_year'] = str(e)

        # Validate activity data values
        for i in range(1, 24):  # 23 criteria
            field_name = f'activity_data_{i}'
            value = data.get(field_name)

            if value is not None and value != '':
                try:
                    DataValidator.validate_positive_number(value, f'Criterion {i} Activity Data')
                except ValidationError as e:
                    errors[field_name] = str(e)

        return errors

    @staticmethod
    def validate_calculation_inputs(
        activity_data: Any,
        emission_factor: Any
    ) -> tuple:
        """
        Validate calculation inputs

        Args:
            activity_data: Activity data value
            emission_factor: Emission factor value

        Returns:
            tuple: (validated_activity_data, validated_emission_factor)

        Raises:
            ValidationError: If validation fails
        """
        ad = DataValidator.validate_positive_number(activity_data, "Activity Data")
        ef = DataValidator.validate_positive_number(emission_factor, "Emission Factor")

        return (ad, ef)

    @staticmethod
    def validate_file_upload(file, max_size_mb: int = 10) -> bool:
        """
        Validate uploaded file

        Args:
            file: Uploaded file object
            max_size_mb: Maximum file size in MB

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If validation fails
        """
        if file is None:
            raise ValidationError("No file uploaded")

        # Check file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to start

        max_size_bytes = max_size_mb * 1024 * 1024

        if file_size > max_size_bytes:
            raise ValidationError(f"File size exceeds {max_size_mb}MB limit")

        # Check file extension
        allowed_extensions = {'.pdf', '.xlsx', '.xls', '.csv', '.jpg', '.jpeg', '.png', '.doc', '.docx'}
        file_ext = '.' + file.name.split('.')[-1].lower()

        if file_ext not in allowed_extensions:
            raise ValidationError(
                f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
            )

        return True
