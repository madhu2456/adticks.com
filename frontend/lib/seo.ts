/**
 * AdTicks — SEO Utilities for meta tags, structured data, and OG tags
 */

import { Metadata } from "next";

export interface SEOMetadata {
  title: string;
  description: string;
  keywords?: string[];
  ogTitle?: string;
  ogDescription?: string;
  ogImage?: string;
  ogType?: string;
  twitterCard?: "summary" | "summary_large_image" | "app" | "player";
  twitterTitle?: string;
  twitterDescription?: string;
  twitterImage?: string;
  canonicalUrl?: string;
  robots?: string;
  language?: string;
}

export function generateSEOMetadata(config: SEOMetadata): Metadata {
  return {
    title: config.title,
    description: config.description,
    keywords: config.keywords,
    openGraph: {
      title: config.ogTitle || config.title,
      description: config.ogDescription || config.description,
      images: config.ogImage ? [{ url: config.ogImage }] : [],
      type: config.ogType as any || "website",
    },
    twitter: {
      card: config.twitterCard || "summary_large_image",
      title: config.twitterTitle || config.title,
      description: config.twitterDescription || config.description,
      images: config.twitterImage ? [config.twitterImage] : [],
    },
    robots: config.robots || "index, follow",
    alternates: config.canonicalUrl ? { canonical: config.canonicalUrl } : undefined,
  };
}

/**
 * Generate JSON-LD Schema markup
 */
export interface SchemaMarkup {
  "@context": string;
  "@type": string;
  [key: string]: any;
}

export function generateOrganizationSchema(config: {
  name: string;
  url: string;
  logo?: string;
  description?: string;
  sameAs?: string[];
}): SchemaMarkup {
  return {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: config.name,
    url: config.url,
    ...(config.logo && { logo: config.logo }),
    ...(config.description && { description: config.description }),
    ...(config.sameAs && { sameAs: config.sameAs }),
  };
}

export function generateArticleSchema(config: {
  headline: string;
  description: string;
  image?: string;
  author?: string;
  datePublished?: string;
  dateModified?: string;
  url?: string;
}): SchemaMarkup {
  return {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: config.headline,
    description: config.description,
    ...(config.image && { image: config.image }),
    ...(config.author && { author: { "@type": "Person", name: config.author } }),
    ...(config.datePublished && { datePublished: config.datePublished }),
    ...(config.dateModified && { dateModified: config.dateModified }),
    ...(config.url && { url: config.url }),
  };
}

export function generateBreadcrumbSchema(items: Array<{ name: string; url?: string }>): SchemaMarkup {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((item, index) => ({
      "@type": "ListItem",
      position: index + 1,
      name: item.name,
      ...(item.url && { item: item.url }),
    })),
  };
}

export function generateProductSchema(config: {
  name: string;
  description?: string;
  image?: string;
  price?: number;
  currency?: string;
  rating?: number;
  reviewCount?: number;
  url?: string;
}): SchemaMarkup {
  return {
    "@context": "https://schema.org",
    "@type": "Product",
    name: config.name,
    ...(config.description && { description: config.description }),
    ...(config.image && { image: config.image }),
    ...(config.price && {
      offers: {
        "@type": "Offer",
        price: config.price,
        priceCurrency: config.currency || "USD",
      },
    }),
    ...(config.rating && {
      aggregateRating: {
        "@type": "AggregateRating",
        ratingValue: config.rating,
        reviewCount: config.reviewCount || 0,
      },
    }),
    ...(config.url && { url: config.url }),
  };
}

export function generateFAQSchema(items: Array<{ question: string; answer: string }>): SchemaMarkup {
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: items.map((item) => ({
      "@type": "Question",
      name: item.question,
      acceptedAnswer: {
        "@type": "Answer",
        text: item.answer,
      },
    })),
  };
}

export function generateLocalBusinessSchema(config: {
  name: string;
  type: string;
  address?: {
    streetAddress: string;
    addressLocality: string;
    addressRegion: string;
    postalCode: string;
  };
  telephone?: string;
  url?: string;
  image?: string;
}): SchemaMarkup {
  return {
    "@context": "https://schema.org",
    "@type": config.type,
    name: config.name,
    ...(config.address && { address: config.address }),
    ...(config.telephone && { telephone: config.telephone }),
    ...(config.url && { url: config.url }),
    ...(config.image && { image: config.image }),
  };
}
