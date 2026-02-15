# Claude Code + Codex MCP 서브에이전트 활용 Q&A 정리

> 작성일: 2026-02-15 (최종 업데이트: 2026-02-15)
> 프로젝트: codex-mcp-bridge

---

## 목차

- [Q1. Claude에서 Codex CLI를 사용할 수 있는가?](#q1)
- [Q2. Claude 사용량 소진 시 Codex로 대체 가능한가?](#q2)
- [Q3. 서브에이전트/멀티에이전트로 어떻게 활용하는가?](#q3)
- [Q4. 서브에이전트(Task 도구)란 무엇인가?](#q4)
- [Q5. 다른 에이전트 프로그램에서도 서브에이전트 개념이 있는가?](#q5)
- [Q6. Task 도구를 직접 구현하려면?](#q6)
- [Q7. 서브에이전트의 순차/병렬 실행은 어떻게 동작하는가?](#q7)
- [Q8. 컨텍스트 격리란 정확히 무엇인가?](#q8)
- [Q9. Claude Code와 OpenCode의 순차/병렬 트리거 방식은?](#q9)
- [Q10. OpenCode가 사용자 개입이 더 많다는 주장의 검증](#q10)
- [참고 링크](#참고-링크)

---

<a id="q1"></a>
## Q1. Claude에서 Codex CLI를 사용할 수 있는가?

**A: 가능하다.**

`codex-bridge` MCP 서버를 통해 Claude Code 세션 안에서 Codex CLI를 호출할 수 있다.

사용 가능한 도구 2가지:
- `consult_codex` — 단일 프롬프트를 보내고 결과를 받음
- `consult_codex_with_stdin` — 큰 입력 콘텐츠와 함께 작업 프롬프트를 보냄

검증 방법:
```
consult_codex(query="Say hello and confirm you are working.")
→ "Hello — I'm here and working on your request."
```

---

<a id="q2"></a>
## Q2. Claude 사용량이 소진됐을 때 모든 동작을 Codex로 대체할 수 있는가?

**A: 불가능하다.**

### 구조적 한계

```
┌─────────────────────────────────┐
│  Claude Code 세션 (오케스트레이터)  │  ← Claude API 사용량 소비
│                                 │
│  ┌───────────┐  ┌────────────┐  │
│  │ Read/Edit │  │ Codex MCP  │  │  ← 도구들 (Claude가 호출)
│  └───────────┘  └────────────┘  │
└─────────────────────────────────┘
```

- Claude가 오케스트레이터 역할을 한다. 요청 이해, 도구 선택, 결과 종합 모두 Claude API를 소비한다.
- Codex MCP는 Claude가 호출하는 도구 중 하나일 뿐, Claude를 대체하지 않는다.
- Claude 사용량이 소진되면 세션 자체가 멈추므로 Codex를 호출할 주체가 없어진다.

### 대안

1. **Codex CLI 직접 사용** — 터미널에서 `codex` 명령어를 직접 실행하면 Codex(OpenAI) 사용량만 소비
2. **작업 분배** — 단순 코드 생성/변환은 Codex MCP로 위임하고, Claude는 오케스트레이션만 담당하면 Claude 토큰 소비 절감 가능

---

<a id="q3"></a>
## Q3. 서브에이전트/멀티에이전트로 어떻게 활용할 수 있는가?

### 활용 패턴 3가지

#### 패턴 1: 직접 도구 호출 — 생성→검토 파이프라인

Codex가 코드를 생성하고 Claude가 검토/수정하는 방식. 서브에이전트를 사용하지 않는다.

```
Claude (메인)
  ├─ Read (소스 코드 읽기)              ← 도구 호출
  ├─ consult_codex_with_stdin          ← 도구 호출 (Codex에 생성 위임)
  └─ Edit (결과 검토 후 적용)           ← 도구 호출
```

#### 패턴 2: 서브에이전트 + Codex 병렬 분석

같은 문제를 Claude 서브에이전트와 Codex가 동시에 다른 관점으로 분석하는 방식.

```
Claude (메인)
  ├─ Task(서브에이전트) → Claude가 코드 분석    ← 서브에이전트 (병렬)
  └─ consult_codex → Codex가 코드 분석          ← 도구 호출 (병렬)
  │
  └─ 두 결과 종합
```

#### 패턴 3: 테스트/보일러플레이트 대량 생성

기존 코드 기반으로 Codex가 테스트 코드를 생성하고 Claude가 검증하는 방식.

```
Claude → 소스 + 기존 테스트 읽기
      → Codex에 누락 테스트 생성 위임
      → 생성된 테스트 검토 + 적용
      → pytest 실행해서 확인
```

### 패턴별 비교

| 패턴 | 서브에이전트 사용 | 방식 | Claude 토큰 절약 |
|------|:-:|---|:-:|
| 생성→검토 파이프라인 | 아니오 | Claude가 도구를 순차 호출 | 높음 |
| 병렬 분석 | 예 | 서브에이전트 + Codex 병렬 | 중간 |
| 테스트 대량 생성 | 아니오 | Codex에 생성 위임 후 검증 | 높음 |

---

<a id="q4"></a>
## Q4. 서브에이전트(Task 도구)란 무엇인가?

### 정의

Claude Code의 **Task 도구**로 생성되는 **독립적인 에이전트 프로세스**.

```python
Task(
    subagent_type="general-purpose",
    prompt="runner.py의 보안 취약점 분석해줘",
    name="security-analyzer"
)
```

### 핵심 특징

- **별도 프로세스**로 실행 (메인 에이전트와 컨텍스트 분리)
- **병렬 실행** 가능 (여러 서브에이전트 동시 실행)
- 작업 완료 후 **결과만 메인에게 반환**

### 에이전트 종류별 가용 도구

| 에이전트 타입 | 가용 도구 | Task 도구 보유 | 특징 |
|---|---|:-:|---|
| **메인 Claude** | 모든 도구 | O | 서브에이전트 생성 가능 |
| **general-purpose** | 모든 도구 | O | 서브에이전트 중첩 생성 가능 |
| **Explore** | Glob, Grep, Read 등 | X | 읽기 전용, 코드 탐색 특화 |
| **Plan** | Glob, Grep, Read 등 | X | 읽기 전용, 설계/계획 특화 |
| **Bash** | Bash만 | X | 명령어 실행만 |
| **claude-code-guide** | Glob, Grep, Read, Web | X | Claude Code 관련 질문 |

### 중첩 구조

```
메인 Claude ─── Task ──→ general-purpose (Task 있음)
                              └─ Task ──→ 또 다른 서브에이전트 (중첩 가능)

메인 Claude ─── Task ──→ Explore (Task 없음)
                              └─ 더 이상 서브에이전트 생성 불가
```

---

<a id="q5"></a>
## Q5. 다른 에이전트 프로그램에서도 서브에이전트 개념이 있는가?

### 주요 도구별 비교

| 도구 | 서브에이전트 | 상태 |
|---|:-:|---|
| **Claude Code** | O | Task 도구로 네이티브 지원. 병렬 실행, 팀 구성 가능 |
| **Codex CLI** | X | 미구현. GitHub 이슈 #2604에서 305+ 투표로 요청 중 |
| **OpenCode** | O | 10개 내장 에이전트 + Sisyphus-Junior (카테고리별 동적 생성) |
| **Aider** | X | Architect/Editor 모드만 존재 (순차 실행) |
| **Continue** | △ | 서브에이전트 내부 테스트 중. 미공개 |
| **Cline** | △ | 기본 CLI 서브프로세스만 가능. 멀티에이전트는 논의 중 |

### Codex CLI의 우회 방법

네이티브 서브에이전트가 없지만 외부 오케스트레이션으로 유사 구현 가능:

```
방법 A: MCP Server + Agents SDK (공식)
┌─ Agents SDK (오케스트레이터) ─┐
│  ├─ Codex (MCP 서버로 실행)   │
│  ├─ Codex (또 다른 인스턴스)   │
│  └─ 다른 에이전트             │
└──────────────────────────────┘

방법 B: 수동 병렬 실행 (커뮤니티)
supervisor가 작업 목록 생성 → 여러 codex exec 병렬 실행
```

---

<a id="q6"></a>
## Q6. Task 도구(서브에이전트 스포너)를 직접 구현하려면?

### 핵심 구성요소

```
┌─ 오케스트레이터 (메인 에이전트) ──────────────────┐
│                                                  │
│  1. 에이전트 루프 (while loop + LLM 호출)         │
│  2. 도구 레지스트리 (허용 도구 정의)               │
│  3. 서브에이전트 스포너                            │
│     ├─ 컨텍스트 격리 (별도 메시지 히스토리)         │
│     ├─ 도구 권한 관리 (에이전트별 허용 도구)        │
│     ├─ 프로세스 관리 (병렬 실행, 타임아웃)          │
│     └─ 결과 수집 (완료 후 메인에 반환)             │
│  4. 상태 관리 (공유 상태 또는 메시지 패싱)          │
└──────────────────────────────────────────────────┘
```

### 최소 구현 예시 (~400줄 Python)

```python
# 1. 에이전트 정의
class SubAgent:
    def __init__(self, name, allowed_tools, llm_client):
        self.name = name
        self.allowed_tools = allowed_tools  # 도구 권한 제한
        self.messages = []                  # 독립된 컨텍스트
        self.llm = llm_client

    def run(self, task: str) -> str:
        self.messages = [{"role": "user", "content": task}]
        while True:
            response = self.llm.chat(self.messages, tools=self.allowed_tools)
            if response.is_final:
                return response.content
            tool_result = execute_tool(response.tool_call)
            self.messages.append(tool_result)

# 2. 오케스트레이터
class Orchestrator:
    def spawn_subagent(self, agent_type, task):
        agent = SubAgent(
            name=agent_type,
            allowed_tools=TOOL_PERMISSIONS[agent_type],
            llm_client=self.llm
        )
        return agent.run(task)

    def spawn_parallel(self, tasks):
        with ThreadPoolExecutor() as pool:
            futures = [pool.submit(self.spawn_subagent, t.type, t.task) for t in tasks]
            return [f.result() for f in futures]

# 3. 도구 권한 매핑
TOOL_PERMISSIONS = {
    "explore": ["read", "glob", "grep"],
    "general": ["read", "write", "edit", "bash"],
    "bash":    ["bash"],
}
```

### 활용 가능한 프레임워크

| 프레임워크 | 특징 | 적합한 경우 |
|---|---|---|
| **LangGraph** | 그래프 기반 워크플로우, DAG 지원 | 복잡한 의존성 있는 작업 |
| **CrewAI** | 역할 기반 팀 구성 | 명확한 역할 분담 필요 시 |
| **AutoGen** | 대화형 멀티에이전트 | 에이전트 간 토론/협업 |
| **Tiny Agents** | MCP 기반, ~70줄 | 가볍게 시작하고 싶을 때 |

---

<a id="q7"></a>
## Q7. 서브에이전트의 순차/병렬 실행은 어떻게 동작하는가?

> Q3에서 "병렬로 나눠서 동시 실행"이라고 설명했으나, 일반적인 서브에이전트는 순차 실행이 기본이 아닌가?라는 질문에서 비롯됨.

### 순차 실행이 기본이다

```
메인 ─── 작업 위임 ──→ 서브에이전트
         (대기 중...)     작업 수행 중...
         (대기 중...)     작업 수행 중...
메인 ←── 결과 반환 ───  완료
이어서 작업 계속
```

위임 → 대기 → 결과 수신 → 계속 진행. 이것이 기본이자 가장 흔한 패턴이다.

### 병렬은 특수한 경우

서로 의존성이 없는 독립 작업이 여러 개일 때만 가능하다:

```
메인 ─┬─ Task A (파일 A 분석) ──→ 결과 A ─┐
      ├─ Task B (파일 B 분석) ──→ 결과 B ─┼─→ 종합
      └─ Task C (파일 C 분석) ──→ 결과 C ─┘
```

대부분의 실제 작업은 이전 결과에 따라 다음 단계가 달라지므로 순차 실행이 맞다:

```
메인 → 서브A: "구조 분석해줘"
         ↓ 결과에 따라
메인 → 서브B: "A 결과를 바탕으로 리팩토링해줘"  ← 병렬 불가
```

---

<a id="q8"></a>
## Q8. 컨텍스트 격리란 정확히 무엇인가?

> Q3에서 "컨텍스트가 오염된다 → 별도 에이전트로 격리"라고 설명했으나, 서브에이전트도 이전 컨텍스트를 전달받지 않느냐는 질문에서 비롯됨.

### 서브에이전트는 이전 컨텍스트를 받지 않는다

Claude Code의 서브에이전트는 **새로운 빈 컨텍스트**에서 시작한다:

```
메인 에이전트의 컨텍스트:
┌─────────────────────────────────┐
│ 사용자 질문                      │
│ 파일 A 읽은 내용 (500줄)         │
│ 파일 B 읽은 내용 (300줄)         │
│ 이전 대화 10턴                   │
│ 검색 결과 5건                    │
│ ... (컨텍스트가 점점 커짐)        │
└─────────────────────────────────┘

서브에이전트가 받는 것:
┌─────────────────────────────────┐
│ prompt: "runner.py의 보안 분석"  │  ← 이것만 받음
│                                 │
│ (이전 대화, 파일 내용 등 없음)     │
└─────────────────────────────────┘
```

### "컨텍스트 오염"의 정확한 의미

오염 = 서브에이전트의 컨텍스트가 더러워진다는 뜻이 **아니다**.
오염 = **메인 에이전트의 컨텍스트 윈도우가 불필요한 정보로 가득 차는 것**이다.

```
서브에이전트 없이 직접 탐색하면:
  메인 컨텍스트에 쌓이는 것:
  ├─ Grep 결과 1 (200줄)         ← 메인 컨텍스트에 들어감
  ├─ Grep 결과 2 (150줄)         ← 메인 컨텍스트에 들어감
  ├─ 파일 읽기 1 (400줄)          ← 메인 컨텍스트에 들어감
  └─ ... 탐색할수록 계속 쌓임
  → 정작 중요한 작업을 할 때 컨텍스트 공간이 부족해짐

서브에이전트에 위임하면:
  서브에이전트 내부 (격리됨):
  ├─ Grep 결과 1 (200줄)
  ├─ 파일 읽기 1 (400줄)
  └─ ... 여기서 다 처리하고 버려짐

  메인 컨텍스트에 돌아오는 것:
  └─ "분석 결과: 3가지 취약점 발견..."  ← 요약된 결과만 받음
  → 메인 컨텍스트가 깨끗하게 유지됨
```

### 필요한 맥락은 prompt에 직접 넣어줘야 한다

```python
Task(
    prompt="""
    다음 코드의 보안 취약점을 분석해줘.

    [배경] 이 프로젝트는 MCP 서버이고, subprocess로 외부 CLI를 실행한다.
    [파일 경로] src/codex_bridge_mcp/runner.py
    [주의 사항] sandbox 모드가 read-only인지 확인할 것
    """,
    subagent_type="Explore"
)
```

서브에이전트가 이전 대화를 자동으로 아는 것이 아니라, **메인이 필요한 맥락을 선별해서 prompt로 전달**하는 구조이다.

---

<a id="q9"></a>
## Q9. Claude Code와 OpenCode의 순차/병렬 트리거 방식 비교

### 두 시스템 모두 모델이 자동 판단한다

사용자가 명시적으로 지시할 필요가 없다. 메인 에이전트(모델)가 작업 의존성을 판단해서 결정한다.

### 트리거 메커니즘: 둘 다 동일한 원리

```
병렬 실행 조건: LLM이 한 응답에 여러 Tool Call을 생성

┌─ LLM 응답 ──────────────────────┐
│  Tool Call 1: Task(explore, A)   │
│  Tool Call 2: Task(explore, B)   │  ← 동시에 실행됨
│  Tool Call 3: Task(librarian, C) │
└──────────────────────────────────┘

순차 실행 조건: LLM이 응답마다 Tool Call을 하나씩 생성

┌─ LLM 응답 1 ─────────────┐
│  Tool Call: Task(분석)     │  → 결과 대기
└───────────────────────────┘
┌─ LLM 응답 2 ─────────────┐
│  Tool Call: Task(구현)     │  → 분석 결과 활용
└───────────────────────────┘
```

### 비교표

| | Claude Code | OpenCode |
|---|---|---|
| **병렬 트리거** | 한 응답에 Task 여러 개 | 한 응답에 tool call 여러 개 |
| **순차 트리거** | 응답마다 Task 하나씩 | `tasks.pop()` 루프로 하나씩 |
| **결정 주체** | LLM이 자동 판단 | LLM이 자동 판단 |
| **프롬프트 가이드** | "Launch multiple agents concurrently whenever possible" | "Launch multiple agents concurrently whenever possible" |
| **사용자 개입** | 선택 사항 (원하면 명시적 지시 가능) | 선택 사항 (원하면 @멘션, 설정 가능) |

프롬프트 가이드가 거의 동일한 문구이다. 두 시스템 모두 "가능하면 병렬로 실행하라"고 모델에게 안내하고, 모델이 의존성을 판단해서 결정한다.

### 사용자가 개입할 수도 있다

자동이 기본이지만, 명시적 지시도 가능하다:

```
Claude Code:
  "세 파일을 병렬로 동시에 분석해줘"     → 병렬 실행
  "하나씩 순서대로 분석해줘"             → 순차 실행

OpenCode:
  @explore "src/ 구조 파악해줘"          → 특정 에이전트 직접 지정
  설정에서 실행 순서 조정 가능            → Issue #6470
```

---

<a id="q10"></a>
## Q10. "OpenCode가 사용자 개입이 더 많다"는 주장의 검증

> Q9의 답변에서 "Claude Code는 모델이 알아서 판단하는 쪽이고, OpenCode는 사용자/설정이 더 많이 개입하는 구조"라고 주장했으나, 그 근거는 무엇인지에 대한 질문에서 비롯됨.

### 결론: 해당 주장은 틀렸다

실제 코드 분석 결과(~/Desktop/real-web/opencode, ~/Desktop/real-web/oh-my-opencode), 두 시스템의 사용자 경험은 거의 동일하다.

### 잘못된 추론의 원인

```
근거로 삼은 것:                      실제 의미:
───────────────────────────────────────────────────
위임 도구 3가지 존재              →  AI가 내부적으로 선택 (사용자가 고르는 게 아님)
(call_omo_agent, sisyphus_task,     - call_omo_agent: explore/librarian만 (하드코딩)
 background_task)                   - sisyphus_task: 카테고리 or 에이전트 지정
                                    - background_task: 범용 백그라운드

11개 에이전트, 41개 훅           →  사전 구성되어 자동으로 작동
                                    - 10개 내장 + Sisyphus-Junior (동적 생성)
                                    - 문서: "Most users don't need to configure anything manually"

실행 순서 설정 이슈 (Issue #6470) →  선택적 옵션 (필수 아님)
```

**시스템 아키텍처의 복잡성을 사용자 부담으로 잘못 등치시킨 것이다.** 구성 요소가 많다고 해서 사용자가 더 많이 개입해야 하는 것은 아니다.

### 실제 코드 기반 검증 결과

#### OpenCode의 자동 에이전트 선택 (Sisyphus 오케스트레이터)

Sisyphus의 시스템 프롬프트에 동적으로 Delegation Table이 생성된다:

```
### Delegation Table (sisyphus.ts에서 동적 생성):

| Domain           | Delegate To                  | Trigger          |
|------------------|------------------------------|------------------|
| Frontend UI/UX   | frontend-ui-ux-engineer      | Visual changes   |
| Exploration      | explore                      | Find X in code   |
| Research         | librarian                    | External docs    |
| Strategic        | oracle                       | Architecture     |
```

모델이 이 테이블을 참조하여 자동으로 적절한 에이전트를 선택한다.

#### Claude Code의 자동 에이전트 선택

Claude(메인 모델)가 작업 성격을 판단하여 subagent_type을 자동 선택한다:

```
탐색 작업 → Explore
설계 작업 → Plan
구현 작업 → general-purpose
명령 실행 → Bash
```

#### 사용자 경험 비교

| | Claude Code | OpenCode |
|---|---|---|
| 일상 사용 | 자연어로 지시 | 자연어로 지시 |
| 에이전트 선택 | 모델이 자동 판단 | 모델이 자동 판단 |
| 순차/병렬 결정 | 모델이 자동 판단 | 모델이 자동 판단 |
| 사용자 오버라이드 | 프롬프트로 지시 | 프롬프트 / @멘션 / config |
| 초기 설정 | 환경 변수 1개 | 플러그인 설치 (인터랙티브 인스톨러) |

**두 시스템 모두 사용자는 자연어로 지시하면 되고, 에이전트 선택과 실행 방식은 모델이 자동으로 판단한다.**

### 실제 차이점 (사용자 경험이 아닌 아키텍처)

```
Claude Code:
  에이전트: 5개 타입
  오케스트레이션: Claude 모델 하나가 모든 판단
  서브에이전트 중첩: general-purpose만 가능
  모델: Claude 전용

OpenCode (oh-my-opencode):
  에이전트: 10개 내장 + Sisyphus-Junior (카테고리별 동적 생성)
  오케스트레이션: Sisyphus가 Delegation Table 기반으로 판단
  서브에이전트 중첩: 불가 (재귀 방지를 위해 차단)
  모델: 75+ 프로바이더 지원 (에이전트별 다른 모델 바인딩)

  ┌─ Sisyphus (오케스트레이터, Opus 4.5) ─────────────────────┐
  │                                                           │
  │  ┌─ call_omo_agent ─┐  explore, librarian만 (하드코딩)    │
  │  ├─ sisyphus_task ──┤  카테고리 or 에이전트 직접 지정      │
  │  └─ background_task ┘  아무 에이전트나 백그라운드 실행     │
  │                                                           │
  │  Sisyphus-Junior가 다시 위임하는 것은 차단됨 (재귀 방지)    │
  └───────────────────────────────────────────────────────────┘
```

---

## 참고 링크

### Codex CLI 관련
- [Codex Subagent 요청 이슈 #2604](https://github.com/openai/codex/issues/2604)
- [Codex + Agents SDK 가이드](https://developers.openai.com/codex/guides/agents-sdk/)
- [Codex 서브에이전트 오케스트레이션 논의](https://github.com/openai/codex/discussions/3898)

### 멀티에이전트 아키텍처
- [Sub-Agent Spawning Pattern](https://agentic-patterns.com/patterns/sub-agent-spawning/)
- [Google 멀티에이전트 디자인 패턴](https://www.infoq.com/news/2026/01/multi-agent-design-patterns/)
- [Claude Code Agent Swarm Architecture](https://www.mejba.me/blog/claude-code-agent-swarm-architecture)
- [Task Tool and Context Isolation](https://deepwiki.com/shareAI-lab/mini-claude-code/6.2-task-tool-and-context-isolation)

### 프레임워크
- [LangGraph 공식 문서](https://www.langchain.com/langgraph)
- [LangGraph 서브에이전트 문서](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents)
- [CrewAI 공식 사이트](https://www.crewai.com/)
- [Tiny Agents (~70줄 구현)](https://huggingface.co/blog/tiny-agents)

### 다른 코딩 에이전트
- [Aider 멀티에이전트 제안](https://github.com/aider-ai/aider/issues/4428)
- [Continue 서브에이전트 이슈](https://github.com/continuedev/continue/issues/9550)
- [Cline 멀티에이전트 논의](https://github.com/cline/cline/discussions/489)

### OpenCode / oh-my-opencode
- [OpenCode Agents 문서](https://opencode.ai/docs/agents/)
- [oh-my-opencode Agent Orchestration Overview](https://deepwiki.com/code-yeongyu/oh-my-opencode/4.1-agent-orchestration-overview)
- [oh-my-opencode Background Execution System](https://deepwiki.com/code-yeongyu/oh-my-opencode/6-background-execution-system)
- [True Async Sub-Agent Delegation 이슈 #5887](https://github.com/anomalyco/opencode/issues/5887)
- [Queue Execution Order 설정 이슈 #6470](https://github.com/anomalyco/opencode/issues/6470)

### Claude Code Agent Teams
- [Claude Code Agent Teams 문서](https://code.claude.com/docs/en/agent-teams)
- [Claude Code Agent Teams 튜토리얼](https://claudefa.st/blog/guide/agents/agent-teams)

### 실제 코드 분석 소스
- `~/Desktop/real-web/opencode/packages/opencode/src/agent/agent.ts` — 에이전트 정의 및 선택 로직
- `~/Desktop/real-web/opencode/packages/opencode/src/tool/task.ts` — TaskTool 구현
- `~/Desktop/real-web/opencode/packages/opencode/src/session/prompt.ts` — 세션 루프 및 작업 실행
- `~/Desktop/real-web/oh-my-opencode/src/agents/sisyphus.ts` — Sisyphus 오케스트레이터 (641줄)
- `~/Desktop/real-web/oh-my-opencode/src/agents/sisyphus-junior.ts` — 카테고리별 동적 에이전트
- `~/Desktop/real-web/oh-my-opencode/src/tools/call-omo-agent/tools.ts` — explore/librarian 위임
- `~/Desktop/real-web/oh-my-opencode/src/tools/sisyphus-task/tools.ts` — 카테고리/에이전트 위임
- `~/Desktop/real-web/oh-my-opencode/src/features/background-agent/manager.ts` — 백그라운드 작업 관리
