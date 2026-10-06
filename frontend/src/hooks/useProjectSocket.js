import { useWebSocket } from './useWebSocket'

export function useProjectSocket(projectId, onNotification) {
  const path = projectId ? `/ws/projects/${projectId}/` : null

  return useWebSocket(path, {
    enabled: !!projectId,
    onMessage: (data) => {
      if (onNotification) {
        onNotification(data)
      }
    },
  })
}

export function useTaskSocket(projectId, onTaskEvent) {
  const path = projectId ? `/ws/projects/${projectId}/tasks/` : null

  return useWebSocket(path, {
    enabled: !!projectId,
    onMessage: (data) => {
      if (onTaskEvent) {
        onTaskEvent(data)
      }
    },
  })
}
