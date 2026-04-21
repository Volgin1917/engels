# Developer Onboarding Guide

Welcome to the **Entity Extraction System** project! This guide will help you set up your development environment, understand the codebase, and start contributing.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python**: Version 3.10 or higher
- **Docker & Docker Compose**: For running dependencies locally
- **Git**: For version control
- **Make** (optional): For running convenience commands

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/entity-extraction.git
cd entity-extraction
```

### 2. Set Up Environment Variables

Copy the example environment file and fill in the required values:

```bash
cp .env.example .env
```

Edit `.env` with your local settings (database credentials, API keys, etc.).

### 3. Start Dependencies with Docker

Run the full stack locally (Postgres, Redis, Strapi):

```bash
docker-compose up -d
```

Verify services are running:

```bash
docker-compose ps
```

### 4. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 5. Install Dependencies

Install core dependencies and development tools:

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 6. Run Database Migrations

Apply the latest schema changes:

```bash
alembic upgrade head
```

### 7. Start the Application

Run the backend server in development mode:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API should now be available at `http://localhost:8000`.

### 8. Run Tests

Ensure everything is working by running the test suite:

```bash
pytest tests/ -v
```

## Project Structure

```
entity-extraction/
├── app/                  # Main application code
│   ├── api/              # API routes and endpoints
│   ├── core/             # Core config and security
│   ├── db/               # Database models and session
│   ├── services/         # Business logic (LLM, extraction)
│   └── workers/          # Background task processors
├── tests/                # Test suite
├── scripts/              # Utility scripts
├── docs/                 # Documentation
├── docker-compose.yml    # Local dev orchestration
├── Dockerfile            # Production container image
└── requirements*.txt     # Python dependencies
```

## Common Development Tasks

### Running Background Workers

If your tasks require async processing (e.g., LLM extraction):

```bash
python -m app.workers.extraction_worker
```

### Accessing the Database

Connect to the local Postgres instance:

```bash
docker-compose exec postgres psql -U postgres -d entity_extraction
```

### Viewing Logs

Tail application logs:

```bash
docker-compose logs -f backend
```

### Resetting the Database

⚠️ **Warning**: This deletes all data.

```bash
docker-compose down -v
docker-compose up -d postgres
alembic upgrade head
```

## Code Style and Linting

We enforce strict code quality standards. Before committing:

1.  **Format code**:
    ```bash
    black app tests
    ```
2.  **Sort imports**:
    ```bash
    isort app tests
    ```
3.  **Lint**:
    ```bash
    flake8 app tests
    ```
4.  **Type check**:
    ```bash
    mypy app
    ```

You can run all checks at once:

```bash
make lint
```

## Commit Message Convention

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]
```

**Examples:**
- `feat(extraction): add support for PDF parsing`
- `fix(api): resolve 500 error on empty payload`
- `docs(readme): update installation steps`

Types: `feat`, `fix`, `chore`, `docs`, `style`, `refactor`, `test`.

## Branching Strategy

- **`main`**: Production-ready code.
- **`develop`**: Integration branch for features.
- **`feature/<name>`**: New features (branch off `develop`).
- **`bugfix/<name>`**: Bug fixes (branch off `develop`).
- **`hotfix/<name>`**: Urgent production fixes (branch off `main`).

## Debugging Tips

- **Breakpoints**: Use `import pdb; pdb.set_trace()` or IDE debugger.
- **API Docs**: Visit `http://localhost:8000/docs` for Swagger UI.
- **DB Inspection**: Use DBeaver or pgAdmin to connect to `localhost:5432`.

## Getting Help

- **Documentation**: Check `/docs` folder for detailed guides.
- **Issues**: Search existing issues on GitHub before creating new ones.
- **Chat**: Join the team Slack channel `#entity-extraction-dev`.

## Next Steps

1.  Pick a "Good First Issue" from the issue tracker.
2.  Create a feature branch.
3.  Make changes, write tests, and ensure CI passes.
4.  Submit a Pull Request!

Happy coding! 🚀
