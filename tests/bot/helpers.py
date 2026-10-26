"""Fake Telegram objects and shortcuts shared by the handler tests."""

from types import SimpleNamespace

from sqlalchemy import select
from telegram.ext import ConversationHandler

from oathforge.bot.handlers import callbacks, creation, text
from oathforge.bot.keyboards import parse
from oathforge.database.models import Character
from oathforge.database.session import session_scope


class Chat:
    def __init__(self):
        self.sent: list[tuple[str, object]] = []
        self.photos: list[object] = []  # what was sent: bytes (upload) or a cached file_id
        self.popups: list[str] = []  # small popups answering a button press (refusals, stale menus)
        self.dropped = 0

    async def send_message(self, text, parse_mode=None, reply_markup=None, **_):
        self.sent.append((text, reply_markup))

    async def send_photo(self, photo, caption=None, **_):
        self.photos.append(photo)
        self.sent.append((caption, None))
        size = SimpleNamespace(file_id=f"FILE{len(self.photos)}", file_unique_id=f"U{len(self.photos)}")
        return SimpleNamespace(photo=[size])

    async def send_action(self, *_):
        pass

    async def send_dice(self, emoji=None, **_):
        self.dice = getattr(self, "dice", 0) + 1


class Query:
    ids = 0

    def __init__(self, data, chat):
        self.data, self.chat, self.message = data, chat, object()
        self.answers = 0
        Query.ids += 1
        self.id = str(Query.ids)

    async def answer(self, text=None, *_, **__):
        self.answers += 1
        assert self.answers == 1, "callback answered twice"
        if text:
            self.chat.popups.append(text)

    async def edit_message_text(self, text, parse_mode=None, reply_markup=None, **_):
        self.chat.sent.append((text, reply_markup))

    async def edit_message_reply_markup(self, reply_markup=None, **_):
        self.chat.dropped += 1  # the pressed message keeps its text and loses its buttons


class Player:
    def __init__(self, llm, tg_id=42, lang="es"):
        self.chat = Chat()
        self.user = SimpleNamespace(id=tg_id, language_code=lang)
        self.ctx = SimpleNamespace(bot_data={"llm": llm}, user_data={}, bot=SimpleNamespace(id=999))

    def update(self, data=None, message=None):
        q = Query(data, self.chat) if data else None
        msg = SimpleNamespace(text=message, message_id=len(self.chat.sent) + 1) if message is not None else None
        return SimpleNamespace(effective_user=self.user, effective_chat=self.chat, callback_query=q, message=msg)

    @property
    def last(self):
        return self.chat.sent[-1]

    def buttons(self):
        kb = self.last[1]
        return [b.callback_data for row in getattr(kb, "inline_keyboard", ()) for b in row]

    def find(self, verb, arg=None):
        for data in (
            d
            for text_, kb in reversed(self.chat.sent)
            if kb
            for row in getattr(kb, "inline_keyboard", ())
            for b in row
            for d in [b.callback_data]
        ):
            v, a, _ = parse(data)
            if v == verb and (arg is None or a == arg or a.startswith(arg)):
                return data
        raise AssertionError(f"no button {verb}|{arg}; last: {self.last[0][:300]!r} {self.buttons()}")

    async def press(self, data):
        await callbacks.on_callback(self.update(data=data), self.ctx)

    async def say(self, message):
        await text.on_text(self.update(message=message), self.ctx)


async def create(p: Player, cls="paladin", gender="male"):
    assert await creation.start(p.update(message="/start"), p.ctx) == creation.NAME
    assert await creation.got_name(p.update(message="x"), p.ctx) == creation.NAME  # invalid name
    assert await creation.got_name(p.update(message="Aldric"), p.ctx) == creation.GENDER
    assert await creation.got_gender(p.update(data="cc|gen:robot"), p.ctx) == creation.GENDER  # unknown
    assert await creation.got_gender(p.update(data=f"cc|gen:{gender}"), p.ctx) == creation.LINEAGE
    assert await creation.got_lineage(p.update(data="cc|lin:human"), p.ctx) == creation.BACKGROUND
    assert await creation.got_background(p.update(data="cc|bg:soldier"), p.ctx) == creation.CLASS
    assert await creation.got_class(p.update(data=f"cc|cls:{cls}"), p.ctx) == creation.ABILITIES
    assert await creation.got_ability(p.update(data="cc|ab:ok"), p.ctx) == creation.ABILITIES  # 27 points left
    assert await creation.got_ability(p.update(data="cc|ab:rec"), p.ctx) == creation.ABILITIES
    assert await creation.got_ability(p.update(data="cc|ab:ok"), p.ctx) == creation.CONFIRM
    assert await creation.confirm(p.update(data="cc|ok"), p.ctx) == ConversationHandler.END


async def char_row() -> Character:
    async with session_scope() as s:
        return await s.scalar(select(Character))


async def creation_free_roll(p):
    from oathforge.bot.handlers import commands

    assert not any("roll" in getattr(h, "commands", ()) for h in commands.handlers())  # no /roll command
    await p.press(p.find("roll"))


class FakeBot:
    def __init__(self, chat: Chat):
        self.chat, self.id = chat, 999

    async def send_message(self, chat_id, text, **kwargs):
        await self.chat.send_message(text, **kwargs)
