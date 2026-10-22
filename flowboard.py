#!/usr/bin/env python3
"""flowboard — 영상 한 편을 만들기 전에 형식 · 스토리 · 컷 편집 · 트랜지션 · 효과 · 자막 · 배경음악 · 도구를 골라 기획서로 남깁니다.

  flowboard                      # 지금 폴더를 프로젝트로 열기 → http://127.0.0.1:8790
  flowboard ~/Videos/my-channel  # 다른 프로젝트 열기
  flowboard --port 9000 --no-open
  flowboard init [프로젝트]       # video/style.json(늘 하는 말 · 새 영상 기본값) 만들기

파이썬 기본 기능만 씁니다(설치 없음). 이 컴퓨터(127.0.0.1)에서만 열립니다.
쓰기는 <프로젝트>/video/ 안의 style.json 과 <영상>/brief.json · brief.md 로 제한합니다.
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
STYLE_TEMPLATE = HERE / "templates" / "style.json"


class Project:
    """열린 프로젝트. 영상 기획은 <프로젝트>/<videos_dir>/<영상>/brief.json 입니다."""

    def __init__(self, root: pathlib.Path, videos_dir: str = "video"):
        self.root = root.resolve()
        self.videos = self.root / videos_dir

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

    def style(self) -> dict:
        """늘 하는 말(rules)과 새 영상 기본값(defaults). 아직 없으면 templates/style.json."""
        path = self.videos / "style.json"
        return json.loads((path if path.exists() else STYLE_TEMPLATE).read_text(encoding="utf-8"))

    def ensure_style(self) -> bool:
        """style.json 이 없으면 만들고 True 를 돌려줍니다."""
        self.videos.mkdir(parents=True, exist_ok=True)
        if (self.videos / "style.json").exists():
            return False
        shutil.copy(STYLE_TEMPLATE, self.videos / "style.json")
        return True


PROJECT: Project


def write_json(path: pathlib.Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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

    def body(self) -> object:
        return json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)).decode("utf-8"))

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
            elif path == "/api/videos":
                self.send_json(200, {"project": project.root.name, "dir": str(project.videos),
                                     "style": project.style(), "videos": project.list_videos()})
            elif path == "/api/video":
                folder = project.video_dir(q["name"])
                self.send_json(200, {"brief": json.loads((folder / "brief.json").read_text(encoding="utf-8"))})
            else:
                self.send_json(404, {"error": "없는 주소"})
        except (KeyError, ValueError, OSError, json.JSONDecodeError) as error:
            self.send_json(400, {"error": str(error)})

    def do_PUT(self) -> None:
        path, q = self.query()
        project = PROJECT
        try:
            data = self.body()
            if not isinstance(data, dict):
                raise ValueError("JSON 객체를 보내야 합니다.")
            if path == "/api/style":
                if not isinstance(data.get("rules"), list):
                    raise ValueError("style.json 에는 rules 목록이 있어야 합니다.")
                project.videos.mkdir(parents=True, exist_ok=True)
                write_json(project.videos / "style.json", data)
                self.send_json(200, {"saved": "style.json"})
            elif path == "/api/video":
                folder = project.video_dir(q["name"])
                if not isinstance(data.get("brief"), dict):
                    raise ValueError("brief 가 있어야 합니다.")
                if q.get("create") and folder.exists():
                    raise ValueError(f"'{q['name']}' 영상이 이미 있습니다.")
                project.ensure_style()
                folder.mkdir(exist_ok=True)
                write_json(folder / "brief.json", data["brief"])
                (folder / "brief.md").write_text(str(data.get("markdown") or ""), encoding="utf-8")
                self.send_json(200, {"saved": f"{folder.name}/brief.md"})
            else:
                self.send_json(404, {"error": "없는 주소"})
        except (KeyError, ValueError, OSError, json.JSONDecodeError) as error:
            self.send_json(400, {"error": str(error)})


# ── 명령 ─────────────────────────────────────────────────────────────────────
def init(project: Project) -> int:
    style = project.videos / "style.json"
    print(f"  만듦: {style}" if project.ensure_style() else f"  있음 — 건너뜀: {style}")
    return 0


def serve(project: Project, port: int, open_browser: bool) -> int:
    global PROJECT
    PROJECT = project
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}"
    print(f"flowboard · {project.root.name} → {url}", flush=True)
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
    parser.add_argument("--dir", default="video", help="영상 기획 폴더 이름(기본: video)")
    parser.add_argument("--port", type=int, default=8790)
    parser.add_argument("--no-open", action="store_true", help="브라우저를 자동으로 열지 않습니다")
    args = parser.parse_args(argv)
    project = Project(pathlib.Path(args.project).expanduser(), args.dir)
    if command == "init":
        return init(project)
    return serve(project, args.port, not args.no_open)


if __name__ == "__main__":
    sys.exit(main())
