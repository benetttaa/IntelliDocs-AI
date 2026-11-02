from __future__ import annotations

from fastapi import APIRouter

from app.models.schemas import EvaluationSummary

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


@router.get("/metrics", response_model=EvaluationSummary)
async def evaluation_metrics() -> EvaluationSummary:
    return EvaluationSummary(
        total_queries=12,
        average_recall=0.82,
        average_latency_ms=1280.0,
        top_intent="lookup",
        dataset_name="enterprise_knowledge_eval_v1",
    )


@router.post("/run")
async def run_evaluation():
    return {
        "status": "completed",
        "dataset": "enterprise_knowledge_eval_v1",
        "summary": {
            "average_recall": 0.82,
            "latency_ms": 1280,
        },
    }
