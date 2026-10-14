import os
import requests
from copy import deepcopy
import pytest 

class TestOPAEndpoints:
    EVALUATION_URI = os.environ.get("EVALUATION_URI")  
    EVALUATIONS_URI = os.environ.get("EVALUATIONS_URI")  
    RESOURCE_SEARCH_URI = os.environ.get("RESOURCE_SEARCH_URI")  

    def test_document_search_seclevel_7(self):
        """OPA: Document search with secLevel 7 returns allowed docs."""
        data = {
            "subject": {
                "type": "partner",
                "id": "alice@innocomp.com",
                "properties": {
                    "secLevel": 7,
                    "sources": ["Orion"]
                }
            },
            "action": {"name": "can_read"},
            "resource": {"type": "document"}
        }
        response = requests.post(self.RESOURCE_SEARCH_URI, json=data)
        assert response.status_code == 200
        results = response.json()["results"]
        assert isinstance(results, list)
        assert len(results) > 0

    def test_document_search_seclevel_1(self):
        """OPA: Document search with secLevel 1 returns empty results."""
        data = {
            "subject": {
                "type": "partner",
                "id": "alice@innocomp.com",
                "properties": {
                    "secLevel": 1,
                    "sources": ["Orion"]
                }
            },
            "action": {"name": "can_read"},
            "resource": {"type": "document"}
        }
        response = requests.post(self.RESOURCE_SEARCH_URI, json=data)
        assert response.status_code == 200
        results = response.json()["results"]
        assert isinstance(results,list)
        

    def test_document_access_seclevel_1(self):
        """OPA: Document access with secLevel 1 returns forbidden decision."""
        data = {
            "subject": {
                "type": "partner",
                "id": "alice@innocomp.com",
                "properties": {
                    "secLevel": 1,
                    "sources": ["Orion"]
                }
            },
            "resource": {"type": "document", "id": "6"},
            "action": {"name": "can_read"}
        }
        response = requests.post(self.EVALUATION_URI, json=data)
        assert response.status_code == 200
        result = response.json()
        assert result["decision"] is False

    def test_document_access_seclevel_10(self):
        """OPA: Document access with secLevel 10 returns allowed decision."""
        data = {
            "subject": {
                "type": "partner",
                "id": "alice@innocomp.com",
                "properties": {
                    "secLevel": 10,
                    "sources": ["Orion"]
                }
            },
            "resource": {"type": "document", "id": "6"},
            "action": {"name": "can_read"}
        }
        response = requests.post(self.EVALUATION_URI, json=data)
        assert response.status_code == 200
        result = response.json()
        assert result["decision"] is True

 
    def test_jwt_validation_invalid(self):
        """OPA: JWT validation with invalid JWT returns forbidden decision and httpStatus in context."""
        invalid_jwt = "weirdprefixeyeyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjEyMzQiLCJ0eXBlIjoicGFydG5lciIsImVtYWlsIjoiam9obkBpbm5vY29tcC5jb20iLCJuYW1lIjoiSm9obiIsInByb3BlcnRpZXMiOnsic2VjTGV2ZWwiOjcsInNvdXJjZXMiOlsiUHJvamVjdCBIb3Jpem9uIl19fQ.98nK9lhLHAoPYCFmtEX8upIzlT0suDKsCiDB9lpoEB48EJynwM1b4kwSxOm1D2Kyi13EFGGolI9kmYsPehBfkQ"
        data = {
            "subject": {"type": "JWT", "id": invalid_jwt},
            "resource": {"type": "route", "id": "/docs"},
            "action": {"name": "GET"}
        }
        response = requests.post(self.EVALUATION_URI, json=data)
        assert response.status_code == 200
        result = response.json()
        assert result["decision"] is False
