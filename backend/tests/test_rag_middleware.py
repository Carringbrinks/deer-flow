"""Tests for the RAG middleware and its streaming search-completion client."""

from __future__ import annotations

import asyncio
import json

import httpx
from langchain.agents.middleware.types import ModelRequest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from deerflow.agents.middlewares.rag_middleware import (
    _AUTHORITY_CONTRACT,
    _RAG_CONTEXT_DATA_KEY,
    RagClient,
    RagMiddleware,
    RagResult,
)
from deerflow.config.rag_config import RagConfig

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_request(messages: list, *, state: dict | None = None) -> ModelRequest:
    return ModelRequest(
        model=object(),
        messages=list(messages),
        state=state if state is not None else {"messages": list(messages)},
    )


class _FakeClient:
    def __init__(self, result: RagResult | None = None, *, fail: bool = False):
        self.result = result
        self.fail = fail
        self.calls = 0
        self.queries: list[str] = []

    def retrieve(self, question: str) -> RagResult | None:
        self.calls += 1
        self.queries.append(question)
        if self.fail:
            raise RuntimeError("boom")
        return self.result

    async def aretrieve(self, question: str) -> RagResult | None:
        self.calls += 1
        self.queries.append(question)
        if self.fail:
            raise RuntimeError("boom")
        return self.result


def _result() -> RagResult:
    return RagResult(
        answer="",
        reference={
            "total": 1,
            "chunks": [
                {
                    "id": "c1",
                    "content": "Fact A content.",
                    "document_name": "doc.pdf",
                    "similarity": 0.9,
                    "positions": [[1, 2, 3]],
                    "image_id": "img-1",
                }
            ],
            "doc_aggs": [{"doc_name": "doc.pdf", "doc_id": "d1", "count": 1}],
        },
    )


def _event(data: object) -> dict:
    return {"code": 0, "message": "", "data": data}


def _sse_body(*events: dict) -> bytes:
    parts: list[str] = []
    for event in events:
        parts.append("data: " + json.dumps(event, ensure_ascii=False))
        parts.append("")
    return ("\n".join(parts) + "\n").encode("utf-8")


# ---------------------------------------------------------------------------
# RagConfig
# ---------------------------------------------------------------------------


class TestRagConfig:
    def test_defaults(self):
        cfg = RagConfig()
        assert cfg.enabled is False
        assert cfg.search_id == ""
        assert cfg.kb_ids == []
        assert cfg.max_context_chars == 6000

    def test_url_builds_completion_endpoint(self):
        assert RagConfig(base_url="http://rag:8080", search_id="abc").url == "http://rag:8080/api/v1/searches/abc/completions"
        assert RagConfig(base_url="http://rag:8080/", search_id="abc").url == "http://rag:8080/api/v1/searches/abc/completions"


# ---------------------------------------------------------------------------
# RagClient SSE parsing / payload / headers
# ---------------------------------------------------------------------------


class TestRagClientParsing:
    def test_parse_sse_accumulates_answer_and_reference(self):
        client = RagClient(RagConfig(search_id="s1"))
        lines = [
            'data: {"code": 0, "message": "", "data": {"answer": "Hello", "reference": {"chunks": [{"id": "1"}]}}}',
            'data: {"code": 0, "message": "", "data": {"answer": " world"}}',
            "data: true",
        ]
        # Note: the sentinel is the wrapped form from the real service, but the
        # parser must also tolerate a bare `data: true`.
        result = client._parse_sse(lines)
        assert result is not None
        assert result.answer == "Hello world"
        assert result.reference == {"chunks": [{"id": "1"}]}

    def test_parse_sse_keeps_last_reference_and_concatenates(self):
        client = RagClient(RagConfig(search_id="s1"))
        lines = [
            'data: {"code": 0, "message": "", "data": {"answer": "a", "reference": {"v": 1}}}',
            'data: {"code": 0, "message": "", "data": {"answer": "b", "reference": {"v": 2}}}',
            'data: {"code": 0, "message": "", "data": true}',
        ]
        result = client._parse_sse(lines)
        assert result is not None
        assert result.answer == "ab"
        assert result.reference == {"v": 2}

    def test_parse_sse_returns_none_when_empty(self):
        client = RagClient(RagConfig(search_id="s1"))
        assert client._parse_sse([]) is None
        assert client._parse_sse(['data: {"code": 0, "message": "", "data": true}']) is None
        assert client._parse_sse(['data: {"code": 0, "message": "", "data": {"answer": "  "}}']) is None

    def test_parse_sse_ignores_error_code_events(self):
        client = RagClient(RagConfig(search_id="s1"))
        lines = [
            'data: {"code": 0, "message": "", "data": {"answer": "ok"}}',
            'data: {"code": 500, "message": "boom", "data": null}',
        ]
        result = client._parse_sse(lines)
        assert result is not None
        assert result.answer == "ok"

    def test_parse_sse_skips_comments_and_unparsable_lines(self):
        client = RagClient(RagConfig(search_id="s1"))
        lines = [
            ": keep-alive",
            "data: not-json",
            "",
            'data: {"code": 0, "message": "", "data": {"answer": "ok"}}',
        ]
        result = client._parse_sse(lines)
        assert result is not None
        assert result.answer == "ok"

    def test_parse_sse_answer_without_done_sentinel(self):
        client = RagClient(RagConfig(search_id="s1"))
        lines = ['data: {"code": 0, "message": "", "data": {"answer": "done"}}']
        result = client._parse_sse(lines)
        assert result is not None
        assert result.answer == "done"

    def test_parse_sse_terminal_content_event_with_final_flag(self):
        # The real service marks the terminal content event with `final: true`
        # inside `data`, followed by the `data: true` sentinel.
        client = RagClient(RagConfig(search_id="s1"))
        lines = [
            'data: {"code": 0, "message": "", "data": {"answer": "", "reference": {"chunks": [{"content": "x"}]}, "final": true}}',
            'data: {"code": 0, "message": "", "data": true}',
        ]
        result = client._parse_sse(lines)
        assert result is not None
        assert result.answer == ""
        assert result.reference == {"chunks": [{"content": "x"}]}

    def test_payload_and_headers(self):
        client = RagClient(RagConfig(search_id="s1", kb_ids=["kb1", "kb2"], api_key="token"))
        assert client._payload("hello") == {"question": "hello", "kb_ids": ["kb1", "kb2"]}
        assert client._headers()["Authorization"] == "Bearer token"
        assert client._headers()["Content-Type"] == "application/json"

    def test_payload_omits_kb_ids_when_empty(self):
        client = RagClient(RagConfig(search_id="s1"))
        assert client._payload("hello") == {"question": "hello"}

    def test_headers_no_api_key(self):
        client = RagClient(RagConfig(search_id="s1"))
        assert "Authorization" not in client._headers()


# ---------------------------------------------------------------------------
# RagClient HTTP roundtrip (mock transport, streaming SSE)
# ---------------------------------------------------------------------------


def _patch_http(monkeypatch, body: bytes, *, status: int = 200):
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["json"] = json.loads(request.content)
        captured["headers"] = dict(request.headers)
        return httpx.Response(status, content=body, headers={"content-type": "text/event-stream"})

    transport = httpx.MockTransport(handler)

    real_client = httpx.Client
    real_async_client = httpx.AsyncClient
    monkeypatch.setattr(httpx, "Client", lambda *, timeout=None: real_client(transport=transport, timeout=timeout))
    monkeypatch.setattr(httpx, "AsyncClient", lambda *, timeout=None: real_async_client(transport=transport, timeout=timeout))
    return captured


class TestRagClientHttp:
    def test_retrieve_roundtrip_streams_sse(self, monkeypatch):
        body = _sse_body(
            _event({"answer": "Hello", "reference": {"chunks": [{"id": "1"}]}}),
            _event({"answer": " world"}),
            _event(True),
        )
        captured = _patch_http(monkeypatch, body)
        client = RagClient(RagConfig(base_url="http://rag", search_id="s1", kb_ids=["kb1"], api_key="tok"))
        result = client.retrieve("what is X")
        assert result is not None
        assert result.answer == "Hello world"
        assert result.reference == {"chunks": [{"id": "1"}]}
        assert captured["json"] == {"question": "what is X", "kb_ids": ["kb1"]}
        assert captured["headers"].get("content-type") == "application/json"
        assert captured["headers"].get("authorization") == "Bearer tok"

    def test_aretrieve_roundtrip(self, monkeypatch):
        body = _sse_body(_event({"answer": "answer"}), _event(True))
        _patch_http(monkeypatch, body)
        client = RagClient(RagConfig(base_url="http://rag", search_id="s1"))
        result = asyncio.run(client.aretrieve("q"))
        assert result is not None
        assert result.answer == "answer"

    def test_retrieve_fails_open_on_http_error(self, monkeypatch):
        _patch_http(monkeypatch, b"", status=500)
        client = RagClient(RagConfig(base_url="http://rag", search_id="s1", timeout_seconds=1.0))
        assert client.retrieve("q") is None

    def test_retrieve_fails_open_on_transport_error(self):
        # Unreachable address -> transport error -> None.
        client = RagClient(RagConfig(base_url="http://127.0.0.1:1", search_id="s1", timeout_seconds=1.0))
        assert client.retrieve("q") is None


# ---------------------------------------------------------------------------
# RagMiddleware injection
# ---------------------------------------------------------------------------


def _middleware(client: _FakeClient, enabled: bool = True) -> RagMiddleware:
    mw = RagMiddleware(config=RagConfig(enabled=enabled, base_url="http://rag", search_id="s1"))
    mw._client = client
    return mw


class TestRagRenderer:
    def _mw(self) -> RagMiddleware:
        return _middleware(_FakeClient(None))

    def test_extracts_content_doc_and_similarity_drops_noise(self):
        mw = self._mw()
        reference = {
            "total": 2,
            "chunks": [
                {
                    "content": "First chunk.",
                    "document_name": "a.pdf",
                    "similarity": 0.75,
                    "positions": [[1, 2, 3]],
                    "image_id": "img",
                },
                {"content": "Second chunk.", "document_name": "b.pdf", "similarity": 0.5},
                {"content": "", "document_name": "empty.pdf"},  # empty content skipped
            ],
            "doc_aggs": [
                {"doc_name": "a.pdf", "doc_id": "d1", "count": 1},
                {"doc_name": "b.pdf", "doc_id": "d2", "count": 1},
            ],
        }
        rendered = mw._render_reference(reference)
        assert "[1] a.pdf (similarity=0.750)" in rendered
        assert "First chunk." in rendered
        assert "[2] b.pdf (similarity=0.500)" in rendered
        assert "Second chunk." in rendered
        assert "Source documents:" in rendered
        assert "- a.pdf: 1 chunk(s)" in rendered
        assert "positions" not in rendered
        assert "image_id" not in rendered
        assert "empty.pdf" not in rendered

    def test_render_reference_empty_and_missing(self):
        mw = self._mw()
        assert mw._render_reference({}) == ""
        assert mw._render_reference({"chunks": []}) == ""
        assert mw._render_reference({"chunks": [{"content": ""}]}) == ""

    def test_render_reference_doc_aggs_only(self):
        mw = self._mw()
        rendered = mw._render_reference({"doc_aggs": [{"doc_name": "x.pdf", "count": 3}]})
        assert "Source documents:" in rendered
        assert "- x.pdf: 3 chunk(s)" in rendered

    def test_render_drops_answer(self):
        mw = self._mw()
        result = RagResult(
            answer="We need to answer the user's query...",
            reference={"chunks": [{"content": "C", "document_name": "d.pdf"}]},
        )
        rendered = mw._render(result)
        assert "We need to answer" not in rendered
        assert rendered == "<rag_context>\n[1] d.pdf\nC\n</rag_context>"

    def test_render_answer_only_is_empty(self):
        mw = self._mw()
        assert mw._render(RagResult(answer="draft reasoning", reference=None)) == ""
        assert mw._render(RagResult(answer="draft reasoning", reference={})) == ""


class TestRagMiddleware:
    def test_injects_before_latest_user_message(self):
        client = _FakeClient(_result())
        mw = _middleware(client)
        request = _make_request([SystemMessage(content="base system"), HumanMessage(content="hi", id="u1")])
        captured: dict = {}

        def handler(req):
            captured["messages"] = req.messages
            return object()

        mw.wrap_model_call(request, handler)
        messages = captured["messages"]
        assert messages[0].content == "base system"
        assert isinstance(messages[1], SystemMessage)
        assert _AUTHORITY_CONTRACT in messages[1].content
        assert isinstance(messages[2], HumanMessage)
        assert messages[2].additional_kwargs["hide_from_ui"] is True
        assert messages[2].additional_kwargs[_RAG_CONTEXT_DATA_KEY] is True
        assert "Fact A content." in messages[2].content
        assert "doc.pdf" in messages[2].content
        assert "similarity=0.900" in messages[2].content
        # retrieval-internal noise must not leak into the injected block
        assert "positions" not in messages[2].content
        assert "image_id" not in messages[2].content
        # the injected pair lands right before the (only) user message
        assert messages[3].content == "hi"

    def test_injects_before_latest_user_message_on_second_turn(self):
        client = _FakeClient(_result())
        mw = _middleware(client)
        history = [
            SystemMessage(content="base system"),
            HumanMessage(content="first", id="u1"),
            AIMessage(content="first answer", id="a1"),
            HumanMessage(content="second", id="u2"),
        ]
        captured: list = []

        mw.wrap_model_call(_make_request(history), lambda req: captured.append(req.messages) or object())
        messages = captured[0]
        # The turn-2 evidence must sit immediately before the *second* user message,
        # not before the first one (the old leading-position behavior buried it at
        # the front of the whole history).
        user1_index = next(i for i, m in enumerate(messages) if isinstance(m, HumanMessage) and m.content == "first")
        data_index = next(i for i, m in enumerate(messages) if isinstance(m, HumanMessage) and _RAG_CONTEXT_DATA_KEY in (m.additional_kwargs or {}))
        user2_index = next(i for i, m in enumerate(messages) if isinstance(m, HumanMessage) and m.content == "second")
        assert data_index > user1_index
        assert data_index == user2_index - 1
        assert client.queries == ["second"]

    def test_retrieves_once_per_turn(self):
        client = _FakeClient(_result())
        mw = _middleware(client)
        request = _make_request([HumanMessage(content="hi", id="u1")])

        mw.wrap_model_call(request, lambda req: object())
        mw.wrap_model_call(request, lambda req: object())
        assert client.calls == 1
        assert client.queries == ["hi"]

    def test_re_queries_for_new_user_message(self):
        client = _FakeClient(_result())
        mw = _middleware(client)

        mw.wrap_model_call(_make_request([HumanMessage(content="first", id="u1")]), lambda req: object())
        mw.wrap_model_call(_make_request([HumanMessage(content="second", id="u2")]), lambda req: object())
        assert client.calls == 2
        assert client.queries == ["first", "second"]

    def test_skips_hidden_messages_as_query_source(self):
        client = _FakeClient(_result())
        mw = _middleware(client)
        hidden = HumanMessage(content="not a real user", id="h1", additional_kwargs={"hide_from_ui": True})
        request = _make_request([hidden])
        captured = []

        mw.wrap_model_call(request, lambda req: captured.append(req.messages) or object())
        assert client.calls == 0
        assert captured == [[hidden]]  # no injection, unchanged

    def test_no_injection_when_retrieval_empty(self):
        client = _FakeClient(None)
        mw = _middleware(client)
        request = _make_request([HumanMessage(content="hi", id="u1")])
        captured = []

        mw.wrap_model_call(request, lambda req: captured.append(req.messages) or object())
        assert captured == [[HumanMessage(content="hi", id="u1")]]
        assert client.calls == 1

    def test_no_injection_when_answer_only_result(self):
        # The service-side answer draft is dropped; with no reference chunks there
        # is nothing to inject, so the request passes through unchanged.
        client = _FakeClient(RagResult(answer="draft reasoning"))
        mw = _middleware(client)
        request = _make_request([HumanMessage(content="hi", id="u1")])
        captured = []

        mw.wrap_model_call(request, lambda req: captured.append(req.messages) or object())
        assert captured == [[HumanMessage(content="hi", id="u1")]]
        assert client.calls == 1

    def test_fails_open_when_client_raises(self):
        client = _FakeClient(fail=True)
        mw = _middleware(client)
        request = _make_request([HumanMessage(content="hi", id="u1")])
        captured = []

        mw.wrap_model_call(request, lambda req: captured.append(req.messages) or object())
        assert client.calls == 1
        assert captured == [[HumanMessage(content="hi", id="u1")]]

    def test_disabled_middleware_is_noop(self):
        client = _FakeClient(_result())
        mw = _middleware(client, enabled=False)
        request = _make_request([HumanMessage(content="hi", id="u1")])
        captured = []

        mw.wrap_model_call(request, lambda req: captured.append(req.messages) or object())
        assert client.calls == 0
        assert captured == [[HumanMessage(content="hi", id="u1")]]

    def test_async_path(self):
        client = _FakeClient(_result())
        mw = _middleware(client)
        request = _make_request([HumanMessage(content="hi", id="u1")])

        async def handler(req):
            return req.messages

        messages = asyncio.run(mw.awrap_model_call(request, handler))
        assert any(isinstance(m, HumanMessage) and _RAG_CONTEXT_DATA_KEY in (m.additional_kwargs or {}) for m in messages)
        assert client.calls == 1

    def test_max_context_chars_truncates(self):
        long_text = "word " * 500
        client = _FakeClient(RagResult(reference={"chunks": [{"content": long_text, "document_name": "d.pdf", "similarity": 0.5}]}))
        mw = RagMiddleware(config=RagConfig(enabled=True, base_url="http://rag", search_id="s1", max_context_chars=100))
        mw._client = client
        request = _make_request([HumanMessage(content="hi", id="u1")])
        captured = []

        mw.wrap_model_call(request, lambda req: captured.append(req.messages) or object())
        injected = captured[0][1]
        assert len(injected.content) <= 100
        assert injected.content.startswith("<rag_context>")
