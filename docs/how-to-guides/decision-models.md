---
title: Choose commit types with a decision model
parent: How-to guides
nav_order: 4
---

# Choose commit types with a decision model

Use a TypeSafe-compatible decision service to select the Conventional Commit type
after LiteLLM drafts the description and optional body.
If you leave the decision URL unset,
LiteLLM chooses the type as usual.

## Before you begin

- [Install the hook](how-to-install.md) and configure a LiteLLM model with `LITELLM_PROXY_MODEL` or `--model`.
- Choose either the [TypeSafe Jev API](https://docs.typesafe.ai/introduction/quickstart) or a running [Ollaya server](https://ollaya.dev/docs/quickstart).

## Use Jev

1. Create an API key in the [TypeSafe dashboard](https://console.typesafe.ai/keys).
2. Set the decision URL and your key in the environment where the Git hook runs:

   ```bash
   export TYPESAFE_BASE_URL=https://api.typesafe.ai
   export TYPESAFE_API_KEY="your-typesafe-key"
   ```

   Replace the example key with your own.
   Jev requires the key in an `Authorization: Bearer` header over HTTPS;
   the decision URL alone cannot authenticate a request.
   The default decision model is `jev-latest`.

## Use Ollaya

1. [Install Ollaya](https://ollaya.dev/docs/quickstart) and load the default `laya` model:

   ```bash
   ollaya run laya "A short text to load the model"
   ```

   This command starts the server and pulls the model if necessary.

2. Point the hook at the local server:

   ```bash
   unset TYPESAFE_API_KEY
   export TYPESAFE_BASE_URL=http://127.0.0.1:11435
   export NO_PROXY=localhost,127.0.0.1
   ```

   Local Ollaya does not require a key unless the server is configured to require one.
   Unset any Jev key in the hook's environment before connecting to a local server.
   The TypeSafe SDK sends a placeholder `local` key when `TYPESAFE_API_KEY` is unset.
   If the server requires a key, set `TYPESAFE_API_KEY` to that key in the hook's environment.
   You can use `TYPESAFE_MODEL` to choose a different installed model.

## Generate a message

Stage your changes and commit normally.
The hook asks LiteLLM to generate the description first,
then sends it to the configured decision service to choose the type.
You still review the completed message before the hook writes it.
If the decision service is unavailable or returns an unsupported type,
the hook stops without writing the message.

You can also set the URL for one invocation with `--decision-url`
and override the decision model with `--decision-model`.
See the [Configuration reference](../references/configuration.md) for all options.
