import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import api from './api'

export function useDrawingsQuery() {
  return useQuery({
    queryKey: ['drawings'],
    queryFn: async () => (await api.get('/drawings')).data,
  })
}

export function useProjectsQuery() {
  return useQuery({
    queryKey: ['projects'],
    queryFn: async () => (await api.get('/projects')).data,
  })
}

export function useApprovalsQuery() {
  return useQuery({
    queryKey: ['approvals', 'pending'],
    queryFn: async () => (await api.get('/approvals/pending')).data,
  })
}

export function useDashboardQuery() {
  return useQuery({
    queryKey: ['stats'],
    queryFn: async () => (await api.get('/stats')).data,
  })
}

export function useCreateDrawing() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload) => (await api.post('/drawings', payload)).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['drawings'] }),
  })
}

export function useApproveVersion() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ versionId, comment }) =>
      (await api.post('/versions/' + versionId + '/approve', { comment })).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['approvals'] }),
  })
}

export function useRejectVersion() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ versionId, comment }) =>
      (await api.post('/versions/' + versionId + '/reject', { comment })).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['approvals'] }),
  })
}
