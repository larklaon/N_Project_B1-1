# LLM 업무 자동화 프롬프트 패키지

> N_Project_B1-1 | 프롬프트 엔지니어링 미션 제출물

회의록 요약 자동화 과업을 기준으로 3종 LLM을 비교하고, 최종 업무 자동화 프롬프트를 설계한 프로젝트입니다. 동일 테스트 케이스를 GLM-5.2, DeepSeek-V4-Pro, Gemini 3.1 Pro Preview에 입력해 정확성, 형식 준수, 환각 억제, 문맥 유지, 실무 재사용성을 평가했습니다.

## 최종 결론

최종 선정 모델은 **GLM-5.2**입니다.

| 순위 | 모델 | 총점 | 선정 판단 |
|---:|---|---:|---|
| 1 | GLM-5.2 | 29 | 환각 억제와 외부 공유용 민감 정보 제거가 가장 안정적 |
| 2 | Gemini 3.1 Pro Preview | 27 | 문장 품질은 우수하나 일부 해석성 표현과 일정 표현 보강 필요 |
| 3 | DeepSeek-V4-Pro | 24 | 구조화 능력은 좋으나 날짜 추론 오류와 민감 수치 미제거 발생 |

## 프로젝트 구성

| 구분 | 파일 | 설명 |
|---|---|---|
| 최종 보고서 | [docs/04_final_report.md](docs/04_final_report.md) | 모델 출시 정보, 실행 환경, 평가표, 최종 선정 근거를 포함한 최종 제출 보고서 |
| 모델 비교 보고서 | [docs/01_model_comparison_test_plan.md](docs/01_model_comparison_test_plan.md) | 비교 목적, 동일 입력, 평가 축, 실행 결과 요약 |
| 시스템 설계 문서 | [docs/02_system_design.md](docs/02_system_design.md) | 페르소나, 시스템 프롬프트, Few-shot 예시, 환각 검증 설계 |
| 실행 로그 | [docs/03_execution_log.md](docs/03_execution_log.md) | 10턴 이상 대화 전문, 조건 변경, 문맥 유지 검증 |
| 원본 대화 로그 | [logs/raw_conversation_log.md](logs/raw_conversation_log.md) | 재현 가능한 대화 원문 |
| 모델 테스트 케이스 | [test_cases/model_comparison_cases.md](test_cases/model_comparison_cases.md) | 3종 모델 비교에 사용한 동일 프롬프트 |
| 환각 테스트 케이스 | [test_cases/hallucination_tests.md](test_cases/hallucination_tests.md) | 사실/수치/정책 질문 검증용 테스트 |

## 실행 결과

| 결과 파일 | 내용 |
|---|---|
| [results/model_comparison_summary_20260721.md](results/model_comparison_summary_20260721.md) | 3종 LLM 비교 결과 요약 |
| [results/ollama_test_summary_20260721_133956.md](results/ollama_test_summary_20260721_133956.md) | GLM-5.2 / DeepSeek-V4-Pro 비교 요약 |
| [results/ollama_raw_outputs_20260721_133956.md](results/ollama_raw_outputs_20260721_133956.md) | Ollama API 원문 응답 로그 |
| [results/gemini_raw_outputs_20260721_134549.md](results/gemini_raw_outputs_20260721_134549.md) | Gemini API 원문 응답 로그 |

## 비교 모델

| 모델 | 분류 | 사용 채널 | 공개/출시 정보 |
|---|---|---|---|
| GLM-5.2 | 공개형/오픈 계열 모델 | Ollama Cloud API | Hugging Face 공개 2026-06-16 |
| DeepSeek-V4-Pro | 공개형/오픈 계열 모델 | Ollama Cloud API | DeepSeek Preview Release 2026-04-24 |
| Gemini 3.1 Pro Preview | 폐쇄형 상용 모델 | Gemini API | Gemini API changelog 기준 2026-02-19 |

## 평가 기준

각 모델은 아래 7개 축으로 1~5점 평가했습니다.

| 평가 축 | 설명 |
|---|---|
| 정확성 | 원문 사실, 수치, 일정 조건을 왜곡 없이 반영하는가 |
| 형식 준수 | 요구한 목차, 표, 출력 규칙을 지키는가 |
| 환각 억제 | 제공되지 않은 정보나 불확실한 일정을 단정하지 않는가 |
| 한국어 업무 톤 | 사내 공유/보고 문서에 맞는 자연스럽고 간결한 한국어인가 |
| Action Item 품질 | 담당 역할, 작업, 기한, 근거가 명확한가 |
| 문맥 유지 | 조건 변경 후에도 이전 조건을 유지하는가 |
| 실무 재사용성 | 결과물을 바로 업무 문서로 활용할 수 있는가 |

## 테스트 케이스

| 번호 | 테스트 | 목적 |
|---:|---|---|
| 1 | 기본 회의록 요약 | 결정사항, Action Items, 리스크 추출 |
| 2 | 모호한 입력 대응 | 확인 질문과 추측 방지 |
| 3 | 조건 변경 및 문맥 유지 | 이전 조건 유지와 변경 조건 반영 |
| 4 | 외부 공유용 민감 정보 제거 | 내부 수치 제거와 외부용 문안 변환 |
| 5 | 계산 및 사실 검증 | 완료율, 잔여 개수, 초과 시간 계산 |
| 6 | 환각 방지 | 자료 없는 규정 질문에 대한 확답 방지 |

## 최종 프롬프트 방향

최종 시스템 프롬프트는 [시스템 설계 문서](docs/02_system_design.md)의 v2 프롬프트를 사용합니다. GLM-5.2 적용 시 다음 보강 규칙을 추가합니다.

```text
불명확한 표현은 가능한 해석을 단정하지 말고 "확인 필요"로 남긴다.
외부 공유용 문안에서는 내부 성능 수치, QA 상세 수치, 미확정 내부 일정, 내부 개발 이슈를 제거한다.
날짜가 상대 표현으로 주어진 경우 현재 날짜를 기준으로 계산하지 말고, 원문에 절대 날짜가 없으면 확인 필요로 표시한다.
최종 문안 제출 전 오타를 1회 점검한다.
```

## 재현 방법

API 키는 파일에 저장하지 않고 환경변수로만 주입합니다.

```bash
export OLLAMA_API_KEY="..."
python3 scripts/run_ollama_tests.py

export GEMINI_API_KEY="..."
python3 scripts/run_gemini_tests.py
```

실행 결과는 `results/` 폴더에 JSON과 Markdown으로 저장됩니다.

## 제출물 체크리스트

- [x] 3종 이상 LLM 비교
- [x] 동일 업무 과업 프롬프트 및 테스트 케이스
- [x] 평가 축 4개 이상과 점수표
- [x] 최종 선정 결론 및 근거
- [x] 시스템 프롬프트와 페르소나 설계
- [x] Few-shot 예시 3개
- [x] 간단 프롬프트 / 개선 프롬프트 전후 비교
- [x] 환각 검증 질문 5개 이상
- [x] 10턴 이상 대화 로그
- [x] 원본 로그 별도 보관

## 참고 자료

- [Z.ai GLM-5.2 문서](https://docs.z.ai/guides/llm/glm-5.2)
- [DeepSeek V4 Preview Release](https://api-docs.deepseek.com/news/news260424/)
- [Ollama DeepSeek-V4-Pro](https://ollama.com/library/deepseek-v4-pro)
- [Gemini 3.1 Pro Preview 문서](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-pro-preview)
- [Gemini API Release Notes](https://ai.google.dev/gemini-api/docs/changelog)
