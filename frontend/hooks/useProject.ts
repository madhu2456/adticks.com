"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";
import { Project } from "@/lib/types";

const MOCK_PROJECTS: Project[] = [];

export function useProjects() {
  return useQuery({
    queryKey: ["projects"],
    queryFn: () => api.projects.list().catch(() => []),
    staleTime: 5 * 60 * 1000,
  });
}

export function useProject(id: string | null) {
  return useQuery({
    queryKey: ["project", id],
    queryFn: () => (id ? api.projects.get(id).catch(() => null) : Promise.resolve(null)),
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { name: string; domain: string; industry?: string }) =>
      api.projects.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useUpdateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Project> }) =>
      api.projects.update(id, data),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      queryClient.invalidateQueries({ queryKey: ["project", updated.id] });
    },
  });
}

export function useActiveProject() {
  const [activeId, setActiveId] = useState<string | null>(null);
  const { data: projects = [] } = useProjects();
  
  // Default to first project if none active
  const activeProject = projects.find((p) => p.id === activeId) || projects[0] || null;
  const effectiveActiveId = activeId || activeProject?.id || null;

  return { 
    activeProject, 
    activeId: effectiveActiveId, 
    setActiveId, 
    projects 
  };
}
