# sesgx-cli

> CLI to perform experiments with the SeSG framework.

## Usage

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

To install the optional dependencies groups, use the following command:

```sh
pip install -e ".[group-name]"
```

For example, if you want to install `lda-topic-extraction` and `bert-word-enrichment`, run the following command:

```sh
pip install -e ".[lda-topic-extraction,bert-word-enrichment]"
```
