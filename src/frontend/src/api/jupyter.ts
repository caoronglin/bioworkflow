/**
 * Jupyter 内核 API 客户端
 */

import { apiClient } from './client'

export interface Kernel {
  kernel_id: string
  kernel_name: string
  created_at: string
  last_activity: string
  execution_count: number
}

export interface KernelStatus {
  kernel_id: string
  kernel_name: string
  status: string
  created_at: string
  last_activity: string
  execution_count: number
}

export interface ExecutionMessage {
  type: 'status' | 'stream' | 'display_data' | 'execute_result' | 'error'
  content: any
  execution_id: string
}

export const jupyterAPI = {
  // 内核管理
  async createKernel(kernelName: string = 'python3'): Promise<{ kernel_id: string; status: string }> {
    const response = await apiClient.post('/jupyter/kernels', { kernel_name: kernelName })
    return response.data
  },

  async shutdownKernel(kernelId: string): Promise<{ kernel_id: string; shutdown: boolean }> {
    const response = await apiClient.delete(`/jupyter/kernels/${kernelId}`)
    return response.data
  },

  async listKernels(): Promise<{ kernels: Kernel[] }> {
    const response = await apiClient.get('/jupyter/kernels')
    return response.data
  },

  async getKernelStatus(kernelId: string): Promise<KernelStatus> {
    const response = await apiClient.get(`/jupyter/kernels/${kernelId}/status`)
    return response.data
  },

  async interruptKernel(kernelId: string): Promise<{ kernel_id: string; interrupted: boolean }> {
    const response = await apiClient.post(`/jupyter/kernels/${kernelId}/interrupt`)
    return response.data
  },

  // WebSocket 连接
  createKernelWebSocket(kernelId: string): WebSocket {
    const wsUrl = apiClient.defaults.baseURL?.replace('http', 'ws') || ''
    return new WebSocket(`${wsUrl}/jupyter/ws/kernels/${kernelId}`)
  },

  createManagementWebSocket(): WebSocket {
    const wsUrl = apiClient.defaults.baseURL?.replace('http', 'ws') || ''
    return new WebSocket(`${wsUrl}/jupyter/ws/kernels`)
  },
}
