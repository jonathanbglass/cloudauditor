# Testing

CloudAuditor's automated suite is pytest. AWS calls are mocked. The suite does not need credentials and does not make network calls.

## Run the tests

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt -r requirements-test.txt
pytest
```

`pytest` reads `pyproject.toml`. It collects `tests/test_*.py`, prints missing lines, and writes an HTML report to `reports/coverage/` (gitignored). The run fails if line coverage of `resource_discovery`, `lib`, `reporting`, and `database_init` drops below 90%.

Useful selections:

```bash
pytest tests/test_discovery_engine.py tests/test_discovery_methods.py
pytest -m unit
pytest -m integration          # moto-backed AWS boundary tests
pytest -m "not slow"
```

## What is covered

| Area | Tests |
| --- | --- |
| Discovery orchestration (method selection, fallback, dedupe, filters) | `tests/test_discovery_engine.py`, `tests/test_engine_coverage.py`, `tests/test_discovery_methods.py` |
| Resource Explorer, Config, and Cloud Control clients | `tests/test_*_client.py`, `tests/test_client_coverage.py` |
| Organizations, account registration, database client | `tests/test_organizations.py`, `tests/test_database.py` |
| Database init Lambda (`database_init/app.py`) | `tests/test_database_init_lambda.py` |
| Query Lambda, report Lambda, Excel output | `tests/test_database_query_lambda.py`, `tests/test_report_generator_lambda.py`, `tests/test_excel_generator.py` |
| Cross-account role verification | `tests/test_verification.py` |
| Real boto3 calls against moto (Organizations, StackSets, Secrets Manager, STS, EC2 regions) | `tests/test_moto_aws.py` |

`tests/conftest.py` sets dummy AWS credentials and disables the EC2 metadata service for every test. Integration tests add `moto.mock_aws()`, which serves those APIs in-process.

Postgres is mocked at `psycopg.connect`. No database is required.

## Continuous integration

`.github/workflows/test.yml` runs this suite on every pull request and on every push to `master` (the default branch). The job name is `pytest`. It installs `requirements.txt` and `requirements-test.txt`, then runs `pytest` with the same dummy credentials. The HTML and XML coverage reports are uploaded as the `coverage` artifact.

The deploy workflow (`.github/workflows/deploy.yml`) is separate. It lints and packages on `main` / `develop`; it does not run this suite and it does not run on `master`.

To make failing tests block a merge, mark the **pytest** check required under branch protection. That setting is not changed by the workflow.
