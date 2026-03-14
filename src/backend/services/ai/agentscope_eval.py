from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class EvaluationRunResult:
    benchmark_name: str
    results_dir: str


def _load_eval_symbols() -> dict[str, Any]:
    evaluate_module = importlib.import_module("agentscope.evaluate")
    return {
        "BenchmarkBase": getattr(evaluate_module, "BenchmarkBase"),
        "FileEvaluatorStorage": getattr(evaluate_module, "FileEvaluatorStorage"),
        "GeneralEvaluator": getattr(evaluate_module, "GeneralEvaluator"),
        "MetricBase": getattr(evaluate_module, "MetricBase"),
        "MetricResult": getattr(evaluate_module, "MetricResult"),
        "MetricType": getattr(evaluate_module, "MetricType"),
        "SolutionOutput": getattr(evaluate_module, "SolutionOutput"),
        "Task": getattr(evaluate_module, "Task"),
    }


async def run_smoke_evaluation(results_dir: str) -> EvaluationRunResult:
    symbols = _load_eval_symbols()
    benchmark_base = symbols["BenchmarkBase"]
    file_evaluator_storage = symbols["FileEvaluatorStorage"]
    general_evaluator = symbols["GeneralEvaluator"]
    metric_base = symbols["MetricBase"]
    metric_result = symbols["MetricResult"]
    metric_type = symbols["MetricType"]
    solution_output = symbols["SolutionOutput"]
    task_type = symbols["Task"]

    class ExactMatchMetric(metric_base):
        def __init__(self, expected: str) -> None:
            super().__init__(
                name="exact_match",
                metric_type=metric_type.NUMERICAL,
                description="Checks exact equality for smoke evaluation.",
                categories=[],
            )
            self.expected = expected

        async def __call__(self, solution: Any) -> Any:
            score = 1.0 if str(solution.output).strip() == self.expected else 0.0
            return metric_result(
                name="exact_match",
                result=score,
                message="matched" if score == 1.0 else "not matched",
            )

    class SmokeBenchmark(benchmark_base):
        def __init__(self) -> None:
            super().__init__(
                name="BioWorkflow AgentScope Smoke Benchmark",
                description="Minimal smoke evaluation for AgentScope integration.",
            )
            self.dataset = [
                task_type(
                    id="smoke-1",
                    input="Return the string OK exactly.",
                    ground_truth="OK",
                    tags={"suite": "smoke"},
                    metrics=[ExactMatchMetric("OK")],
                    metadata={},
                ),
            ]

        def __iter__(self) -> Any:
            for task in self.dataset:
                yield task

        def __getitem__(self, index: int) -> Any:
            return self.dataset[index]

        def __len__(self) -> int:
            return len(self.dataset)

    async def solve(task: Any, _pre_hook: Any) -> Any:
        return solution_output(success=True, output="OK", trajectory=[])

    output_dir = Path(results_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    evaluator = general_evaluator(
        name="BioWorkflow AgentScope Smoke Evaluation",
        benchmark=SmokeBenchmark(),
        n_repeat=1,
        storage=file_evaluator_storage(save_dir=str(output_dir)),
        n_workers=1,
    )
    await evaluator.run(solve)

    return EvaluationRunResult(
        benchmark_name="BioWorkflow AgentScope Smoke Benchmark",
        results_dir=str(output_dir),
    )
