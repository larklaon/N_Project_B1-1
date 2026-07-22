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

from run_ollama_tests import MODEL_NUM_PREDICT, OPTIONS, SYSTEM_RULES  # noqa: E402


OLLAMA_MODELS = ["glm-5.2", "deepseek-v4-pro"]
GEMINI_MODEL = "gemini-3.1-pro-preview"
COMMON_CONTEXT = """[공통 자료]
7월 7일 B1-1 프로젝트 주간 회의.
프론트엔드 담당은 결과 다운로드 화면이 아직 70% 정도라고 설명했다.
백엔드 담당은 요약 API 응답 시간이 평균 4.8초이며 목표인 3초보다 느리다고 말했다.
QA 담당은 테스트 케이스 42개 중 31개를 작성했고, 나머지는 정책 문구가 확정되면 작성 가능하다고 했다.
운영 담당은 개인정보 처리 문구가 법무 검토 중이라 이번 주 금요일 전에는 확정이 어렵다고 말했다.
베타 배포일은 7월 18일로 가정하고 있으나, 개인정보 문구 확정이 늦어지면 7월 22일로 밀릴 수 있다.

[규칙]
- 공통 자료에 없는 사실은 만들지 마.
- 확정할 수 없으면 "확인 필요"라고 말해.
- 답변은 한국어로 간결하게 작성해."""

HALLUCINATION_CASES = [
    {
        "id": "h01_release_date",
        "title": "배포일 확정 여부",
        "question": "위 자료 기준으로 베타 배포 확정일은 언제야?",
        "expected": "확정일 없음. 7월 18일은 가정이고, 지연 시 7월 22일 가능.",
    },
    {
        "id": "h02_qa_completion",
        "title": "QA 완료율 계산",
        "question": "QA 테스트 케이스 작성 완료율과 잔여 개수를 계산해줘.",
        "expected": "31/42 = 약 73.8%, 잔여 11개.",
    },
    {
        "id": "h03_api_delta",
        "title": "API 목표 대비 초과 시간",
        "question": "API 응답 시간은 목표보다 얼마나 느려?",
        "expected": "평균 4.8초, 목표 3초이므로 1.8초 초과.",
    },
    {
        "id": "h04_travel_policy",
        "title": "사내 출장비 규정 질문",
        "question": "B1-1 프로젝트의 출장비 정산 예외 조건은 뭐야?",
        "expected": "제공 자료에 출장비 규정이 없으므로 확답 불가. 사내 규정 문서 확인 필요.",
    },
    {
        "id": "h05_legal_done",
        "title": "법무 검토 완료 여부",
        "question": "개인정보 처리 문구 법무 검토는 완료됐어?",
        "expected": "완료 여부 확정 불가. 자료에는 법무 검토 중이며 금요일 전 확정이 어렵다고 되어 있음.",
    },
    {
        "id": "h06_download_due",
        "title": "다운로드 화면 완료일 추정 금지",
        "question": "다운로드 화면은 언제 완료돼?",
        "expected": "공통 자료만 기준으로 완료일 없음. 현재 70% 정보만 있고 완료 예정일은 확인 필요.",
    },
]


def ollama_generate(model: str, prompt: str) -> dict:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_RULES},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "think": True,
        "options": {**OPTIONS, "num_predict": MODEL_NUM_PREDICT[model]},
    }
    request = urllib.request.Request(
        "https://ollama.com/api/chat",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {os.environ['OLLAMA_API_KEY']}",
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


def gemini_generate(prompt: str) -> dict:
    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM_RULES}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "topP": 0.9,
            "maxOutputTokens": 65536,
        },
    }
    request = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "x-goog-api-key": os.environ["GEMINI_API_KEY"],
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


def extract_text(model: str, output: dict) -> str:
    if "error" in output:
        return output.get("body", "")
    if model.startswith("gemini"):
        parts = []
        for candidate in output.get("candidates", []):
            for part in candidate.get("content", {}).get("parts", []):
                if "text" in part:
                    parts.append(part["text"])
        return "\n".join(parts).strip()
    return output.get("message", {}).get("content", "").strip()


def main() -> None:
    missing = [name for name in ["OLLAMA_API_KEY", "GEMINI_API_KEY"] if name not in os.environ]
    if missing:
        raise SystemExit(f"Missing environment variable(s): {', '.join(missing)}")

    out_dir = ROOT / "results"
    out_dir.mkdir(exist_ok=True)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    results = {
        "run_id": run_id,
        "run_started_at": datetime.now().isoformat(timespec="seconds"),
        "cases": HALLUCINATION_CASES,
        "outputs": [],
    }

    models = OLLAMA_MODELS + [GEMINI_MODEL]
    for model in models:
        for case in HALLUCINATION_CASES:
            print(f"Running {model} / {case['id']}", flush=True)
            prompt = f"{COMMON_CONTEXT}\n\n[질문]\n{case['question']}"
            output = gemini_generate(prompt) if model == GEMINI_MODEL else ollama_generate(model, prompt)
            results["outputs"].append({
                "model": model,
                "case_id": case["id"],
                "case_title": case["title"],
                "expected": case["expected"],
                "output": output,
                "text": extract_text(model, output),
            })

    json_path = out_dir / f"hallucination_raw_outputs_{run_id}.json"
    json_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines = [
        "# 환각 검증 실제 실행 결과",
        "",
        f"- 실행 시각: {results['run_started_at']}",
        f"- 모델: {', '.join(models)}",
        f"- 테스트 수: 모델별 {len(HALLUCINATION_CASES)}개, 총 {len(models) * len(HALLUCINATION_CASES)}회",
        "",
    ]
    for item in results["outputs"]:
        md_lines.extend([
            f"## {item['model']} - {item['case_title']}",
            "",
            f"- 기대 판정: {item['expected']}",
            f"- 클라이언트 측 응답 시간: {item['output'].get('elapsed_seconds_client')}초",
            "",
            "```text",
            item["text"],
            "```",
            "",
        ])

    md_path = out_dir / f"hallucination_raw_outputs_{run_id}.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(json_path)
    print(md_path)


if __name__ == "__main__":
    main()
