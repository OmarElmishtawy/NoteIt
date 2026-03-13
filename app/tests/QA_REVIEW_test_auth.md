# QA Review: test_auth.py

## Executive Summary
The auth test module covers main happy paths and some error cases but has critical bugs (raw password storage), missing tests (logout, authenticated redirect), and structural gaps. Below is a prioritized fix plan and recommendations.

---

## 🔴 Critical Issues

### 1. Raw Password Stored as Hash (Lines 56, 66)
```python
password_hash=user['password']  # WRONG: stores "anypassword" as plain text
```
**Problem:** User model expects a bcrypt/scrypt hash. Storing plain text breaks `check_password_hash()` and creates invalid user records.
**Fix:** Use `generate_password_hash(user['password'])`.

### 2. Debug Print Left In (Line 37)
```python
print(response.data)  # Remove before commit
```

### 3. No Test for Logout
The `/logout` route exists but has zero test coverage.

### 4. No Test for Authenticated Redirect
The `auth_bp.before_request` redirects logged-in users away from `/login` and `/register` to dashboard. This behavior is untested.

### 5. Fragile Assertions
Using `endswith('/dashboard')` may fail depending on how Flask returns redirect URLs (with/without host). Prefer `'/dashboard' in response.location`.

---

## 🟡 Moderate Issues

### 6. Duplicated User Creation Logic
User creation appears in multiple tests (lines 29–32, 56, 66). Extract to a reusable fixture (`registered_user`).

### 7. Missing Login-By-Email Test
The route accepts username OR email as identifier. Only username login is tested.

### 8. Missing Empty/Missing Field Tests
No tests for empty `username`, `password`, or `email`—common validation gaps.

### 9. Register Success Doesn't Verify Side Effects
`test_register_with_valid_credentials` only checks redirect. It should assert the User (and Personal folder) were created in the DB.

### 10. Ambiguous Invalid-Credentials Test
`test_login_with_invalid_credentials` doesn't create a user—so it tests "user not found" not "wrong password." Either create a user first or rename the test to reflect what it actually tests.

---

## 🟢 Minor Issues

### 11. No conftest.py
Shared fixtures (`app`, `client`) should live in `conftest.py` for reuse across test modules.

### 12. No Docstrings
Tests lack docstrings describing expected behavior.

### 13. Magic Strings
URLs, flash messages, and field names are hardcoded. Consider constants or fixtures.

### 14. Inconsistent Test Data Structure
Some tests build dicts inline, others reuse. Standardize a schema for form data.

---

## Improvement Plan

### Phase 1 — Critical Fixes (Do First)
- [x] Fix raw password storage in `test_register_with_existing_email` and `test_register_with_existing_username`
- [x] Remove `print(response.data)` from production code

### Phase 2 — Structural
- [x] Create `conftest.py` with `app`, `client`, and `registered_user` fixtures
- [x] Add `test_logout`
- [x] Add `test_authenticated_user_redirected_from_login`
- [x] Add `test_authenticated_user_redirected_from_register`

### Phase 3 — Coverage Gaps
- [x] Add `test_login_with_email_as_identifier`
- [x] Add `test_login_with_empty_credentials`
- [x] Add `test_register_with_empty_fields`
- [x] Add `test_register_creates_user_and_personal_folder` (verify DB state)

### Phase 4 — Polish
- [x] Add docstrings to each test
- [x] Extract constants (URLs, messages, form keys)
- [ ] Use `@pytest.mark.parametrize` for similar cases (e.g. invalid email variants) — optional
- [x] Add `pytest.ini` with `pythonpath` for consistent runs
