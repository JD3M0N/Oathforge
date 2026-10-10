"""NPC conversation: persona + retrieved memories -> line + memory proposal."""

from pydantic import BaseModel, Field

from oathforge.ai.client import LLM
from oathforge.ai.prompts import LANGUAGE_NAMES, NPC_SYSTEM
from oathforge.content.schemas import Npc


class NpcReply(BaseModel):
    line: str
    memory_note: str = ""
    importance: int = Field(1, ge=1, le=5)
    trust_delta: int = Field(0, ge=-2, le=2)


async def reply(
    llm: LLM, *, npc: Npc, lang: str, player: str, player_text: str, trust: int, reputation: int | None,
    memories: list[str], rumors: list[str], time_of_day: str, user_id: int | None,
) -> NpcReply | None:
    system = NPC_SYSTEM.format(
        name=npc.name.en, title=npc.title.en, persona=npc.persona, goals=npc.goals, secrets=npc.secrets,
        knowledge=npc.knowledge, language=LANGUAGE_NAMES.get(lang, "English"),
    )
    prompt = (
        f"Time: {time_of_day}\n"
        f"Speaking to: {player}\n"
        f"Your trust in them (-10..10): {trust}\n"
        + (f"Their standing with your faction (-100..100): {reputation}\n" if reputation is not None else "")
        + "Your memories of them:\n" + ("\n".join(f"- {m}" for m in memories) or "- (you have never met them)")
        + "\nRumors you have heard lately:\n" + ("\n".join(f"- {r}" for r in rumors) or "- (none)")
        + f"\n\n<player_text>\n{player_text[:600]}\n</player_text>"
    )
    return await llm.json(tier="narrative", system=system, prompt=prompt, schema=NpcReply, user_id=user_id)
