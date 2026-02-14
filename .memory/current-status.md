# Codex MCP Bridge Lite - Current Status (2026-02-14)

## 목표/범위 요약 (PRD 기반)
- 목표: Claude CLI에서 MCP 도구를 통해 로컬 `codex exec`를 비대화식으로 호출하고 결과를 안정적으로 반환.
- 범위:
  - `consult_codex`
  - `consult_codex_with_stdin`
  - 기본 sandbox=`read-only`
  - 디렉터리 allowlist 정책
  - 출력 길이 제한/절단
  - 핵심 오류 케이스(미설치/인증/타임아웃/비정상 종료/출력 읽기 실패)
- 비범위:
  - Claude 모델 백엔드 교체
  - 원격/멀티테넌트 서비스화
  - 구독/인증 우회

## 완료된 구현 항목 체크리스트
- [x] FastMCP stdio 서버 엔트리포인트 구현 (`mcp.run(transport="stdio")`)
- [x] 공개 도구 2종 구현
  - [x] `consult_codex`
  - [x] `consult_codex_with_stdin`
- [x] `codex exec -` 비대화식 실행 구현
- [x] `--output-last-message` 파일 우선 결과 캡처 + stdout fallback
- [x] 기본 sandbox 값 및 override 처리 (`read-only` 기본)
- [x] 선택적 allowlist (`CODEX_ALLOWED_DIRS`) 적용
- [x] 출력 길이 제한 (`CODEX_MAX_OUTPUT_CHARS`) 및 `...(truncated)` 마커
- [x] 핵심 오류 처리
  - [x] codex CLI 미설치
  - [x] 인증 불가 힌트 (`codex login`)
  - [x] 타임아웃
  - [x] non-zero exit + stderr 절단
  - [x] 빈 출력 오류
- [x] README 설치/실행/등록 가이드 작성
- [x] 기본/확장 단위 테스트 작성 및 실행 통과
- [x] stdout 오염 회귀 스크립트 추가 (`scripts/check_stdout_clean.sh`)
- [x] 통합 스모크 스크립트 추가 (`scripts/it_smoke_codex_bridge.sh`)

## 파일 구조 스냅샷
- `/Users/dante/codex-mcp-bridge/pyproject.toml`
- `/Users/dante/codex-mcp-bridge/README.md`
- `/Users/dante/codex-mcp-bridge/src/codex_bridge_mcp/__init__.py`
- `/Users/dante/codex-mcp-bridge/src/codex_bridge_mcp/server.py`
- `/Users/dante/codex-mcp-bridge/src/codex_bridge_mcp/runner.py`
- `/Users/dante/codex-mcp-bridge/src/codex_bridge_mcp/config.py`
- `/Users/dante/codex-mcp-bridge/src/codex_bridge_mcp/types.py`
- `/Users/dante/codex-mcp-bridge/tests/test_config.py`
- `/Users/dante/codex-mcp-bridge/tests/test_runner.py`

## 환경/실행 명령
```bash
cd /Users/dante/codex-mcp-bridge
uv run codex-mcp-bridge
```

```bash
cd /Users/dante/codex-mcp-bridge
uv run --with '.[dev]' pytest
```

```bash
cd /Users/dante/codex-mcp-bridge
uv run python -m py_compile src/codex_bridge_mcp/*.py
```

```bash
cd /Users/dante/codex-mcp-bridge
./scripts/check_stdout_clean.sh
```

```bash
cd /Users/dante/codex-mcp-bridge
./scripts/it_smoke_codex_bridge.sh
```

## 최신 검증 결과
- 단위 테스트: `19 passed`
- 문법 컴파일 체크: `ok` (`py_compile` 성공)
- 모듈 import 확인: `import-ok True`
- stdout 오염 회귀 스크립트: `OK`
- 통합 스모크:
  - `consult_codex`: 성공 (`{"status":"ok"}`)
  - `consult_codex_with_stdin`: 성공 (JSON 응답 반환)

## 미완료/리스크
- 실제 Claude MCP 클라이언트 CLI 왕복(등록→호출) 완전 자동화는 아직 없음.
- `consult_codex_with_stdin`의 매우 큰 입력 처리(메모리/시간) 한계값 스트레스 테스트 미흡.
- strict JSON 보장(`--output-schema`)은 M2 항목으로 미구현.

## 다음 작업 우선순위
1. Claude CLI 기반 실제 MCP 호출 경로 자동화(등록/호출/해제) 스크립트화.
2. 대용량 stdin 입력 및 장시간 timeout 경계 스트레스 테스트 추가.
3. M2 준비: JSON schema 기반 응답 강제 옵션 설계 및 검증.
