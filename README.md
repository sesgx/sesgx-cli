
![sesgx logo](sesgx_header.png)
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

To run llm models using Ollama please install it based on these instructions:

- [Ollama Download](https://ollama.com/download)

Once ollama is properly installed you can download a model using:

```sh
ollama pull {model_name}
```

> All models available [here](https://ollama.com/library).

More commands can be discovered using:
```sh
ollama -h
```

> Be aware that each model will require a minimum of hardware specs.

#### Using OpenAi models for llm strategy

To use any OpenAi models it is necessary to provide a key. **This is sensible information please use .env, do not expose private keys**.

Enter your key using "OPENAI_API_KEY" value. See [.env.example](.env.example).

> Be aware that OpenAi api is a paid service.

--- 
### Telegram report

The `sesg experiment start` and `sesg scopus search` commands has a optional parameter name `telegram_report (-tr)`. This option enable a execution report to be sent via telegram.

1. Follow these [instructions](https://gist.github.com/nafiesl/4ad622f344cd1dc3bb1ecbe468ff9f8a) to set a telegram bot.
   
2. Create a group and add the bot created.
   > Tip: make sure tour bot has the correct admin rights. Through @BotFather and set `Manage Topics` to be true. And also allow it to be added in groups.

3. Enable the topic feature of the group. 
   > Tip: send a message to your newly created group, go to group info, under reactions there will be a toggle switch for the `topics` option.

4. You can get the group chat id using this request directly in your browser:
   ```url
      https://api.telegram.org/bot<YourBOTToken>/getUpdates
   ```

5. Get its token and your chat id. Add these variable to your `.env` file.
   ```python
      TELEGRAM_TOKEN="" # bot token.
      TELEGRAM_CHAT_ID_EXPERIMENT="" # your chat id for the experiment chat.
      TELEGRAM_CHAT_ID_SCOPUS="" # your chat id for the scopus chat.
      PC_SPECS="" # your hardware specs.
   ```

:warning: **Note**: this works as a local bot. To only store your experiments information, such as time of execution or execution checkpoints. This is not a live server conversational bot.