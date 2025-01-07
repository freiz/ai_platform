# Development

## Setup Environment

1. Create `.env` file under project root with 
   * `OPENAI_API_KEY=<YOUR_OPENAI_API_KEY>`
   * `TRUCKQUOTE_API_KEY=<YOUR_TRUCKQUOTE_AIP_KEY>`
2. Install Dependencies

``` bash
pip install -r requirements.txt
```

## Run the App

``` bash
dotenv run uvicorn src.api.main:app --port 8000
```
**Remarks**:
* prefix `dotenv run` will set environment values defined inside `.env` to the following command.
* --autoreload is not recommended, I met multiple bugs.

## Run Tests

### Unit Tests

There are two folders under `tests`:

- `unit_tests` for unit tests
- `component_tests` for component tests (with openai call)

just run with `PYTHONPATH=$PYTHONPATH:. pytest tests/unit_tests/`
or `PYTHONPATH=$PYTHONPATH:. pytest tests/component_tests/`

### Integration Tests

You need to first start the app to run integration tests.

Then run `PYTHONPATH=$PYTHONPATH:. pytest tests/functional_tests/`

local development db (sqlite) is located at `data/dev.db`
