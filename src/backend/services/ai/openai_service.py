"""
OpenAI Service for BioWorkflow

Provides AI-powered features including:
- Natural language to SQL query generation
- Data analysis and insights
- Code generation and assistance
- Chat completion with streaming support
"""

import os
import json
from typing import List, Dict, Any, AsyncGenerator, Optional
from datetime import datetime
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
import pandas as pd


class ChatMessage(BaseModel):
    """Chat message model"""

    role: str = Field(..., description="Message role: system, user, or assistant")
    content: str = Field(..., description="Message content")


class SQLGenerationRequest(BaseModel):
    """SQL generation request"""

    natural_query: str = Field(..., description="Natural language query")
    schema: Dict[str, Any] = Field(..., description="Database schema information")
    context: Optional[str] = Field(None, description="Additional context")


class DataAnalysisRequest(BaseModel):
    """Data analysis request"""

    data: List[Dict[str, Any]] = Field(..., description="Data to analyze")
    context: str = Field(..., description="Analysis context")
    focus_areas: Optional[List[str]] = Field(None, description="Specific areas to focus on")


class ChartSuggestion(BaseModel):
    """Chart suggestion model"""

    chart_type: str = Field(..., description="Suggested chart type")
    reason: str = Field(..., description="Why this chart type is suggested")
    configuration: Dict[str, Any] = Field(..., description="Chart configuration")


class OpenAIService:
    """
    OpenAI Service for BioWorkflow

    Provides AI-powered features for the platform.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        """
        Initialize OpenAI Service

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            base_url: Custom base URL for OpenAI API
            default_model: Default model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self.default_model = default_model
        self.temperature = temperature
        self.max_tokens = max_tokens

        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Please set OPENAI_API_KEY environment variable."
            )

        # Initialize AsyncOpenAI client
        self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        tools: Optional[List[Dict]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Chat completion with streaming support

        Args:
            messages: List of chat messages
            model: Model to use (defaults to self.default_model)
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            stream: Whether to stream response
            tools: Tools for function calling

        Yields:
            Response chunks (if streaming) or full response
        """
        response = await self.client.chat.completions.create(
            model=model or self.default_model,
            messages=messages,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
            stream=stream,
            tools=tools,
        )

        if stream:
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        else:
            yield response.choices[0].message.content

    async def generate_sql(self, request: SQLGenerationRequest) -> Dict[str, Any]:
        """
        Generate SQL from natural language query

        Args:
            request: SQL generation request with natural query and schema

        Returns:
            Dictionary with generated SQL and metadata
        """
        prompt = f"""You are a SQL expert. Convert the following natural language query into SQL.

Database Schema:
{json.dumps(request.schema, indent=2, ensure_ascii=False)}

Natural Language Query:
{request.natural_query}

{f"Additional Context: {request.context}" if request.context else ""}

Requirements:
1. Generate syntactically correct SQL
2. Use appropriate JOINs when needed
3. Include proper WHERE clauses
4. Use parameterized queries (use placeholders like %s or :param)
5. Optimize for readability and performance
6. Add comments for complex logic

Return ONLY the SQL query without any explanation or markdown formatting."""

        response = ""
        async for chunk in self.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,  # Low temperature for consistency
        ):
            response += chunk

        sql = response.strip()

        # Remove markdown code blocks if present
        if sql.startswith("```sql"):
            sql = sql[6:]
        if sql.startswith("```"):
            sql = sql[3:]
        if sql.endswith("```"):
            sql = sql[:-3]

        sql = sql.strip()

        return {
            "sql": sql,
            "natural_query": request.natural_query,
            "schema_used": request.schema,
            "confidence": "high" if sql else "low",
            "generated_at": datetime.now().isoformat(),
        }

    async def analyze_data(self, request: DataAnalysisRequest) -> Dict[str, Any]:
        """
        Analyze data and generate insights

        Args:
            request: Data analysis request with data and context

        Returns:
            Dictionary with analysis results and insights
        """
        # Convert data to DataFrame for analysis
        df = pd.DataFrame(request.data)

        # Generate basic statistics
        stats = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "dtypes": df.dtypes.to_dict(),
            "memory_usage": df.memory_usage(deep=True).sum(),
        }

        # Generate description for numeric columns
        if df.select_dtypes(include=["number"]).columns.any():
            numeric_desc = df.describe().to_dict()
            stats["numeric_summary"] = numeric_desc

        # Prepare data sample for AI analysis
        data_sample = df.head(50).to_dict(orient="records")

        prompt = f"""You are a data analysis expert. Analyze the following data and provide insights.

Context: {request.context}

Data Statistics:
- Total Rows: {stats["row_count"]}
- Total Columns: {stats["column_count"]}
- Columns: {", ".join(stats["columns"])}

Data Sample (first 50 rows):
{json.dumps(data_sample, indent=2, ensure_ascii=False)}

{f"Focus Areas: {', '.join(request.focus_areas)}" if request.focus_areas else ""}

Please provide a comprehensive analysis including:

1. **Key Metrics**: Most important numbers and what they indicate
2. **Anomaly Detection**: Any unusual patterns, outliers, or unexpected values
3. **Trend Analysis**: Patterns over time (if temporal data present)
4. **Recommendations**: Actionable suggestions based on the data

Format your response in clear sections with headers. Be specific and reference actual values from the data."""

        response = ""
        async for chunk in self.chat_completion(
            messages=[{"role": "user", "content": prompt}], temperature=0.7
        ):
            response += chunk

        # Extract chart suggestions if applicable
        chart_suggestions = await self._suggest_charts(df, request.context)

        return {
            "analysis": response,
            "statistics": stats,
            "chart_suggestions": chart_suggestions,
            "data_sample": data_sample,
            "generated_at": datetime.now().isoformat(),
            "focus_areas": request.focus_areas or [],
        }

    async def _suggest_charts(self, df: pd.DataFrame, context: str) -> List[ChartSuggestion]:
        """Suggest appropriate chart types for the data"""
        suggestions = []

        # Analyze data types
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        datetime_cols = df.select_dtypes(include=["datetime"]).columns.tolist()

        # Suggest line chart for time series
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
                )
            )

        # Suggest bar chart for categorical comparison
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
                )
            )

        # Suggest pie chart for distribution
        if len(categorical_cols) > 0 and len(numeric_cols) > 0:
            suggestions.append(
                ChartSuggestion(
                    chart_type="pie",
                    reason="Shows distribution of categories as proportions of a whole.",
                    configuration={"category": categorical_cols[0], "value": numeric_cols[0]},
                )
            )

        # Suggest scatter plot for correlation
        if len(numeric_cols) >= 2:
            suggestions.append(
                ChartSuggestion(
                    chart_type="scatter",
                    reason="Two numeric variables detected. Scatter plot reveals correlations and distributions.",
                    configuration={
                        "x_axis": numeric_cols[0],
                        "y_axis": numeric_cols[1],
                        "size": None,
                        "color": categorical_cols[0] if categorical_cols else None,
                    },
                )
            )

        return suggestions


# Singleton instance
_openai_service: Optional[OpenAIService] = None


async def get_openai_service() -> OpenAIService:
    """Get or create OpenAI service singleton"""
    global _openai_service
    if _openai_service is None:
        _openai_service = OpenAIService()
    return _openai_service
