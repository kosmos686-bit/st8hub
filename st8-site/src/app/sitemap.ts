import type { MetadataRoute } from "next";
import { solutions } from "@/lib/data/solutions";
import { cases } from "@/lib/data/cases";

const siteUrl = "https://st8-ai.ru";

export default function sitemap(): MetadataRoute.Sitemap {
  const staticRoutes = [
    "",
    "/solutions",
    "/cases",
    "/about",
    "/integrations",
    "/pricing",
    "/contact",
    "/blog",
  ].map((path) => ({
    url: `${siteUrl}${path}`,
    lastModified: new Date(),
  }));

  const solutionRoutes = solutions.map((s) => ({
    url: `${siteUrl}/solutions/${s.slug}`,
    lastModified: new Date(),
  }));

  const caseRoutes = cases.map((c) => ({
    url: `${siteUrl}/cases/${c.slug}`,
    lastModified: new Date(),
  }));

  return [...staticRoutes, ...solutionRoutes, ...caseRoutes];
}
