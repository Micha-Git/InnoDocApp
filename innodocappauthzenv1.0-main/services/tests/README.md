# Tests

Automated tests for InnoDocApp and its authorization flow.

## Structure

- `integration/`: Integration tests (OPA API, resource search, JWT validation, etc.)
- `results/`: Test reports

## Running Tests

### With Docker Compose (Recommended)

Tests are automatically run when the entire architecture is deployed:

```sh
docker compose up --build
```

The tests container will execute all integration tests and generate a report. Test results are written to `results/report.txt` inside the container. Mount the results directory to access the report on the host:

```yaml
volumes:
  - ./services/tests/results:/app/results
```

### Locally (Development)

To run tests locally without Docker:

1. **Install dependencies:**

   ```sh
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```

2. **Ensure services are running:**
   - Start the full architecture with `docker compose up` in the project root
   - Or configure `.env` to point to your local/remote service endpoints

3. **Run tests:**

   ```sh
   pytest src/integration/
   ```

4. **View results:**
   ```sh
   cat results/report.txt
   ```

**Note:** Local test execution requires the services (OPA, InnoDocApp, PostgreSQL, etc.) to be accessible at the URLs configured in your environment.
