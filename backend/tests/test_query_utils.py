from backend.services import query


def test_build_context_formats_entries():
    chunks = [
        {
            "document": "Spec content",
            "metadata": {"source_file": "Spec.pdf", "page_number": 2},
        }
    ]
    context = query.build_context(chunks)
    assert "[Source: Spec.pdf, Page: 2]" in context


def test_build_citations_extracts_pages():
    answer = "Use M35 concrete [Ref: Page 5]"
    chunks = [
        {
            "document": "Use M35 concrete for foundations.",
            "metadata": {"source_file": "Spec.pdf", "page_number": 5},
        }
    ]
    citations = query.build_citations(answer, chunks)
    assert citations[0]["page_number"] == 5


