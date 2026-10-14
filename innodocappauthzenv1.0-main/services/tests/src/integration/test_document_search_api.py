import requests
import os
import json
import pytest

class TestDocumentSearchAPI:
    RESOURCE_SEARCH_ENDPOINT = f"{os.environ.get("INNODOCAPP_HOST")}/docs"
    JSON_HEADER = {"Content-Type": "application/json"}

    @pytest.mark.parametrize(
        argnames=["subject_type", "sources", "secLevel","expected_file_ids", "expected_status"],
        argvalues=[
            # Orion TEST CASES
            # Partners can only access documents from their sources below or equal to their secLevel
            ("partner", ["Orion"], 5, [6,7,101,103,105,107,109,119], 200),
            ("partner", ["Orion"], 1, [101,119], 200),
            ("partner", ["Orion"], 10, [6, 7, 101, 103, 105, 107, 109, 111, 113, 115, 117, 119], 200),
            # since we are accessing InnoDocApp directly, the endpoint is not protected by InnoDocApp-Proxy
            ("project manager", ["Orion"], 1, [], 200),
            ("project manager", ["Orion"], 10, [], 200),

            # Horizon TEST CASES
            ("partner", ["Horizon"], 5, [4,5,100,102,104,106, 108, 118, 120], 200),
            ("partner", ["Horizon"], 1, [100,118], 200),
            ("partner", ["Horizon"], 10, [4, 5, 100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120], 200),
            # Since we are accessing InnoDocApp directly, the endpoint is not protected by InnoDocApp-Proxy
            ("project manager", ["Horizon"], 1, [], 200),
            ("project manager", ["Horizon"], 10, [], 200),
        ],
        ids=[
            "partner_seclevel5_project_orion",
            "partner_seclevel1_project_orion",
            "partner_seclevel10_project_orion",
            "projectmanager_seclevel1_project_orion",
            "projectmanager_seclevel10_project_orion",
            "partner_seclevel5_project_horizon",
            "partner_seclevel1_project_horizon",
            "partner_seclevel10_project_horizon",
            "projectmanager_seclevel1_project_horizon",
            "projectmanager_seclevel10_project_horizon",
        ]
    )
    def test_validate_document_search(self, subject_type, sources, secLevel, expected_file_ids, expected_status):
        subjectInfo = {
            "type": subject_type,
            "id": "kyle@innocomp.com",
            "properties": {
                "secLevel": secLevel,
                "sources": sources
            }
        }

        self.JSON_HEADER.update({"Authorization": json.dumps(subjectInfo)})
        response = requests.get(self.RESOURCE_SEARCH_ENDPOINT, 
                                 headers=self.JSON_HEADER)

        assert response.status_code == expected_status
        if response.status_code != 200:
            return
        result = response.json()
        ids = [item['file_id'] for item in result]
        assert sorted(ids) == expected_file_ids
