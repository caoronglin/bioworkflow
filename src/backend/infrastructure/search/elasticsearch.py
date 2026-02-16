"""
Elasticsearch 搜索服务实现
"""

from typing import Any

from elasticsearch import AsyncElasticsearch
from loguru import logger

from backend.core.config import settings
from backend.core.interfaces import SearchService


class ElasticsearchService(SearchService):
    """Elasticsearch 搜索服务实现"""

    def __init__(self):
        self._client: AsyncElasticsearch | None = None

    async def _get_client(self) -> AsyncElasticsearch:
        """获取 ES 客户端（延迟初始化）"""
        if self._client is None:
            self._client = AsyncElasticsearch(
                hosts=[f"http://{settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}"],
            )
        return self._client

    async def search(
        self,
        query: str,
        index: str | None = None,
        filters: dict[str, Any] | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """执行搜索"""
        try:
            client = await self._get_client()

            search_body = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["*"],
                    }
                },
                "size": limit,
            }

            if filters:
                search_body["query"] = {
                    "bool": {
                        "must": search_body["query"],
                        "filter": [
                            {"term": {k: v}} for k, v in filters.items()
                        ],
                    }
                }

            response = await client.search(
                index=index or "_all",
                body=search_body,
            )

            results = []
            for hit in response["hits"]["hits"]:
                results.append({
                    "id": hit["_id"],
                    "index": hit["_index"],
                    "score": hit["_score"],
                    "source": hit["_source"],
                })

            return results

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    async def index_document(
        self,
        index: str,
        doc_id: str,
        document: dict[str, Any],
    ) -> bool:
        """索引文档"""
        try:
            client = await self._get_client()
            await client.index(index=index, id=doc_id, document=document)
            return True
        except Exception as e:
            logger.error(f"Index error: {e}")
            return False

    async def delete_document(self, index: str, doc_id: str) -> bool:
        """删除文档"""
        try:
            client = await self._get_client()
            await client.delete(index=index, id=doc_id)
            return True
        except Exception as e:
            logger.error(f"Delete error: {e}")
            return False

    async def create_index(self, index: str, mappings: dict | None = None) -> bool:
        """创建索引"""
        try:
            client = await self._get_client()
            body = {"mappings": mappings} if mappings else None
            await client.indices.create(index=index, body=body)
            return True
        except Exception as e:
            logger.error(f"Create index error: {e}")
            return False

    async def close(self) -> None:
        """关闭连接"""
        if self._client:
            await self._client.close()
            self._client = None


class InMemorySearchService(SearchService):
    """内存搜索服务（用于开发和测试）"""

    def __init__(self):
        self._documents: dict[str, dict[str, dict]] = {}

    async def search(
        self,
        query: str,
        index: str | None = None,
        filters: dict[str, Any] | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """简单文本搜索"""
        results = []
        indices = [index] if index else self._documents.keys()

        for idx in indices:
            if idx not in self._documents:
                continue

            for doc_id, doc in self._documents[idx].items():
                # 简单匹配
                doc_str = str(doc).lower()
                if query.lower() in doc_str:
                    if filters:
                        # 检查过滤器
                        match = all(
                            doc.get(k) == v for k, v in filters.items()
                        )
                        if not match:
                            continue

                    results.append({
                        "id": doc_id,
                        "index": idx,
                        "score": 1.0,
                        "source": doc,
                    })

                    if len(results) >= limit:
                        break

        return results

    async def index_document(
        self,
        index: str,
        doc_id: str,
        document: dict[str, Any],
    ) -> bool:
        """索引文档"""
        if index not in self._documents:
            self._documents[index] = {}
        self._documents[index][doc_id] = document
        return True
