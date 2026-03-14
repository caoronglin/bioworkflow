from __future__ import annotations

import asyncio
import importlib
import os
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field

MAX_DATA_ROWS = 10000


class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role: system, user, or assistant")
    content: str = Field(..., description="Message content")


class SQLGenerationRequest(BaseModel):
    natural_query: str = Field(..., description="Natural language query")
    database_schema: dict[str, Any] = Field(..., description="Database schema information")
    context: str | None = Field(None, description="Additional context")


class DataAnalysisRequest(BaseModel):
    data: list[dict[str, Any]] = Field(..., description="Data to analyze")
    context: str = Field(..., description="Analysis context")
    focus_areas: list[str] | None = Field(None, description="Specific areas to focus on")


class ChartSuggestion(BaseModel):
    chart_type: str = Field(..., description="Suggested chart type")
    reason: str = Field(..., description="Why this chart type is suggested")
    configuration: dict[str, Any] = Field(..., description="Chart configuration")


class SQLResponseModel(BaseModel):
    sql: str = Field(..., description="Generated SQL query")
    confidence: str = Field(..., description="Confidence level: high, medium, or low")


class OpenAIService:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        default_model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> None:
        self.api_key: str | None = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url: str | None = base_url or os.getenv("OPENAI_BASE_URL")
        self.default_model: str = default_model
        self.temperature: float = temperature
        self.max_tokens: int = max_tokens

        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Please set OPENAI_API_KEY environment variable.",
            )

    def _create_model(
        self,
        model_name: str | None = None,
        temperature: float | None = None,
        stream: bool = False,
        max_tokens: int | None = None,
    ) -> Any:
        openai_chat_model = getattr(importlib.import_module("agentscope.model"), "OpenAIChatModel")

        client_kwargs: dict[str, Any] = {}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url

        return openai_chat_model(
            model_name=model_name or self.default_model,
            api_key=self.api_key,
            stream=stream,
            client_kwargs=client_kwargs or None,
            generate_kwargs={
                "temperature": self.temperature if temperature is None else temperature,
                "max_tokens": self.max_tokens if max_tokens is None else max_tokens,
            },
        )

    async def _run_agent(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        model_name: str | None = None,
        temperature: float | None = None,
        stream: bool = False,
        max_tokens: int | None = None,
        structured_model: type[BaseModel] | None = None,
    ) -> tuple[str, dict[str, Any]]:
        react_agent = getattr(importlib.import_module("agentscope.agent"), "ReActAgent")
        openai_chat_formatter = getattr(
            importlib.import_module("agentscope.formatter"),
            "OpenAIChatFormatter",
        )
        in_memory_memory = getattr(importlib.import_module("agentscope.memory"), "InMemoryMemory")
        msg_type = getattr(importlib.import_module("agentscope.message"), "Msg")

        agent = react_agent(
            name="BioWorkflowAI",
            sys_prompt=system_prompt,
            model=self._create_model(
                model_name=model_name,
                temperature=temperature,
                stream=stream,
                max_tokens=max_tokens,
            ),
            formatter=openai_chat_formatter(),
            memory=in_memory_memory(),
        )
        response = await agent(
            msg_type(name="user", content=user_prompt, role="user"),
            structured_model=structured_model,
        )
        content = response.get_text_content()
        metadata = dict(response.metadata) if isinstance(response.metadata, dict) else {}
        return content, metadata

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stream: bool = False,
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncGenerator[str, None]:
        del tools
        system_prompt = "You are a helpful AI assistant for BioWorkflow."
        non_system_messages = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            if role == "system":
                system_prompt = content
            else:
                non_system_messages.append(f"{role.upper()}: {content}")

        user_prompt = "\n\n".join(non_system_messages) or "Please respond to the user."
        content, _ = await self._run_agent(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model_name=model,
            temperature=temperature,
            stream=stream,
            max_tokens=max_tokens,
        )

        if stream:
            for chunk in self._chunk_text(content):
                yield chunk
            return

        yield content

    async def generate_sql(self, request: SQLGenerationRequest) -> dict[str, Any]:
        prompt = (
            "Convert the following natural language request into safe SQL.\n\n"
            f"Database schema:\n{request.database_schema}\n\n"
            f"Natural language query:\n{request.natural_query}\n\n"
            f"Additional context:\n{request.context or 'N/A'}\n\n"
            "Requirements:\n"
            "1. Return syntactically valid SQL.\n"
            "2. Prefer readable SQL.\n"
            "3. Use placeholders for parameters when needed.\n"
            "4. Do not add markdown fences."
        )
        _, metadata = await self._run_agent(
            system_prompt="You are a SQL expert for workflow metadata databases.",
            user_prompt=prompt,
            temperature=0.1,
            structured_model=SQLResponseModel,
        )
        sql = str(metadata.get("sql", "")).strip()
        confidence = str(metadata.get("confidence", "medium")).strip() or "medium"

        return {
            "sql": sql,
            "natural_query": request.natural_query,
            "schema_used": request.database_schema,
            "confidence": confidence,
            "generated_at": datetime.now().isoformat(),
        }

    async def analyze_data(self, request: DataAnalysisRequest) -> dict[str, Any]:
        if len(request.data) > MAX_DATA_ROWS:
            raise ValueError(
                f"Data exceeds maximum allowed rows ({MAX_DATA_ROWS}). Please reduce dataset size.",
            )

        df = pd.DataFrame(request.data)
        columns = [str(column) for column in df.columns]
        stats: dict[str, Any] = {
            "row_count": len(df),
            "column_count": len(columns),
            "columns": columns,
            "dtypes": {str(key): str(value) for key, value in df.dtypes.to_dict().items()},
            "memory_usage": int(df.memory_usage(deep=True).sum()),
        }

        numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()
        if numeric_columns:
            stats["numeric_summary"] = df[numeric_columns].describe().to_dict()

        data_sample = df.head(50).to_dict(orient="records")
        focus_areas = request.focus_areas or []
        prompt = (
            f"Context: {request.context}\n\n"
            f"Columns: {', '.join(columns)}\n"
            f"Row count: {stats['row_count']}\n"
            f"Focus areas: {', '.join(focus_areas) if focus_areas else 'general analysis'}\n\n"
            f"Data sample:\n{data_sample}\n\n"
            "Provide concise sections for key metrics, anomalies, trends, and recommendations."
        )

        analysis, _ = await self._run_agent(
            system_prompt="You are a data analyst for workflow and execution telemetry.",
            user_prompt=prompt,
            temperature=0.4,
        )
        chart_suggestions = [
            suggestion.model_dump()
            for suggestion in await self._suggest_charts(df, request.context)
        ]

        return {
            "analysis": analysis,
            "statistics": stats,
            "chart_suggestions": chart_suggestions,
            "data_sample": data_sample,
            "generated_at": datetime.now().isoformat(),
            "focus_areas": focus_areas,
        }

    async def _suggest_charts(
        self,
        df: pd.DataFrame,
        context: str,
    ) -> list[ChartSuggestion]:
        del context
        suggestions: list[ChartSuggestion] = []
        numeric_cols = [
            str(column) for column in df.select_dtypes(include=["number"]).columns.tolist()
        ]
        categorical_cols = [
            str(column)
            for column in df.select_dtypes(include=["object", "category"]).columns.tolist()
        ]
        datetime_cols = [
            str(column) for column in df.select_dtypes(include=["datetime"]).columns.tolist()
        ]

        if datetime_cols and numeric_cols:
            suggestions.append(
                ChartSuggestion(
                    chart_type="line",
                    reason="Time series data detected. Line chart best shows trends over time.",
                    configuration={
                        "x_axis": datetime_cols[0],
                        "y_axis": numeric_cols[0],
                        "time_unit": "auto",
                    },
                ),
            )

        if categorical_cols and numeric_cols:
            suggestions.append(
                ChartSuggestion(
                    chart_type="bar",
                    reason="Categorical data with numeric values. Bar chart enables easy comparison.",
                    configuration={
                        "x_axis": categorical_cols[0],
                        "y_axis": numeric_cols[0],
                        "aggregation": "sum",
                    },
                ),
            )

        if len(categorical_cols) > 0 and len(numeric_cols) > 0:
            suggestions.append(
                ChartSuggestion(
                    chart_type="pie",
                    reason="Shows distribution of categories as proportions of a whole.",
                    configuration={"category": categorical_cols[0], "value": numeric_cols[0]},
                ),
            )

        if len(numeric_cols) >= 2:
            suggestions.append(
                ChartSuggestion(
                    chart_type="scatter",
                    reason="Two numeric variables detected. Scatter plot reveals correlations.",
                    configuration={
                        "x_axis": numeric_cols[0],
                        "y_axis": numeric_cols[1],
                        "color": categorical_cols[0] if categorical_cols else None,
                    },
                ),
            )

        return suggestions

    @staticmethod
    def _chunk_text(content: str, chunk_size: int = 120) -> list[str]:
        return [
            content[index : index + chunk_size] for index in range(0, len(content), chunk_size)
        ] or [""]


_openai_service: OpenAIService | None = None
_openai_lock = asyncio.Lock()


async def get_openai_service() -> OpenAIService:
    global _openai_service
    if _openai_service is None:
        async with _openai_lock:
            if _openai_service is None:
                _openai_service = OpenAIService()
    return _openai_service
