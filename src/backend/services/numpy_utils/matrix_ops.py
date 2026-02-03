"""
矩阵操作模块
提供相关性分析、距离计算、降维等功能
"""

from dataclasses import dataclass
from typing import Literal, Optional, Tuple

import numpy as np
from loguru import logger


@dataclass
class PCAResult:
    """PCA 结果"""
    transformed: np.ndarray
    components: np.ndarray
    explained_variance: np.ndarray
    explained_variance_ratio: np.ndarray
    n_components: int


class MatrixOperations:
    """矩阵操作类"""

    @staticmethod
    def correlation_matrix(
        data: np.ndarray,
        method: Literal["pearson", "spearman"] = "pearson"
    ) -> np.ndarray:
        """
        计算相关系数矩阵
        
        Args:
            data: 输入数据 (样本 x 特征)
            method: 相关系数类型
            
        Returns:
            相关系数矩阵
        """
        if method == "pearson":
            return np.corrcoef(data, rowvar=False)
        
        elif method == "spearman":
            # Spearman 相关系数 = Pearson(rank(x), rank(y))
            from scipy import stats
            n_features = data.shape[1]
            corr = np.zeros((n_features, n_features))
            
            for i in range(n_features):
                for j in range(i, n_features):
                    rho, _ = stats.spearmanr(data[:, i], data[:, j])
                    corr[i, j] = rho
                    corr[j, i] = rho
            
            return corr
        
        else:
            raise ValueError(f"未知的相关系数方法: {method}")

    @staticmethod
    def distance_matrix(
        data: np.ndarray,
        metric: Literal["euclidean", "manhattan", "cosine", "correlation"] = "euclidean"
    ) -> np.ndarray:
        """
        计算距离矩阵
        
        Args:
            data: 输入数据 (样本 x 特征)
            metric: 距离度量方法
            
        Returns:
            距离矩阵
        """
        n_samples = data.shape[0]
        distances = np.zeros((n_samples, n_samples))

        if metric == "euclidean":
            for i in range(n_samples):
                for j in range(i + 1, n_samples):
                    d = np.sqrt(np.sum((data[i] - data[j]) ** 2))
                    distances[i, j] = d
                    distances[j, i] = d

        elif metric == "manhattan":
            for i in range(n_samples):
                for j in range(i + 1, n_samples):
                    d = np.sum(np.abs(data[i] - data[j]))
                    distances[i, j] = d
                    distances[j, i] = d

        elif metric == "cosine":
            # 余弦距离 = 1 - 余弦相似度
            norms = np.linalg.norm(data, axis=1, keepdims=True)
            norms[norms == 0] = 1
            normalized = data / norms
            similarity = normalized @ normalized.T
            distances = 1 - similarity

        elif metric == "correlation":
            # 相关距离 = 1 - 相关系数
            corr = np.corrcoef(data)
            distances = 1 - corr

        else:
            raise ValueError(f"未知的距离度量: {metric}")

        return distances

    @staticmethod
    def pca_transform(
        data: np.ndarray,
        n_components: Optional[int] = None,
        explained_variance_threshold: Optional[float] = None
    ) -> PCAResult:
        """
        PCA 降维
        
        Args:
            data: 输入数据 (样本 x 特征)
            n_components: 保留的主成分数量
            explained_variance_threshold: 保留的方差比例阈值
            
        Returns:
            PCA 结果
        """
        # 中心化
        mean = np.mean(data, axis=0)
        centered = data - mean
        
        # SVD 分解
        U, S, Vt = np.linalg.svd(centered, full_matrices=False)
        
        # 计算解释方差
        explained_variance = (S ** 2) / (data.shape[0] - 1)
        total_variance = np.sum(explained_variance)
        explained_variance_ratio = explained_variance / total_variance
        
        # 确定组件数量
        if n_components is None and explained_variance_threshold is not None:
            cumsum = np.cumsum(explained_variance_ratio)
            n_components = np.searchsorted(cumsum, explained_variance_threshold) + 1
        elif n_components is None:
            n_components = min(data.shape)
        
        n_components = min(n_components, len(S))
        
        # 投影
        components = Vt[:n_components]
        transformed = centered @ components.T
        
        return PCAResult(
            transformed=transformed,
            components=components,
            explained_variance=explained_variance[:n_components],
            explained_variance_ratio=explained_variance_ratio[:n_components],
            n_components=n_components,
        )

    @staticmethod
    def hierarchical_cluster(
        distance_matrix: np.ndarray,
        method: Literal["single", "complete", "average"] = "average"
    ) -> np.ndarray:
        """
        层次聚类
        
        Args:
            distance_matrix: 距离矩阵
            method: 连接方法
            
        Returns:
            聚类链接矩阵
        """
        n = distance_matrix.shape[0]
        clusters = [[i] for i in range(n)]
        linkage = []
        
        # 复制距离矩阵
        dist = distance_matrix.copy()
        np.fill_diagonal(dist, np.inf)
        
        cluster_id = n
        active = list(range(n))
        
        while len(active) > 1:
            # 找最小距离
            min_dist = np.inf
            merge_i, merge_j = 0, 1
            
            for i in range(len(active)):
                for j in range(i + 1, len(active)):
                    if dist[active[i], active[j]] < min_dist:
                        min_dist = dist[active[i], active[j]]
                        merge_i, merge_j = i, j
            
            ci, cj = active[merge_i], active[merge_j]
            
            # 记录链接
            linkage.append([ci, cj, min_dist, len(clusters[ci]) + len(clusters[cj])])
            
            # 合并聚类
            new_cluster = clusters[ci] + clusters[cj]
            clusters.append(new_cluster)
            
            # 更新距离
            new_dists = np.full(n + len(linkage), np.inf)
            for k in active:
                if k != ci and k != cj:
                    if method == "single":
                        new_dists[k] = min(dist[ci, k], dist[cj, k])
                    elif method == "complete":
                        new_dists[k] = max(dist[ci, k], dist[cj, k])
                    elif method == "average":
                        new_dists[k] = (dist[ci, k] * len(clusters[ci]) + 
                                       dist[cj, k] * len(clusters[cj])) / len(new_cluster)
            
            # 更新活跃聚类
            active.remove(ci)
            active.remove(cj)
            active.append(cluster_id)
            
            # 扩展距离矩阵
            dist = np.pad(dist, ((0, 1), (0, 1)), constant_values=np.inf)
            dist[cluster_id, :len(new_dists)] = new_dists
            dist[:len(new_dists), cluster_id] = new_dists
            
            cluster_id += 1
        
        return np.array(linkage)


# 便捷函数
def correlation_matrix(data: np.ndarray, method: str = "pearson") -> np.ndarray:
    """计算相关系数矩阵"""
    return MatrixOperations.correlation_matrix(data, method)


def distance_matrix(data: np.ndarray, metric: str = "euclidean") -> np.ndarray:
    """计算距离矩阵"""
    return MatrixOperations.distance_matrix(data, metric)


def pca_transform(data: np.ndarray, n_components: int = 2) -> PCAResult:
    """PCA 降维"""
    return MatrixOperations.pca_transform(data, n_components)
