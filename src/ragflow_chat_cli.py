"""Simple CLI chat application for a RAGFlow dataset using ragflow-sdk."""
from __future__ import annotations

import inspect
import os
import sys
from typing import Any, Callable, Iterable, Optional

DATASET_ENV_VAR = "RAGFLOW_DATASET"
DATASET_ID_ENV_VAR = "RAGFLOW_DATASET_ID"
DEFAULT_DATASET_NAME = "ragflow-doc"
QUIT_COMMANDS = {"quit", "exit", "q"}


class RagflowChatError(RuntimeError):
    """Raised when we cannot complete a chat request via ragflow-sdk."""


def _load_sdk_client() -> Any:
    try:
        import ragflow_sdk  # type: ignore
    except ImportError as exc:  # pragma: no cover - noisy failure path
        raise SystemExit(
            "ragflow-sdk is required. Install it with `pip install ragflow-sdk`."
        ) from exc

    client_cls: Optional[type[Any]] = getattr(ragflow_sdk, "RagflowClient", None)
    if client_cls is None:
        client_module = getattr(ragflow_sdk, "client", None)
        client_cls = getattr(client_module, "RagflowClient", None) if client_module else None

    if client_cls is None:
        raise SystemExit(
            "Unable to locate RagflowClient in ragflow_sdk. Check your ragflow-sdk version."
        )

    base_url = os.getenv("RAGFLOW_BASE_URL", "http://localhost:9380")
    api_key = os.getenv("RAGFLOW_API_KEY")
    if not api_key:
        raise SystemExit("Set the RAGFLOW_API_KEY environment variable before running the chat.")

    init_signature = inspect.signature(client_cls.__init__)
    kwargs: dict[str, Any] = {}

    if "base_url" in init_signature.parameters:
        kwargs["base_url"] = base_url
    elif "endpoint" in init_signature.parameters:
        kwargs["endpoint"] = base_url
    elif "host" in init_signature.parameters:
        kwargs["host"] = base_url

    if "api_key" in init_signature.parameters:
        kwargs["api_key"] = api_key
    elif "token" in init_signature.parameters:
        kwargs["token"] = api_key
    elif "auth_token" in init_signature.parameters:
        kwargs["auth_token"] = api_key

    # Fall back to positional construction if the signature is unexpected.
    if not kwargs:
        return client_cls(base_url, api_key)

    return client_cls(**kwargs)


def _dataset_identifier(dataset: Any) -> Optional[str]:
    if dataset is None:
        return None
    if isinstance(dataset, dict):
        return dataset.get("id") or dataset.get("dataset_id")
    for attr in ("id", "dataset_id", "uuid"):
        if hasattr(dataset, attr):
            value = str(getattr(dataset, attr))
            if value:
                return value
    return None


def _dataset_matches(dataset: Any, name: str) -> bool:
    if dataset is None:
        return False
    lowered = name.lower()
    if isinstance(dataset, dict):
        for key in ("name", "dataset_name", "slug", "title"):
            value = dataset.get(key)
            if isinstance(value, str) and value.lower() == lowered:
                return True
        return False
    for attr in ("name", "dataset_name", "slug", "title"):
        value = getattr(dataset, attr, None)
        if isinstance(value, str) and value.lower() == lowered:
            return True
    return False


def _resolve_dataset(client: Any, dataset_name: str) -> Any:
    dataset_id_override = os.getenv(DATASET_ID_ENV_VAR)
    if dataset_id_override:
        return {"id": dataset_id_override, "name": dataset_name}

    datasets_accessor = getattr(client, "datasets", None)
    if datasets_accessor:
        fetchers: Iterable[tuple[str, dict[str, Any]]] = (
            ("get_by_name", {"name": dataset_name}),
            ("get_by_slug", {"slug": dataset_name}),
            ("get", {"name": dataset_name}),
            ("retrieve", {"name": dataset_name}),
        )
        for method_name, kwargs in fetchers:
            method = getattr(datasets_accessor, method_name, None)
            if callable(method):
                try:
                    dataset = method(**kwargs)
                except TypeError:
                    continue
                if dataset:
                    return dataset

        list_method = getattr(datasets_accessor, "list", None)
        if callable(list_method):
            try:
                datasets = list_method()
            except TypeError:
                datasets = list_method({})
            if datasets:
                for dataset in datasets:
                    if _dataset_matches(dataset, dataset_name):
                        return dataset

    legacy_method = getattr(client, "get_dataset", None)
    if callable(legacy_method):
        try:
            dataset = legacy_method(dataset_name)
        except TypeError:
            dataset = legacy_method(name=dataset_name)
        if dataset:
            return dataset

    raise RagflowChatError(f"Unable to locate dataset '{dataset_name}' via ragflow-sdk.")


def _call_with_variants(func: Callable[..., Any], variants: Iterable[dict[str, Any]]) -> Any:
    for payload in variants:
        try:
            return func(**payload)
        except TypeError:
            continue
    raise RagflowChatError("ragflow-sdk chat endpoint signature not recognized.")


def _perform_query(client: Any, dataset_id: str, question: str) -> Any:
    # Try modern chat endpoint exposed via attribute.
    chat_section = getattr(client, "chat", None)
    if callable(chat_section):
        return _call_with_variants(
            chat_section,
            (
                {"dataset_id": dataset_id, "question": question},
                {"dataset_id": dataset_id, "query": question},
                {"datasetId": dataset_id, "query": question},
            ),
        )

    if chat_section is not None:
        for method_name in ("query", "ask", "create", "complete", "run"):
            method = getattr(chat_section, method_name, None)
            if callable(method):
                return _call_with_variants(
                    method,
                    (
                        {"dataset_id": dataset_id, "question": question},
                        {"dataset_id": dataset_id, "query": question},
                        {"datasetId": dataset_id, "query": question},
                        {"dataset": dataset_id, "question": question},
                    ),
                )

    for method_name in ("chat", "query", "ask", "answer", "complete"):
        method = getattr(client, method_name, None)
        if callable(method):
            return _call_with_variants(
                method,
                (
                    {"dataset_id": dataset_id, "question": question},
                    {"dataset_id": dataset_id, "query": question},
                    {"dataset": dataset_id, "question": question},
                    {"dataset": dataset_id, "query": question},
                    {"dataset_name": DEFAULT_DATASET_NAME, "question": question},
                ),
            )

    raise RagflowChatError("No usable chat method found on ragflow-sdk client.")


def _extract_answer(response: Any) -> str:
    if response is None:
        return "<no response>"
    if isinstance(response, str):
        return response
    if isinstance(response, dict):
        for key in ("answer", "content", "text", "message", "result"):
            value = response.get(key)
            if isinstance(value, str):
                return value
            if isinstance(value, dict):
                nested = value.get("text") or value.get("value")
                if isinstance(nested, str):
                    return nested
        # Some SDKs wrap data inside `data` or `choices`
        data = response.get("data")
        if isinstance(data, dict):
            return _extract_answer(data)
        choices = response.get("choices")
        if isinstance(choices, list) and choices:
            return _extract_answer(choices[0])
        return str(response)

    for attr in ("answer", "content", "text", "message", "result"):
        value = getattr(response, attr, None)
        if isinstance(value, str):
            return value
    if hasattr(response, "model_dump"):
        return _extract_answer(response.model_dump())
    return str(response)


def main() -> None:
    dataset_name = os.getenv(DATASET_ENV_VAR, DEFAULT_DATASET_NAME)
    client = _load_sdk_client()
    dataset = _resolve_dataset(client, dataset_name)
    dataset_id = _dataset_identifier(dataset)
    if not dataset_id:
        raise SystemExit(f"Could not determine dataset id for '{dataset_name}'.")

    print("Connected to RAGFlow dataset:", dataset_name)
    print("Type your question and press Enter. Type 'quit' to exit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()  # newline for clean exit
            break

        if not user_input:
            continue
        if user_input.lower() in QUIT_COMMANDS:
            break

        try:
            response = _perform_query(client, dataset_id, user_input)
        except RagflowChatError as exc:
            print(f"[ragflow-sdk] {exc}")
            continue
        except Exception as exc:  # pragma: no cover - surface unexpected SDK errors
            print(f"[ragflow-sdk] Error: {exc}")
            continue

        answer = _extract_answer(response)
        print(f"RAGFlow: {answer}\n")

    print("Goodbye!")


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    try:
        main()
    except SystemExit as exc:
        if exc.code:
            print(exc)
            sys.exit(exc.code)
        sys.exit(0)
