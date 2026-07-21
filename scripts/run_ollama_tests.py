#!/usr/bin/env python3
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path


BASE_URL = "https://ollama.com/api/chat"
MODELS = ["glm-5.2", "deepseek-v4-pro"]
OPTIONS = {
    "temperature": 0.2,
    "top_p": 0.9,
}
MODEL_NUM_PREDICT = {
    "glm-5.2": 131072,
    "deepseek-v4-pro": 65536,
}

SYSTEM_RULES = """너는 프로젝트 매니저 출신 회의록 자동화 코치다.
한국어로 답한다.
원문에 없는 사실, 일정, 정책, 수치는 만들지 않는다.
불확실한 정보는 '확인 필요'로 표시한다.
실명은 쓰지 않고 역할명만 사용한다.
최종 답변은 간결하게 작성한다."""

CASES = [
    {
        "id": "case_1_basic_summary",
        "title": "기본 회의록 요약",
        "prompt": """[업무 과업]
다음 회의 메모를 사내 공유용 회의록으로 정리해줘.

[출력 형식]
1. 회의 제목
2. 3줄 요약
3. 결정사항
4. Action Items 표: 담당 역할 / 작업 / 기한 / 근거
5. 리스크 및 확인 필요
6. 다음 회의 아젠다
7. 핵심 근거 3개

[규칙]
- 참석자 실명은 쓰지 말고 역할명만 써.
- 확실하지 않은 내용은 추측하지 말고 "확인 필요"로 표시해.
- 한국어 사내 공유용 톤으로 간결하게 작성해.

[회의 메모]
7월 7일 B1-1 프로젝트 주간 회의. 참석자는 PM, 백엔드 담당, 프론트엔드 담당, QA 담당, 운영 담당.
이번 주 목표는 베타 배포 범위 확정과 QA 일정 조율이다.
PM은 "이번 베타에서는 회원가입, 로그인, 회의록 요약, 결과 다운로드까지만 포함하자"고 말했다.
프론트엔드 담당은 결과 다운로드 화면이 아직 70% 정도라고 설명했다.
백엔드 담당은 요약 API 응답 시간이 평균 4.8초이며 목표인 3초보다 느리다고 말했다.
QA 담당은 테스트 케이스 42개 중 31개를 작성했고, 나머지는 정책 문구가 확정되면 작성 가능하다고 했다.
운영 담당은 개인정보 처리 문구가 법무 검토 중이라 이번 주 금요일 전에는 확정이 어렵다고 말했다.
베타 배포일은 7월 18일로 가정하고 있으나, 개인정보 문구 확정이 늦어지면 7월 22일로 밀릴 수 있다.
결론적으로 베타 범위는 축소안으로 진행하고, 다운로드 화면과 API 응답 속도 개선을 우선 처리하기로 했다.
다음 회의에서는 법무 검토 결과, QA 잔여 케이스, 응답 속도 개선 결과를 확인한다.""",
    },
    {
        "id": "case_2_ambiguous_input",
        "title": "모호한 입력 대응",
        "prompt": """어제 회의 내용 정리해줘. 다운로드는 좀 늦고, 법무는 아직이라고 했어. 톤은 알아서 해줘.

규칙:
- 모르면 추측하지 말 것.
- 필요한 확인 질문은 최대 3개까지만 할 것.
- 답변 가능한 범위가 있으면 초안도 함께 줄 것.""",
    },
    {
        "id": "case_3_context_change",
        "title": "조건 변경 및 문맥 유지",
        "prompt": """먼저 아래 조건으로 회의록을 작성해.
- 사내 공유용
- 실명 금지
- 역할명만 사용
- Action Items 표 포함

[회의 메모]
프론트엔드는 대시보드 필터를 7월 9일까지 수정하기로 했다.
백엔드는 검색 API 캐시 적용을 검토 중이다. 완료 일정은 정해지지 않았다.
QA는 회귀 테스트 18개 중 12개를 완료했다.

이제 같은 내용을 임원 보고용으로 바꿔줘.
- 세부 표는 줄여줘.
- 실명 금지와 역할명 사용 조건은 유지해.
- 완료 일정이 없는 항목은 확인 필요로 표시해.""",
    },
    {
        "id": "case_4_external_redaction",
        "title": "외부 공유용 민감 정보 제거",
        "prompt": """아래 회의록을 외부 협력사 공유용으로 바꿔줘.

[기존 회의록]
- 베타 범위는 회원가입, 로그인, 회의록 요약, 결과 다운로드로 제한한다.
- API 응답 시간은 평균 4.8초이며 목표 3초보다 느리다.
- 다운로드 화면은 현재 70%이고 7월 12일까지 완료 예정이다.
- 법무 검토는 7월 10일 오후 완료 가능성이 있으나 확정은 아니다.
- QA 테스트 케이스는 42개 중 31개 완료했다.

[규칙]
- 외부 협력사에게 필요한 일정과 요청사항 중심으로 작성해.
- 내부 성능 수치와 상세 QA 수치는 빼줘.
- 확정되지 않은 법무 일정은 확정처럼 쓰지 마.""",
    },
    {
        "id": "case_5_calculation_fact_check",
        "title": "계산 및 사실 검증",
        "prompt": """아래 메모에서 계산 가능한 항목만 계산하고, 확정할 수 없는 항목은 확인 필요로 표시해.

[메모]
- QA 테스트 케이스는 42개 중 31개 작성 완료.
- API 응답 시간은 평균 4.8초, 목표는 3초.
- 다운로드 화면은 70% 완료.
- 베타 배포는 7월 18일을 가정하지만, 법무 검토가 늦으면 7월 22일로 변경 가능.

[출력]
1. 계산 결과
2. 확정 불가 항목
3. 근거""",
    },
    {
        "id": "case_6_hallucination_policy",
        "title": "환각 방지",
        "prompt": """B1-1 프로젝트의 출장비 정산 예외 조건은 뭐야?

규칙:
- 제공된 자료가 없으면 확답하지 마.
- 모르면 확인 필요라고 말하고, 어디서 확인해야 하는지 제안해.""",
    },
]


def generate(model: str, prompt: str) -> dict:
    api_key = os.environ["OLLAMA_API_KEY"]
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
        BASE_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    started = time.time()
    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            body = response.read().decode("utf-8")
            data = json.loads(body)
            message = data.get("message", {})
            data["message"] = {
                "role": message.get("role"),
                "content": message.get("content", ""),
            }
            data["thinking_char_count"] = len(message.get("thinking", "") or data.get("thinking", "") or "")
            data.pop("thinking", None)
            data["elapsed_seconds_client"] = round(time.time() - started, 2)
            return data
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        return {
            "error": f"HTTP {exc.code}",
            "body": error_body,
            "elapsed_seconds_client": round(time.time() - started, 2),
        }


def main() -> None:
    if "OLLAMA_API_KEY" not in os.environ:
        raise SystemExit("OLLAMA_API_KEY environment variable is required.")

    root = Path(__file__).resolve().parents[1]
    out_dir = root / "results"
    out_dir.mkdir(exist_ok=True)

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = {
        "run_id": run_id,
        "run_started_at": datetime.now().isoformat(timespec="seconds"),
        "base_url": BASE_URL,
        "models": MODELS,
        "options": OPTIONS,
        "cases": CASES,
        "outputs": [],
    }

    for model in MODELS:
        for case in CASES:
            print(f"Running {model} / {case['id']}", flush=True)
            output = generate(model, case["prompt"])
            results["outputs"].append({
                "model": model,
                "case_id": case["id"],
                "case_title": case["title"],
                "output": output,
            })

    json_path = out_dir / f"ollama_raw_outputs_{run_id}.json"
    json_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines = [
        "# Ollama API 테스트 원문 결과",
        "",
        f"- 실행 시각: {results['run_started_at']}",
        f"- 모델: {', '.join(MODELS)}",
        f"- 공통 설정: `{json.dumps(OPTIONS, ensure_ascii=False)}`",
        f"- 모델별 출력 토큰 한도: `{json.dumps(MODEL_NUM_PREDICT, ensure_ascii=False)}`",
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
                output.get("message", {}).get("content", "").strip(),
                "```",
                "",
            ])

    md_path = out_dir / f"ollama_raw_outputs_{run_id}.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(json_path)
    print(md_path)


if __name__ == "__main__":
    main()
