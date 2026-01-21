import { useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import useWebSocket from 'react-use-websocket';
import type { Project } from 'shared/types';
import { projectsApi } from '@/lib/api';

export interface UseProjectsResult {
  projects: Project[];
  projectsById: Record<string, Project>;
  isLoading: boolean;
  isConnected: boolean;
  error: Error | null;
}

const getWsUrl = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}/api/ws`;
};

export function useProjects(): UseProjectsResult {
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.list(),
    // Polling removed in favor of WebSocket updates
    // refetchInterval: 5000, 
  });

  const { lastJsonMessage } = useWebSocket(getWsUrl(), {
    onOpen: () => console.log('WebSocket connected'),
    shouldReconnect: () => true,
    filter: (message) => {
      try {
        const data = JSON.parse(message.data);
        return data.type === 'project_created';
      } catch {
        return false;
      }
    }
  });

  // Listen for WS messages
  useMemo(() => {
    if (lastJsonMessage &&
      typeof lastJsonMessage === 'object' &&
      'type' in lastJsonMessage &&
      lastJsonMessage.type === 'project_created') {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    }
  }, [lastJsonMessage, queryClient]);

  const projectsById = useMemo(() => {
    if (!data) return {};
    return data.reduce((acc, project) => {
      acc[project.id] = project;
      return acc;
    }, {} as Record<string, Project>);
  }, [data]);

  const projects = useMemo(() => {
    return (data || []).sort(
      (a, b) =>
        new Date((b.created_at as unknown as string) || 0).getTime() -
        new Date((a.created_at as unknown as string) || 0).getTime()
    );
  }, [data]);

  return {
    projects,
    projectsById,
    isLoading,
    isConnected: !error,
    error: error as Error | null,
  };
}
