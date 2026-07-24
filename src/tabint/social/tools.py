"""Social-content MCP tools — templates, campaigns, search targets, posts,
feedback, and template-change proposals. A thin data/CRUD surface over the
user's Table Intelligence account via the integration control-plane client.

The agent DOES NOT post, publish, or scrape. It (a) stores templates/campaigns,
(b) emits structured SEARCH SPECS (reads deferred to the harness), (c) stores
drafted posts + replies, and (d) captures feedback and PROPOSES template
changes (never silently mutating the user's playbook). No client-side gating:
the API enforces entitlement server-side.

Mirrors outreach/tools.py. The one cleanup vs outreach: a single _NEED_KEY and
_cfg (outreach has these defined twice — harmless but duplicated — which we do
not propagate here).
"""
from tabint.integration.service import platform as _platform
from tabint.shared.server import mcp

_NEED_KEY_SOCIAL = {
    "ok": False,
    "error": "not_configured",
    "message": "Set TABINT_API_KEY (from your account at shubhamrandive.com) to use social.",
}


def _cfg(fn, *a, **k):
    return fn(*a, **k) if _platform.configured() else _NEED_KEY_SOCIAL


# --------------------------------------------------------------------------- #
# templates — the reusable playbook (product, audience, platforms, keywords,
# do's/don'ts, tone, recency). Layer 1 of the three-layer instruction model.
# --------------------------------------------------------------------------- #

@mcp.tool()
def social_create_template(title: str, prompt: str, status: str = "active") -> dict:
    """Create a reusable social-content template. `prompt` is the playbook the
    agent follows on every campaign (product/offer, audience, target
    platforms, keywords + sample questions for discovery, do's/don'ts, tone per
    platform, recency window). status: 'active' or 'inactive'."""
    return _cfg(_platform.social_create_template, title, prompt, status)


@mcp.tool()
def social_list_templates(status: str | None = None,
                          frm: str | None = None, to: str | None = None) -> dict:
    """List social templates. Optional filters: status ('active'/'inactive'),
    frm/to (ISO date range on created_at)."""
    return _cfg(_platform.social_list_templates, status, frm, to)


@mcp.tool()
def social_get_template(template_id: str) -> dict:
    """Read one social template (title, prompt, status)."""
    return _cfg(_platform.social_get_template, template_id)


@mcp.tool()
def social_update_template(template_id: str, fields: dict) -> dict:
    """Update a template. `fields` may include title, prompt, status. Prefer
    routing durable changes through social_propose_template_change so the user
    approves — only call this directly for trivial edits the user asked for."""
    return _cfg(_platform.social_update_template, template_id, fields)


@mcp.tool()
def social_delete_template(template_id: str) -> dict:
    """Delete a template by id."""
    return _cfg(_platform.social_delete_template, template_id)


# --------------------------------------------------------------------------- #
# campaigns — a run. setup FREEZES the template prompt into the campaign.
# --------------------------------------------------------------------------- #

@mcp.tool()
def social_setup_campaign(template_id: str, title: str | None = None) -> dict:
    """Start a new campaign from a template. The template's prompt is COPIED
    into the campaign (frozen — later template edits don't affect it). The
    campaign starts empty; add search targets and posts with the tools below."""
    return _cfg(_platform.social_setup_campaign, template_id, title)


@mcp.tool()
def social_get_campaign(campaign_id: str) -> dict:
    """Get a campaign incl. its frozen prompt."""
    return _cfg(_platform.social_get_campaign, campaign_id)


@mcp.tool()
def social_list_campaigns(status: str | None = None, template_id: str | None = None,
                          frm: str | None = None, to: str | None = None) -> dict:
    """List campaigns with optional filters (status, template_id, created_at range)."""
    return _cfg(_platform.social_list_campaigns, status, template_id, frm, to)


# --------------------------------------------------------------------------- #
# search targets — structured SEARCH SPECS. The agent emits these; the HARNESS
# runs them (the agent never scrapes). Each spec says: which platform, what to
# look for (threads/articles/tweets/posts), the queries, the scopes
# (subreddits/publications/groups/handles), a recency window, and keywords.
# --------------------------------------------------------------------------- #

@mcp.tool()
def social_add_search_target(campaign_id: str, platform: str, search_type: str,
                             queries: list, scopes: list | None = None,
                             recency: str = "7d", keywords: list | None = None,
                             max_results: int = 15) -> dict:
    """Add a search spec to a campaign. The HARNESS runs these (the agent does
    not scrape). `platform`: reddit|medium|twitter|facebook|linkedin.
    `search_type`: find_threads (reddit/FB), find_articles (medium),
    find_tweets/find_posts (twitter). `queries`: sample questions/search terms
    from the template. `scopes`: subreddits/publications/group names/handles.
    `recency`: e.g. '7d','3d' — RECENT ONLY. `keywords`: product/audience terms
    to match. `max_results`: cap (default 15)."""
    return _cfg(_platform.social_add_search_target, campaign_id, platform,
                search_type, queries, scopes, recency, keywords, max_results)


@mcp.tool()
def social_list_search_targets(campaign_id: str, platform: str | None = None,
                               status: str | None = None) -> dict:
    """List search specs in a campaign. Filter by platform and status
    ('open'/'done')."""
    return _cfg(_platform.social_list_search_targets, campaign_id, platform, status)


@mcp.tool()
def social_update_search_target(search_target_id: str, fields: dict) -> dict:
    """Update a search spec — e.g. mark status 'done' or attach a result_count
    after the harness has run it."""
    return _cfg(_platform.social_update_search_target, search_target_id, fields)


@mcp.tool()
def social_delete_search_target(search_target_id: str) -> dict:
    """Delete a search spec."""
    return _cfg(_platform.social_delete_search_target, search_target_id)


# --------------------------------------------------------------------------- #
# posts — unified AUTHOR + REPLY content.
#   kind='author' : original content to publish (linkedin_post, medium_article,
#                   tweet/thread, facebook_post).
#   kind='reply'  : a response to an existing post/thread/article; carries
#                   target_url + target_kind + (optional) target_title/author.
# status: draft -> posted -> (or 'failed'). delete = reject.
# The list filters (platform/kind) power RULE A dedup before authoring.
# --------------------------------------------------------------------------- #

@mcp.tool()
def social_add_post(campaign_id: str, platform: str, kind: str, content: str,
                    content_format: str = "text",
                    target_url: str | None = None, target_kind: str | None = None,
                    target_title: str | None = None, target_author: str | None = None,
                    notes: str | None = None) -> dict:
    """Add a drafted post to a campaign (status 'draft').
    `platform`: reddit|medium|linkedin|twitter|facebook.
    `kind`: 'author' (original) or 'reply'.
    `content`: the drafted text. `content_format`: 'text' or 'markdown'.
    For replies: `target_url` (the thread/article/tweet to reply to),
    `target_kind` (reddit_thread|medium_article|tweet|facebook_post|linkedin_post),
    optional target_title/target_author. `notes`: any internal note."""
    return _cfg(_platform.social_add_post, campaign_id, platform, kind, content,
                content_format, target_url, target_kind, target_title,
                target_author, notes)


@mcp.tool()
def social_list_posts(campaign_id: str, status: str | None = None,
                      platform: str | None = None, kind: str | None = None) -> dict:
    """List posts in a campaign. Filter by status ('draft'/'posted'/'failed'),
    platform, and kind ('author'/'reply'). Call with kind='author' + platform
    BEFORE drafting new original content to avoid duplicates (RULE A)."""
    return _cfg(_platform.social_list_posts, campaign_id, status, platform, kind)


@mcp.tool()
def social_get_post(post_id: str) -> dict:
    """Read one post (content, target, status, notes)."""
    return _cfg(_platform.social_get_post, post_id)


@mcp.tool()
def social_update_post(post_id: str, fields: dict) -> dict:
    """Update a post. `fields` may include content, content_format, status
    ('draft'/'posted'/'failed'), posted_at, notes, rejection_reason. After the
    user/harness posts it, set status to 'posted' to record it."""
    return _cfg(_platform.social_update_post, post_id, fields)


@mcp.tool()
def social_delete_post(post_id: str, reason: str | None = None) -> dict:
    """Delete/reject a post so it won't be published. If a reason is given it is
    recorded as feedback (kind='rejection') so the agent can learn."""
    return _cfg(_platform.social_delete_post, post_id, reason)


# --------------------------------------------------------------------------- #
# feedback — rejections + free-text notes, scoped to a campaign (+ optional
# post). The agent READS this before every run and folds it in.
# --------------------------------------------------------------------------- #

@mcp.tool()
def social_add_feedback(campaign_id: str, kind: str, reason: str,
                        note: str | None = None, post_id: str | None = None) -> dict:
    """Capture feedback. `kind`: 'rejection' (a post was rejected) or 'note'
    (free text). `reason`: short label/cause. `note`: longer detail. `post_id`:
    optional link to a specific post. The agent reads this before each run."""
    return _cfg(_platform.social_add_feedback, campaign_id, kind, reason,
                note, post_id)


@mcp.tool()
def social_list_feedback(campaign_id: str | None = None,
                         kind: str | None = None) -> dict:
    """List feedback notes/rejections. Call before each run to fold them in."""
    return _cfg(_platform.social_list_feedback, campaign_id, kind)


@mcp.tool()
def social_delete_feedback(feedback_id: str) -> dict:
    """Delete a feedback entry."""
    return _cfg(_platform.social_delete_feedback, feedback_id)


# --------------------------------------------------------------------------- #
# template-change proposals — durable, generic feedback becomes a PROPOSED
# patch to the template. The user approves/rejects. Nothing is silently mutated.
# --------------------------------------------------------------------------- #

@mcp.tool()
def social_propose_template_change(template_id: str, change_kind: str,
                                   rationale: str, proposed_patch: str,
                                   source_feedback_ids: list | None = None) -> dict:
    """Propose a change to a template (status 'proposed'). Use when a feedback
    note is GENERIC and PERMANENT (a rule for all future work), not just about
    one post. `change_kind`: 'append' | 'replace' | 'add_rule'. `rationale`:
    why. `proposed_patch`: the text to add/replace. `source_feedback_ids`: the
    feedback that motivated it. The user approves/rejects; on approval, call
    social_apply_template_change."""
    return _cfg(_platform.social_propose_template_change, template_id,
                change_kind, rationale, proposed_patch, source_feedback_ids)


@mcp.tool()
def social_list_template_changes(template_id: str | None = None,
                                 status: str | None = None) -> dict:
    """List template-change proposals. Filter by status
    ('proposed'/'approved'/'rejected'/'applied')."""
    return _cfg(_platform.social_list_template_changes, template_id, status)


@mcp.tool()
def social_update_template_change(change_id: str, status: str,
                                 decision_note: str | None = None) -> dict:
    """Approve or reject a template-change proposal. `status`: 'approved' or
    'rejected'. `decision_note`: optional. Does NOT apply the patch — call
    social_apply_template_change after approving."""
    return _cfg(_platform.social_update_template_change, change_id, status,
                decision_note)


@mcp.tool()
def social_apply_template_change(change_id: str) -> dict:
    """Apply an APPROVED template-change proposal to the template (calls the
    underlying template update). Only applies proposals whose status is
    'approved'. Returns the updated template."""
    return _cfg(_platform.social_apply_template_change, change_id)


# --------------------------------------------------------------------------- #
# social explainer (static; no account needed)
# --------------------------------------------------------------------------- #

@mcp.tool()
def social_how_it_works() -> dict:
    """Explain what the social-content agent does, step by step, and how to use
    it. Call when the user asks what the social agent is, how it works, or how
    to get started. Free — no subscription required, no API key needed."""
    return {
        "name": "Social-content agent",
        "summary": (
            "Helps build awareness for a product/project across social "
            "platforms: build a reusable template, run campaigns that emit "
            "search specs (the harness finds recent threads/articles/tweets to "
            "reply to) and draft varied original posts + helpful replies, "
            "capture feedback, and propose template changes — then the user/"
            "harness publishes."
        ),
        "principle": "own the read (deferred to harness), defer the write",
        "does_not_publish": True,
        "publishing_note": (
            "This agent never posts, publishes, replies, or scrapes. "
            "Publishing is done by the user/harness's own tools; the agent "
            "drafts content + saves reply targets, and records the result "
            "after each post. (Mirrors outreach's 'we don't send email'.)"
        ),
        "three_layer_instruction_model": [
            "1. USER TEMPLATE (highest precedence — wins on conflict): the "
            "frozen campaign prompt (product, audience, keywords, do's/don'ts).",
            "2. AGENT INSTRUCTION: the social_agent prompt (workflow, rules).",
            "3. PLATFORM INSTRUCTION: the social_platform_* prompt + the "
            "study/social/0N-*.md note (format, length, etiquette).",
        ],
        "platforms": {
            "reddit": "subreddits/threads; NO self-promo; helpful-first; 7d recency",
            "medium": "articles (long-form) + comments; markdown; 14d recency for comments",
            "linkedin": "feed posts; self-promo allowed; hook+story+CTA+hashtags",
            "twitter": "<=280 chars or threads; self-promo allowed; 3d recency for replies",
            "facebook": "groups; respect group rules; helpful-first; 7d recency",
        },
        "authoring_rules": [
            "RULE A — DEDUP: before drafting an original post, call "
            "social_list_posts(campaign_id, platform, kind='author') and avoid "
            "reused angles/hooks/headlines.",
            "RULE B — TOPIC INTAKE: when no topic is given, ask once; if the "
            "user says 'you pick', derive a topic from the template + recent "
            "feedback and state it before drafting.",
        ],
        "feedback_loop": (
            "Rejections/notes are captured as feedback; the agent reads them "
            "before each run. Generic+permanent feedback becomes a PROPOSED "
            "template change the user approves. Template always wins."
        ),
        "steps": [
            {"n": 1, "name": "Create a template",
             "how": "The agent interviews you about the product, audience, "
                    "platforms, keywords/sample questions, do's/don'ts, tone, "
                    "recency — iterating until you're happy — then saves a "
                    "reusable template.",
             "tool": "social_create_template"},
            {"n": 2, "name": "Run a campaign",
             "how": "You pick a template and say 'run a campaign'. The agent "
                    "freezes the template into a campaign, reads recent "
                    "feedback, then either emits search specs (discovery) or "
                    "drafts posts (authoring), or both.",
             "tools": ["social_setup_campaign", "social_add_search_target",
                       "social_add_post"]},
            {"n": 3, "name": "Discovery (harness runs the reads)",
             "how": "The agent saves structured SEARCH SPECS (platform, "
                    "queries, scopes, recency, keywords). The HARNESS runs "
                    "them; found threads/articles/tweets come back, and the "
                    "agent drafts a helpful reply for each.",
             "tools": ["social_add_search_target", "social_add_post"]},
            {"n": 4, "name": "Stop & report",
             "how": "Once posts are drafted, the agent stops and tells you to "
                    "review. It does NOT publish at this stage."},
            {"n": 5, "name": "Review, edit, publish (separate step)",
             "how": "Review/edit in the dashboard or via tools; publish via "
                    "your/harness's tools; the agent records each as 'posted'. "
                    "For replies, each post carries the target URL + exact "
                    "reply text to paste.",
             "tools": ["social_list_posts", "social_update_post",
                       "social_delete_post"]},
        ],
        "get_started": (
            "To begin, ask the agent to create a new social template (it will "
            "interview you), or ask 'what can the social agent do?' for a tour."
        ),
        "load_playbook_prompt": "social_agent",
        "load_platform_prompts": [
            "social_platform_reddit", "social_platform_medium",
            "social_platform_linkedin", "social_platform_twitter",
            "social_platform_facebook",
        ],
    }
