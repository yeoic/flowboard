---
name: flowboard
description: 영상 기획 화면(flowboard)을 열거나 video/ 기획서를 만들고 고칠 때, 그리고 영상 일(대본 · 컷 목록 · 자막 · 편집 코드 · 트랜지션 · 효과 · 배경음악 · 효과음 · 쇼츠/롱폼)을 시작할 때 사용한다. "flowboard 열어줘", "영상 기획", "새 영상", "brief.md", "늘 하는 말", video/*/brief.md 가 있는 프로젝트에서 영상 작업을 할 때.
---

# flowboard

저장소: `~/Projects/flowboard` (github.com/yeoic/flowboard). 명령: `flowboard` (`flowboard.py` 심볼릭 링크).

## 화면 열기

1. 이미 떠 있는지 본다: `curl -s http://127.0.0.1:8790/api/videos`
2. 없으면 프로젝트 루트에서 켠다. 프로젝트 `.claude/launch.json` 에 아래 항목이 있으면 preview 도구로 켜고, 없으면 추가한다.
   ```json
   { "name": "flowboard", "runtimeExecutable": "flowboard", "runtimeArgs": [".", "--port", "8790", "--no-open"], "port": 8790 }
   ```
   preview 도구가 없으면 터미널(백그라운드)에서 `flowboard <프로젝트> --no-open`.
3. 사용자가 볼 브라우저로 연다: `open -a "Google Chrome" http://127.0.0.1:8790/#<영상 이름>`
4. 서버 코드(`flowboard.py`)를 고쳤으면 서버를 다시 켠다. `editor.html` 만 고쳤으면 새로 고침으로 충분하다.

## 영상 일을 할 때

- 위치: `<프로젝트>/video/style.json`(늘 하는 말 `rules` · 새 영상 기본값 `defaults`), `video/<영상>/brief.json`(화면이 읽고 씀) · `brief.md`(사람 · Claude가 읽는 기획서).
- 대본 · 컷 목록 · 자막 · 편집 코드 · 음악 고르기를 시작하기 전에 `video/style.json` 의 `rules` 와 그 영상의 `brief.md` 를 먼저 읽고 따른다.
  "쓰지 않는다"로 고른 트랜지션 · 효과는 쓰지 않고, 목록에 없는 것은 먼저 묻는다.
- 기획서에 콘티(`shots`)가 있으면 그것이 기준이다. 컷 순서 · 길이(`sec`) · 화면(`kind`) · 소재(`asset`, `video/<영상>/` 기준 경로) · 카메라 · 자막 · 들어올 때 트랜지션(`trans`) · 효과(`fx`) · 효과음(`sfx`: `{k, at}`, `at` 은 컷 시작 기준 초) · 음악 크기(`music`)를 바꾸지 않고 따른다.
  코드(Remotion 등)로 만들면 `brief.json` 의 `shots` 를 그대로 읽어 그리는 구조로 짜서, 고칠 때 데이터만 바꾸면 되게 한다. "없는 소재 파일" · "소재 미정"은 작업 전에 먼저 알린다.
- 콘티를 새로 짜 달라고 하면 `brief.json` 의 `shots` 에 위 필드로 적고 `brief.md` 를 맞춘 뒤, 화면의 "콘티 · 1차 안" 칸에서 재생해 보라고 안내한다(렌더 전에 검토).
- 결과물은 기획서 "도구"의 "Claude가 넘길 것"(SRT · 컷 목록 · EDL · Remotion 코드 · ffmpeg 스크립트 등) 형태로 낸다.
- 쇼츠는 기획서의 안전 영역(위 · 아래 · 오른쪽)에 자막 · 얼굴 · 중요한 글자를 두지 않는다.
- 사용자가 같은 지적을 두 번 하거나 "앞으로는 ~"이라고 하면 `video/style.json` 의 `rules` 에 `{"area": "…", "text": "…"}` 한 줄로 추가하고 알린다.
  area 는 스토리 · 컷 · 트랜지션 · 자막 · 음악 · 화면 · 도구 · 기타 중 하나. 이 영상에만 해당하면 `brief.json` 의 `notes` 에 적는다.
- `brief.json` 을 직접 고쳤으면 `brief.md` 도 같이 맞춘다(화면에서 저장하면 다시 만들어진다). 화면이 떠 있으면 새로 고침해야 바뀐 파일이 보인다.
- 새 영상 기획을 부탁받으면 화면의 "+ 새 영상"을 안내하거나, `video/<날짜-이름>/brief.json` 을 `defaults` 를 바탕으로 만든다.

## 고도화할 때

- 화면은 `editor.html` 한 파일, 서버는 `flowboard.py` 한 파일이다. 둘 다 바깥 패키지 없이 유지한다.
- 고를 거리(스토리 구조 · 컷 · 트랜지션 · 효과 · 자막 · 음악 · 효과음 · 도구)는 `editor.html` 위쪽의 상수(`STORIES` · `CUTS` · `TRANS` · `EFFECTS` · `CAPS` · `MOODS` · `SFX` · `EDITORS`)에 있다.
  콘티의 화면 종류 · 카메라 · 트랜지션 시간 · 임시 비트는 `SHOT_KINDS` · `CAMS` · `TR_SEC` · `GROOVES` 에 있다.
  움직이는 예시가 있는 것(트랜지션 · 효과)은 같은 이름의 CSS 애니메이션도 같이 추가한다.
- 바꾼 뒤 확인: 서버를 켜고 모든 칸을 눌러 콘솔 오류가 없는지, 예시가 움직이는지, 저장하면 brief.md 가 만들어지는지 본다.
- 디자인 토큰은 Archify(MIT) 방식이다. 출처 표기(README · LICENSE)를 지우지 않는다.
