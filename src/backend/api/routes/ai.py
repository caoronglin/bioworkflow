from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.services.ai.openai_service import (
    ChatMessage,
    DataAnalysisRequest,
    OpenAIService,
    SQLGenerationRequest,
    get_openai_service,
)

router = APIRouter(prefix="/ai", tags=["ai"])


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., description="Chat messages")
    model: str = Field(default="gpt-4", description="Model to use")
    temperature: float = Field(default=0.7, ge=0, le=2, description="Sampling temperature")
    stream: bool = Field(default=False, description="Stream response")


class ChatResponse(BaseModel):
    content: str = Field(..., description="Response content")
    model: str = Field(..., description="Model used")
    usage: dict[str, int] | None = Field(None, description="Token usage")
    created_at: str = Field(..., description="Response timestamp")


class SQLGenerateRequest(BaseModel):
    natural_query: str = Field(..., description="Natural language query", min_length=1)
    database_schema: dict[str, Any] = Field(..., description="Database schema")
    context: str | None = Field(None, description="Additional context")


class SQLGenerateResponse(BaseModel):
    sql: str = Field(..., description="Generated SQL query")
    natural_query: str = Field(..., description="Original natural language query")
    confidence: str = Field(..., description="Confidence level")
    schema_used: dict[str, Any] = Field(..., description="Schema used for generation")
    generated_at: str = Field(..., description="Generation timestamp")


class DataAnalyzeRequest(BaseModel):
    data: list[dict[str, Any]] = Field(..., description="Data to analyze", min_length=1)
    context: str = Field(..., description="Analysis context", min_length=1)
    focus_areas: list[str] | None = Field(None, description="Specific areas to focus on")


class DataAnalyzeResponse(BaseModel):
    analysis: str = Field(..., description="AI-generated analysis")
    statistics: dict[str, Any] = Field(..., description="Data statistics")
    chart_suggestions: list[dict[str, Any]] = Field(..., description="Suggested chart types")
    data_sample: list[dict[str, Any]] = Field(..., description="Sample of analyzed data")
    generated_at: str = Field(..., description="Analysis timestamp")
    focus_areas: list[str] = Field(default_factory=list, description="Areas focused on")


class ChartSuggestRequest(BaseModel):
    data: list[dict[str, Any]] = Field(..., description="Data to visualize", min_length=1)
    context: str = Field(..., description="Visualization context")


class ChartSuggestResponse(BaseModel):
    suggestions: list[dict[str, Any]] = Field(..., description="Chart suggestions")
    data_summary: dict[str, Any] = Field(..., description="Summary of analyzed data")
    context: str = Field(..., description="Original context")
    generated_at: str = Field(..., description="Generation timestamp")


@router.post("/chat", response_model=ChatResponse)
async def chat_completion(
    request: ChatRequest,
    ai_service: OpenAIService = Depends(get_openai_service),
) -> ChatResponse:
    try:
        if request.stream:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Streaming not supported on this endpoint. Use /chat/stream",
            )

        response_content = ""
        async for chunk in ai_service.chat_completion(
            messages=[
                {"role": message.role, "content": message.content} for message in request.messages
            ],
            model=request.model,
            temperature=request.temperature,
            stream=False,
        ):
            response_content += chunk

        return ChatResponse(
            content=response_content,
            model=request.model,
            usage=None,
            created_at=datetime.now().isoformat(),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat completion failed: {exc}",
        ) from exc


@router.post("/chat/stream")
async def chat_completion_stream(
    request: ChatRequest,
    ai_service: OpenAIService = Depends(get_openai_service),
) -> StreamingResponse:
    async def generate_stream() -> Any:
        try:
            async for chunk in ai_service.chat_completion(
                messages=[
                    {"role": message.role, "content": message.content}
                    for message in request.messages
                ],
                model=request.model,
                temperature=request.temperature,
                stream=True,
            ):
                yield f"data: {json.dumps({'content': chunk})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(generate_stream(), media_type="text/event-stream")


@router.post("/sql/generate", response_model=SQLGenerateResponse)
async def generate_sql(
    request: SQLGenerateRequest,
    ai_service: OpenAIService = Depends(get_openai_service),
) -> SQLGenerateResponse:
    try:
        result = await ai_service.generate_sql(
            SQLGenerationRequest(
                natural_query=request.natural_query,
                database_schema=request.database_schema,
                context=request.context,
            ),
        )
        return SQLGenerateResponse(**result)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SQL generation failed: {exc}",
        ) from exc


@router.post("/data/analyze", response_model=DataAnalyzeResponse)
async def analyze_data(
    request: DataAnalyzeRequest,
    ai_service: OpenAIService = Depends(get_openai_service),
) -> DataAnalyzeResponse:
    try:
        result = await ai_service.analyze_data(
            DataAnalysisRequest(
                data=request.data,
                context=request.context,
                focus_areas=request.focus_areas,
            ),
        )
        return DataAnalyzeResponse(**result)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data analysis failed: {exc}",
        ) from exc


@router.post("/charts/suggest", response_model=ChartSuggestResponse)
async def suggest_charts(
    request: ChartSuggestRequest,
    ai_service: OpenAIService = Depends(get_openai_service),
) -> ChartSuggestResponse:
    del ai_service
    try:
        df = pd.DataFrame(request.data)
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
        suggestions: list[dict[str, Any]] = []

        if datetime_cols and numeric_cols:
            suggestions.append(
                {
                    "chart_type": "line",
                    "reason": "Time series data detected. Line chart best shows trends over time.",
                    "configuration": {
                        "x_axis": datetime_cols[0],
                        "y_axis": numeric_cols[0],
                        "time_unit": "auto",
                    },
                },
            )

        if categorical_cols and numeric_cols:
            suggestions.append(
                {
                    "chart_type": "bar",
                    "reason": "Categorical data with numeric values. Bar chart enables easy comparison.",
                    "configuration": {
                        "x_axis": categorical_cols[0],
                        "y_axis": numeric_cols[0],
                        "aggregation": "sum",
                    },
                },
            )

        if len(numeric_cols) >= 2:
            suggestions.append(
                {
                    "chart_type": "scatter",
                    "reason": "Two numeric variables detected. Scatter plot reveals correlations.",
                    "configuration": {
                        "x_axis": numeric_cols[0],
                        "y_axis": numeric_cols[1],
                        "color": categorical_cols[0] if categorical_cols else None,
                    },
                },
            )

        return ChartSuggestResponse(
            suggestions=suggestions,
            data_summary={
                "row_count": len(df),
                "column_count": len(df.columns),
                "numeric_columns": len(numeric_cols),
                "categorical_columns": len(categorical_cols),
                "datetime_columns": len(datetime_cols),
            },
            context=request.context,
            generated_at=datetime.now().isoformat(),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chart suggestion failed: {exc}",
        ) from exc


@router.get("/health")
async def ai_health_check() -> dict[str, str]:
    try:
        service = await get_openai_service()
        return {
            "status": "healthy",
            "service": "agentscope",
            "model": service.default_model,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as exc:
        return {
            "status": "unhealthy",
            "error": str(exc),
            "timestamp": datetime.now().isoformat(),
        }
