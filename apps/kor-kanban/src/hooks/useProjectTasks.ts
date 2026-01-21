import { useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import useWebSocket from 'react-use-websocket';
import type { TaskStatus, TaskWithAttemptStatus } from 'shared/types';
import { tasksApi } from '@/lib/api';

export interface UseProjectTasksResult {
  tasks: TaskWithAttemptStatus[];
  tasksById: Record<string, TaskWithAttemptStatus>;
  tasksByStatus: Record<TaskStatus, TaskWithAttemptStatus[]>;
  isLoading: boolean;
  isConnected: boolean;
  error: string | null;
}

const getWsUrl = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}/api/ws`;
};

export const useProjectTasks = (projectId: string): UseProjectTasksResult => {
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ['tasks', projectId],
    queryFn: () => tasksApi.list(projectId),
    enabled: !!projectId,
    // Polling removed in favor of WebSocket updates
    // refetchInterval: 5000,
  });

  const { lastJsonMessage } = useWebSocket(getWsUrl(), {
    onOpen: () => console.log('WebSocket connected'),
    shouldReconnect: () => true,
    filter: (message) => {
      try {
        const data = JSON.parse(message.data);
        return ['task_created', 'task_updated', 'task_deleted'].includes(data.type);
      } catch {
        return false;
      }
    }
  });

  // Listen for WS messages
  useMemo(() => {
    if (lastJsonMessage &&
      typeof lastJsonMessage === 'object' &&
      'type' in lastJsonMessage) {

      const msgData = (lastJsonMessage as any).data;

      // Only invalidate if the task belongs to the current project
      if (msgData && msgData.project_id === projectId) {
        queryClient.invalidateQueries({ queryKey: ['tasks', projectId] });
      }
    }
  }, [lastJsonMessage, queryClient, projectId]);

  const { tasks, tasksById, tasksByStatus } = useMemo(() => {
    const taskList = (data as TaskWithAttemptStatus[]) || [];
    const merged: Record<string, TaskWithAttemptStatus> = {};
    const byStatus: Record<TaskStatus, TaskWithAttemptStatus[]> = {
      todo: [],
      inprogress: [],
      inreview: [],
      done: [],
      cancelled: [],
    };

    taskList.forEach((task) => {
      merged[task.id] = task;
      byStatus[task.status]?.push(task);
    });

    const sorted = Object.values(merged).sort(
      (a, b) =>
        new Date(b.created_at as string).getTime() -
        new Date(a.created_at as string).getTime()
    );

    (Object.values(byStatus) as TaskWithAttemptStatus[][]).forEach((list) => {
      list.sort(
        (a, b) =>
          new Date(b.created_at as string).getTime() -
          new Date(a.created_at as string).getTime()
      );
    });

    return { tasks: sorted, tasksById: merged, tasksByStatus: byStatus };
  }, [data]);

  return {
    tasks,
    tasksById,
    tasksByStatus,
    isLoading,
    isConnected: !error,
    error: error ? (error as Error).message : null,
  };
};
