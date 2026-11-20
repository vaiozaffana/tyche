"""Cache-first budgeted page-reader subgraph."""

from typing import Any, Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from tyche_ai.job_search.models import Budget, PageContent
from tyche_ai.job_search.tools.cache import ScrapeCache
from tyche_ai.job_search.tools.firecrawl import PageReader


class PageReaderInput(TypedDict):
    url: str
    budget: Budget


class PageReaderOutput(TypedDict):
    content: PageContent
    source: Literal["cached", "scraped", "failed", "skipped"]


def build_page_reader(
    reader: PageReader,
    cache: ScrapeCache,
) -> CompiledStateGraph[Any, Any, Any, Any]:
    def read(state: PageReaderInput) -> PageReaderOutput:
        cached = cache.get(state["url"])
        if cached:
            state["budget"].record_cache_hit()
            return {"content": cached, "source": "cached"}
        if not state["budget"].take_firecrawl():
            return {
                "content": PageContent(status="failed", error="Firecrawl budget exhausted"),
                "source": "skipped",
            }
        content = reader.read(state["url"])
        if content.status == "ok":
            cache.put(state["url"], content)
        return {"content": content, "source": "scraped" if content.status == "ok" else "failed"}

    graph = StateGraph(
        PageReaderOutput, input_schema=PageReaderInput, output_schema=PageReaderOutput
    )
    graph.add_node("read", read)
    graph.add_edge(START, "read")
    graph.add_edge("read", END)
    return graph.compile(name="page_reader")
