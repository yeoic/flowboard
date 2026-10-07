---
name: flowboard
description: 프로젝트의 개발 흐름·인프라·AI 워크플로우·Claude 설정을 보고 고치는 로컬 화면(flowboard)을 열거나, workflow/*/flow.json 을 만들고 고칠 때 사용한다. "편집 화면 열어줘", "flowboard 열어줘", "워크플로우 화면", "flow.json", "flowboard init", 단계 폴더(step-N)·실행 기록(runs/) 작업에서 사용.
---

# flowboard

저장소: `~/Projects/flowboard` (github.com/yeoic/flowboard). 명령: `flowboard` (`flowboard.py` 심볼릭 링크).

## 화면 열기

1. 이미 떠 있는지 본다: `curl -s http://127.0.0.1:8790/api/info`
2. 없으면 프로젝트 루트에서 켠다. 프로젝트 `.claude/launch.json` 에 아래 항목이 있으면 preview 도구로 켜고, 없으면 추가한다.
   ```json
   { "name": "flowboard", "runtimeExecutable": "flowboard", "runtimeArgs": [".", "--port", "8790", "--no-open"], "port": 8790 }
   ```
   preview 도구가 없으면 터미널(백그라운드)에서 `flowboard <프로젝트> --no-open`.
3. 사용자가 볼 브라우저로 연다: `open -a "Google Chrome" http://127.0.0.1:8790/#<탭>` (탭: dev · infra · workflow · claude)
4. 서버 코드(`flowboard.py`)를 고쳤으면 서버를 다시 켠다. `editor.html` 만 고쳤으면 새로 고침으로 충분하다.

흐름이 하나도 없는 프로젝트면 `flowboard init <프로젝트>` 로 기본 흐름을 만든다(이미 있는 흐름은 건드리지 않음).

## flow.json 약속

- 위치: `<프로젝트>/workflow/<흐름>/flow.json`. 형식은 저장소 `README.md` 의 flow.json 절이 기준이다.
- `tab` 으로 어느 탭에 나올지, `vocabulary` 로 칸 종류(dev | actor)를 정한다.
- 칸 위치(x, y)는 사용자가 화면에서 끌어 정한다. 새 칸을 넣을 때는 기존 칸과 겹치지 않게, 선이 다른 칸을 가로지르지 않게 놓는다(열 간격 250px, 줄 간격 120px 기준).
- 단계 스크립트는 모델·지시문을 `flow.json` 에서 읽는다(`lib/flowboard_run.py` 의 `agent_node`). 모델·지시문을 코드에 따로 적지 않는다 — 화면과 실제 실행이 어긋난다.
- 실행 기록은 `runs/<run-id>/<칸 id>/` 에 prompt.md · thinking.md · output.json · response.json · meta.json 으로 남긴다(`save_node_record`). `runs/` 는 git 에서 뺀다.

## 고도화할 때

- 화면은 `editor.html` 한 파일, 서버는 `flowboard.py` 한 파일이다. 둘 다 바깥 패키지 없이 유지한다.
- 바꾼 뒤 확인: 서버를 켜고 네 탭을 열어 콘솔 오류가 없는지, 칸 끌기·저장·마우스 강조가 되는지 본다.
- 디자인 토큰은 Archify(MIT) 방식이다. 출처 표기(README · LICENSE)를 지우지 않는다.
