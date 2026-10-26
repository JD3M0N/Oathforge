"""What every validation module shares."""


def collector():
    """A fresh error list and ``need``, which reports a key missing from its pool."""
    errors: list[str] = []

    def need(kind: str, key: str | None, pool: dict, where: str) -> None:
        if key is not None and key not in pool:
            errors.append(f"{where}: unknown {kind} '{key}'")

    return errors, need
