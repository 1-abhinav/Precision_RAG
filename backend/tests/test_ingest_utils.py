from backend.services import ingest


def test_normalize_text_removes_extra_whitespace():
    text = "Concrete   grade\n\nshall be  M35."
    assert ingest._normalize_text(text) == "Concrete grade shall be M35."


def test_chunk_sha_is_deterministic():
    text = "Sample chunk"
    assert ingest._chunk_sha(text) == ingest._chunk_sha(text)


