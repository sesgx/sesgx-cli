# package-name

> Description (same that is provided in the pyproject.toml, which is the same as the repository description).

## Usage

```python
# code example of how to use the package
```

## Development

Create a virtual environment:

```sh
python -m venv .venv
```

Activate the virtual environment:

```sh
source .venv/bin/activate  # if using linux
```

Install the project in editable mode:

```sh
pip install -e .
```

### Testing (ONLY IF PACKAGE HAS TESTS)

Install test dependencies:

```sh
pip install ".[dev-test]"
```

Run the test command from the provided script:

```sh
./scripts/test.sh
```

After running the tests, a coverage report will be available in `htmlcov/index.html`. You can run the following command to open the report using google chrome:

```
google-chrome htmlcov/index.html
```
