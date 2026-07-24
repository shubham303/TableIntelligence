"""Integration tests for the social CRUD surface + the explainer tool.

The MCP server imposes no role gating; it only checks that an API key is
configured (the ``_cfg`` helper) before calling the platform — a missing key
surfaces a ``not_configured`` hint rather than hitting the network. The
platform functions themselves are monkeypatched here (the one external
dependency); everything else runs unmodified.

Mirrors: src/tabint/social/tools.py  (structure follows
tests/integration/outreach/test_outreach.py)
"""
import pytest

from tabint.social import tools as M
from tabint.integration.service import platform as _platform
from tabint.integration.service import entitlement


# --- the explainer tool (static; no account/key needed) --------------------- #

def test_how_it_works_is_static_dict():
    r = M.social_how_it_works()
    assert isinstance(r, dict)
    assert r["name"] == "Social-content agent"
    assert r["does_not_publish"] is True
    assert r["principle"] == "own the read (deferred to harness), defer the write"
    assert r["load_playbook_prompt"] == "social_agent"
    assert len(r["platforms"]) == 5
    for plat in ("reddit", "medium", "linkedin", "twitter", "facebook"):
        assert plat in r["platforms"]


def test_how_it_works_lists_platform_prompts():
    r = M.social_how_it_works()
    prompts = r["load_platform_prompts"]
    for name in (
        "social_platform_reddit", "social_platform_medium",
        "social_platform_linkedin", "social_platform_twitter",
        "social_platform_facebook",
    ):
        assert name in prompts


def test_how_it_works_states_authoring_rules():
    r = M.social_how_it_works()
    rules = " ".join(r["authoring_rules"])
    assert "DEDUP" in rules and "social_list_posts" in rules
    assert "TOPIC INTAKE" in rules


def test_how_it_works_needs_no_key():
    # The unit conftest clears the env; the tool is static and must return its
    # payload (not a not_configured / error hint).
    r = M.social_how_it_works()
    assert r.get("error") is None
    assert r.get("name") == "Social-content agent"


# --- key-presence gate (configured check) ----------------------------------- #

def _platform_configured(monkeypatch):
    """Tell _cfg an API key is set so the tool body runs (CI has no key)."""
    monkeypatch.setattr(_platform, "configured", lambda: True)


def test_social_crud_tools_hint_when_no_key(monkeypatch):
    # With no API key configured, tools surface a not_configured hint rather
    # than making a doomed HTTP call. (Key-presence check, not role gating.)
    monkeypatch.setattr(_platform, "configured", lambda: False)
    r = M.social_list_posts("c1")
    assert r.get("error") == "not_configured"


# --- no client-side gating on the CRUD surface ------------------------------ #

# Valid positional args for each tool so the body actually runs.
_TOOL_ARGS = {
    "social_create_template": ("t", "p"),
    "social_setup_campaign": ("t",),
    "social_add_search_target": ("c", "reddit", "find_threads", ["q"]),
    "social_add_post": ("c", "reddit", "reply", "content"),
    "social_list_posts": ("c",),
    "social_add_feedback": ("c", "note", "reason"),
    "social_propose_template_change": ("t", "append", "why", "patch"),
}


@pytest.mark.parametrize("tool", list(_TOOL_ARGS))
def test_social_crud_tools_not_role_gated(monkeypatch, tool):
    # Even with a FREE role and a configured key, the tool must reach the
    # platform layer (not short-circuit to a pro_feature upgrade dict). We stub
    # the platform call to assert the body ran.
    monkeypatch.setattr(entitlement, "is_pro", lambda: False)
    monkeypatch.setattr(entitlement, "role", lambda: "free")
    monkeypatch.setattr(_platform, "configured", lambda: True)
    # stub every social_* platform fn the tools reach for
    for name in (
        "social_create_template", "social_setup_campaign",
        "social_add_search_target", "social_add_post",
        "social_add_feedback", "social_propose_template_change",
    ):
        monkeypatch.setattr(_platform, name, lambda *a, **k: {"ok": True})
    monkeypatch.setattr(_platform, "social_list_posts", lambda *a, **k: {"posts": []})
    fn = getattr(M, tool)
    r = fn(*_TOOL_ARGS[tool])
    assert r.get("error") != "pro_feature"      # not role-gated


# --- list filters pass through to the platform client ----------------------- #

def test_list_posts_passes_filters_through(monkeypatch):
    _platform_configured(monkeypatch)
    captured = {}

    def _list(campaign_id, status=None, platform=None, kind=None):
        captured.update(campaign_id=campaign_id, status=status,
                        platform=platform, kind=kind)
        return {"posts": []}

    monkeypatch.setattr(_platform, "social_list_posts", _list)
    M.social_list_posts("c1", status="draft", platform="reddit", kind="author")
    assert captured == {"campaign_id": "c1", "status": "draft",
                        "platform": "reddit", "kind": "author"}


def test_delete_post_with_reason_is_routed(monkeypatch):
    _platform_configured(monkeypatch)
    captured = {}

    def _del(post_id, reason=None):
        captured.update(post_id=post_id, reason=reason)
        return {"ok": True}

    monkeypatch.setattr(_platform, "social_delete_post", _del)
    M.social_delete_post("p1", reason="too salesy")
    assert captured == {"post_id": "p1", "reason": "too salesy"}


def test_delete_post_without_reason_sends_no_body(monkeypatch):
    _platform_configured(monkeypatch)
    captured = {}

    def _del(post_id, reason=None):
        captured.update(post_id=post_id, reason=reason)
        return {"ok": True}

    monkeypatch.setattr(_platform, "social_delete_post", _del)
    M.social_delete_post("p1")
    assert captured == {"post_id": "p1", "reason": None}
