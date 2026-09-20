from backend.app.skills.ship30 import Ship30For30Skill, get_ship30_skill


def test_ship30_skill_defaults():
    skill = Ship30For30Skill()

    assert skill.name == "ship30_for_30"
    assert skill.target_word_count == 1250
    assert "Ship 30 for 30" in skill.system_prompt


def test_get_ship30_skill():
    skill = get_ship30_skill()

    assert isinstance(skill, Ship30For30Skill)
    assert skill.name == "ship30_for_30"


def test_system_prompt_contains_core_writing_principles():
    skill = get_ship30_skill()

    prompt = skill.system_prompt

    assert "CLARITY BEFORE CLEVERNESS" in prompt
    assert "STRONG HOOK" in prompt
    assert "SPECIFIC HEADLINE" in prompt
    assert "SKIMMABLE SECTIONS" in prompt
    assert "PRACTICAL TAKEAWAY" in prompt
    assert "GROUNDING REQUIREMENT" in prompt


def test_system_prompt_requires_transcript_grounding():
    skill = get_ship30_skill()

    prompt = skill.system_prompt

    assert "Lenny transcript evidence" in prompt
    assert "Do not invent it." in prompt
    assert "Do not fabricate quotations" in prompt
    assert "Do not create citations" in prompt


def test_build_prompt_contains_topic_and_evidence():
    skill = get_ship30_skill()

    topic = "How should product teams prioritize features?"
    evidence = (
        "Product teams should begin with customer problems before "
        "deciding which features to build."
    )

    prompt = skill.build_prompt(
        topic=topic,
        transcript_evidence=evidence,
    )

    assert topic in prompt
    assert evidence in prompt
    assert "LENNY TRANSCRIPT EVIDENCE" in prompt
    assert "GROUNDING RULE" in prompt
    assert "Return ONLY the finished Markdown article." in prompt


def test_build_prompt_includes_conversation_context():
    skill = get_ship30_skill()

    prompt = skill.build_prompt(
        topic="How should teams prioritize features?",
        transcript_evidence="Start with the customer problem.",
        additional_context="The user wants a practical framework.",
    )

    assert "CURRENT CONVERSATION CONTEXT" in prompt
    assert "The user wants a practical framework." in prompt


def test_build_prompt_without_optional_context():
    skill = get_ship30_skill()

    prompt = skill.build_prompt(
        topic="How should teams prioritize features?",
        transcript_evidence="Start with the customer problem.",
    )

    assert "CURRENT CONVERSATION CONTEXT" not in prompt
    assert "Start with the customer problem." in prompt


def test_skill_does_not_generate_fake_citations():
    skill = get_ship30_skill()

    prompt = skill.build_prompt(
        topic="Product prioritization",
        transcript_evidence="Prioritize problems before solutions.",
    )

    assert "Do not invent citation numbers." in prompt
    assert "Do not add a References section." in prompt
    assert "Do not create citations" in skill.system_prompt