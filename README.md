# flowboard

프로젝트의 **개발 흐름 · 인프라 · AI 워크플로우 · Claude 설정**을 한 화면에서 보고 고치는 로컬 도구입니다.
칸을 끌어 옮기고, 선을 잇고, 칸을 누르면 설정과 실제 파일·실행 기록이 열립니다. 고친 내용은 프로젝트 안의 `flow.json`에 저장됩니다.

- 파이썬 3.10+ 기본 기능만 씁니다. 설치할 패키지가 없습니다.
- 이 컴퓨터(127.0.0.1)에서만 열립니다.

## 쓰는 법

```bash
flowboard                      # 지금 폴더를 프로젝트로 열기 → http://127.0.0.1:8790
flowboard ~/Projects/my-app    # 다른 프로젝트 열기
flowboard --port 9000 --no-open
flowboard init ~/Projects/my-app   # workflow/ 에 기본 흐름(개발 · 인프라 · Claude · 예시 워크플로우) 만들기
```

설치(한 번):

```bash
git clone https://github.com/yeoic/flowboard ~/Projects/flowboard
ln -s ~/Projects/flowboard/flowboard.py /opt/homebrew/bin/flowboard   # PATH 에 있는 아무 폴더
ln -s ~/Projects/flowboard/skill ~/.claude/skills/flowboard            # Claude Code 스킬(선택)
```

## 탭

| 탭 | 무엇 | 칸 종류 |
|---|---|---|
| 개발 | 요청 → 확인 → 커밋 → 배포 | frontend · backend · database · cloud · security · messagebus · external |
| 인프라 | 서비스가 어디서 돌고 무엇과 연결되는지 | 위와 같음 |
| 워크플로우 | 사람 · 스크립트 · AI 에이전트가 주고받는 일 | 사람 · 스크립트 · AI 에이전트 · 외부 서비스 |
| Claude | CLAUDE.md · 메모리 · hook · 권한 · skill · agent | 개발 어휘. 칸을 누르면 실제 파일 내용 |

- 칸에 마우스를 올리면 연결된 칸과 선만 남고 나머지는 흐려집니다.
- 저장은 `Cmd+S` 또는 저장 버튼. 지시문(`prompt.md`)과 CLAUDE.md는 패널의 버튼으로 바로 저장됩니다.

## 프로젝트 쪽 구조

```
<프로젝트>/workflow/
  <흐름>/
    flow.json            칸 · 선 · 칸 설정(이 화면이 읽고 씀)
    step-N-이름/          단계 폴더(README · prompt.md · script.py)
    runs/<run-id>/       실행 기록(git 제외 권장)
```

### flow.json

```json
{
  "tab": "workflow",             // dev | infra | workflow | claude
  "vocabulary": "actor",         // dev(개발 어휘) | actor(사람 · 스크립트 · AI 에이전트 · 외부 서비스)
  "title": "레시피 등록 자동화",
  "summary": "한 줄 설명",
  "work":   [{ "name": "", "desc": "", "who": ["human"], "status": "동작함" }],
  "lanes":  [{ "label": "사람", "y": 30, "h": 110 }],
  "phases": [{ "label": "찾기", "x": 40 }],
  "nodes":  [{ "id": "judge", "kind": "agent", "name": "", "meta": "", "status": "동작함", "x": 290, "y": 210,
              "tag": "", "role": [], "runner": "claude -p", "model": "claude-sonnet-5-5", "tools": "",
              "step": "step-1-search", "prompt": "step-1-search/prompt.md",
              "inputs": [], "outputs": [], "criteria": [], "command": "", "runFiles": ["step-1.json"],
              "source": "claude-md" }],
  "edges":  [{ "from": "a", "to": "b", "label": "", "kind": "main" }]   // kind: main | loop | (없음)
}
```

- `status`: 동작함 · 고치는 중 · 명령만 있음 · 없음 · 사람
- `source`(Claude 탭): claude-md · memory · hooks · permissions · skills · agents
- `runFiles`: 실행 기록에서 이 칸에 같이 보여 줄 단계 결과 파일

### 단계 스크립트와 맞물리기

[`lib/flowboard_run.py`](lib/flowboard_run.py)의 `agent_node()`로 모델 · 지시문을 `flow.json`에서 읽고,
`save_node_record()`로 `runs/<run-id>/<칸 id>/`에 보낸 프롬프트 · 결과물 · 비용을 남기면 화면에 나옵니다.

## 출처

화면의 색 · 글꼴 · 칸 모양 · 연결 강조는 [Archify](https://github.com/tt-a1i/archify)(MIT, © 2026 tt-a1i, © 2025 Cocoon AI)의 방식을 따랐습니다.
글꼴은 Google Fonts의 JetBrains Mono(OFL)를 씁니다.
