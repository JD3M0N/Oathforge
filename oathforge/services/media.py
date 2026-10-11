"""Cache of Telegram file_ids for catalog images (see oathforge/content/media.py)."""

from sqlalchemy.ext.asyncio import AsyncSession

from oathforge.content.media import MediaAsset
from oathforge.database.models import MediaFile


async def get_file_id(session: AsyncSession, bot_id: int, asset: MediaAsset) -> str | None:
    """The cached file_id, or None if never uploaded by this bot or the file has changed since."""
    row = await session.get(MediaFile, (bot_id, asset.key))
    return row.file_id if row is not None and row.checksum == asset.checksum else None


async def remember(session: AsyncSession, bot_id: int, asset: MediaAsset, file_id: str, file_unique_id: str) -> None:
    row = await session.get(MediaFile, (bot_id, asset.key))
    if row is None:
        session.add(MediaFile(bot_id=bot_id, asset_key=asset.key, checksum=asset.checksum,
                              file_id=file_id, file_unique_id=file_unique_id))
    else:
        row.checksum, row.file_id, row.file_unique_id = asset.checksum, file_id, file_unique_id


async def forget(session: AsyncSession, bot_id: int, asset: MediaAsset) -> None:
    """Drop a file_id Telegram rejected, so the next send uploads the file again."""
    row = await session.get(MediaFile, (bot_id, asset.key))
    if row is not None:
        await session.delete(row)
