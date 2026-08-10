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
    text = '["第一个仓库的简介。", "第二个仓库的简介。"]'
    assert _parse_introductions(text, 2) == ["第一个仓库的简介。", "第二个仓库的简介。"]


def test_parse_introductions_with_surrounding_text() -> None:
    text = '好的，以下是简介：\n```\n["简介甲", "简介乙"]\n```'
    assert _parse_introductions(text, 2) == ["简介甲", "简介乙"]


def test_parse_introductions_raises_on_garbage() -> None:
    with pytest.raises(IntroductionGenerationError):
        _parse_introductions("抱歉，我无法完成这个请求。", 1)


def test_generate_introductions_success(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[list[str]] = []

    class FakeResult:
        returncode = 0
        stdout = '{"type":"text","part":{"type":"text","text":"[\\"简介一\\",\\"简介二\\"]"}}'
        stderr = ""

    import subprocess

    def fake_run(args, **kwargs):
        captured.append(args)
        return FakeResult()

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(
        "app.services.introduction_service._find_opencode", lambda: "opencode"
    )
    texts = generate_introductions([make_brief("a"), make_brief("b")], model="m")
    assert texts == ["简介一", "简介二"]
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


def test_find_opencode_raises_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.services.introduction_service.shutil.which", lambda name: None
    )
    with pytest.raises(IntroductionGenerationError):
        _find_opencode()
