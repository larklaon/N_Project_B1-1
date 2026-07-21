#!/usr/bin/env python3
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_ollama_tests import CASES, SYSTEM_RULES  # noqa: E402


MODEL = "gemini-3.1-pro-preview"
BASE_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
GENERATION_CONFIG = {
    "temperature": 0.2,
    "topP": 0.9,
    "maxOutputTokens": 65536,
}


def generate(prompt: str) -> dict:
    api_key = os.environ["GEMINI_API_KEY"]
    payload = {
        "systemInstruction": {
            "parts": [{"text": SYSTEM_RULES}],
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": GENERATION_CONFIG,
    }
    request = urllib.request.Request(
        BASE_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "x-goog-api-key": api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    started = time.time()
    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            data = json.loads(response.read().decode("utf-8"))
            data["elapsed_seconds_client"] = round(time.time() - started, 2)
            return data
    except urllib.error.HTTPError as exc:
        return {
            "error": f"HTTP {exc.code}",
            "body": exc.read().decode("utf-8", errors="replace"),
            "elapsed_seconds_client": round(time.time() - started, 2),
        }


def extract_text(output: dict) -> str:
    parts = []
    for candidate in output.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            if "text" in part:
                parts.append(part["text"])
    return "\n".join(parts).strip()


def main() -> None:
    if "GEMINI_API_KEY" not in os.environ:
        raise SystemExit("GEMINI_API_KEY environment variable is required.")

    out_dir = ROOT / "results"
    out_dir.mkdir(exist_ok=True)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    results = {
        "run_id": run_id,
        "run_started_at": datetime.now().isoformat(timespec="seconds"),
        "model": MODEL,
        "base_url": BASE_URL,
        "generation_config": GENERATION_CONFIG,
        "cases": CASES,
        "outputs": [],
    }

    for case in CASES:
        print(f"Running {MODEL} / {case['id']}", flush=True)
        output = generate(case["prompt"])
        results["outputs"].append({
            "model": MODEL,
            "case_id": case["id"],
            "case_title": case["title"],
            "output": output,
            "text": extract_text(output),
        })

    json_path = out_dir / f"gemini_raw_outputs_{run_id}.json"
    json_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines = [
        "# Gemini API 테스트 원문 결과",
        "",
        f"- 실행 시각: {results['run_started_at']}",
        f"- 모델: {MODEL}",
        f"- 설정: `{json.dumps(GENERATION_CONFIG, ensure_ascii=False)}`",
        "",
    ]
    for item in results["outputs"]:
        md_lines.extend([
            f"## {item['model']} - {item['case_title']}",
            "",
        ])
        output = item["output"]
        if "error" in output:
            md_lines.extend([
                f"오류: `{output['error']}`",
                "",
                "```text",
                output.get("body", ""),
                "```",
                "",
            ])
        else:
            md_lines.extend([
                f"- 클라이언트 측 응답 시간: {output.get('elapsed_seconds_client')}초",
                "",
                "```text",
                item["text"],
                "```",
                "",
            ])

    md_path = out_dir / f"gemini_raw_outputs_{run_id}.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(json_path)
    print(md_path)


if __name__ == "__main__":
    main()
