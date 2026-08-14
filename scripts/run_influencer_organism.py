"""Run the BEAST organism against a sourced tech-influencer signal set.

The web research is intentionally separated from the evolutionary runtime:
public evidence is collected and normalized first, then the real
``LamarckianEcosystem`` evolves a search policy over that evidence. This keeps
the run deterministic, auditable, and safe to reproduce without scraping the
web in a tight loop.

Usage::

    python3 scripts/run_influencer_organism.py

Outputs:

* ``docs/influencer-organism-10000-report.md``
* ``docs/influencer-organism-10000-results.json``
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

from evolution.lamarckian import LamarckianEcosystem, LamarckianOrganism


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "docs" / "influencer-organism-10000-report.md"
RESULTS_PATH = ROOT / "docs" / "influencer-organism-10000-results.json"
SOURCE_NOTES_PATH = ROOT / "research" / "organism-influencer-source-notes.md"


@dataclass(frozen=True)
class InfluencerSignal:
    """A publicly observable signal that a brand welcomes creator partners."""

    brand: str
    category: str
    source_url: str
    evidence: str
    source_grade: str
    first_party: float
    explicit_application: float
    freshness: float
    india_relevance: float
    tech_fit: float
    route: str


SIGNALS: tuple[InfluencerSignal, ...] = (
    InfluencerSignal(
        brand="MeetGeek",
        category="AI meeting automation",
        source_url="https://support.meetgeek.ai/en/articles/8046477-join-meetgeek-referral-program",
        evidence="First-party help article updated this week describes a Refer & earn $50 flow, social/blog/newsletter sharing, and a marketing contact.",
        source_grade="A",
        first_party=1.0,
        explicit_application=0.88,
        freshness=1.0,
        india_relevance=0.15,
        tech_fit=1.0,
        route="Existing user referral widget; marketing@meetgeek.ai",
    ),
    InfluencerSignal(
        brand="ClickUp",
        category="AI productivity SaaS",
        source_url="https://clickup.com/partners/affiliates",
        evidence="First-party affiliate page has a live Join Now portal, up to $25 per new free workspace, and instructions for blogs, comparisons, and social channels.",
        source_grade="A",
        first_party=1.0,
        explicit_application=1.0,
        freshness=0.92,
        india_relevance=0.20,
        tech_fit=1.0,
        route="PartnerStack Join Now portal",
    ),
    InfluencerSignal(
        brand="Gamma",
        category="AI presentations and content",
        source_url="https://help.gamma.app/en/articles/11048092-how-do-i-join-the-gamma-affiliate-program",
        evidence="First-party help article dated October 10, 2025 says creators, educators, founders, and community builders can apply through a PartnerStack portal.",
        source_grade="A",
        first_party=1.0,
        explicit_application=1.0,
        freshness=0.82,
        india_relevance=0.20,
        tech_fit=1.0,
        route="https://gammaapp.partnerstack.com/?group=affiliates",
    ),
    InfluencerSignal(
        brand="Creatify AI",
        category="AI video creation",
        source_url="https://creatify.ai/affiliate",
        evidence="First-party Partner with Creatify page offers a free-to-join affiliate program, 25% recurring commission, an application route, and possible brand collaborations.",
        source_grade="A",
        first_party=1.0,
        explicit_application=0.95,
        freshness=0.86,
        india_relevance=0.20,
        tech_fit=1.0,
        route="Affiliate application on Creatify",
    ),
    InfluencerSignal(
        brand="Amazon India",
        category="Technology commerce",
        source_url="https://affiliate-program.amazon.in/influencers",
        evidence="India storefront says creators can sign up, build a personalized storefront, publish livestreams and shoppable media, and earn commissions; applications accept major social platforms.",
        source_grade="A",
        first_party=1.0,
        explicit_application=1.0,
        freshness=0.90,
        india_relevance=1.0,
        tech_fit=0.85,
        route="Amazon India Influencer sign-up",
    ),
    InfluencerSignal(
        brand="DJI India",
        category="Creator hardware",
        source_url="https://djiindiashop.com/pages/influencer-program",
        evidence="India storefront exposes an Influencer Program page, but the public extraction did not reveal clear application terms or a visible offer.",
        source_grade="B",
        first_party=0.95,
        explicit_application=0.30,
        freshness=0.55,
        india_relevance=1.0,
        tech_fit=1.0,
        route="Influencer Program page; revalidate contact route",
    ),
    InfluencerSignal(
        brand="Reclaim.AI",
        category="AI scheduling SaaS",
        source_url="https://partnerstack.com/articles/ai-affiliate-programs-2026",
        evidence="PartnerStack’s June 2026 roundup lists Reclaim.AI with a public recurring commission structure; brand-owned terms should be checked before outreach.",
        source_grade="B",
        first_party=0.45,
        explicit_application=0.60,
        freshness=0.92,
        india_relevance=0.15,
        tech_fit=1.0,
        route="Validate through PartnerStack marketplace / brand site",
    ),
    InfluencerSignal(
        brand="AdCreative.ai",
        category="AI advertising SaaS",
        source_url="https://partnerstack.com/articles/ai-affiliate-programs-2026",
        evidence="PartnerStack’s June 2026 roundup lists a 30% recurring revenue-share program; this is a discovery signal rather than an independently checked brand-owned page.",
        source_grade="B",
        first_party=0.45,
        explicit_application=0.60,
        freshness=0.92,
        india_relevance=0.15,
        tech_fit=1.0,
        route="Validate through PartnerStack marketplace / brand site",
    ),
    InfluencerSignal(
        brand="Unity",
        category="Game and 3D development",
        source_url="https://afluencer.com/blog/software-brands-looking-for-tech-influencers",
        evidence="Afluencer’s March 2022 article describes an influencer application with early access and event/staff access; the signal is stale and third-party.",
        source_grade="C",
        first_party=0.15,
        explicit_application=0.45,
        freshness=0.20,
        india_relevance=0.10,
        tech_fit=1.0,
        route="Revalidate independently before any outreach",
    ),
    InfluencerSignal(
        brand="InterServer",
        category="Web hosting",
        source_url="https://afluencer.com/blog/software-brands-looking-for-tech-influencers",
        evidence="Afluencer’s March 2022 article says InterServer sought software and marketing influencers for pay-per-post sponsorship; the signal is stale and third-party.",
        source_grade="C",
        first_party=0.15,
        explicit_application=0.45,
        freshness=0.20,
        india_relevance=0.10,
        tech_fit=1.0,
        route="Revalidate independently before any outreach",
    ),
)


def _normalise(weights: Mapping[str, float]) -> Dict[str, float]:
    total = sum(weights.values())
    return {key: value / total for key, value in weights.items()}


def search_policy(organism: LamarckianOrganism) -> Dict[str, float]:
    """Map the organism's mutable genome and learned culture to search weights."""

    genome = organism.genome
    learned = set(organism.learned_strategies)
    weights = {
        "first_party": 0.24 + 0.22 * genome.learning_rate,
        "explicit_application": 0.20 + 0.20 * genome.cultural_receptivity,
        "freshness": 0.17 + 0.18 * genome.curiosity,
        "india_relevance": 0.07 + 0.14 * genome.cooperation,
        "tech_fit": 0.18 + 0.08 * genome.cooperation,
    }
    if any("prioritize_first_party" in name for name in learned):
        weights["first_party"] += 0.12
    if any("prefer_recent_public_signal" in name for name in learned):
        weights["freshness"] += 0.10
    if any("india_first" in name for name in learned):
        weights["india_relevance"] += 0.12
    return _normalise(weights)


def rank_signals(organism: LamarckianOrganism) -> List[Dict[str, Any]]:
    policy = search_policy(organism)
    ranked: List[Dict[str, Any]] = []
    for signal in SIGNALS:
        score = sum(
            policy[field] * getattr(signal, field)
            for field in policy
        )
        ranked.append({"score": round(score, 6), **asdict(signal)})
    return sorted(ranked, key=lambda item: (-item["score"], item["brand"]))


class InfluencerSearchEcosystem(LamarckianEcosystem):
    """BEAST ecosystem whose selection includes evidence-ranking quality."""

    def _search_quality(self, organism: LamarckianOrganism) -> float:
        ranked = rank_signals(organism)
        top = ranked[:3]
        average_top = sum(item["score"] for item in top) / len(top)
        india_bonus = 0.04 if any(item["india_relevance"] >= 0.9 for item in top) else 0.0
        return min(0.99, average_top + india_bonus)

    def _adaptive_score(self, organism: LamarckianOrganism, environment: Mapping[str, Any]) -> float:
        base = super()._adaptive_score(organism, environment)
        return min(0.99, 0.72 * base + 0.28 * self._search_quality(organism))


def _snapshot(ecosystem: InfluencerSearchEcosystem, generation: int) -> Dict[str, Any]:
    champion = ecosystem.get_champion()
    if champion is None:
        raise RuntimeError("organism population unexpectedly empty")
    ranked = rank_signals(champion)
    return {
        "generation": generation,
        "champion_id": champion.object_id,
        "search_quality": round(ecosystem._search_quality(champion), 6),
        "top_candidate": ranked[0]["brand"],
        "top_score": ranked[0]["score"],
        "policy": {key: round(value, 6) for key, value in search_policy(champion).items()},
        "champion_genome": champion.genome.to_dict(),
        "champion_strategies": sorted(strategy.name for strategy in champion.learned_strategies.values()),
        "fitness": round(ecosystem.history[-1].average_fitness, 6),
        "culture": round(ecosystem.history[-1].cultural_complexity, 6),
        "mutation_rate": round(ecosystem.history[-1].average_mutation_rate, 6),
        "novelty_count": ecosystem.history[-1].novelty_count,
        "archive_size": ecosystem.history[-1].archive_size,
    }


def _pct_change(start: float, end: float) -> float:
    if start == 0:
        return 0.0
    return round(100.0 * (end - start) / abs(start), 2)


def _delta_display(start: float, end: float) -> str:
    if start == 0:
        return f"{end - start:+.4f} absolute"
    return f"{_pct_change(start, end):+.2f}%"


def _markdown_report(result: Mapping[str, Any]) -> str:
    initial = result["checkpoints"][0]
    final = result["checkpoints"][-1]
    lines = [
        "# BEAST Organism: 10,000-Generation Tech Influencer-Signal Report",
        "",
        "> **Scope.** This is a reproducible artificial-life experiment. The organism did not claim that a brand has an unadvertised budget or that it will accept a pitch. It ranked brands using public creator, affiliate, ambassador, or referral signals that were verified before the run.",
        "",
        "## Executive result",
        "",
        f"The run completed **{result['generations']:,} generations** with a population of **{result['population_size']}** and seed **{result['seed']}** in **{result['runtime_seconds']:.3f} seconds**. The final champion ranked **{final['top_candidate']}** first under its evolved evidence policy, with a search-quality score of **{final['search_quality']:.4f}**. The top actionable set is the group of A-grade first-party programs below; B- and C-grade entries are validation leads, not confirmed active campaigns.",
        "",
        "| Metric | Initial | Final | Change |",
        "|---|---:|---:|---:|",
        f"| Average fitness | {initial['fitness']:.4f} | {final['fitness']:.4f} | {_delta_display(initial['fitness'], final['fitness'])} |",
        f"| Cultural complexity | {initial['culture']:.4f} | {final['culture']:.4f} | {_delta_display(initial['culture'], final['culture'])} |",
        f"| Average mutation rate | {initial['mutation_rate']:.4f} | {final['mutation_rate']:.4f} | {_delta_display(initial['mutation_rate'], final['mutation_rate'])} |",
        f"| Novelty descriptors | {initial['novelty_count']} | {final['novelty_count']} | {final['novelty_count'] - initial['novelty_count']} |",
        f"| Cultural archive strategies | {initial['archive_size']} | {final['archive_size']} | {final['archive_size'] - initial['archive_size']} |",
        f"| Search quality | {initial['search_quality']:.4f} | {final['search_quality']:.4f} | {_delta_display(initial['search_quality'], final['search_quality'])} |",
        "",
        "## Final ranked leads",
        "",
        "| Rank | Brand | Score | Grade | Public signal | Next route |",
        "|---:|---|---:|:---:|---|---|",
    ]
    for rank, item in enumerate(result["final_ranked_signals"], start=1):
        lines.append(
            f"| {rank} | **{item['brand']}** | {item['score']:.4f} | {item['source_grade']} | {item['evidence']} | {item['route']} |"
        )
    lines += [
        "",
        "## How to interpret the grades",
        "",
        "| Grade | Meaning | Recommended use |",
        "|:---:|---|---|",
        "| A | First-party public program with an application, referral, or creator route and a relatively current signal | Reasonable first outreach targets; verify terms and geography before pitching |",
        "| B | Current third-party marketplace discovery or a weak first-party page | Research and independently validate the brand-owned route |",
        "| C | Old or third-party directory signal | Do not treat as active without fresh confirmation |",
        "",
        "## Organism behavior",
        "",
        "The organism used the repository’s real Lamarckian engine. Its learned evidence strategies were stored in the shared memome, inherited by descendants, and mixed with mutable genome traits. The policy rewarded first-party evidence, an explicit application path, freshness, technical fit, and India relevance. This is not a web crawler: the public evidence set was curated from the cited pages, and the organism performed the 10,000-generation search-policy evolution and ranking step over that real evidence.",
        "",
        "| Checkpoint | Gen | Champion | Search quality | First-party weight | Freshness weight | India weight |",
        "|---|---:|---|---:|---:|---:|---:|",
    ]
    for checkpoint in result["checkpoints"]:
        policy = checkpoint["policy"]
        lines.append(
            f"| {checkpoint['label']} | {checkpoint['generation']:,} | {checkpoint['top_candidate']} | {checkpoint['search_quality']:.4f} | {policy['first_party']:.4f} | {policy['freshness']:.4f} | {policy['india_relevance']:.4f} |"
        )
    lines += [
        "",
        "## Reproduce the run",
        "",
        "```bash",
        "cd /home/ubuntu/living-objects021",
        "python3 scripts/run_influencer_organism.py",
        "```",
        "",
        f"The source ledger is [{SOURCE_NOTES_PATH.relative_to(ROOT)}](../research/organism-influencer-source-notes.md), and the machine-readable output is [{RESULTS_PATH.name}]({RESULTS_PATH.name}). The public pages should be rechecked immediately before outreach because partner programs, commissions, eligibility, and regional availability can change.",
        "",
        "## Limitations and responsible outreach",
        "",
        "An affiliate or referral program is evidence that a company supports partner-driven acquisition; it is not proof that the company is currently buying managed influencer-marketing services. A marketing agency should use the A-grade rows as permissioned, evidence-based prospecting targets, ask whether they want managed creator campaigns in the target region, disclose affiliate relationships, and avoid claiming guaranteed access or guaranteed conversions.",
        "",
        "### Sources",
        "",
    ]
    unique_sources = []
    seen = set()
    for item in result["final_ranked_signals"]:
        if item["source_url"] not in seen:
            seen.add(item["source_url"])
            unique_sources.append(item)
    for index, item in enumerate(unique_sources, start=1):
        lines.append(f"{index}. [{item['brand']} source]({item['source_url']}) — {item['evidence']}")
    return "\n".join(lines) + "\n"


def run(generations: int = 10_000, population_size: int = 4, seed: int = 20260814) -> Dict[str, Any]:
    started = time.perf_counter()
    checkpoints: List[Dict[str, Any]] = []
    with InfluencerSearchEcosystem(seed=seed, population_size=population_size) as ecosystem:
        ecosystem.spawn_population()
        founder = ecosystem.population[0]
        founder.learn(
            "prioritize_first_party",
            descriptor="evidence:first_party",
            effectiveness=0.94,
        )
        founder.learn(
            "prefer_recent_public_signal",
            descriptor="evidence:freshness",
            effectiveness=0.91,
        )
        ecosystem.population[1].adopt_from_memome(limit=2, minimum_effectiveness=0.80)
        checkpoints.append({"label": "initial", **_snapshot(ecosystem, 0)})
        for generation in range(1, generations + 1):
            ecosystem.step()
            if generation in {1, 10, 100, 1_000, 5_000, 10_000}:
                checkpoints.append({"label": f"g{generation:,}", **_snapshot(ecosystem, generation)})
        champion = ecosystem.get_champion()
        if champion is None:
            raise RuntimeError("no champion after run")
        final_ranked = rank_signals(champion)
        result: Dict[str, Any] = {
            "experiment": "beast-influencer-signal-search",
            "seed": seed,
            "generations": generations,
            "population_size": population_size,
            "runtime_seconds": round(time.perf_counter() - started, 3),
            "candidate_count": len(SIGNALS),
            "checkpoints": checkpoints,
            "final_ranked_signals": final_ranked,
            "final_champion": {
                "id": champion.object_id,
                "genome": champion.genome.to_dict(),
                "strategies": sorted(strategy.name for strategy in champion.learned_strategies.values()),
            },
            "memome_summary": ecosystem.memome.get_summary(),
            "source_notes": str(SOURCE_NOTES_PATH.relative_to(ROOT)),
        }
    RESULTS_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(_markdown_report(result), encoding="utf-8")
    print(json.dumps({
        "generations": generations,
        "population_size": population_size,
        "runtime_seconds": result["runtime_seconds"],
        "top_three": [item["brand"] for item in final_ranked[:3]],
        "final_search_quality": checkpoints[-1]["search_quality"],
        "final_novelty_count": checkpoints[-1]["novelty_count"],
        "final_archive_size": checkpoints[-1]["archive_size"],
        "report": str(REPORT_PATH),
        "results": str(RESULTS_PATH),
    }, indent=2))
    return result


if __name__ == "__main__":
    run()
