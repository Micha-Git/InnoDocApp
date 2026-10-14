from email import header
import json
import requests
import os
import pytest

class TestDocumentAccessAPI:
    DOCUMENT_ENDPOINT = f"{os.environ.get("INNODOCAPP_HOST")}/docs"
    JSON_HEADER = {"Content-Type": "application/json"}
    def build_doc_url(self, doc_path):
        return f"{self.DOCUMENT_ENDPOINT}/{doc_path}"

    @pytest.mark.parametrize(
        argnames=["subject_type", "sources", "secLevels", "path_to_access", "expected_status"],
        # Orion/overview.txt requires secLevel >= 3
        argvalues=[
            # ALLOWABLE PROJECT, CONDITIONAL ACCESS BASED ON SECLEVEL
            # Orion
            ("partner", ["Orion"], range(1, 3), "Orion/overview.txt", 403),
            ("partner", ["Orion"], range(3,11), "Orion/overview.txt", 200),
            ("project manager", ["Orion"], range(1,11), "Orion/overview.txt", 403),

            # Horizon
            # Horizon/0_Project_Description/project_overview.docx requires secLevel >= 2
            ("partner", ["Horizon"], range(1, 2), "Horizon/0_Project_Description/project_overview.docx", 403),
            ("partner", ["Horizon"], range(2,11), "Horizon/0_Project_Description/project_overview.docx", 200),
            ("project manager", ["Horizon"], range(1,11), "Horizon/0_Project_Description/project_overview.docx", 403),

            # UNALLOWABLE PROJECT, ACCESS DENIED TO ALL SECLEVELS
            # Orion trying to access Horizon documents
            ("project manager", ["Orion"], range(1,11), "Horizon/0_Project_Description/project_overview.docx", 403),
            ("partner", ["Orion"], range(1,11), "Horizon/0_Project_Description/project_overview.docx", 403),
            # Horizon trying to access Orion documents
            ("project manager", ["Horizon"], range(1,11), "Orion/overview.txt", 403),
            ("partner", ["Horizon"], range(1,11), "Orion/overview.txt", 403),
        ],
        ids=[
            "partner_orion_below_secLevel",
            "partner_orion_meets_secLevel",
            "projectmanager_orion_any_secLevel",
            "partner_horizon_below_secLevel",
            "partner_horizon_meets_secLevel",
            "projectmanager_horizon_any_secLevel",
            "projectmanager_orion_accessing_horizon",
            "partner_orion_accessing_horizon",
            "projectmanager_horizon_accessing_orion",
            "partner_horizon_accessing_orion",
        ]
    )
    def test_validate_authorization_status_code(self, subject_type, sources, secLevels, path_to_access, expected_status):
        subjectInfo = {
            "type": subject_type,
            "id": "john@innocomp.com",
            "properties": {
                "sources": sources,
                "secLevel": 1,
            }
        }

        for secLevel in secLevels:
            subjectInfo["properties"]["secLevel"] = secLevel
            self.JSON_HEADER.update({"Authorization": json.dumps(subjectInfo)})
            response = requests.get(
                self.build_doc_url(path_to_access),
                headers=self.JSON_HEADER,
                json=subjectInfo
            )
            assert response.status_code == expected_status
