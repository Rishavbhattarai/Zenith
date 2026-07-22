from notetaker.support_agent import (
    DocChunk,
    MockAnswerGenerator,
    ask_support_agent,
    load_knowledge_base,
    retrieve,
)


def test_load_knowledge_base_finds_demo_runbooks():
    chunks = load_knowledge_base()

    doc_titles = {c.doc_title for c in chunks}
    assert "Power Supply Failures" in doc_titles
    assert "Escalation Policy" in doc_titles
    assert len(chunks) > 4  # multiple headings per doc


def test_retrieve_finds_topically_relevant_chunk():
    chunks = [
        DocChunk(doc_title="Power Supply Failures", heading="Symptoms", text="power draw PSU failing"),
        DocChunk(doc_title="Network Degradation", heading="Symptoms", text="latency packet loss signal"),
    ]

    results = retrieve("why would power draw be spiking on a node", chunks, top_k=1)

    assert results[0].doc_title == "Power Supply Failures"


def test_retrieve_returns_empty_for_no_overlap():
    chunks = [DocChunk(doc_title="Power Supply Failures", heading="Symptoms", text="power draw PSU")]

    results = retrieve("what is the weather today", chunks)

    assert results == []


def test_mock_answer_generator_uses_top_chunk():
    chunks = [DocChunk(doc_title="Power Supply Failures", heading="Symptoms", text="check power_draw trend")]

    answer = MockAnswerGenerator().generate("power issue", chunks)

    assert "Power Supply Failures" in answer
    assert "check power_draw trend" in answer


def test_mock_answer_generator_handles_no_matches():
    answer = MockAnswerGenerator().generate("anything", [])

    assert "No relevant documentation" in answer


def test_ask_support_agent_end_to_end_with_mock():
    result = ask_support_agent("What should I do about a failing power supply?", generator=MockAnswerGenerator())

    assert result.answer
    assert any("Power Supply" in s for s in result.sources)
