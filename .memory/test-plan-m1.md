# M1 Test Plan - Codex MCP Bridge Lite

## 테스트 전략
- Unit:
  - 설정 파싱/정책/출력 절단/실행 오류 분기 등 순수 로직 검증.
  - `subprocess.run`, `shutil.which` 모킹 기반으로 결정적 결과 확보.
- Integration:
  - 로컬 codex 인증 환경에서 실제 `codex exec` 호출 흐름 확인.
  - MCP 도구 경유 동작과 반환 메시지 형태 확인.
- Regression:
  - stdout 오염, 에러 문구 회귀, 절단 마커, allowlist 보안 정책 고정.

## 실행 방법
```bash
cd /Users/dante/codex-mcp-bridge
uv run --with '.[dev]' pytest
```

```bash
cd /Users/dante/codex-mcp-bridge
uv run python -m py_compile src/codex_bridge_mcp/*.py
```

선택적 통합 스모크:
- 전제: `codex login` 완료, 로컬에서 `codex exec` 동작 가능.
- MCP 등록 예:
```bash
claude mcp add codex-bridge -- uv --directory /Users/dante/codex-mcp-bridge run codex-mcp-bridge
```

회귀/통합 실행 스크립트:
```bash
cd /Users/dante/codex-mcp-bridge
./scripts/check_stdout_clean.sh
./scripts/it_smoke_codex_bridge.sh
```

## 테스트 매트릭스
| Case ID | 목적 | 입력/조건 | 기대 결과 | 자동화 |
|---|---|---|---|---|
| UT-CONFIG-001 | env precedence 검증 | tool input + env + default 혼합 | 우선순위 `입력 > env > default` 적용 | 완료 |
| UT-CONFIG-002 | invalid env fallback | 잘못된 timeout/sandbox env 값 | 안전한 default로 fallback | 완료 |
| UT-CONFIG-003 | allowlist 경계 검증 | allowlist 내부/외부 디렉터리 | 내부 허용, 외부 명확한 에러 | 완료 |
| UT-CONFIG-004 | truncation 경계 검증 | `max_output_chars` 초과 문자열 | 길이 제한 + `...(truncated)` 포함 | 완료 |
| UT-RUN-001 | codex 미설치 처리 | `shutil.which("codex") -> None` | 설치/PATH 안내 에러 | 완료 |
| UT-RUN-002 | timeout 처리 | `subprocess.TimeoutExpired` 발생 | 타임아웃 에러 문자열 반환 | 완료 |
| UT-RUN-003 | non-zero exit 처리 | returncode!=0 + stderr 포함 | 코드/요약 stderr 포함 에러 | 완료 |
| UT-RUN-004 | 인증 실패 힌트 분기 | stderr에 auth/login 관련 키워드 | `codex login` 안내 에러 | 완료 |
| UT-RUN-005 | output file 성공 경로 | output 파일에 결과 존재 | 파일 결과 우선 반환 | 완료 |
| UT-RUN-006 | stdout fallback 경로 | output 파일 비어있음 + stdout 존재 | stdout 결과 반환 | 완료 |
| UT-RUN-007 | 빈 출력 처리 | output 파일/ stdout 모두 빈 값 | `Codex produced no output` 에러 | 완료 |
| UT-SERVER-001 | consult_codex 매핑 | 유효 입력 모델 | `CodexRequest`로 정확 매핑/호출 | 완료 |
| UT-SERVER-002 | consult_codex_with_stdin 래핑 | stdin_content + prompt | INPUT/TASK 래핑 포맷 정확 | 완료 |
| RG-STDOUT-001 | stdout 오염 회귀 | 서버 실행 중 로그 출력 점검 | stdout 프로토콜 외 출력 없음 | 완료 |
| IT-SMOKE-001 | e2e 스모크 | 로그인된 codex + MCP 등록 | 도구 2종 정상 응답 | 완료(스크립트) |

## PRD 수용기준(9.x) 매핑
- 9.1 Functional
  - #1 도구 노출/호출 가능: IT-SMOKE-001
  - #2 `consult_codex` 응답: IT-SMOKE-001, UT-SERVER-001
  - #3 `consult_codex_with_stdin` 응답: IT-SMOKE-001, UT-SERVER-002
  - #4 codex 미설치 에러: UT-RUN-001
  - #5 timeout 안정성: UT-RUN-002
- 9.2 Reliability
  - #1 stdout 오염 없음: RG-STDOUT-001
  - #2 non-zero exit + stderr 절단: UT-RUN-003
  - #3 truncation 표식: UT-CONFIG-004
- 9.3 Security
  - #1 기본 sandbox read-only: UT-CONFIG-001/002에서 기본값 검증
  - #2 allowlist 범위 외 차단: UT-CONFIG-003

## 실패 시 트리아지 규칙
1. 재현성 확인: 동일 명령 2회 이상 재실행 후 로그/오류 문자열 고정 여부 확인.
2. 분류: 설정 파싱(`config.py`), 실행(`runner.py`), 인터페이스(`server.py`) 중 원인 모듈 식별.
3. 영향도 평가:
   - P0: stdout 오염, 프로세스 크래시, 보안 정책 위반
   - P1: 도구 호출 실패/오류 메시지 오분류
   - P2: 포맷/문구/경계값 불일치
4. 대응:
   - P0/P1 즉시 수정 + 회귀 테스트 추가
   - P2 배치 수정 가능하나 릴리즈 전 반드시 테스트 반영
5. 종료 조건: 실패 케이스 재통과 + 연관 회귀 케이스 통과 확인.

## 합격 기준 체크
- [x] 테스트 계획에 최소 15개 케이스 정의
- [x] PRD 기능/신뢰성/보안 수용기준 매핑 포함
- [x] 실행 명령 재현 가능 형태로 명시
- [x] 자동화/수동 구분 및 후속 보강 범위 명시
- [x] 모든 M1 케이스 구현/실행 상태 반영
