"""Manual, one-job sanity check for LlmFieldExtractor against a real
sample (../../offre.md's first offer, "Senior mendix developer"/Rechtspraak).

Deliberately NOT a pytest test and NOT run against the full dataset: while
GROQ_API_KEY is a temporary stand-in for a not-yet-pulled local Ollama
model, this avoids burning API quota/rate limits on the whole corpus. Swap
client=GroqClient() back to client=OllamaClient() once a model is pulled.

Usage:
    python scripts/test_llm_extraction.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.freep_pipeline.extraction.groq_client import GroqClient
from src.freep_pipeline.extraction.llm_field_extractor import LlmFieldExtractor

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


def main() -> None:
    extractor = LlmFieldExtractor(client=GroqClient())

    result = extractor.extract(title=TITLE, hard_requirements=HARD_REQUIREMENTS, wishes=WISHES)

    print(json.dumps(result.__dict__, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
