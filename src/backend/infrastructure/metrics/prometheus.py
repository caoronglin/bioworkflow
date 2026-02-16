"""
Prometheus 指标收集实现

用于性能监控和告警
"""

from typing import Any

from prometheus_client import Counter, Gauge, Histogram, Info, generate_latest

from backend.core.interfaces import MetricsCollector


class PrometheusMetrics(MetricsCollector):
    """Prometheus 指标收集器"""

    def __init__(self):
        self._counters: dict[str, Counter] = {}
        self._histograms: dict[str, Histogram] = {}
        self._gauges: dict[str, Gauge] = {}
        self._infos: dict[str, Info] = {}

    def _get_or_create_counter(
        self,
        name: str,
        description: str = "",
        labels: list[str] | None = None,
    ) -> Counter:
        if name not in self._counters:
            self._counters[name] = Counter(
                name,
                description,
                labels or [],
            )
        return self._counters[name]

    def _get_or_create_histogram(
        self,
        name: str,
        description: str = "",
        labels: list[str] | None = None,
        buckets: list[float] | None = None,
    ) -> Histogram:
        if name not in self._histograms:
            kwargs = {
                "name": name,
                "documentation": description,
                "labelnames": labels or [],
            }
            if buckets:
                kwargs["buckets"] = buckets
            self._histograms[name] = Histogram(**kwargs)
        return self._histograms[name]

    def _get_or_create_gauge(
        self,
        name: str,
        description: str = "",
        labels: list[str] | None = None,
    ) -> Gauge:
        if name not in self._gauges:
            self._gauges[name] = Gauge(
                name,
                description,
                labels or [],
            )
        return self._gauges[name]

    def record_counter(
        self,
        name: str,
        value: int = 1,
        labels: dict[str, str] | None = None,
    ) -> None:
        """记录计数器"""
        counter = self._get_or_create_counter(name)
        if labels:
            counter.labels(**labels).inc(value)
        else:
            counter.inc(value)

    def record_histogram(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """记录直方图"""
        histogram = self._get_or_create_histogram(name)
        if labels:
            histogram.labels(**labels).observe(value)
        else:
            histogram.observe(value)

    def record_gauge(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """记录仪表盘"""
        gauge = self._get_or_create_gauge(name)
        if labels:
            gauge.labels(**labels).set(value)
        else:
            gauge.set(value)

    def get_metrics(self) -> bytes:
        """获取 Prometheus 格式的指标数据"""
        return generate_latest()


class NoOpMetricsCollector(MetricsCollector):
    """空实现（用于测试）"""

    def record_counter(
        self,
        name: str,
        value: int = 1,
        labels: dict[str, str] | None = None,
    ) -> None:
        pass

    def record_histogram(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        pass

    def record_gauge(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        pass
