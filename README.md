# Development

## Setup Environment

1. Create `.env` file under project root with `OPENAI_API_KEY=<YOUR_OPENAI_API_KEY>`
2. Install Dependencies

``` bash
pip install -r requirements.txt
```

## Run the App

``` bash
uvicorn src.api.main:app --reload --port 8000
```

## Run Tests

### Unit Tests

There are two folders under `tests`:

- `unit_tests` for unit tests
- `component_tests` for component tests (with openai call)

just run with `pytest tests/unit_tests/`
or `pytest tests/component_tests/`

### Integration Tests

You need to first start the app to run integration tests.

Then run `pytest tests/functional_tests/`

local development db (sqlite) is located at `data/dev.db`