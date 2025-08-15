### Test suite fixes and improvements (testfixes-1)

Goal: tighten tests to accurately validate intended behavior, remove false positives, improve determinism, and make DB usage safer.

### Quick wins (do these first)
- [ ] Fix missing factory reference
  - File: `python-backend/tests/factories.py`
    - Either define `PhotoRevealFactory` or replace it with the existing `UserPhotoFactory` in both `setup_factories` and any returns.
  - File: `python-backend/tests/conftest.py`
    - In the `factories` fixture, change `'photo_reveal': PhotoRevealFactory` to `'photo_reveal': UserPhotoFactory`.

- [ ] Seed randomness to avoid flakes
  - File: `python-backend/tests/conftest.py`
    - Near the top:
```python
import random
from faker import Faker
random.seed(1)
Faker.seed(1)
```

- [ ] Gate destructive test DB operations
  - File: `python-backend/tests/conftest.py`
    - Make `TEST_DATABASE_URL` read from env with a safe default and guard drop/create:
```python
import os
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///file::memory:?cache=shared")

is_sqlite = TEST_DATABASE_URL.startswith("sqlite")
@pytest.fixture(scope="session")
def test_db():
    if not is_sqlite:
        # Only allow drop/create if explicitly enabled
        if os.getenv("ALLOW_DB_DROP") == "1":
            if database_exists(TEST_DATABASE_URL):
                drop_database(TEST_DATABASE_URL)
            create_database(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    if not is_sqlite and os.getenv("ALLOW_DB_DROP") == "1":
        drop_database(TEST_DATABASE_URL)
```

### Tighten assertions (remove permissive status ranges)
- [ ] `python-backend/tests/test_api_integration.py`
  - Replace allowed sets like `[200, 404]` with the expected result for implemented endpoints.
  - Validate response bodies and critical fields, not only status codes. Example:
```python
res = client.post("/api/v1/matches", headers=headers, json=match_data)
assert res.status_code == status.HTTP_201_CREATED
body = res.json()
assert body["target_user_id"] == target_user.id
```
- [ ] `python-backend/tests/test_core_components.py`
  - Use `pytest.raises` for invalid token cases instead of checking “in [401, 422]” after try/except.
- [ ] `python-backend/tests/test_auth_core.py`
  - Remove try/except blocks that only set booleans; assert explicit outcomes or use `pytest.raises`.

### Replace loops+try/except with parametrization
- [ ] `python-backend/tests/test_core_components.py` and `test_auth_core.py`
  - Use `@pytest.mark.parametrize` for malformed tokens, weak passwords, etc. Example:
```python
@pytest.mark.parametrize("token", ["not.a.token", "too.many.parts.here.invalid", "", None])
def test_decode_invalid_token_param(token):
    assert decode_access_token(token) is None
```

### Scope performance and load tests
- [ ] Ensure performance tests are marked `@pytest.mark.performance` (already marked in many places).
- [ ] Exclude by default in CI: run with `-m "not performance"` for regular pipelines; keep a separate job to run them.

### Improve coverage quality (not just %)
- [ ] After tightening assertions, raise `--cov-fail-under` in `python-backend/pytest.ini` from 75 to 85.
- [ ] Add behavioral assertions (DB side effects, field values) where applicable to increase meaningful coverage.

### Safer and faster database usage
- [ ] Prefer SQLite in-memory for unit tests; reserve Postgres for integration/e2e.
- [ ] Consider separate fixtures: lightweight `db_session` for unit (SQLite), and `pg_db_session` for integration (Postgres), selected via markers.

### WebSocket tests stability
- [ ] Ensure auth tokens used in `websocket_connect` are valid for your WS auth logic; otherwise, mark such tests `@pytest.mark.integration` and gate them behind integration runs.
- [ ] Where possible, mock `ConnectionManager` and assert interactions (already done in parts).

### Concrete file-by-file to-dos
- [ ] `python-backend/tests/factories.py`
  - Replace `PhotoRevealFactory` references with `UserPhotoFactory`, or add:
```python
PhotoRevealFactory = UserPhotoFactory
```
  - Keep `setup_factories` consistent.

- [ ] `python-backend/tests/conftest.py`
  - Fix factories dict to use `UserPhotoFactory`.
  - Seed `random`/`Faker`.
  - DB URL/env + drop/create guard as above.

- [ ] `python-backend/tests/test_api_integration.py`
  - Authentication flow: assert exact codes and body shapes; don’t accept 404 for implemented endpoints.
  - Matches/message flows: assert creation codes and payload structure; remove permissive lists.

- [ ] `python-backend/tests/test_core_components.py`
  - Replace broad `in [...]` status checks with `pytest.raises` and exact expectations for invalid tokens and inactive users.

- [ ] `python-backend/tests/test_auth_core.py`
  - Remove try/except “graceful” patterns; assert correct return values and errors.
  - Parametrize malformed tokens.

- [ ] `python-backend/python-backend/pytest.ini`
  - Raise `cov-fail-under` to 85 after fixes.

### Suggested CI adjustments
- [ ] Default job: `pytest -m "not performance" --maxfail=1 -q` (still keeps coverage).
- [ ] Performance job: `pytest -m performance -q` (non-blocking, optional).

### Verification steps
- [ ] Run full suite locally: `pytest -q` (or excluding performance as above).
- [ ] Inspect coverage report (`htmlcov/index.html`) for untested lines in critical modules and add targeted tests.
- [ ] Ensure no test touches a non-test database by default; validate via `TEST_DATABASE_URL` echo in logs if needed.

### Notes
- Several current tests explicitly allow unimplemented behavior (e.g., accepting 404 for key endpoints). Tightening these will surface failures; fix the tests first, then align implementation or mark tests with `xfail`/`skip` temporarily where behavior is genuinely pending.


