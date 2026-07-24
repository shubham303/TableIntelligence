"""Tests for the social agent prompts (pure — no platform calls).

The CRUD/platform social tests live in
``integration/social/test_social.py``.

Mirrors: src/tabint/social/prompts.py
"""
from tabint.social import prompts


# --- the agent prompt ------------------------------------------------------- #

def test_social_agent_prompt_is_non_empty_string():
    p = prompts.social_agent()
    assert isinstance(p, str) and len(p) > 500


def test_social_agent_prompt_covers_stages():
    p = prompts.social_agent()
    for marker in (
        "STAGE 1", "STAGE 2", "STAGE 3", "STAGE 4",
        "CREATE A TEMPLATE", "RUN A CAMPAIGN", "STOP & REPORT",
        "DISCOVERY", "AUTHORING",
    ):
        assert marker in p, f"prompt missing stage marker: {marker!r}"


def test_social_agent_prompt_states_it_does_not_publish():
    p = prompts.social_agent()
    assert "DO NOT POST" in p or "does not post" in p.lower()
    # and it must defer publishing to the user/harness
    assert "harness" in p.lower() or "user" in p.lower()


def test_social_agent_prompt_states_three_layer_precedence():
    p = prompts.social_agent()
    # the precedence rule and the template-wins clause
    assert "THREE-LAYER" in p or "three-layer" in p.lower()
    assert "WINS" in p or "wins" in p.lower()
    assert "USER TEMPLATE" in p


def test_social_agent_prompt_carries_authoring_rules():
    p = prompts.social_agent()
    # RULE A — dedup
    assert "RULE A" in p
    assert "social_list_posts" in p and "author" in p.lower()
    # RULE B — topic intake
    assert "RULE B" in p
    assert "you pick" in p.lower()


def test_social_agent_prompt_carries_feedback_loop():
    p = prompts.social_agent()
    assert "FEEDBACK LOOP" in p
    assert "social_list_feedback" in p
    assert "social_propose_template_change" in p


def test_social_agent_prompt_lists_the_tools():
    p = prompts.social_agent()
    for tool in (
        "social_create_template", "social_setup_campaign",
        "social_add_search_target", "social_add_post", "social_list_posts",
        "social_add_feedback", "social_propose_template_change",
        "social_how_it_works",
    ):
        assert tool in p, f"prompt missing tool reference: {tool!r}"


def test_social_agent_prompt_lists_platforms():
    p = prompts.social_agent()
    for plat in ("reddit", "medium", "linkedin", "twitter", "facebook"):
        assert plat in p.lower(), f"prompt missing platform: {plat!r}"


# --- the five platform prompts ---------------------------------------------- #

def test_platform_prompts_are_non_empty_and_distinct():
    fns = [
        prompts.social_platform_reddit,
        prompts.social_platform_medium,
        prompts.social_platform_linkedin,
        prompts.social_platform_twitter,
        prompts.social_platform_facebook,
    ]
    texts = [fn() for fn in fns]
    for t in texts:
        assert isinstance(t, str) and len(t) > 100
    # all five are distinct
    assert len(set(texts)) == 5


def test_reddit_prompt_states_no_self_promotion():
    p = prompts.social_platform_reddit()
    assert "NO SELF-PROMOTION" in p or "no self-promotion" in p.lower()
    assert "7" in p and "day" in p.lower()      # recency window


def test_twitter_prompt_states_280_char_limit():
    p = prompts.social_platform_twitter()
    assert "280" in p
    assert "3" in p and "day" in p.lower()      # recency window


def test_linkedin_prompt_allows_self_promotion():
    p = prompts.social_platform_linkedin()
    assert "SELF-PROMOTION IS FINE" in p or "self-promotion is" in p.lower()
