import json

import pytest

from app.services.introduction_service import (
    IntroductionGenerationError,
    RepositoryBrief,
    _build_prompt,
    _find_opencode,
    _parse_introductions,
    _parse_opencode_output,
    generate_introductions,
)


def make_brief(name: str = "demo-skill", topics: list[str] | None = None) -> RepositoryBrief:
    return RepositoryBrief(
        owner="octocat",
        name=name,
        description="A demo agent skill",
        language="Python",
        topics=topics or ["ai-skills"],
        stars_count=1234,
        homepage=None,
        html_url="https://github.com/octocat/demo-skill",
    )


def test_build_prompt_contains_repo_info() -> None:
    prompt = _build_prompt([make_brief()])
    assert "demo-skill" in prompt
    assert "ai-skills" in prompt
    assert "octocat" in prompt
    assert "JSON" in prompt
    assert "usage" in prompt
    assert "domains" in prompt


def test_parse_opencode_output_joins_text_events() -> None:
    lines = [
        '{"type":"step_start","part":{"type":"step-start"}}',
        '{"type":"text","part":{"type":"text","text":"项目简介"}}',
        '{"type":"text","part":{"type":"text","text":"的第一部分。"}}',
        '{"type":"step_finish","part":{"type":"step-finish"}}',
        '{"type":"error","error":{}}',
    ]
    assert _parse_opencode_output("\n".join(lines)) == "项目简介的第一部分。"


def test_parse_introductions_from_json_array() -> None:
    text = (
        '[{"introduction": "第一个仓库的简介。", "usage": "直接运行", '
        '"domains": ["AI Agent"]}, '
        '{"introduction": "第二个仓库的简介。", "usage": "pip 安装", '
        '"domains": ["自动化", "RAG"]}]'
    )
    assert _parse_introductions(text, 2) == [
        json.dumps(
            {"introduction": "第一个仓库的简介。", "usage": "直接运行", "domains": ["AI Agent"]},
            ensure_ascii=False,
        ),
        json.dumps(
            {"introduction": "第二个仓库的简介。", "usage": "pip 安装", "domains": ["自动化", "RAG"]},
            ensure_ascii=False,
        ),
    ]


def test_parse_introductions_with_surrounding_text() -> None:
    text = (
        '好的，以下是简介：\n```\n'
        '[{"introduction": "简介甲", "usage": "用法甲", "domains": ["领域甲"]}, '
        '{"introduction": "简介乙", "usage": "用法乙", "domains": ["领域乙"]}]\n```'
    )
    assert _parse_introductions(text, 2) == [
        json.dumps(
            {"introduction": "简介甲", "usage": "用法甲", "domains": ["领域甲"]},
            ensure_ascii=False,
        ),
        json.dumps(
            {"introduction": "简介乙", "usage": "用法乙", "domains": ["领域乙"]},
            ensure_ascii=False,
        ),
    ]


def test_parse_introductions_accepts_plain_strings() -> None:
    text = '["简介一", "简介二"]'
    assert _parse_introductions(text, 2) == [
        json.dumps({"introduction": "简介一", "usage": "", "domains": []}, ensure_ascii=False),
        json.dumps({"introduction": "简介二", "usage": "", "domains": []}, ensure_ascii=False),
    ]


def test_parse_introductions_raises_on_garbage() -> None:
    with pytest.raises(IntroductionGenerationError):
        _parse_introductions("抱歉，我无法完成这个请求。", 1)


def test_generate_introductions_success(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[list[str]] = []

    class FakeResult:
        returncode = 0
        stdout = (
            '{"type":"text","part":{"type":"text","text":"[{\\"introduction\\":\\"简介一\\",'
            '\\"usage\\":\\"用法一\\",\\"domains\\":[\\"领域一\\"]}]"}}'
        )
        stderr = ""

    import subprocess

    def fake_run(args, **kwargs):
        captured.append(args)
        return FakeResult()

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(
        "app.services.introduction_service._find_opencode", lambda: "opencode"
    )
    texts = generate_introductions([make_brief("a")], model="m")
    assert texts == [
        json.dumps(
            {"introduction": "简介一", "usage": "用法一", "domains": ["领域一"]},
            ensure_ascii=False,
        )
    ]
    assert "--format" in captured[0]
    assert "json" in captured[0]
    assert "-m" in captured[0]
    assert "m" in captured[0]


def test_generate_introductions_raises_on_nonzero_exit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import subprocess

    class FakeResult:
        returncode = 1
        stdout = ""
        stderr = "boom"

    monkeypatch.setattr(subprocess, "run", lambda args, **kwargs: FakeResult())
    monkeypatch.setattr(
        "app.services.introduction_service._find_opencode", lambda: "opencode"
    )
    with pytest.raises(IntroductionGenerationError):
        generate_introductions([make_brief()], model="m")


def test_find_opencode_returns_exe(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.services.introduction_service.shutil.which",
        lambda name: r"C:\opencode.exe" if name == "opencode.exe" else None,
    )
    assert _find_opencode() == r"C:\opencode.exe"


def test_find_opencode_skips_cmd_shim(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_which(name: str) -> str | None:
        if name == "opencode.cmd":
            return r"C:\npm\opencode.cmd"
        if name == "opencode.ps1":
            return r"C:\npm\opencode.ps1"
        return None

    monkeypatch.setattr(
        "app.services.introduction_service.shutil.which", fake_which
    )
    monkeypatch.setattr(
        "app.services.introduction_service.Path.exists", lambda self: True
    )
    assert _find_opencode() == r"C:\npm\node_modules\opencode-ai\bin\opencode.exe"


def test_find_opencode_raises_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.services.introduction_service.shutil.which", lambda name: None
    )
    with pytest.raises(IntroductionGenerationError):
        _find_opencode()
