"""Run every adapter in the environment that holds its framework, then merge the reports.

Frameworks pin conflicting versions of the provider SDKs, so the published results come from
several virtualenvs. Usage: python tools/run_matrix.py <venvs-dir> <out-dir>

Expected layout under <venvs-dir> (see docs/matrix.md for the exact pip installs):
  a  openai anthropic google-genai litellm langchain-* llama-index-llms-openai/-google-genai
     pydantic-ai-slim openai-agents haystack-ai anthropic-haystack google-genai-haystack
     autogen-ext smolagents
  b  crewai[anthropic,google-genai]
  c  semantic-kernel agent-framework-openai agent-framework-anthropic
  d  google-adk litellm agno llm llm-anthropic
  e  strands-agents[openai,anthropic,gemini,litellm]
  f  llama-index-llms-anthropic with anthropic<0.76 (0.13.0 breaks on anthropic>=1)
"""

from __future__ import annotations

import os
import subprocess
import sys

MATRIX = {
    "a": [
        "openai-python.chat",
        "openai-python.responses",
        "anthropic-python",
        "google-genai",
        "litellm",
        "litellm.responses",
        "langchain-openai",
        "langchain-openai.responses",
        "langchain-anthropic",
        "langchain-google-genai",
        "llama-index-openai",
        "llama-index-google-genai",
        "pydantic-ai.openai-chat",
        "pydantic-ai.openai-responses",
        "pydantic-ai.anthropic",
        "pydantic-ai.google",
        "openai-agents.chat",
        "openai-agents.responses",
        "haystack.openai",
        "haystack.anthropic",
        "haystack.google-genai",
        "autogen.openai",
        "smolagents.openai",
        "smolagents.litellm",
    ],
    "b": ["crewai"],
    "c": ["semantic-kernel.openai", "agent-framework.openai", "agent-framework.anthropic"],
    "d": ["google-adk.litellm", "google-adk.gemini", "agno.openai", "agno.anthropic", "llm.openai", "llm.anthropic"],
    "e": ["strands.openai", "strands.anthropic", "strands.gemini", "strands.litellm"],
    "f": ["llama-index-anthropic", "autogen.anthropic"],
}


def main(venvs: str, out: str) -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "..", "src")
    env = dict(os.environ, PYTHONPATH=src)
    reports = []
    for venv, adapters in MATRIX.items():
        py = os.path.join(venvs, venv, "Scripts" if os.name == "nt" else "bin", "python")
        rep = os.path.join(out, f"report-{venv}.json")
        args = [py, "-m", "llm_stream_check", "run", "--json", rep]
        for a in adapters:
            args += ["--adapter", a]
        print("==", venv, flush=True)
        subprocess.run(args, env=env)
        reports.append(rep)
    return subprocess.run(
        [sys.executable, "-m", "llm_stream_check", "report", *reports, "--json", os.path.join(out, "report.json")],
        env=env,
    ).returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
