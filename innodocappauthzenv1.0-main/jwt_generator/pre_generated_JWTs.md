# JWT Signature Keys and Resulting JWTs

This document provides a list of signed JWTs using the pre-generated PEM cryptographic keys. The JWT-encoded JSON objects are described in the subject.json file.

---

## 1. Valid JWT

**Signature key:**

- `sts_private_key.pem`

**Resulting JWT:**

```
eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjEyMzQiLCJ0eXBlIjoicGFydG5lciIsImVtYWlsIjoiam9obkBpbm5vY29tcC5jb20iLCJuYW1lIjoiSm9obiIsInByb3BlcnRpZXMiOnsic2VjTGV2ZWwiOjcsInNvdXJjZXMiOlsiUHJvamVjdCBIb3Jpem9uIl19fQ.98nK9lhLHAoPYCFmtEX8upIzlT0suDKsCiDB9lpoEB48EJynwM1b4kwSxOm1D2Kyi13EFGGolI9kmYsPehBfkQ
```

---

## 2. Invalid JWT (Prefixed / Corrupted)

**Signature key:**

- `sts_private_key.pem`

**Resulting JWT:**

```
weirdprefixeyeyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjEyMzQiLCJ0eXBlIjoicGFydG5lciIsImVtYWlsIjoiam9obkBpbm5vY29tcC5jb20iLCJuYW1lIjoiSm9obiIsInByb3BlcnRpZXMiOnsic2VjTGV2ZWwiOjcsInNvdXJjZXMiOlsiUHJvamVjdCBIb3Jpem9uIl19fQ.98nK9lhLHAoPYCFmtEX8upIzlT0suDKsCiDB9lpoEB48EJynwM1b4kwSxOm1D2Kyi13EFGGolI9kmYsPehBfkQ
```

---

## 3. JWT Signed With Unallowed Issuer and Subject Keys

**Signature key:**

- `unallowed_private_key.pem`

**Resulting JWT:**

```
eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjEyMzQiLCJ0eXBlIjoicGFydG5lciIsImVtYWlsIjoiam9obkBpbm5vY29tcC5jb20iLCJuYW1lIjoiSm9obiIsInByb3BlcnRpZXMiOnsic2VjTGV2ZWwiOjcsInNvdXJjZXMiOlsiUHJvamVjdCBIb3Jpem9uIl19fQ.ibsSkyeqpQ4pH8CCV3ugGjjw3u-CX-vuikxM1sSpg_ti6UFtwHF09NEzO-BxSfUKLeeGiloglvLyIvotAJZuFg
```

---
