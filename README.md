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
---
### Run instructions

#### Using Ollama for llm strategy

To run llm models using Ollama please install it base on these instructions:

- [Ollama Download](https://ollama.com/download)

Once ollama is properly installed you can download a model using:

```sh
ollama pull {model_name}
```

> All models available [here](https://ollama.com/library).

More commands acn be discovered using:
```sh
ollama -h
```

> Be aware that each model will require a minimum of hardware specs.

#### Using OpenAi models for llm strategy

To use any OpenAi models it is necessary to provide a key. **This is sensible information please use .env, do not public private keys**.

Enter your key using "OPENAI_API_KEY" value. See [.env.example](.env.example).

> Be aware that OpenAi api is a paid service.
