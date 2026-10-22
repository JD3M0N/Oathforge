from oathforge.ai import moderation


class ReviewLLM:
    def __init__(self, response):
        self.response = response
        self.system = ""
        self.prompt = ""

    async def json(self, *, system, prompt, schema, **_):
        self.system, self.prompt = system, prompt
        return schema.model_validate(self.response)


async def test_background_review_grounds_an_adaptation_in_trusted_context():
    llm = ReviewLLM({
        "status": "adapted",
        "reason": "Replaced the modern platform.",
        "title": "  Courtesan  ",
        "story": "Offered discreet company to adult clients until debts forced her to flee.",
    })
    review = await moderation.review_background(
        llm, lang="en", title="Online model",
        story="I sold subscriptions on a modern platform until I fled my debts.",
        world_context="No internet; engineering includes gunpowder.",
        lineage_context="Human: adaptable and ambitious.", user_id=1,
    )
    assert review and review.status == "adapted" and review.title == "Courtesan"
    assert "No internet" in llm.system and "<world_guide>" in llm.system
    assert "<character_context>" in llm.prompt and "<player_text>" in llm.prompt


async def test_background_review_preserves_an_accepted_story_and_rejects_bad_proposals():
    story = "I kept a lonely lighthouse on the coast before answering the road's call."
    accepted = ReviewLLM({"status": "accepted", "title": "Keeper", "story": "Changed by the model."})
    review = await moderation.review_background(
        accepted, lang="en", title="keeper", story=story, world_context="Fantasy.",
        lineage_context="Human.", user_id=1,
    )
    assert review and review.story == story

    invalid = ReviewLLM({"status": "adapted", "title": "Keeper", "story": "Too short."})
    assert await moderation.review_background(
        invalid, lang="en", title="keeper", story=story, world_context="Fantasy.",
        lineage_context="Human.", user_id=1,
    ) is None
