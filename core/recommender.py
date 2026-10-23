"""Explainable, local rules for waste sorting; no LLM or network calls."""
import re

RULES = {
    "plastic": {"bin":"Recycling bin", "color":"#2878c8", "stream":"Recyclable", "how":"Empty and rinse bottles, then use the local recycling stream for accepted rigid plastics. Keep film and wrappers separate unless your local program accepts them."},
    "paper": {"bin":"Paper recycling", "color":"#d9a51c", "stream":"Recyclable", "how":"Keep paper and cardboard dry and clean; flatten boxes before placing them in paper recycling."},
    "metal": {"bin":"Metal recycling", "color":"#697985", "stream":"Recyclable", "how":"Empty food or drink cans and give them a quick rinse before recycling."},
    "glass": {"bin":"Glass recycling", "color":"#24966b", "stream":"Recyclable", "how":"Empty glass containers and use the local glass collection point. Handle broken glass carefully; never place loose shards in a bag."},
    "organic": {"bin":"Wet waste / compost", "color":"#855b36", "stream":"Compostable", "how":"Put food scraps in the wet-waste or composting stream. Keep plastic packaging out of the compost."},
    "general": {"bin":"Residual waste", "color":"#65736b", "stream":"Neither (usually)", "how":"Use residual waste only when no local recycling or composting route accepts the item. Keep batteries, chemicals, and electronics out of ordinary bins; check a local drop-off service."},
}

ITEM_LOOKUP = {
    "plastic bottle":"plastic", "soda bottle":"plastic", "water bottle":"plastic", "pet bottle":"plastic",
    "plastic bag":"plastic", "wrapper":"plastic", "plastic wrapper":"plastic", "snack wrapper":"plastic",
    "plastic cup":"plastic", "food packaging":"plastic", "cardboard":"paper", "cardboard box":"paper",
    "paper":"paper", "newspaper":"paper", "book":"paper", "paper cup":"paper", "carton":"paper",
    "aluminum can":"metal", "aluminium can":"metal", "tin can":"metal", "metal can":"metal", "soda can":"metal",
    "glass bottle":"glass", "wine bottle":"glass", "glass jar":"glass", "jar":"glass", "broken glass":"glass",
    "food scraps":"organic", "food waste":"organic", "leftovers":"organic", "banana peel":"organic",
    "fruit peel":"organic", "eggshell":"organic", "eggshells":"organic", "egg shell":"organic", "egg shells":"organic", "vegetable scraps":"organic", "coffee grounds":"organic",
    "foam":"general", "styrofoam":"general", "diaper":"general", "battery":"general", "general waste":"general",
}

def _normalize(value):
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value.lower()).split())

def classify_item(item):
    """Return category and match explanation for a free-text item description."""
    query = _normalize(item)
    if not query:
        return "general", "empty"
    if query in RULES:
        return query, "category"
    if query in ITEM_LOOKUP:
        return ITEM_LOOKUP[query], "exact"
    # Match a known phrase inside a longer user description, longest first.
    for alias in sorted(ITEM_LOOKUP, key=len, reverse=True):
        if alias in query:
            return ITEM_LOOKUP[alias], f"contains:{alias}"
    # Conservative phrase cues for items not listed above.
    cues = [
        (("plastic", "polyethylene", "pet "), "plastic"),
        (("cardboard", "paper", "newspaper", "book", "carton"), "paper"),
        (("aluminium", "aluminum", "metal", "tin can"), "metal"),
        (("glass", "jar"), "glass"),
        (("food", "fruit", "vegetable", "peel", "leftover", "organic"), "organic"),
    ]
    for words, category in cues:
        if any(word in query for word in words):
            return category, "keyword"
    return "general", "fallback"

def guidance(category_or_item):
    category, _ = classify_item(category_or_item)
    return category, RULES[category]
