"""단계 스크립트가 flowboard 와 맞물리게 하는 도구 두 가지.

  - agent_node: flow.json 에서 이 단계의 에이전트 칸(모델 · 지시문 경로)을 읽습니다.
    화면에서 모델을 바꾸고 저장하면 다음 실행부터 그 값을 씁니다.
  - save_node_record: 칸 하나의 실행 기록을 runs/<run-id>/<칸 id>/ 에 남깁니다.
    화면의 '이번 배치 기록' 탭이 이 파일들을 보여 줍니다.

쓰는 법(단계 스크립트 안에서):

    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path.home() / "Projects/flowboard/lib"))   # 또는 이 파일을 복사
    import flowboard_run as fb

    flow = pathlib.Path(__file__).resolve().parents[1]          # workflow/<흐름>/
    node = fb.agent_node(flow, "step-1-collect")
    ...
    fb.save_node_record(flow, run_id, node["id"], prompt=prompt, output=result, meta={"model": node["model"], "usd": 0.04})

실행 기록 약속:
    runs/<run-id>/
      step-N.json      단계 결과(다음 단계가 읽는 파일)
      <칸 id>/
        prompt.md      실제로 보낸 프롬프트
        thinking.md    생각 과정(있을 때)
        output.json    결과물
        response.json  모델 응답 원문
        meta.json      model · usd · seconds · inputTokens · outputTokens
"""
from __future__ import annotations

import datetime
import json
import pathlib


def load_flow(flow_dir: pathlib.Path) -> dict:
    return json.loads((pathlib.Path(flow_dir) / "flow.json").read_text(encoding="utf-8"))


def agent_node(flow_dir: pathlib.Path, step_id: str, runner: str = "claude -p") -> dict:
    """flow.json 에서 step == step_id 이고 runner 가 같은 칸을 돌려줍니다."""
    for node in load_flow(flow_dir)["nodes"]:
        if node.get("step") == step_id and node.get("runner") == runner:
            return node
    raise SystemExit(f"flow.json 에 '{step_id}' 단계의 '{runner}' 칸이 없습니다.")


def new_run_id() -> str:
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


def save_node_record(flow_dir: pathlib.Path, run_id: str, node_id: str, *, prompt: str | None = None,
                     output: object = None, response: object = None, thinking: str | None = None,
                     meta: dict | None = None) -> pathlib.Path:
    folder = pathlib.Path(flow_dir) / "runs" / run_id / node_id
    folder.mkdir(parents=True, exist_ok=True)
    if prompt is not None:
        (folder / "prompt.md").write_text(prompt, encoding="utf-8")
    if thinking:
        (folder / "thinking.md").write_text(thinking, encoding="utf-8")
    if output is not None:
        (folder / "output.json").write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    if response is not None:
        (folder / "response.json").write_text(json.dumps(response, ensure_ascii=False, indent=2), encoding="utf-8")
    (folder / "meta.json").write_text(json.dumps(meta or {}, ensure_ascii=False, indent=2), encoding="utf-8")
    return folder
