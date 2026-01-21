import { useCallback, useEffect, useMemo, useState } from 'react';
import type { TaskStatus, TaskWithAttemptStatus } from 'shared/types';

export interface UseProjectTasksResult {
  tasks: TaskWithAttemptStatus[];
  tasksById: Record<string, TaskWithAttemptStatus>;
  tasksByStatus: Record<TaskStatus, TaskWithAttemptStatus[]>;
  isLoading: boolean;
  isConnected: boolean;
  error: string | null;
}

export const useProjectTasks = (projectId: string): UseProjectTasksResult => {
  const [tasksById, setTasksById] = useState<Record<string, TaskWithAttemptStatus>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTasks = useCallback(async () => {
    try {
      // We assume GET /api/tasks returns access to all tasks or filtered by project
      const response = await fetch(`/api/tasks?project_id=${encodeURIComponent(projectId)}`);
      if (!response.ok) throw new Error('Failed to fetch tasks');
      const json = await response.json();

      const map: Record<string, TaskWithAttemptStatus> = {};
      if (json.success && Array.isArray(json.data)) {
        json.data.forEach((t: TaskWithAttemptStatus) => {
          map[t.id] = t;
        });
      }
      setTasksById(map);
      setIsLoading(false);
    } catch (err: any) {
      console.error(err);
      setError(err.message);
      setIsLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    if (projectId) {
      fetchTasks();
      const interval = setInterval(fetchTasks, 5000); // Poll every 5s
      return () => clearInterval(interval);
    }
  }, [projectId, fetchTasks]);

  const { tasks, tasksByStatus } = useMemo(() => {
    const merged: Record<string, TaskWithAttemptStatus> = { ...tasksById };
    const byStatus: Record<TaskStatus, TaskWithAttemptStatus[]> = {
      todo: [],
      inprogress: [],
      inreview: [],
      done: [],
      cancelled: [],
    };

    Object.values(merged).forEach((task) => {
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
  }, [tasksById]);

  return {
    tasks,
    tasksById,
    tasksByStatus,
    isLoading,
    isConnected: true, // Mocked
    error,
  };
};
