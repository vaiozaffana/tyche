"""Cost-bounded parent LangGraph workflow."""

import logging
from typing import Any, cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.runtime import Runtime
from langgraph.types import Send

from tyche_ai.job_search.agents.dynamic.factory import build_specialist, route_candidate
from tyche_ai.job_search.agents.predefined.job_scout import build_job_scout
from tyche_ai.job_search.agents.predefined.page_reader import build_page_reader
from tyche_ai.job_search.agents.predefined.query_analyst import (
    PromptParseError,
    build_query_analyst,
)
from tyche_ai.job_search.agents.predefined.specialist_planner import build_specialist_planner
from tyche_ai.job_search.graph.context import RunContext
from tyche_ai.job_search.graph.nodes import candidate_id, recency_days
from tyche_ai.job_search.graph.state import (
    AssessmentDispatch,
    JobSearchInput,
    JobSearchOutput,
    JobSearchState,
)
from tyche_ai.job_search.models import (
    AssessedCandidate,
    PipelineResult,
    PipelineStats,
    RankedJob,
)
from tyche_ai.job_search.screening.dedup import deduplicate
from tyche_ai.job_search.screening.gate import GateSettings, decide
from tyche_ai.job_search.screening.title_filter import title_matches

LOGGER = logging.getLogger(__name__)


def build_job_search_graph() -> CompiledStateGraph[Any, Any, Any, Any]:
    def analyze_query(state: JobSearchState, runtime: Runtime[RunContext]) -> dict[str, Any]:
        try:
            output = build_query_analyst(runtime.context.llm).invoke({"prompt": state["prompt"]})
            return {
                "status": "running",
                "parsed_query": output["parsed_query"],
                "run_log": [{"event": "query_parsed"}],
            }
        except PromptParseError as error:
            return {
                "status": "failed",
                "error_code": "prompt_parse",
                "error_message": str(error),
                "run_log": [{"event": "prompt_parse_failed"}],
            }

    def after_analysis(state: JobSearchState) -> str:
        return "finalize" if state.get("status") == "failed" else "plan_specialists"

    def plan_specialists(state: JobSearchState, runtime: Runtime[RunContext]) -> dict[str, Any]:
        output = build_specialist_planner(
            runtime.context.llm,
            max_specialists=runtime.context.settings.job_search_max_specialists,
        ).invoke({"parsed_query": state["parsed_query"]})
        return {
            "specs": output["specs"],
            "run_log": [{"event": "specialists_planned", "count": len(output["specs"])}],
        }

    def search_jobs(state: JobSearchState, runtime: Runtime[RunContext]) -> dict[str, Any]:
        output = build_job_scout(runtime.context.provider).invoke(
            {
                "parsed_query": state["parsed_query"],
                "budget": runtime.context.budget,
                "page_token": state.get("next_page_token"),
            }
        )
        return {
            "raw_candidates": output["page"].candidates,
            "next_page_token": output["page"].next_page_token,
            "run_log": [
                {
                    "event": "search_page",
                    "count": len(output["page"].candidates),
                    "reason": output["refusal_reason"],
                }
            ],
        }

    def after_search(state: JobSearchState, runtime: Runtime[RunContext]) -> str:
        enough = (
            len(state.get("raw_candidates", [])) >= runtime.context.settings.job_search_max_results
        )
        can_continue = runtime.context.budget.serp_calls < runtime.context.budget.max_serp_calls
        return (
            "search_jobs"
            if state.get("next_page_token") and not enough and can_continue
            else "dedupe_filter"
        )

    def dedupe_filter(state: JobSearchState, runtime: Runtime[RunContext]) -> dict[str, Any]:
        deduped = deduplicate(state.get("raw_candidates", []))
        threshold = runtime.context.settings.job_search_title_match_threshold
        filtered = [
            candidate
            for candidate in deduped
            if title_matches(candidate, state["parsed_query"], threshold=threshold)[0]
        ]
        return {
            "candidates": filtered,
            "run_log": [
                {
                    "event": "screened",
                    "after_dedup": len(deduped),
                    "after_filter": len(filtered),
                }
            ],
        }

    def after_filter(state: JobSearchState) -> str:
        return "gate_and_read" if state.get("candidates") else "finalize"

    def gate_and_read(state: JobSearchState, runtime: Runtime[RunContext]) -> dict[str, Any]:
        settings = runtime.context.settings
        gate_settings = GateSettings(
            min_description_chars=settings.job_search_min_description_chars,
            title_match_threshold=settings.job_search_title_match_threshold,
            blocked_domains=settings.job_search_scrape_blocked_domains,
        )
        reader = build_page_reader(runtime.context.reader, runtime.context.cache)
        contents = {}
        enrichment = {}
        logs: list[dict[str, object]] = []
        for candidate in state["candidates"]:
            key = candidate_id(candidate)
            decision = decide(
                candidate, state["parsed_query"], gate_settings, runtime.context.budget
            )
            LOGGER.info(
                "job_search_gate search_id=%s candidate=%s reason=%s",
                runtime.context.search_id,
                key,
                decision.reason,
            )
            logs.append({"event": "gate", "candidate": key, "reason": decision.reason})
            if not decision.scrape or not candidate.source_url:
                enrichment[key] = (
                    "not_needed" if decision.reason == "description_sufficient" else "skipped"
                )
                continue
            output = reader.invoke({"url": candidate.source_url, "budget": runtime.context.budget})
            contents[key] = output["content"]
            enrichment[key] = cast(Any, output["source"])
        return {"page_contents": contents, "enrichment": enrichment, "run_log": logs}

    def dispatch_assessments(
        state: JobSearchState,
        runtime: Runtime[RunContext],
    ) -> list[Send] | str:
        sends: list[Send] = []
        for candidate in state.get("candidates", []):
            if not runtime.context.budget.take_llm():
                break
            key = candidate_id(candidate)
            spec = route_candidate(candidate, state["specs"])
            sends.append(
                Send(
                    "assess_job",
                    AssessmentDispatch(
                        query=state["parsed_query"],
                        candidate=candidate,
                        page_content=state.get("page_contents", {}).get(key),
                        spec=spec,
                        enrichment_status=state.get("enrichment", {}).get(key, "not_needed"),
                    ),
                )
            )
        return sends or "rank_and_finalize"

    def assess_job(state: AssessmentDispatch, runtime: Runtime[RunContext]) -> dict[str, Any]:
        output = build_specialist(state["spec"], runtime.context.llm).invoke(
            {
                "query": state["query"],
                "candidate": state["candidate"],
                "page_content": state["page_content"],
            }
        )
        return {
            "assessed": [
                AssessedCandidate(
                    candidate=state["candidate"],
                    assessment=output["assessment"],
                    specialist_id=output["specialist_id"],
                    enrichment_status=state["enrichment_status"],
                )
            ]
        }

    def rank_and_finalize(state: JobSearchState, runtime: Runtime[RunContext]) -> dict[str, Any]:
        assessed = sorted(
            state.get("assessed", []),
            key=lambda item: (
                -(item.assessment.fit_score if item.assessment.fit_score is not None else -1),
                0 if item.assessment.salary or item.candidate.salary_raw else 1,
                recency_days(item.candidate.posted_at),
            ),
        )[: runtime.context.settings.job_search_max_results]
        results = [
            RankedJob(
                candidate=item.candidate,
                assessment=item.assessment,
                rank=index,
                specialist_id=item.specialist_id,
                enrichment_status=item.enrichment_status,
            )
            for index, item in enumerate(assessed, start=1)
        ]
        return {"results": results, "status": "completed"}

    def finalize(state: JobSearchState, runtime: Runtime[RunContext]) -> JobSearchOutput:
        budget = runtime.context.budget
        result = PipelineResult(
            status="failed" if state.get("status") == "failed" else "completed",
            parsed_query=state.get("parsed_query"),
            specs=[
                cast(dict[str, object], spec.model_dump(mode="json"))
                for spec in state.get("specs", [])
            ],
            results=state.get("results", []),
            stats=PipelineStats(
                serp_calls=budget.serp_calls,
                candidates=len(state.get("raw_candidates", [])),
                after_dedup=len(deduplicate(state.get("raw_candidates", []))),
                after_filter=len(state.get("candidates", [])),
                firecrawl_calls=budget.firecrawl_calls,
                cache_hits=budget.cache_hits,
                llm_calls=budget.llm_calls,
                specialists=len(state.get("specs", [])),
            ),
            run_log=state.get("run_log", [])[:200],
            error_code=state.get("error_code"),
            error_message=state.get("error_message"),
        )
        return {"result": result}

    graph = StateGraph(
        JobSearchState,
        context_schema=RunContext,
        input_schema=JobSearchInput,
        output_schema=JobSearchOutput,
    )
    graph.add_node("analyze_query", analyze_query)
    graph.add_node("plan_specialists", plan_specialists)
    graph.add_node("search_jobs", search_jobs)
    graph.add_node("dedupe_filter", dedupe_filter)
    graph.add_node("gate_and_read", gate_and_read)
    graph.add_node("assess_job", assess_job)
    graph.add_node("rank_and_finalize", rank_and_finalize)
    graph.add_node("finalize", finalize)
    graph.add_edge(START, "analyze_query")
    graph.add_conditional_edges("analyze_query", after_analysis)
    graph.add_edge("plan_specialists", "search_jobs")
    graph.add_conditional_edges("search_jobs", after_search)
    graph.add_conditional_edges("dedupe_filter", after_filter)
    graph.add_edge("gate_and_read", "dispatch_assessments")
    graph.add_node("dispatch_assessments", lambda state: {})
    graph.add_conditional_edges("dispatch_assessments", dispatch_assessments)
    graph.add_edge("assess_job", "rank_and_finalize")
    graph.add_edge("rank_and_finalize", "finalize")
    graph.add_edge("finalize", END)
    return graph.compile(name="job_search")


def run_job_search(prompt: str, context: RunContext) -> PipelineResult:
    output = build_job_search_graph().invoke(
        {"prompt": prompt},
        context=context,
        config={"max_concurrency": context.settings.job_search_max_concurrency},
    )
    return cast(PipelineResult, output["result"])
