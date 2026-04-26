import type { MetadataRoute } from "next";

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = process.env.NEXT_PUBLIC_APP_URL || "https://adticks.com";

  const routes = [
    "",
    "/auth/login",
    "/auth/register",
    "/dashboard",
    "/dashboard/projects",
    "/dashboard/seo",
    "/dashboard/ai",
    "/dashboard/analytics",
  ];

  return routes.map((route) => ({
    url: `${baseUrl}${route}`,
    lastModified: new Date(),
    changeFrequency: route === "" ? "weekly" : "daily",
    priority: route === "" ? 1 : route.includes("dashboard") ? 0.8 : 0.6,
  }));
}
