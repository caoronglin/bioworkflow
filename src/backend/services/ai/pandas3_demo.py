"""
Pandas 3.x Best Practices and Examples for BioWorkflow

This module demonstrates pandas 3.x features and best practices
for bioinformatics workflow data processing.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta


class Pandas3Demo:
    """
    Demonstrates pandas 3.x features for BioWorkflow
    """

    def __init__(self):
        """Initialize with pandas 3.x configuration"""
        # Enable Copy-on-Write (new in pandas 3.0)
        pd.set_option("mode.copy_on_write", True)

        # Enable PyArrow backend for better performance
        self.use_pyarrow = True

    def create_sample_pipeline_data(self, n: int = 1000) -> pd.DataFrame:
        """
        Create sample pipeline execution data

        Args:
            n: Number of records to generate

        Returns:
            DataFrame with pipeline execution data
        """
        np.random.seed(42)

        data = {
            "pipeline_id": range(1, n + 1),
            "name": [f"Pipeline_{i}" for i in range(1, n + 1)],
            "status": np.random.choice(
                ["success", "failed", "running", "pending"], n, p=[0.7, 0.15, 0.1, 0.05]
            ),
            "duration_seconds": np.random.exponential(300, n).astype(int),
            "cpu_percent": np.random.normal(50, 15, n).clip(0, 100),
            "memory_mb": np.random.normal(2048, 512, n).clip(512, 8192),
            "created_at": pd.date_range(
                start=datetime.now() - timedelta(days=30), periods=n, freq="min"
            ),
        }

        df = pd.DataFrame(data)

        # Convert to PyArrow types for better performance (pandas 3.x)
        if self.use_pyarrow:
            df = df.convert_dtypes(dtype_backend="pyarrow")

        return df

    def demonstrate_features(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Demonstrate pandas 3.x features

        Args:
            df: DataFrame to analyze

        Returns:
            Dictionary with analysis results
        """
        results = {
            "pandas_version": pd.__version__,
            "data_shape": df.shape,
            "memory_usage": {},
            "performance_metrics": {},
            "demonstrations": {},
        }

        # 1. Memory optimization with PyArrow
        results["memory_usage"]["with_pyarrow"] = df.memory_usage(deep=True).sum()

        # Compare with object dtype
        df_object = df.copy()
        for col in df_object.select_dtypes(include=["string"]).columns:
            df_object[col] = df_object[col].astype("object")
        results["memory_usage"]["without_pyarrow"] = df_object.memory_usage(deep=True).sum()

        # 2. String operations (optimized in pandas 3.x with PyArrow)
        if "name" in df.columns:
            results["demonstrations"]["string_ops"] = {
                "uppercase": df["name"].str.upper().head(3).tolist(),
                "contains": df["name"].str.contains("Pipeline_1").sum(),
            }

        # 3. Groupby operations
        if "status" in df.columns:
            status_stats = (
                df.groupby("status")
                .agg(
                    {
                        "duration_seconds": ["mean", "median", "count"],
                        "cpu_percent": "mean",
                        "memory_mb": "mean",
                    }
                )
                .round(2)
            )

            results["demonstrations"]["groupby"] = {
                "status_summary": status_stats.to_dict(),
                "total_groups": len(status_stats),
            }

        # 4. Query operations (Copy-on-Write safe)
        if "duration_seconds" in df.columns and "status" in df.columns:
            # This operation is safe with CoW enabled (pandas 3.x)
            long_running = df.query('duration_seconds > 600 and status == "success"')

            results["demonstrations"]["query"] = {
                "long_running_count": len(long_running),
                "avg_duration": long_running["duration_seconds"].mean()
                if len(long_running) > 0
                else 0,
            }

        # 5. Performance metrics
        import time

        start = time.time()
        _ = df.groupby("status")["duration_seconds"].mean()
        results["performance_metrics"]["groupby_ms"] = (time.time() - start) * 1000

        start = time.time()
        _ = df.query("duration_seconds > 100")
        results["performance_metrics"]["query_ms"] = (time.time() - start) * 1000

        return results


def demo_pandas3_features():
    """
    Main demonstration function

    Run this to see pandas 3.x features in action
    """
    print("🐼 Pandas 3.x Demo for BioWorkflow")
    print("=" * 50)
    print()

    # Initialize demo
    demo = Pandas3Demo()

    # Create sample data
    print("📊 Creating sample pipeline data...")
    df = demo.create_sample_pipeline_data(n=10000)
    print(f"✅ Created DataFrame with shape: {df.shape}")
    print()

    # Show data types
    print("📋 Data Types:")
    print(df.dtypes)
    print()

    # Demonstrate features
    print("🚀 Running feature demonstrations...")
    results = demo.demonstrate_features(df)

    # Print results
    print("\n" + "=" * 50)
    print("📈 RESULTS")
    print("=" * 50)

    print(f"\n🐼 Pandas Version: {results['pandas_version']}")
    print(f"📊 Data Shape: {results['data_shape']}")

    print("\n💾 Memory Usage:")
    for key, value in results["memory_usage"].items():
        print(f"  {key}: {value:,} bytes")

    if "string_ops" in results["demonstrations"]:
        print("\n📝 String Operations:")
        for key, value in results["demonstrations"]["string_ops"].items():
            print(f"  {key}: {value}")

    if "groupby" in results["demonstrations"]:
        print("\n📊 GroupBy Results:")
        print(f"  Total Groups: {results['demonstrations']['groupby']['total_groups']}")

    if "query" in results["demonstrations"]:
        print("\n🔍 Query Results:")
        for key, value in results["demonstrations"]["query"].items():
            print(f"  {key}: {value}")

    print("\n⚡ Performance Metrics:")
    for key, value in results["performance_metrics"].items():
        print(f"  {key}: {value:.2f} ms")

    print("\n" + "=" * 50)
    print("✅ Demo completed successfully!")
    print("=" * 50)

    return results


if __name__ == "__main__":
    demo_pandas3_features()
