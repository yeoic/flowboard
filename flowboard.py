#!/usr/bin/env python3
"""flowboard — 프로젝트의 개발 흐름 · 인프라 · AI 워크플로우 · 영상 기획 · Claude 설정을 한 화면에서 보고 고칩니다.

  flowboard                      # 지금 폴더를 프로젝트로 열기 → http://127.0.0.1:8790
  flowboard ~/Projects/my-app    # 다른 프로젝트 열기
  flowboard --port 9000 --no-open
  flowboard init [프로젝트]       # workflow/ 에 기본 흐름(개발 · 인프라 · Claude), video/ 에 채널 규칙 만들기

파이썬 기본 기능만 씁니다(설치 없음). 이 컴퓨터(127.0.0.1)에서만 열립니다.
쓰기는 <프로젝트>/workflow/<흐름>/ 안의 flow.json 과 .md 파일, <프로젝트>/video/ 안의 style.json 과
<영상>/brief.json · brief.md, 그리고 프로젝트 CLAUDE.md 로 제한합니다.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import sys
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = pathlib.Path(__file__).resolve().parent
EDITOR = HERE / "editor.html"
TEMPLATES = HERE / "templates"
VIDEO_STYLE = TEMPLATES / "video" / "style.json"
HOME_CLAUDE = pathlib.Path.home() / ".claude"
MAX_FILE_BYTES = 400_000          # 실행 기록 파일 하나를 화면에 보낼 때의 상한
TABS = ("dev", "infra", "workflow", "claude")


class Project:
    """열린 프로젝트. 흐름은 <프로젝트>/<flows_dir>/<흐름>/flow.json, 영상 기획은 <프로젝트>/video/ 입니다."""

    def __init__(self, root: pathlib.Path, flows_dir: str = "workflow"):
        self.root = root.resolve()
        self.flows = self.root / flows_dir
        self.videos = self.root / "video"

    @property
    def main_checkout(self) -> pathlib.Path:
        """Claude Code worktree(.claude/worktrees/…) 안이면 메인 체크아웃을 돌려줍니다."""
        text = str(self.root)
        return pathlib.Path(text.split("/.claude/worktrees/")[0]) if "/.claude/worktrees/" in text else self.root

    @property
    def memory_dir(self) -> pathlib.Path:
        """Claude 메모리 폴더: ~/.claude/projects/<메인 체크아웃 경로의 / 를 - 로>/memory"""
        return HOME_CLAUDE / "projects" / str(self.main_checkout).replace("/", "-") / "memory"

    def flow_dir(self, name: str) -> pathlib.Path:
        path = (self.flows / name).resolve()
        if path.parent != self.flows.resolve() or not (path / "flow.json").exists():
            raise ValueError(f"흐름 '{name}'이 없습니다.")
        return path

    def list_flows(self) -> list[dict]:
        found = []
        for path in sorted(self.flows.glob("*/flow.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            tab = data.get("tab") if data.get("tab") in TABS else "workflow"
            found.append({"name": path.parent.name, "tab": tab, "title": data.get("title") or path.parent.name})
        return found

    def video_dir(self, name: str) -> pathlib.Path:
        path = (self.videos / name).resolve()
        if not name.strip() or name.startswith(".") or path.parent != self.videos.resolve():
            raise ValueError(f"영상 이름 '{name}'은 쓸 수 없습니다.")
        return path

    def list_videos(self) -> list[dict]:
        """영상 기획 목록. 최근에 고친 것부터."""
        found = []
        for path in sorted(self.videos.glob("*/brief.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            found.append({"name": path.parent.name, "title": data.get("title") or path.parent.name, "format": data.get("format", "")})
        return found

    def video_style(self) -> dict:
        """채널 규칙(늘 하는 말)과 새 영상 기본값. 아직 없으면 templates/video/style.json."""
        path = self.videos / "style.json"
        return json.loads((path if path.exists() else VIDEO_STYLE).read_text(encoding="utf-8"))

    def ensure_video_style(self) -> None:
        self.videos.mkdir(parents=True, exist_ok=True)
        if not (self.videos / "style.json").exists():
            shutil.copy(VIDEO_STYLE, self.videos / "style.json")


PROJECT: Project


# ── 파일 읽기 도우미 ─────────────────────────────────────────────────────────
def inside(base: pathlib.Path, relative: str) -> pathlib.Path:
    """base 안의 경로만 허용합니다(../ 로 밖에 나가는 경로 차단)."""
    path = (base / relative).resolve()
    if base.resolve() not in path.parents and path != base.resolve():
        raise ValueError(f"허용되지 않은 경로: {relative}")
    return path


def read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")[:MAX_FILE_BYTES]


def front_matter(text: str) -> dict[str, str]:
    """--- 사이의 한 줄 값(name · description)과 들여쓴 type 을 읽습니다."""
    meta: dict[str, str] = {}
    if not text.startswith("---"):
        return meta
    for line in text.split("\n")[1:]:
        if line.strip() == "---":
            break
        key, sep, value = line.strip().partition(":")
        value = value.strip().strip('"').strip("'")
        if not sep or not value or value in (">", "|"):
            continue
        if not line.startswith(" ") or key == "type":
            meta.setdefault(key, value)
    return meta


def list_runs(flow: pathlib.Path) -> list[dict]:
    runs_dir = flow / "runs"
    if not runs_dir.exists():
        return []
    runs = sorted((p for p in runs_dir.iterdir() if p.is_dir()), key=lambda p: p.stat().st_mtime, reverse=True)
    return [{"id": p.name, "mtime": p.stat().st_mtime} for p in runs]


def read_run(flow: pathlib.Path, run_id: str) -> dict:
    """실행 기록 폴더의 파일을 {상대 경로: 내용}으로. JSON은 풀어서, 큰 파일은 앞부분만."""
    run_path = inside(flow / "runs", run_id)
    files: dict[str, object] = {}
    for path in sorted(run_path.rglob("*")):
        if not path.is_file():
            continue
        key = str(path.relative_to(run_path))
        raw = path.read_bytes()
        text = raw[:MAX_FILE_BYTES].decode("utf-8", "replace")
        if path.suffix == ".json" and len(raw) <= MAX_FILE_BYTES:
            try:
                files[key] = json.loads(text)
                continue
            except json.JSONDecodeError:
                pass
        files[key] = text + ("\n…(잘림)" if len(raw) > MAX_FILE_BYTES else "")
    return files


def claude_overview(project: Project) -> dict:
    """Claude 탭: CLAUDE.md · hook · 권한 · skill/agent · 메모리."""
    root = project.root
    settings_path = root / ".claude" / "settings.json"
    settings = json.loads(settings_path.read_text(encoding="utf-8")) if settings_path.exists() else {}
    hooks_dir = root / ".claude" / "hooks"
    hook_files = {str(p.relative_to(root)): read_text(p) for p in sorted(hooks_dir.glob("*")) if p.is_file()} if hooks_dir.exists() else {}

    def collect(folder: pathlib.Path, pattern: str, scope: str, kind: str) -> list[dict]:
        found = []
        for path in sorted(folder.glob(pattern)):
            text = read_text(path)
            meta = front_matter(text)
            default = path.parent.name if kind == "skill" else path.stem
            found.append({"scope": scope, "kind": kind, "name": meta.get("name", default),
                          "description": meta.get("description", ""), "path": str(path), "text": text})
        return found

    extensions = (collect(root / ".claude" / "skills", "*/SKILL.md", "프로젝트", "skill")
                  + collect(root / ".claude" / "agents", "*.md", "프로젝트", "agent")
                  + collect(HOME_CLAUDE / "skills", "*/SKILL.md", "사용자", "skill")
                  + collect(HOME_CLAUDE / "agents", "*.md", "사용자", "agent"))

    mem = project.memory_dir
    memories = []
    for path in sorted(mem.glob("*.md")):
        if path.name == "MEMORY.md":
            continue
        text = read_text(path)
        meta = front_matter(text)
        body = text.split("---", 2)[2].strip() if text.startswith("---") and text.count("---") >= 2 else text
        memories.append({"file": path.name, "name": meta.get("name", path.stem), "description": meta.get("description", ""),
                         "type": meta.get("type", ""), "body": body})
    claude_md = root / "CLAUDE.md"
    return {
        "claudeMd": read_text(claude_md) if claude_md.exists() else "",
        "settings": {k: settings.get(k) for k in ("hooks", "permissions") if k in settings},
        "hookFiles": hook_files,
        "extensions": extensions,
        "memoryIndex": read_text(mem / "MEMORY.md") if (mem / "MEMORY.md").exists() else "",
        "memories": memories,
        "paths": {"claudeMd": str(claude_md), "settings": str(settings_path), "memory": str(mem)},
    }


# ── HTTP ─────────────────────────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:  # 요청마다 찍는 기본 로그는 줄입니다
        pass

    def send_json(self, status: int, body: object) -> None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def query(self) -> tuple[str, dict[str, str]]:
        parsed = urllib.parse.urlparse(self.path)
        return parsed.path, {k: v[0] for k, v in urllib.parse.parse_qs(parsed.query).items()}

    def body(self) -> bytes:
        return self.rfile.read(int(self.headers.get("Content-Length") or 0))

    def do_GET(self) -> None:
        path, q = self.query()
        project = PROJECT
        try:
            if path in ("/", "/index.html"):
                data = EDITOR.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(data)
            elif path == "/api/info":
                self.send_json(200, {"project": project.main_checkout.name, "root": str(project.root),
                                     "flowsDir": str(project.flows), "flows": project.list_flows()})
            elif path == "/api/flow":
                flow = project.flow_dir(q["name"])
                self.send_json(200, {"flow": json.loads((flow / "flow.json").read_text(encoding="utf-8")),
                                     "runs": list_runs(flow)})
            elif path == "/api/file":
                flow = project.flow_dir(q["name"])
                target = inside(flow, q["path"])
                self.send_json(200, {"path": q["path"], "text": target.read_text(encoding="utf-8") if target.exists() else None})
            elif path == "/api/run":
                self.send_json(200, read_run(project.flow_dir(q["name"]), q["id"]))
            elif path == "/api/claude":
                self.send_json(200, claude_overview(project))
            elif path == "/api/videos":
                self.send_json(200, {"dir": str(project.videos), "style": project.video_style(), "videos": project.list_videos()})
            elif path == "/api/video":
                folder = project.video_dir(q["name"])
                self.send_json(200, {"brief": json.loads((folder / "brief.json").read_text(encoding="utf-8"))})
            else:
                self.send_json(404, {"error": "없는 주소"})
        except (KeyError, ValueError, OSError) as error:
            self.send_json(400, {"error": str(error)})

    def do_PUT(self) -> None:
        path, q = self.query()
        project = PROJECT
        try:
            if path == "/api/claude-md":
                (project.root / "CLAUDE.md").write_text(self.body().decode("utf-8"), encoding="utf-8")
                self.send_json(200, {"saved": "CLAUDE.md"})
                return
            if path == "/api/video-style":
                data = json.loads(self.body().decode("utf-8"))
                if not isinstance(data.get("rules"), list):
                    raise ValueError("style.json 에는 rules 목록이 있어야 합니다.")
                project.videos.mkdir(parents=True, exist_ok=True)
                (project.videos / "style.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                self.send_json(200, {"saved": "video/style.json"})
                return
            if path == "/api/video":
                folder = project.video_dir(q["name"])
                data = json.loads(self.body().decode("utf-8"))
                if not isinstance(data.get("brief"), dict):
                    raise ValueError("brief 가 있어야 합니다.")
                if q.get("create") and folder.exists():
                    raise ValueError(f"'{q['name']}' 영상이 이미 있습니다.")
                project.ensure_video_style()
                folder.mkdir(exist_ok=True)
                (folder / "brief.json").write_text(json.dumps(data["brief"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                (folder / "brief.md").write_text(str(data.get("markdown") or ""), encoding="utf-8")
                self.send_json(200, {"saved": f"video/{folder.name}/brief.md"})
                return
            flow = project.flow_dir(q["name"])
            if path == "/api/flow":
                data = json.loads(self.body().decode("utf-8"))
                if not isinstance(data.get("nodes"), list) or not isinstance(data.get("edges"), list):
                    raise ValueError("flow.json 에는 nodes 와 edges 목록이 있어야 합니다.")
                (flow / "flow.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                self.send_json(200, {"saved": "flow.json"})
            elif path == "/api/file":
                target = inside(flow, q["path"])
                if target.suffix != ".md" or "runs" in target.relative_to(flow).parts:
                    raise ValueError("지시문(.md) 파일만 저장할 수 있습니다.")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(self.body().decode("utf-8"), encoding="utf-8")
                self.send_json(200, {"saved": q["path"]})
            else:
                self.send_json(404, {"error": "없는 주소"})
        except (KeyError, ValueError, OSError, json.JSONDecodeError) as error:
            self.send_json(400, {"error": str(error)})


# ── 명령 ─────────────────────────────────────────────────────────────────────
def init(project: Project) -> int:
    """templates/ 의 기본 흐름을 프로젝트 workflow/ 에 복사합니다. 이미 있는 흐름은 건드리지 않습니다."""
    project.flows.mkdir(parents=True, exist_ok=True)
    for template in sorted(p for p in TEMPLATES.iterdir() if (p / "flow.json").exists()):
        target = project.flows / template.name
        if target.exists():
            print(f"  있음 — 건너뜀: {target}")
            continue
        shutil.copytree(template, target)
        print(f"  만듦: {target}")
    style = project.videos / "style.json"
    if style.exists():
        print(f"  있음 — 건너뜀: {style}")
    else:
        project.ensure_video_style()
        print(f"  만듦: {style}")
    gitignore = project.root / ".gitignore"
    rule = f"{project.flows.relative_to(project.root)}/*/runs/"
    if not gitignore.exists() or rule not in gitignore.read_text(encoding="utf-8"):
        with gitignore.open("a", encoding="utf-8") as handle:
            handle.write(f"\n# flowboard 실행 기록\n{rule}\n")
        print(f"  .gitignore 에 {rule} 추가")
    return 0


def serve(project: Project, port: int, open_browser: bool) -> int:
    global PROJECT
    PROJECT = project
    if not project.flows.exists():
        print(f"흐름 폴더가 없습니다: {project.flows}\n  flowboard init {project.root}  로 기본 흐름을 만드세요.", file=sys.stderr)
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}"
    print(f"flowboard · {project.main_checkout.name} → {url}", flush=True)
    if open_browser:
        webbrowser.open(url)
    server.serve_forever()
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    command = "serve"
    if argv and argv[0] in ("serve", "init"):
        command = argv.pop(0)
    parser = argparse.ArgumentParser(prog="flowboard", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("project", nargs="?", default=".", help="프로젝트 폴더(기본: 지금 폴더)")
    parser.add_argument("--dir", default="workflow", help="흐름 폴더 이름(기본: workflow)")
    parser.add_argument("--port", type=int, default=8790)
    parser.add_argument("--no-open", action="store_true", help="브라우저를 자동으로 열지 않습니다")
    args = parser.parse_args(argv)
    project = Project(pathlib.Path(args.project).expanduser(), args.dir)
    if command == "init":
        return init(project)
    return serve(project, args.port, not args.no_open)


if __name__ == "__main__":
    sys.exit(main())
