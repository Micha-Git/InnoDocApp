import pytest
import requests
import os


class TestVPJWTValidation:

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test configuration."""
        self.proxy_url = os.getenv("INNODOCAPP_PROXY_HOST")
        if not self.proxy_url:
            raise RuntimeError("INNODOCAPP_PROXY_HOST must be set for proxy JWT tests")
        self.valid_jwt = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjEyMzQiLCJ0eXBlIjoicGFydG5lciIsImVtYWlsIjoiam9obkBpbm5vY29tcC5jb20iLCJuYW1lIjoiSm9obiIsInByb3BlcnRpZXMiOnsic2VjTGV2ZWwiOjcsInNvdXJjZXMiOlsiUHJvamVjdCBIb3Jpem9uIl19fQ.98nK9lhLHAoPYCFmtEX8upIzlT0suDKsCiDB9lpoEB48EJynwM1b4kwSxOm1D2Kyi13EFGGolI9kmYsPehBfkQ"
        self.invalid_prefix_jwt = "weirdprefixeyeyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjEyMzQiLCJ0eXBlIjoicGFydG5lciIsImVtYWlsIjoiam9obkBpbm5vY29tcC5jb20iLCJuYW1lIjoiSm9obiIsInByb3BlcnRpZXMiOnsic2VjTGV2ZWwiOjcsInNvdXJjZXMiOlsiUHJvamVjdCBIb3Jpem9uIl19fQ.98nK9lhLHAoPYCFmtEX8upIzlT0suDKsCiDB9lpoEB48EJynwM1b4kwSxOm1D2Kyi13EFGGolI9kmYsPehBfkQ"
        self.unallowed_keys_jwt = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjEyMzQiLCJ0eXBlIjoicGFydG5lciIsImVtYWlsIjoiam9obkBpbm5vY29tcC5jb20iLCJuYW1lIjoiSm9obiIsInByb3BlcnRpZXMiOnsic2VjTGV2ZWwiOjcsInNvdXJjZXMiOlsiUHJvamVjdCBIb3Jpem9uIl19fQ.ibsSkyeqpQ4pH8CCV3ugGjjw3u-CX-vuikxM1sSpg_ti6UFtwHF09NEzO-BxSfUKLeeGiloglvLyIvotAJZuFg"

    def make_proxy_request(self, jwt_token: str) -> requests.Response:
        """Helper method to call InnoDocApp-Proxy with a Bearer JWT."""
        headers = {"Authorization": f"Bearer {jwt_token}"}
        return requests.get(f"{self.proxy_url}/docs", headers=headers)

    def test_verify_jwt_valid(self):
        """Test that a valid JWT is accepted by the proxy."""
        response = self.make_proxy_request(self.valid_jwt)
        assert response.status_code in [200, 403]

    def test_verify_jwt_invalid_jwt(self):
        """Test that a JWT with invalid prefix is rejected."""
        response = self.make_proxy_request(self.invalid_prefix_jwt)
        assert response.status_code == 401

    def test_verify_jwt_signed_unallowed_keys(self):
        """Test that a JWT signed with unallowed keys is rejected."""
        response = self.make_proxy_request(self.unallowed_keys_jwt)
        assert response.status_code == 401

    