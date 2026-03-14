from __future__ import annotations

import asyncio
import importlib.util
import sys
import types
from collections.abc import Awaitable, Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _load_module(module_name: str, path: Path) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load module: {module_name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class _FakeResponse:
    def __init__(self, text: str, metadata: dict[str, object]) -> None:
        self._text: str = text
        self.metadata: dict[str, object] = metadata

    def get_text_content(self) -> str:
        return self._text


class _FakeReActAgent:
    def __init__(self, **_: object) -> None:
        pass

    async def __call__(self, msg: object, structured_model: object = None) -> _FakeResponse:
        del msg, structured_model
        return _FakeResponse("OK", {"sql": "SELECT 1", "confidence": "high"})


class _FakeFormatter:
    def __init__(self) -> None:
        pass


class _FakeMemory:
    def __init__(self) -> None:
        pass


class _FakeMsg:
    def __init__(self, **_: object) -> None:
        pass


class _FakeModel:
    def __init__(self, **_: object) -> None:
        pass


class _FakeMetricBase:
    def __init__(self, **_: object) -> None:
        pass


class _FakeMetricType:
    NUMERICAL: str = "numerical"


class _FakeMetricResult:
    def __init__(self, **kwargs: object) -> None:
        self.kwargs: dict[str, object] = dict(kwargs)


class _FakeTask:
    def __init__(self, **kwargs: object) -> None:
        self.__dict__.update(kwargs)


class _FakeBenchmarkBase:
    def __init__(self, **_: object) -> None:
        pass


class _FakeSolutionOutput:
    def __init__(self, **kwargs: object) -> None:
        self.__dict__.update(kwargs)


class _FakeStorage:
    def __init__(self, save_dir: str) -> None:
        self.save_dir: str = save_dir
        Path(save_dir).mkdir(parents=True, exist_ok=True)


class _FakeEvaluator:
    def __init__(self, **_: object) -> None:
        pass

    async def run(self, solve: Callable[[object, object], Awaitable[object]]) -> None:
        await solve(_FakeTask(input="Return OK"), None)


def _install_fake_agentscope_modules() -> None:
    agent_module = types.ModuleType("agentscope.agent")
    setattr(agent_module, "ReActAgent", _FakeReActAgent)
    formatter_module = types.ModuleType("agentscope.formatter")
    setattr(formatter_module, "OpenAIChatFormatter", _FakeFormatter)
    memory_module = types.ModuleType("agentscope.memory")
    setattr(memory_module, "InMemoryMemory", _FakeMemory)
    message_module = types.ModuleType("agentscope.message")
    setattr(message_module, "Msg", _FakeMsg)
    model_module = types.ModuleType("agentscope.model")
    setattr(model_module, "OpenAIChatModel", _FakeModel)
    evaluate_module = types.ModuleType("agentscope.evaluate")
    setattr(evaluate_module, "BenchmarkBase", _FakeBenchmarkBase)
    setattr(evaluate_module, "FileEvaluatorStorage", _FakeStorage)
    setattr(evaluate_module, "GeneralEvaluator", _FakeEvaluator)
    setattr(evaluate_module, "MetricBase", _FakeMetricBase)
    setattr(evaluate_module, "MetricResult", _FakeMetricResult)
    setattr(evaluate_module, "MetricType", _FakeMetricType)
    setattr(evaluate_module, "SolutionOutput", _FakeSolutionOutput)
    setattr(evaluate_module, "Task", _FakeTask)

    sys.modules["agentscope.agent"] = agent_module
    sys.modules["agentscope.formatter"] = formatter_module
    sys.modules["agentscope.memory"] = memory_module
    sys.modules["agentscope.message"] = message_module
    sys.modules["agentscope.model"] = model_module
    sys.modules["agentscope.evaluate"] = evaluate_module


async def _run() -> None:
    _install_fake_agentscope_modules()
    openai_service = _load_module(
        "backend.services.ai.openai_service",
        SRC / "backend" / "services" / "ai" / "openai_service.py",
    )
    agentscope_eval = _load_module(
        "backend.services.ai.agentscope_eval",
        SRC / "backend" / "services" / "ai" / "agentscope_eval.py",
    )

    service = openai_service.OpenAIService(api_key="test-key", default_model="gpt-4o-mini")
    chunks: list[str] = []
    async for chunk in service.chat_completion(
        messages=[{"role": "user", "content": "hello"}],
        stream=False,
    ):
        chunks.append(chunk)
    assert "OK" in "".join(chunks)

    sql_result = await service.generate_sql(
        openai_service.SQLGenerationRequest(
            natural_query="count rows",
            database_schema={"table": ["id"]},
            context=None,
        ),
    )
    assert sql_result["sql"] == "SELECT 1"
    assert sql_result["confidence"] == "high"

    eval_result = await agentscope_eval.run_smoke_evaluation("/tmp/agentscope-eval-smoke")
    assert Path(eval_result.results_dir).exists()


if __name__ == "__main__":
    asyncio.run(_run())
