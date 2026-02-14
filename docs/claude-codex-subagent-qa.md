# Claude Code + Codex MCP 서브에이전트 활용 Q&A 정리

> 작성일: 2026-02-15
> 프로젝트: codex-mcp-bridge

---

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

## Q5. 다른 에이전트 프로그램에서도 서브에이전트 개념이 있는가?

### 주요 도구별 비교

| 도구 | 서브에이전트 | 상태 |
|---|:-:|---|
| **Claude Code** | O | Task 도구로 네이티브 지원. 병렬 실행, 팀 구성 가능 |
| **Codex CLI** | X | 미구현. GitHub 이슈 #2604에서 305+ 투표로 요청 중 |
| **OpenCode** | O | 4개 내장 에이전트 + 서브에이전트 위임 지원 |
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
