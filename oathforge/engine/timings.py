"""How long things take and what resting gives back: the one table (roadmap_balance §12).

The rulebook, the Activities panel and the services read these numbers and no others. Travel, crafting and
refining have no timer of their own (a trip is a risk, not a wait). A game day lasts four real hours.
"""

GATHER_SECONDS = 4 * 60  # normal gathering: 3-5 minutes
STAY_SECONDS = 15 * 60  # a long expedition: 12-15 minutes
TRACK_SECONDS = 3 * 60  # tracking: 2-4 minutes
REST_SECONDS = 15 * 60  # a long rest, somewhere safe: 15-20 minutes
SHORT_REST_SECONDS = 3 * 60  # a short rest: 2-3 minutes

SHORT_REST_HP_PCT = 0.30  # of max HP, never past the injury cap
SHORT_REST_POOL_PCT = 0.5  # of a class bar
SHORT_REST_USES = 1  # of the most spent limited ability, for classes without a bar
SHORT_RESTS_PER_LONG = 2  # a long rest gives them back; without it the third one is refused

SECONDS = {
    "gather": GATHER_SECONDS,
    "stay": STAY_SECONDS,
    "track": TRACK_SECONDS,
    "rest": REST_SECONDS,
    "short_rest": SHORT_REST_SECONDS,
}
