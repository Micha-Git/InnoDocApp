import os
import requests
import json
import pytest


class TestSubjectFormat:
    RESOURCE_SEARCH_ENDPOINT = f"{os.environ.get("INNODOCAPP_HOST")}/docs"
    DOCUMENT_ENDPOINT = f"{os.environ.get("INNODOCAPP_HOST")}/docs"
    JSON_HEADER = {"Content-Type": "application/json"}
    def build_doc_url(self, doc_path):
        return f"{self.DOCUMENT_ENDPOINT}/{doc_path}"

    @pytest.mark.parametrize(
        argnames=["sources", "expected_statuses"],
        argvalues=[
            # valid sources
            (["Horizon"], [200, 403]),
            (["Orion"], [200, 403]),
            (["Orion", "Horizon"], [200, 403]),
            (["Project Valid"], [200,403]),
            (["Orion", "Project Valid"], [200,403]),
            # invalid sources
            ("invalid source", [401]),
            ([12], [401]),
            ({}, [401]),
            (12, [401]),
            (None, [401])
        ],
        ids=[
            "valid_single_source_horizon",
            "valid_single_source_orion",
            "valid_both_sources",
            "valid_project",
            "valid_mixed_sources",
            "numeric_invalid",
            "string_invalid",
            "dict_invalid",
            "numeric_invalid_2",
            "none_invalid",
        ]
    )
    def test_validate_sources(self, sources, expected_statuses):
        subjectInfo = {
            "type": "partner",
            "id": "john@innocomp.com",
            "properties": {
                "sources": sources,
                "secLevel": 7,
            }
        }

        self.JSON_HEADER.update({"Authorization": json.dumps(subjectInfo)})
        response = requests.get(self.RESOURCE_SEARCH_ENDPOINT, 
                                 headers=self.JSON_HEADER)

        assert response.status_code in expected_statuses
        response = requests.get(self.build_doc_url("Horizon/0_Project_Description/project_overview.docx"), 
                                 headers=self.JSON_HEADER)

        assert response.status_code in expected_statuses


    @pytest.mark.parametrize(
        argnames=["id", "expected_statuses"],
        argvalues=[
            # valid subject types
            ("john@innocomp.com", [200, 403]),
            ("string id", [200,403]),
            ("12", [200,403]),
            # invalid subject types
            (12, [401]),
            (None, [401])
        ],
        ids=[
            "valid_email",
            "invalid_id",
            "emailish_but_not_email",
            "numeric_invalid",
            "none_invalid",
        ]
    )
    def test_validate_id(self, id, expected_statuses):
        subjectInfo = {
            "type": "partner",
            "id": id,
            "properties": {
                "secLevel": 7,
                "sources": ["Horizon", "Orion"]
            }
        }

        self.JSON_HEADER.update({"Authorization": json.dumps(subjectInfo)})
        response = requests.get(self.RESOURCE_SEARCH_ENDPOINT, 
                                 headers=self.JSON_HEADER)

        assert response.status_code in expected_statuses
        response = requests.get(self.build_doc_url("Horizon/0_Project_Description/project_overview.docx"), 
                                 headers=self.JSON_HEADER)

        assert response.status_code in expected_statuses

    @pytest.mark.parametrize(
        argnames=["subject_type", "expected_statuses"],
        argvalues=[
            # valid subject types
            ("partner", [200]),
            ("project manager", [200,403]),
            # invalid subject types
            ("invalid subject", [401]),
            (12, [401]),
            (None, [401])
        ],
        ids=[
            "partner_valid",
            "project_manager_valid",
            "invalid_subject",
            "numeric_invalid",
            "none_invalid",
        ]
    )
    def test_validate_subject_type(self, subject_type, expected_statuses):
        subjectInfo = {
            "type": subject_type,
            "id": "john@innocomp.com",
            "properties": {
                "secLevel": 7,
                "sources": ["Horizon", "Orion"]
            }
        }

        self.JSON_HEADER.update({"Authorization": json.dumps(subjectInfo)})
        response = requests.get(self.RESOURCE_SEARCH_ENDPOINT, 
                                 headers=self.JSON_HEADER)

        assert response.status_code in expected_statuses
    
        response = requests.get(self.build_doc_url("Horizon/0_Project_Description/project_overview.docx"), 
                                 headers=self.JSON_HEADER)

        assert response.status_code in expected_statuses



    
    @pytest.mark.parametrize(
        argnames=["secLevel", "expected_statuses"],
        argvalues=[
            (-1, [401]),
            (11, [401]),
            (10, [200, 403]),
            (0, [401, 403]),
        ],
        ids=[
            "below_lower_bound",
            "above_upper_bound",
            "valid_upper_bound",
            "valid_lower_bound",
        ]
    )
    def test_secLevel_validation(self, secLevel, expected_statuses):
        subjectInfo = {
            "type": "partner",
            "id": "john@innocomp.com",
            "properties": {
                "secLevel": secLevel,
                "sources": ["Horizon", "Orion"]
            }
        }
        self.JSON_HEADER.update({"Authorization": json.dumps(subjectInfo)})
        response = requests.get(self.RESOURCE_SEARCH_ENDPOINT, headers=self.JSON_HEADER)
        assert response.status_code in expected_statuses
    
        response = requests.get(self.build_doc_url("Horizon/0_Project_Description/project_overview.docx"), headers=self.JSON_HEADER)
        assert response.status_code in expected_statuses



    def test_resource_search_invalid_attribute(self):
        subjectInfo = {
            "someExtraAttribute": "extraValue",
            "type": "partner",
            "id": "john@innocomp.com",
            "properties": {
                "secLevel": 1,
                "sources": ["Horizon", "Orion"]
            }
        }

        self.JSON_HEADER.update({"Authorization": json.dumps(subjectInfo)})
        response = requests.get(self.RESOURCE_SEARCH_ENDPOINT, 
                                 headers=self.JSON_HEADER)

        assert response.status_code in [200,403]

        response = requests.get(self.build_doc_url("Horizon/0_Project_Description/project_overview.docx"),
                                    headers=self.JSON_HEADER)
        assert response.status_code in [200,403]



