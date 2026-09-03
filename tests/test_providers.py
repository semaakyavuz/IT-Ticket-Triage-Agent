import pytest

from app import config, providers


def test_collection_name_is_chroma_safe_and_provider_specific(monkeypatch):
    monkeypatch.setattr(config, "EMBEDDING_PROVIDER", "fastembed")
    monkeypatch.setattr(
        config, "FASTEMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

    name = providers.collection_name()

    assert name == "tickets_fastembed_paraphrase-multilingual-MiniLM-L12-v2"
    assert 3 <= len(name) <= 63


def test_collection_name_changes_with_embedding_model(monkeypatch):
    monkeypatch.setattr(config, "EMBEDDING_PROVIDER", "ollama")
    monkeypatch.setattr(config, "OLLAMA_EMBED_MODEL", "nomic-embed-text")
    ollama_name = providers.collection_name()

    monkeypatch.setattr(config, "EMBEDDING_PROVIDER", "fastembed")
    fastembed_name = providers.collection_name()

    assert ollama_name != fastembed_name


def test_describe_providers_has_no_secrets(monkeypatch):
    monkeypatch.setattr(config, "LLM_PROVIDER", "groq")
    monkeypatch.setattr(config, "GROQ_MODEL", "llama-3.3-70b-versatile")
    monkeypatch.setattr(config, "GROQ_API_KEY", "gsk_super_secret")

    info = providers.describe_providers()

    assert info["llm_provider"] == "groq"
    assert info["llm_model"] == "llama-3.3-70b-versatile"
    assert "gsk_super_secret" not in str(info)


def test_get_chat_model_requires_groq_api_key(monkeypatch):
    monkeypatch.setattr(config, "LLM_PROVIDER", "groq")
    monkeypatch.setattr(config, "GROQ_API_KEY", "")

    with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
        providers.get_chat_model()


def test_unknown_provider_raises(monkeypatch):
    monkeypatch.setattr(config, "LLM_PROVIDER", "bilinmeyen")
    with pytest.raises(ValueError, match="LLM_PROVIDER"):
        providers.get_chat_model()

    monkeypatch.setattr(config, "EMBEDDING_PROVIDER", "bilinmeyen")
    with pytest.raises(ValueError, match="EMBEDDING_PROVIDER"):
        providers.get_embeddings()
