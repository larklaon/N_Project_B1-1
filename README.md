# N_Project_B1-1

LLM 프롬프트 엔지니어링 미션 제출 패키지입니다.

이번 버전은 실제 LLM 3종 비교 실행이 어려운 상황을 전제로, 동일 업무 과업을 여러 모델에 투입할 수 있는 테스트 케이스와 평가표를 먼저 완성했습니다. 업무 과업은 `회의록 요약 자동화`로 설정했습니다.

## 산출물

- [모델 비교·선정 테스트 설계 보고서](docs/01_model_comparison_test_plan.md)
- [시스템 설계 문서](docs/02_system_design.md)
- [실행 로그](docs/03_execution_log.md)
- [원본 대화 로그](logs/raw_conversation_log.md)
- [모델 비교 테스트 케이스](test_cases/model_comparison_cases.md)
- [환각 검증 테스트 케이스](test_cases/hallucination_tests.md)

## 사용 방법

1. `test_cases/model_comparison_cases.md`의 동일 입력을 3개 이상의 LLM에 그대로 입력한다.
2. 각 모델의 답변을 `docs/01_model_comparison_test_plan.md`의 평가표에 기록한다.
3. 점수와 근거를 바탕으로 최종 선정 결론을 작성한다.
4. 최종 선택 모델에는 `docs/02_system_design.md`의 v2 시스템 프롬프트를 적용한다.
