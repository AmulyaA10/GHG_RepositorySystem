"""
File Storage Management
"""
from pathlib import Path
from typing import Optional
import shutil
from datetime import datetime
from core.config import settings
import logging

logger = logging.getLogger(__name__)

class FileStorage:
    """File storage manager"""

    def __init__(self):
        self.base_dir = settings.UPLOAD_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_project_dir(self, project_id: int) -> Path:
        """
        Get directory for a specific project

        Args:
            project_id: Project ID

        Returns:
            Path: Project directory path
        """
        project_dir = self.base_dir / str(project_id)
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir

    def get_evidence_dir(self, project_id: int, criteria_id: int) -> Path:
        """
        Get directory for evidence files

        Args:
            project_id: Project ID
            criteria_id: Criteria ID

        Returns:
            Path: Evidence directory path
        """
        evidence_dir = self.get_project_dir(project_id) / f"criteria_{criteria_id}"
        evidence_dir.mkdir(parents=True, exist_ok=True)
        return evidence_dir

    def save_evidence_file(
        self,
        file,
        project_id: int,
        criteria_id: int
    ) -> str:
        """
        Save an evidence file

        Args:
            file: File object from Streamlit uploader
            project_id: Project ID
            criteria_id: Criteria ID

        Returns:
            str: Relative path to saved file
        """
        try:
            evidence_dir = self.get_evidence_dir(project_id, criteria_id)

            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            original_name = file.name
            file_extension = original_name.split('.')[-1]
            filename = f"{timestamp}_{original_name}"

            file_path = evidence_dir / filename

            # Save file
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())

            logger.info(f"Evidence file saved: {file_path}")

            # Return relative path
            return str(file_path.relative_to(self.base_dir))

        except Exception as e:
            logger.error(f"Error saving evidence file: {e}")
            raise

    def get_evidence_file_path(self, relative_path: str) -> Path:
        """
        Get absolute path for an evidence file

        Args:
            relative_path: Relative path from storage

        Returns:
            Path: Absolute file path
        """
        return self.base_dir / relative_path

    def delete_evidence_file(self, relative_path: str) -> bool:
        """
        Delete an evidence file

        Args:
            relative_path: Relative path from storage

        Returns:
            bool: True if deleted successfully
        """
        try:
            file_path = self.get_evidence_file_path(relative_path)
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Evidence file deleted: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting evidence file: {e}")
            return False

    def list_evidence_files(self, project_id: int, criteria_id: int) -> list:
        """
        List all evidence files for a criteria

        Args:
            project_id: Project ID
            criteria_id: Criteria ID

        Returns:
            list: List of file paths
        """
        evidence_dir = self.get_evidence_dir(project_id, criteria_id)
        files = []

        if evidence_dir.exists():
            for file_path in evidence_dir.iterdir():
                if file_path.is_file():
                    relative_path = str(file_path.relative_to(self.base_dir))
                    files.append({
                        'name': file_path.name,
                        'path': relative_path,
                        'size': file_path.stat().st_size,
                        'modified': datetime.fromtimestamp(file_path.stat().st_mtime)
                    })

        return files

# Global instance
storage = FileStorage()
