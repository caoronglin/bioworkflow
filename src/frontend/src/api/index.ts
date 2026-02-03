import api from './client'

// Pipelines API
export const pipelinesAPI = {
  list: () => api.get('/pipelines'),
  get: (id: string) => api.get(`/pipelines/${id}`),
  create: (data: any) => api.post('/pipelines', data),
  update: (id: string, data: any) => api.put(`/pipelines/${id}`, data),
  delete: (id: string) => api.delete(`/pipelines/${id}`),
  execute: (id: string, params?: any) => api.post(`/pipelines/${id}/execute`, params),
  getExecutions: (id: string) => api.get(`/pipelines/${id}/executions`),
}

// Conda API
export const condaAPI = {
  listEnvironments: () => api.get('/conda/envs'),
  createEnvironment: (name: string, packages?: string[]) =>
    api.post('/conda/envs', { name, packages }),
  deleteEnvironment: (name: string) => api.delete(`/conda/envs/${name}`),
  listPackages: (env: string) => api.get(`/conda/envs/${env}/packages`),
  searchPackages: (query: string, channel?: string) =>
    api.get('/conda/packages', { params: { query, channel } }),
  installPackage: (name: string, version?: string, env?: string) =>
    api.post('/conda/packages/install', { package_name: name, version, environment: env }),
  uninstallPackage: (name: string, env?: string) =>
    api.post('/conda/packages/uninstall', { package_name: name, environment: env }),
  getChannels: () => api.get('/conda/channels'),
  configureChannels: (channels: string[]) =>
    api.post('/conda/channels', { channels }),
}

// Knowledge Base API
export const knowledgeAPI = {
  listDocuments: (skip?: number, limit?: number) =>
    api.get('/knowledge/documents', { params: { skip, limit } }),
  getDocument: (id: string) => api.get(`/knowledge/documents/${id}`),
  createDocument: (data: any) => api.post('/knowledge/documents', data),
  updateDocument: (id: string, data: any) => api.put(`/knowledge/documents/${id}`, data),
  deleteDocument: (id: string) => api.delete(`/knowledge/documents/${id}`),
  search: (query: string) => api.post('/knowledge/search', { query }),
  aiQuery: (question: string, useContext?: boolean) =>
    api.post('/knowledge/ai-query', { question, use_context: useContext }),
}

// MCP API
export const mcpAPI = {
  registerService: (data: any) => api.post('/mcp/services/register', data),
  listServices: () => api.get('/mcp/services'),
  getService: (id: string) => api.get(`/mcp/services/${id}`),
  unregisterService: (id: string) => api.delete(`/mcp/services/${id}`),
  createWorkflow: (data: any) => api.post('/mcp/workflows', data),
  getWorkflow: (id: string) => api.get(`/mcp/workflows/${id}`),
  executeWorkflow: (id: string, data?: any) =>
    api.post(`/mcp/workflows/${id}/execute`, data),
}
