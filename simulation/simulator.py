import json
import os
import aisuite
from dotenv import load_dotenv
from simulation.prompt_builder import build_simulation_prompt, build_narrative_prompt

load_dotenv()

MODELS = {
    "Claude (Anthropic)": "anthropic:claude-opus-4-5",
    "GPT-4o (OpenAI)": "openai:gpt-4o",
}
DEFAULT_MODEL_LABEL = "Claude (Anthropic)"


def _get_client(anthropic_key: str = "", openai_key: str = "") -> aisuite.Client:
    if anthropic_key:
        os.environ["ANTHROPIC_API_KEY"] = anthropic_key
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key
    return aisuite.Client()


def run_simulation(
    features: dict,
    drug_data: dict,
    drug_names: list[str],
    treatment_intent: str,
    model_label: str = DEFAULT_MODEL_LABEL,
    anthropic_key: str = "",
    openai_key: str = "",
) -> dict:
    model = MODELS.get(model_label, MODELS[DEFAULT_MODEL_LABEL])
    client = _get_client(anthropic_key=anthropic_key, openai_key=openai_key)
    prompt = build_simulation_prompt(features, drug_data, treatment_intent)

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    raw = response.choices[0].message.content.strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        cleaned = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            result = json.loads(cleaned)
        except json.JSONDecodeError:
            return {"parse_error": True, "raw_response": raw}

    narrative_prompt = build_narrative_prompt(result, features, drug_names)
    narrative_response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": narrative_prompt}],
        temperature=0.3,
    )
    result["narrative"] = narrative_response.choices[0].message.content.strip()
    result["model_used"] = model

    return result
