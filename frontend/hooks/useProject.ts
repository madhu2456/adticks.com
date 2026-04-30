"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";
import { Project } from "@/lib/types";
import { create } from 'zustand';

const MOCK_PROJECTS: Project[] = [];

interface ProjectStore {
  activeId: string | null;
  setActiveId: (id: string | null) => void;
}

export const useProjectStore = create<ProjectStore>((set) => ({
  activeId: null,
  setActiveId: (id) => set({ activeId: id }),
}));

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
  const setActiveId = useProjectStore((state) => state.setActiveId);
  return useMutation({
    mutationFn: (data: { brand_name: string; domain: string; industry?: string }) =>
      api.projects.create(data),
    onSuccess: (newProject) => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      if (newProject?.id) {
        setActiveId(newProject.id);
      }
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
  const activeId = useProjectStore((state) => state.activeId);
  const setActiveId = useProjectStore((state) => state.setActiveId);
  const query = useProjects();
  const projects = Array.isArray(query.data) ? query.data : [];
  
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
