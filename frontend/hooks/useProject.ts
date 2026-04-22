"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";
import { Project } from "@/lib/types";

const MOCK_PROJECTS: Project[] = [
  { id: "proj1", name: "AdTicks.io", domain: "adticks.io", created_at: new Date().toISOString(), updated_at: new Date().toISOString(), gsc_connected: true, ads_connected: true },
  { id: "proj2", name: "Marketing Blog", domain: "blog.adticks.io", created_at: new Date().toISOString(), updated_at: new Date().toISOString(), gsc_connected: false, ads_connected: false },
];

export function useProjects() {
  return useQuery({
    queryKey: ["projects"],
    queryFn: () => api.projects.list().catch(() => MOCK_PROJECTS),
    initialData: MOCK_PROJECTS,
    staleTime: 5 * 60 * 1000,
  });
}

export function useProject(id: string) {
  return useQuery({
    queryKey: ["project", id],
    queryFn: () => api.projects.get(id).catch(() => MOCK_PROJECTS.find((p) => p.id === id)),
    staleTime: 5 * 60 * 1000,
  });
}

export function useActiveProject() {
  const [activeId, setActiveId] = useState("proj1");
  const { data: projects } = useProjects();
  const activeProject = projects?.find((p) => p.id === activeId) ?? projects?.[0];
  return { activeProject, activeId, setActiveId, projects: projects ?? [] };
}
