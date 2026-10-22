---
name: flowboard
description: 프로젝트의 개발 흐름·인프라·AI 워크플로우·영상 기획·Claude 설정을 보고 고치는 로컬 화면(flowboard)을 열거나, workflow/*/flow.json · video/ 기획서를 만들고 고칠 때 사용한다. "편집 화면 열어줘", "flowboard 열어줘", "워크플로우 화면", "flow.json", "flowboard init", 단계 폴더(step-N)·실행 기록(runs/) 작업, 그리고 영상 편집·컷·자막·트랜지션·배경음악·쇼츠/롱폼 작업이나 video/*/brief.md 가 있는 프로젝트에서 영상 일을 시작할 때 사용.
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
3. 사용자가 볼 브라우저로 연다: `open -a "Google Chrome" http://127.0.0.1:8790/#<탭>` (탭: dev · infra · workflow · video · claude)
4. 서버 코드(`flowboard.py`)를 고쳤으면 서버를 다시 켠다. `editor.html` 만 고쳤으면 새로 고침으로 충분하다.

흐름이 하나도 없는 프로젝트면 `flowboard init <프로젝트>` 로 기본 흐름을 만든다(이미 있는 흐름은 건드리지 않음).

## flow.json 약속

- 위치: `<프로젝트>/workflow/<흐름>/flow.json`. 형식은 저장소 `README.md` 의 flow.json 절이 기준이다.
- `tab` 으로 어느 탭에 나올지, `vocabulary` 로 칸 종류(dev | actor)를 정한다.
- 칸 위치(x, y)는 사용자가 화면에서 끌어 정한다. 새 칸을 넣을 때는 기존 칸과 겹치지 않게, 선이 다른 칸을 가로지르지 않게 놓는다(열 간격 250px, 줄 간격 120px 기준).
- 단계 스크립트는 모델·지시문을 `flow.json` 에서 읽는다(`lib/flowboard_run.py` 의 `agent_node`). 모델·지시문을 코드에 따로 적지 않는다 — 화면과 실제 실행이 어긋난다.
- 실행 기록은 `runs/<run-id>/<칸 id>/` 에 prompt.md · thinking.md · output.json · response.json · meta.json 으로 남긴다(`save_node_record`). `runs/` 는 git 에서 뺀다.

## 영상 기획 (영상 탭)

- 위치: `<프로젝트>/video/style.json`(늘 하는 말 `rules` · 새 영상 기본값 `defaults`), `video/<영상>/brief.json`(화면이 읽고 씀) · `brief.md`(사람 · Claude가 읽는 기획서).
- 영상 일(대본, 컷 목록, 자막, 편집 코드, 음악 고르기)을 시작하기 전에 `video/style.json` 의 `rules` 와 그 영상의 `brief.md` 를 먼저 읽고 따른다. 기획서의 "Claude가 넘길 것"(SRT · 컷 목록 · Remotion 코드 등)에 맞는 형태로 결과를 낸다.
- 사용자가 같은 지적을 두 번 하거나 "앞으로는 ~"이라고 하면 `video/style.json` 의 `rules` 에 `{"area": "…", "text": "…"}` 한 줄로 추가하고 사용자에게 알린다. area 는 스토리 · 컷 · 트랜지션 · 자막 · 음악 · 화면 · 도구 · 기타 중 하나. 이 영상에만 해당하면 `brief.json` 의 `notes` 에 적는다.
- `brief.json` 을 직접 고쳤으면 `brief.md` 도 같이 맞춘다(화면에서 저장하면 다시 만들어진다). 화면이 떠 있으면 새로 고침해야 바뀐 파일이 보인다.
- 새 영상 기획을 부탁받으면 화면(`#video`)의 "+ 새 영상"을 안내하거나, `video/<날짜-이름>/brief.json` 을 `defaults` 를 바탕으로 만든다.

## 고도화할 때

- 화면은 `editor.html` 한 파일, 서버는 `flowboard.py` 한 파일이다. 둘 다 바깥 패키지 없이 유지한다.
- 바꾼 뒤 확인: 서버를 켜고 다섯 탭을 열어 콘솔 오류가 없는지, 칸 끌기·저장·마우스 강조가 되는지, 영상 탭의 미리보기가 움직이고 저장하면 brief.md 가 만들어지는지 본다.
- 디자인 토큰은 Archify(MIT) 방식이다. 출처 표기(README · LICENSE)를 지우지 않는다.
