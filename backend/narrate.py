"""
narrate.py — LLM-powered satellite change analysis narrative generator.

Calls the Gemini Flash 2.0 REST API via httpx (no SDK needed).
Returns:
    - analysis:   2-3 sentence plain-language description of what changed
    - prediction: 1-2 sentence projection of what is likely next
    - confidence: HIGH | MEDIUM | LOW
    - tags:       list of change-type labels
"""

from __future__ import annotations
import os
import httpx
import json
from typing import Optional

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Gemini 3.6 Flash — fast, cheap, great at structured reasoning
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-3.6-flash:generateContent"
)


def _build_prompt(
    location_name: str,
    before_date: str,
    after_date: str,
    infra_pct: float,
    veg_loss_pct: float,
    veg_gain_pct: float,
    ssim_score: float,
    ssim_pct: float,
    tier: str,
    hotspot_count: int,
    hotspot_types: list[str],
    is_stable: bool,
) -> str:
    tier_label = (
        "0.6m sub-meter Maxar/Esri Wayback orthophoto"
        if tier == "0.6m"
        else "10m Copernicus Sentinel-2 multispectral granule"
    )
    hotspot_str = ", ".join(hotspot_types[:4]) if hotspot_types else "no hotspots detected"
    stable_str = "No significant change was detected." if is_stable else ""

    return f"""You are a Nagpur Municipal Corporation (NMC) satellite urban-change intelligence analyst.
You have been given quantitative metrics from a dual-tier satellite change-detection run.
Write a concise, professional, yet easy-to-understand briefing for a town-planning officer.

### INPUT METRICS
- Location: {location_name}
- Baseline date: {before_date}
- Current date: {after_date}
- Sensor tier: {tier_label}
- Infrastructure / Construction delta: {infra_pct:.2f}%
- Tree Canopy / Biomass Loss: {veg_loss_pct:.2f}%
- Afforestation / Vegetation Gain: {veg_gain_pct:.2f}%
- SSIM Structural Index: {ssim_score:.4f}  (lower = more structural change)
- SSIM Structural Divergence: {ssim_pct:.2f}%
- Flagged hotspot count: {hotspot_count}
- Hotspot change typologies: {hotspot_str}
{stable_str}

### YOUR TASK
Return a JSON object with EXACTLY these four fields (no markdown, no extra text):

{{
  "analysis": "<2-3 sentences describing exactly what satellite data shows happened between the two dates. Be specific — mention construction, vegetation loss/gain, structural footprint expansion, or stability as the data dictates. Use accessible language a non-expert can understand.>",
  "prediction": "<1-2 sentences predicting the most likely urban development trajectory over the next 12-24 months based on the observed trend. Be grounded in the data — do not invent information not supported by the metrics. Use phrases like 'If this trend continues...' or 'Based on the detected...' .>",
  "confidence": "<one of: HIGH | MEDIUM | LOW — based on how clear the satellite signal is>",
  "tags": ["<tag1>", "<tag2>", "<tag3>"]
}}

Tags should be short 2-3 word labels like "Infrastructure Growth", "Canopy Loss", "Stable Zone", "High SSIM Change", "New Construction", "Afforestation" — pick whichever apply."""


def generate_narrative(
    *,
    location_name: str,
    before_date: str = "2019-01-31",
    after_date: str = "2025-01-30",
    infra_pct: float = 0.0,
    veg_loss_pct: float = 0.0,
    veg_gain_pct: float = 0.0,
    ssim_score: float = 0.85,
    ssim_pct: float = 0.0,
    tier: str = "0.6m",
    hotspot_count: int = 0,
    hotspot_types: Optional[list] = None,
    is_stable: bool = False,
) -> dict:
    """
    Calls Gemini Flash and returns a dict with:
      analysis, prediction, confidence, tags
    Falls back to a rule-based summary if the API key is missing or call fails.
    """
    if hotspot_types is None:
        hotspot_types = []

    # ── Rule-based fallback (no API key) ────────────────────────
    if not GEMINI_API_KEY:
        return _rule_based_fallback(
            location_name=location_name,
            before_date=before_date,
            after_date=after_date,
            infra_pct=infra_pct,
            veg_loss_pct=veg_loss_pct,
            veg_gain_pct=veg_gain_pct,
            ssim_score=ssim_score,
            ssim_pct=ssim_pct,
            is_stable=is_stable,
        )

    prompt = _build_prompt(
        location_name=location_name,
        before_date=before_date,
        after_date=after_date,
        infra_pct=infra_pct,
        veg_loss_pct=veg_loss_pct,
        veg_gain_pct=veg_gain_pct,
        ssim_score=ssim_score,
        ssim_pct=ssim_pct,
        tier=tier,
        hotspot_count=hotspot_count,
        hotspot_types=hotspot_types,
        is_stable=is_stable,
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 600,
        },
    }

    try:
        resp = httpx.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            json=payload,
            timeout=20.0,
        )
        resp.raise_for_status()
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()

        # Robustly extract JSON: strip markdown fences, find first { ... }
        if "```" in text:
            # Extract content between first ``` pair
            parts = text.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith("json"):
                    part = part[4:].strip()
                if part.startswith("{"):
                    text = part
                    break

        # Find the JSON object boundaries
        start = text.find("{")
        end   = text.rfind("}") + 1
        if start != -1 and end > start:
            text = text[start:end]

        result = json.loads(text)

        # Validate expected keys
        for key in ("analysis", "prediction", "confidence", "tags"):
            if key not in result:
                raise ValueError(f"Missing key in LLM response: {key}")

        return result

    except Exception as exc:
        print(f"[narrate] Gemini call failed: {exc}. Using rule-based fallback.")
        return _rule_based_fallback(
            location_name=location_name,
            before_date=before_date,
            after_date=after_date,
            infra_pct=infra_pct,
            veg_loss_pct=veg_loss_pct,
            veg_gain_pct=veg_gain_pct,
            ssim_score=ssim_score,
            ssim_pct=ssim_pct,
            is_stable=is_stable,
        )


# ── Rule-Based Fallback (deterministic, no API key needed) ──────────────────

def _rule_based_fallback(
    *,
    location_name: str,
    before_date: str,
    after_date: str,
    infra_pct: float,
    veg_loss_pct: float,
    veg_gain_pct: float,
    ssim_score: float,
    ssim_pct: float,
    is_stable: bool,
) -> dict:
    tags = []

    if is_stable or (infra_pct < 0.5 and veg_loss_pct < 0.5 and ssim_pct < 2.0):
        analysis = (
            f"Satellite imagery of {location_name} between {before_date} and {after_date} "
            f"shows minimal detectable change. The structural SSIM index of {ssim_score:.3f} "
            f"confirms that the built environment and vegetation canopy remain largely stable."
        )
        prediction = (
            "Based on the low change signal, this area is expected to maintain its current land-use "
            "profile over the next 12 months without significant structural transformation."
        )
        confidence = "HIGH"
        tags = ["Stable Zone", "Low Change", "Canopy Intact"]

    else:
        parts = []

        if infra_pct > 1.5:
            parts.append(
                f"infrastructure and construction activity at {infra_pct:.1f}% "
                f"indicating new building foundations or structural grading"
            )
            tags.append("Infrastructure Growth")
        if infra_pct > 4.0:
            tags.append("High Construction Activity")

        if veg_loss_pct > 1.0:
            parts.append(
                f"tree canopy loss of {veg_loss_pct:.1f}%, "
                f"consistent with clearance for construction or open-plot development"
            )
            tags.append("Canopy Loss")

        if veg_gain_pct > 1.0:
            parts.append(
                f"new vegetation gain of {veg_gain_pct:.1f}%, "
                f"suggesting afforestation or green-corridor planting"
            )
            tags.append("Afforestation")

        if ssim_pct > 5.0:
            tags.append("High SSIM Change")

        if not parts:
            parts.append(f"moderate structural divergence ({ssim_pct:.1f}% SSIM change)")
            tags.append("Structural Change")

        change_str = "; and ".join(parts)
        analysis = (
            f"Between {before_date} and {after_date}, satellite analysis of {location_name} detected "
            f"{change_str}. The structural similarity index (SSIM) of {ssim_score:.3f} confirms "
            f"significant transformation of the built environment."
        )

        # Prediction based on dominant signal
        if infra_pct > 3.0:
            prediction = (
                f"If this construction trajectory continues, {location_name} is likely to see "
                f"additional structural footprint expansion over the next 12-24 months. "
                f"A field audit by the Town Planning Department is recommended to verify "
                f"sanctioned development approvals."
            )
        elif veg_loss_pct > 2.0:
            prediction = (
                f"Continued canopy clearance in {location_name} suggests ongoing land preparation. "
                f"Monitoring is advised to ensure compliance with NMC green-cover mandates."
            )
        else:
            prediction = (
                f"The observed changes in {location_name} suggest active but early-stage development. "
                f"A follow-up scan in 6 months will provide clearer insight into the final land-use outcome."
            )

        confidence = "HIGH" if ssim_pct > 8.0 or infra_pct > 3.0 else "MEDIUM"

    return {
        "analysis": analysis,
        "prediction": prediction,
        "confidence": confidence,
        "tags": tags,
    }
