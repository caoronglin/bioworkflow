"""
AI API Routes

Provides endpoints for AI-powered features:
- Chat completion
- SQL generation from natural language
- Data analysis and insights
- Chart suggestions
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.services.ai.openai_service import (
    get_openai_service,
    OpenAIService,
    SQLGenerationRequest,
    DataAnalysisRequest,
    ChatMessage,
)

router = APIRouter(prefix="/ai", tags=["ai"])


# Request/Response Models
class ChatRequest(BaseModel):
    """Chat completion request"""

    messages: List[ChatMessage] = Field(..., description="Chat messages")
    model: str = Field(default="gpt-4", description="Model to use")
    temperature: float = Field(default=0.7, ge=0, le=2, description="Sampling temperature")
    stream: bool = Field(default=False, description="Stream response")

    class Config:
        json_schema_extra = {
            "example": {
                "messages": [{"role": "user", "content": "Hello, how are you?"}],
                "model": "gpt-4",
                "temperature": 0.7,
                "stream": False,
            }
        }


class ChatResponse(BaseModel):
    """Chat completion response"""

    content: str = Field(..., description="Response content")
    model: str = Field(..., description="Model used")
    usage: Optional[Dict[str, int]] = Field(None, description="Token usage")
    created_at: str = Field(..., description="Response timestamp")


class SQLGenerateRequest(BaseModel):
    """SQL generation request"""

    natural_query: str = Field(..., description="Natural language query", min_length=1)
    schema: Dict[str, Any] = Field(..., description="Database schema")
    context: Optional[str] = Field(None, description="Additional context")

    class Config:
        json_schema_extra = {
            "example": {
                "natural_query": "Find all pipelines created in the last 7 days",
                "schema": {
                    "pipelines": {
                        "columns": ["id", "name", "created_at", "status"],
                        "types": ["integer", "string", "datetime", "string"],
                    }
                },
                "context": "Looking for recently created pipelines",
            }
        }


class SQLGenerateResponse(BaseModel):
    """SQL generation response"""

    sql: str = Field(..., description="Generated SQL query")
    natural_query: str = Field(..., description="Original natural language query")
    confidence: str = Field(..., description="Confidence level (high/medium/low)")
    schema_used: Dict[str, Any] = Field(..., description="Schema used for generation")
    generated_at: str = Field(..., description="Generation timestamp")


class DataAnalyzeRequest(BaseModel):
    """Data analysis request"""

    data: List[Dict[str, Any]] = Field(..., description="Data to analyze", min_items=1)
    context: str = Field(..., description="Analysis context", min_length=1)
    focus_areas: Optional[List[str]] = Field(None, description="Specific areas to focus on")

    class Config:
        json_schema_extra = {
            "example": {
                "data": [
                    {"pipeline_id": 1, "status": "success", "duration": 120},
                    {"pipeline_id": 2, "status": "failed", "duration": 45},
                ],
                "context": "Pipeline execution performance analysis",
                "focus_areas": ["performance", "failure_patterns"],
            }
        }


class DataAnalyzeResponse(BaseModel):
    """Data analysis response"""

    analysis: str = Field(..., description="AI-generated analysis")
    statistics: Dict[str, Any] = Field(..., description="Data statistics")
    chart_suggestions: List[Dict[str, Any]] = Field(..., description="Suggested chart types")
    data_sample: List[Dict[str, Any]] = Field(..., description="Sample of analyzed data")
    generated_at: str = Field(..., description="Analysis timestamp")
    focus_areas: List[str] = Field(default=[], description="Areas focused on")


class ChartSuggestRequest(BaseModel):
    """Chart suggestion request"""

    data: List[Dict[str, Any]] = Field(..., description="Data to visualize", min_items=1)
    context: str = Field(..., description="Visualization context")

    class Config:
        json_schema_extra = {
            "example": {
                "data": [
                    {"date": "2024-01-01", "value": 100},
                    {"date": "2024-01-02", "value": 150},
                ],
                "context": "Time series trend visualization",
            }
        }


class ChartSuggestResponse(BaseModel):
    """Chart suggestion response"""

    suggestions: List[Dict[str, Any]] = Field(..., description="Chart suggestions")
    data_summary: Dict[str, Any] = Field(..., description="Summary of analyzed data")
    context: str = Field(..., description="Original context")
    generated_at: str = Field(..., description="Generation timestamp")


# API Endpoints


@router.post("/chat", response_model=ChatResponse)
async def chat_completion(
    request: ChatRequest, ai_service: OpenAIService = Depends(get_openai_service)
) -> ChatResponse:
    """
    Chat completion endpoint

    Supports both streaming and non-streaming responses.
    For streaming, use the /chat/stream endpoint.
    """
    try:
        if request.stream:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Streaming not supported on this endpoint. Use /chat/stream",
            )

        response_content = ""
        async for chunk in ai_service.chat_completion(
            messages=[{"role": m.role, "content": m.content} for m in request.messages],
            model=request.model,
            temperature=request.temperature,
            stream=False,
        ):
            response_content += chunk

        return ChatResponse(
            content=response_content, model=request.model, created_at=datetime.now().isoformat()
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat completion failed: {str(e)}",
        )


@router.post("/chat/stream")
async def chat_completion_stream(
    request: ChatRequest, ai_service: OpenAIService = Depends(get_openai_service)
):
    """
    Streaming chat completion endpoint

    Returns a stream of text chunks for real-time chat experience.
    """
    from fastapi.responses import StreamingResponse

    async def generate_stream():
        try:
            async for chunk in ai_service.chat_completion(
                messages=[{"role": m.role, "content": m.content} for m in request.messages],
                model=request.model,
                temperature=request.temperature,
                stream=True,
            ):
                yield f"data: {json.dumps({'content': chunk})}\n\n"

            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate_stream(), media_type="text/event-stream")


@router.post("/sql/generate", response_model=SQLGenerateResponse)
async def generate_sql(
    request: SQLGenerateRequest, ai_service: OpenAIService = Depends(get_openai_service)
) -> SQLGenerateResponse:
    """
    Generate SQL from natural language query

    Takes a natural language query and database schema,
    returns a generated SQL query.
    """
    try:
        result = await ai_service.generate_sql(
            SQLGenerationRequest(
                natural_query=request.natural_query, schema=request.schema, context=request.context
            )
        )

        return SQLGenerateResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SQL generation failed: {str(e)}",
        )


@router.post("/data/analyze", response_model=DataAnalyzeResponse)
async def analyze_data(
    request: DataAnalyzeRequest, ai_service: OpenAIService = Depends(get_openai_service)
) -> DataAnalyzeResponse:
    """
    Analyze data and generate insights

    Takes data and context, returns AI-generated analysis
    with statistics, chart suggestions, and recommendations.
    """
    try:
        result = await ai_service.analyze_data(
            DataAnalysisRequest(
                data=request.data, context=request.context, focus_areas=request.focus_areas
            )
        )

        return DataAnalyzeResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data analysis failed: {str(e)}",
        )


@router.post("/charts/suggest", response_model=ChartSuggestResponse)
async def suggest_charts(
    request: ChartSuggestRequest, ai_service: OpenAIService = Depends(get_openai_service)
) -> ChartSuggestResponse:
    """
    Suggest appropriate chart types for data

    Analyzes data structure and suggests best visualization types.
    """
    try:
        # Create a small DataFrame to analyze
        df = pd.DataFrame(request.data)

        # Get suggestions from AI service
        # This is a simplified version - in production,
        # you'd call a specific method on the service
        suggestions = []

        # Analyze data types
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        datetime_cols = df.select_dtypes(include=["datetime"]).columns.tolist()

        # Generate suggestions based on data types
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
                }
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
                }
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
                }
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

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chart suggestion failed: {str(e)}",
        )


# Health check endpoint
@router.get("/health")
async def ai_health_check():
    """Check AI service health"""
    try:
        # Try to initialize the service
        service = await get_openai_service()
        return {
            "status": "healthy",
            "service": "openai",
            "model": service.default_model,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e), "timestamp": datetime.now().isoformat()}
