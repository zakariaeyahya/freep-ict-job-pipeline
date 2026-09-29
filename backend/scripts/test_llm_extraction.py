"""Manual, one-job sanity check for LlmFieldExtractor against a real
sample (../../offre.md's first offer, "Senior mendix developer"/Rechtspraak).

Deliberately NOT a pytest test and NOT run against the full dataset: keeps
the check fast and focused on one known example while the prompt/
extraction logic is still being validated. Defaults to --provider
fallback, the same OpenAI-primary/Groq-fallback client the real pipeline
uses (FallbackLlmClient); pass --provider openai or --provider groq to
force one provider in isolation for debugging.

Note: contract_type is expected to stay null here — this script only feeds
hard_requirements/wishes, but contract_type ("detachering"/"freelance") in
the real pipeline comes from JobParser._extract_contract_type's HTML badge
selector, not from the LLM (see pipeline.py's _enrich_with_llm_fields: the
parser's value always wins when present).

Usage:
    python scripts/test_llm_extraction.py [--provider fallback|openai|groq]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.freep_pipeline.extraction.fallback_llm_client import FallbackLlmClient
from src.freep_pipeline.extraction.groq_client import GroqClient
from src.freep_pipeline.extraction.llm_field_extractor import LlmFieldExtractor
from src.freep_pipeline.extraction.openai_client import OpenAiClient

TITLE = "Senior mendix developer"

HARD_REQUIREMENTS = [
    "Bachelor's (BSc) of master's (MSc) diploma in de vakgebieden IT en/of bedrijfskunde",
    "Communicatief vaardig: duidelijk communiceren met teamleden en gebruikers",
    "Meer dan 3 jaar ervaring met low-code oplossingsarchitectuur en/of -ontwikkeling, bij voorkeur met Mendix",
]

WISHES = [
    "Platform certificering, een professioneel/gevorderd of expert certificaat voor Mendix is gewenst of wordt "
    "in de nabije toekomst nagestreefd",
    "Platformontwikkeling; Rechtspraak ervaring",
    "Mendix-koppelingen; AI-oplossingen met Mendix; Contentoplossingen met Mendix",
]


def main(provider: str) -> None:
    if provider == "groq":
        client = GroqClient()
    elif provider == "openai":
        client = OpenAiClient()
    else:
        client = FallbackLlmClient()
    extractor = LlmFieldExtractor(client=client)

    result = extractor.extract(title=TITLE, hard_requirements=HARD_REQUIREMENTS, wishes=WISHES)

    print(json.dumps(result.__dict__, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["fallback", "openai", "groq"], default="fallback")
    args = parser.parse_args()
    main(args.provider)
