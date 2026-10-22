# flowboard

영상 한 편을 만들기 전에 **형식 · 스토리 · 컷 편집 · 트랜지션 · 효과 · 자막 · 배경음악 · 효과음 · 도구 · 레퍼런스**를 고르고,
매번 하는 지적은 **늘 하는 말**로 모아 두는 로컬 도구입니다. 고른 내용은 프로젝트 안의 기획서(`brief.md`)로 남아서,
사람과 Claude가 같은 기준으로 편집합니다.

- 파이썬 3.10+ 기본 기능만 씁니다. 설치할 패키지가 없습니다.
- 이 컴퓨터(127.0.0.1)에서만 열립니다.

## 쓰는 법

```bash
flowboard                         # 지금 폴더를 프로젝트로 열기 → http://127.0.0.1:8790
flowboard ~/Videos/my-channel     # 다른 프로젝트 열기
flowboard --port 9000 --no-open
flowboard init ~/Videos/my-channel   # video/style.json(늘 하는 말 · 새 영상 기본값) 만들기
```

설치(한 번):

```bash
git clone https://github.com/yeoic/flowboard ~/Projects/flowboard
ln -s ~/Projects/flowboard/flowboard.py /opt/homebrew/bin/flowboard   # PATH 에 있는 아무 폴더
ln -s ~/Projects/flowboard/skill ~/.claude/skills/flowboard            # Claude Code 스킬(선택)
```

## 고르는 것

| 칸 | 고르는 것 |
|---|---|
| 기본 | 쇼츠(9:16) · 롱폼(16:9) · 둘 다, 길이, 올릴 곳, 한 줄 기획, 보는 사람 |
| 스토리 | 구조 9가지(훅 → 핵심 → 반전, 3막, Top N, 결과 먼저 → 과정 → 공개 …). 구간 길이 · 긴장도 곡선 그림, 쇼츠는 "첫 3초" 표시 |
| 컷 편집 | 빠른 리듬 · 점프컷 · 비트 싱크 · 롱테이크 · 몽타주 · A롤/B롤 · J컷 · L컷 · 펀치 인 · 교차 편집 — 움직이는 타임라인 예시 |
| 트랜지션 | 하드 컷 · 디졸브 · 휩 팬 · 줌 · 와이프 · 매치 컷 · 가리고 넘기기 등 14가지 — A → B 애니메이션, 쓴다 / 안 쓴다 |
| 효과 | 글리치(지지직) · RGB 분리 · VHS · TV 노이즈 · 필름 그레인 · CRT · 흔들림 · 비트 줌 · 스트로브 · 반전 · 라이트 릭 · 레터박스 · 흑백 → 컬러 · 포커스 인 · 스피드 램프 · 프리즈 프레임 — 움직이는 예시와 어울리는 효과음 |
| 자막 | 말 자막 전체 · 단어 팝 · 위 제목 고정 · 키워드만 · 없음. 쇼츠 안전 영역(앱 UI가 덮는 곳) 표시 |
| 배경음악 | 분위기 9가지(BPM 빠르기로 움직이는 막대), BPM · 출처 · 볼륨 규칙 · 구간별 음악 |
| 효과음 | 휙 · 뽁 · 띵 · 딸깍 · 지지직 · 끊김 · 라이저 · 쿵 · 테이프 멈춤 · 스크래치 · 띠용 · 타자 — ▶ 로 바로 들어 보기(브라우저 합성 견본) |
| 도구 | 편집 프로그램(CapCut · Premiere · DaVinci · Final Cut · Vrew · Remotion · ffmpeg)과 Claude가 넘길 결과물, 촬영 · 자막 · 목소리 · AI 생성 · 썸네일 도구 |
| 레퍼런스 | 링크 · 구간 · 무엇을 가져올지(유튜브는 썸네일 표시) |
| 늘 하는 말 | 모든 영상 기획서에 들어가는 채널 규칙, "지금 선택을 새 영상 기본값으로" |
| 기획서 | 저장하면 만들어지는 `brief.md` 미리보기 · 복사 |

## 프로젝트 쪽 구조

```
<프로젝트>/video/
  style.json             늘 하는 말(rules) · 새 영상 기본값(defaults)
  <영상>/
    brief.json           이 화면이 읽고 쓰는 기획
    brief.md             사람 · Claude가 읽는 기획서(저장할 때 같이 만들어짐)
```

Claude Code에는 `video/<영상>/brief.md 읽고 시작해`라고 하면 됩니다. 스킬(`skill/SKILL.md`)을 연결해 두면 Claude가 영상 작업 전에
늘 하는 말과 기획서를 먼저 읽고, 같은 지적이 두 번 나오면 `style.json` 규칙에 스스로 추가합니다.

## 출처

화면의 색 · 글꼴 · 카드 모양은 [Archify](https://github.com/tt-a1i/archify)(MIT, © 2026 tt-a1i, © 2025 Cocoon AI)의 방식을 따랐습니다.
글꼴은 Google Fonts의 JetBrains Mono(OFL)를 씁니다.
