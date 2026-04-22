"""
AI prompt generator for AdTicks.
Generates 100-300 prompts across brand awareness, comparison, problem-solving,
recommendation, and trust signal categories using OpenAI.
"""

import logging
import json
import re
from typing import List, Dict, Any, Optional
import uuid

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

PROMPT_CATEGORIES = [
    "brand_awareness",
    "comparison",
    "problem_solving",
    "recommendations",
    "trust_signals",
]


def _build_fallback_prompts(
    brand_name: str,
    domain: str,
    industry: str,
    competitors: List[str],
) -> List[Dict[str, Any]]:
    """
    Generate a comprehensive set of prompts using templates when OpenAI is unavailable.

    Args:
        brand_name: The brand name
        domain: Brand domain
        industry: Industry category
        competitors: List of competitor names

    Returns:
        List of prompt dicts
    """
    prompts = []

    # Brand awareness
    brand_awareness_templates = [
        f"What is {brand_name}?",
        f"Tell me about {brand_name}",
        f"Who is {brand_name}?",
        f"What does {brand_name} do?",
        f"What products does {brand_name} offer?",
        f"Is {brand_name} a good company?",
        f"What is {brand_name} known for?",
        f"How long has {brand_name} been in business?",
        f"Where is {brand_name} based?",
        f"What are the main features of {brand_name}?",
        f"Who uses {brand_name}?",
        f"What is the history of {brand_name}?",
        f"How big is {brand_name} as a company?",
        f"What sets {brand_name} apart from competitors?",
        f"What is {brand_name}'s mission?",
    ]
    for t in brand_awareness_templates:
        prompts.append({"text": t, "category": "brand_awareness"})

    # Comparison prompts
    for comp in competitors[:4]:
        comparison_templates = [
            f"Compare {brand_name} vs {comp}",
            f"{brand_name} vs {comp}: which is better?",
            f"What are the differences between {brand_name} and {comp}?",
            f"Should I use {brand_name} or {comp}?",
            f"Best alternatives to {comp}",
            f"Why choose {brand_name} over {comp}?",
            f"How does {brand_name} compare to {comp} in terms of pricing?",
            f"Is {brand_name} better than {comp} for {industry}?",
        ]
        for t in comparison_templates:
            prompts.append({"text": t, "category": "comparison"})

    # Problem solving
    use_cases = ["small businesses", "enterprise teams", "startups", "marketing teams", "remote teams", "agencies"]
    problems = [
        f"How to improve {industry.lower()} performance",
        f"Best tools for {industry.lower()} automation",
        f"How to increase ROI in {industry.lower()}",
        f"How to scale {industry.lower()} operations",
        f"How to reduce costs in {industry.lower()}",
    ]
    for uc in use_cases[:4]:
        prompts.append({"text": f"Best {industry.lower()} tool for {uc}", "category": "problem_solving"})
    for p in problems:
        prompts.append({"text": p, "category": "problem_solving"})

    problem_solving_extra = [
        f"What software should I use for {industry.lower()}?",
        f"How to automate {industry.lower()} workflows",
        f"How to get started with {industry.lower()}",
        f"Common challenges in {industry.lower()} and how to solve them",
        f"What is the best platform for {industry.lower()}?",
        f"How do I choose a {industry.lower()} solution?",
        f"Top {industry.lower()} strategies for 2024",
        f"How to measure success in {industry.lower()}",
    ]
    for t in problem_solving_extra:
        prompts.append({"text": t, "category": "problem_solving"})

    # Recommendations
    product_categories = [industry, f"{industry} software", f"{industry} platform", f"{industry} tool"]
    rec_use_cases = ["lead generation", "customer acquisition", "brand growth", "performance tracking", "reporting"]
    for pc in product_categories[:2]:
        for uc in rec_use_cases[:3]:
            prompts.append({"text": f"What {pc} should I use for {uc}?", "category": "recommendations"})
    rec_extra = [
        f"Recommend a {industry.lower()} platform for beginners",
        f"Best {industry.lower()} tools recommended by experts",
        f"Top-rated {industry.lower()} solutions for 2024",
        f"What {industry.lower()} tool do professionals use?",
        f"Most popular {industry.lower()} platforms",
    ]
    for t in rec_extra:
        prompts.append({"text": t, "category": "recommendations"})

    # Trust signals
    trust_templates = [
        f"Is {brand_name} trustworthy?",
        f"Reviews of {brand_name}",
        f"{brand_name} customer reviews",
        f"Is {brand_name} legitimate?",
        f"Is {brand_name} worth it?",
        f"{brand_name} pros and cons",
        f"What do users say about {brand_name}?",
        f"Is {brand_name} safe to use?",
        f"{brand_name} rating and reviews",
        f"Has anyone had problems with {brand_name}?",
        f"What are the negative reviews of {brand_name}?",
        f"Is {brand_name} reliable for businesses?",
        f"{brand_name} customer support quality",
        f"Does {brand_name} have a money-back guarantee?",
        f"Is {brand_name} GDPR compliant?",
    ]
    for t in trust_templates:
        prompts.append({"text": t, "category": "trust_signals"})

    return prompts


async def generate_prompts(
    brand_name: str,
    domain: str,
    industry: str,
    competitors: Optional[List[str]] = None,
    target_count: int = 150,
) -> List[Dict[str, Any]]:
    """
    Generate 100-300 diverse prompts across all categories for AI visibility testing.

    Args:
        brand_name: The brand name to generate prompts for
        domain: Brand's domain name
        industry: Industry category
        competitors: List of competitor brand names
        target_count: Target number of prompts to generate

    Returns:
        List of Prompt dicts with: id, text, category
    """
    logger.info(f"Generating prompts for brand={brand_name} industry={industry} competitors={competitors}")
    competitors = competitors or []
    prompts_raw: List[Dict[str, Any]] = []

    if OPENAI_AVAILABLE:
        try:
            client = AsyncOpenAI()
            comp_str = ", ".join(competitors[:5]) if competitors else "major industry players"
            prompt = f"""You are an AI visibility expert. Generate {target_count} diverse prompts that users might type into AI assistants (ChatGPT, Claude, Gemini) related to:

Brand: {brand_name}
Domain: {domain}
Industry: {industry}
Competitors: {comp_str}

Generate prompts across these 5 categories (distribute roughly equally):
1. brand_awareness: Direct questions about {brand_name} ("What is {brand_name}?", "Tell me about {brand_name}")
2. comparison: Comparing {brand_name} to competitors ("Compare {brand_name} vs [competitor]", "Best alternatives to [competitor]")
3. problem_solving: Industry problem/solution queries ("Best tool for [use case]", "How to [solve problem]")
4. recommendations: Product recommendation queries ("What {industry} tool should I use for [use case]?")
5. trust_signals: Trust and review queries ("Is {brand_name} trustworthy?", "Reviews of {brand_name}")

Make prompts sound natural and conversational, as real users would type them.
Include a mix of simple and complex prompts.

Return a JSON array of objects with:
- text: the prompt string
- category: one of the 5 categories above

Return only the JSON array, no extra text."""

            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=6000,
            )
            raw = response.choices[0].message.content.strip()
            raw = re.sub(r"^```json\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
            parsed = json.loads(raw)

            for item in parsed:
                cat = item.get("category", "brand_awareness")
                if cat not in PROMPT_CATEGORIES:
                    cat = "brand_awareness"
                prompts_raw.append({
                    "text": str(item.get("text", "")),
                    "category": cat,
                })

            logger.info(f"OpenAI generated {len(prompts_raw)} prompts")
        except Exception as e:
            logger.warning(f"OpenAI prompt generation failed: {e}. Using fallback.")
            prompts_raw = []

    if not prompts_raw:
        prompts_raw = _build_fallback_prompts(brand_name, domain, industry, competitors)

    # Assign IDs and filter empty texts
    result = []
    for p in prompts_raw:
        if p.get("text", "").strip():
            result.append({
                "id": str(uuid.uuid4()),
                "text": p["text"].strip(),
                "category": p.get("category", "brand_awareness"),
            })

    logger.info(f"Total prompts prepared: {len(result)} across categories: { {c: sum(1 for p in result if p['category']==c) for c in PROMPT_CATEGORIES} }")
    return result
