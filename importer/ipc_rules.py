"""Parse the IPC allocation grammar used by the EPO business distribution scheme.

The published rules are compressed, and the compression is context-sensitive --
the same token means different things depending on what preceded it and on
whether it sits inside an exclusion. Worked examples from the 2026 scheme:

    B66B, 68                  -> B66B and B68        (class continuation)
    C13B5, 15                 -> C13B 5 and C13B 15  (group continuation)
    G07B (exc. 15)            -> exclude G07B 15     (not class G15)
    B01 (exc. D53/00-53/24;   -> exclude B01D 53/00-53/24 and B01D 61-71
         D61-71)                 (note the semicolon INSIDE the parenthetical)
    F16J-T                    -> subclasses F16J..F16T
    G01B-N (exc. N33)         -> G01B..G01N, less G01N 33

Two disambiguation rules carry most of the weight:

1. A bare number continues the *group* if the preceding token had an explicit
   group ("C13B5, 15"), and continues the *class* if it did not ("B66B, 68").
2. Inside an exclusion a bare number is always a group of the class being
   excluded from -- you cannot exclude a foreign class from a class you are
   including. This is what makes "G07B (exc. 15)" mean G07B 15.

`:IPCClass.symbol` in the graph is "A61K 31/00" -- section+class+subclass, a
space, main group, "/", subgroup -- so a rule expands to symbol *prefixes*
matched with STARTS WITH.

Subgroup ranges are deliberately NOT materialised. "A61K31/00-31/375" cannot be
expressed as a prefix, and approximating it to the whole main group A61K 31
would hand all of A61K 31 to board 3.3.04 while 3.3.07 excludes exactly that
range from its own A61K 31 -- two boards claiming the same subject matter. Such
main groups are reported as `contested` and dropped from materialisation, so the
graph under-claims rather than allocating an IPC class to the wrong board.
"""

import re

# Fully-qualified forms, longest first -- ordering matters, since a group range
# also matches the shorter group pattern.
PATTERNS = [
    # A61K31/00-31/375, A61F2/26-17/00
    ("subgroup_range", re.compile(r"^([A-H])(\d{2})([A-Z])(\d+)/(\w+)-(\d+)/(\w+)$")),
    # A61K31/00, H01L51/30, G03F7/42
    ("subgroup", re.compile(r"^([A-H])(\d{2})([A-Z])(\d+)/(\w+)$")),
    # C07K14-19, A61F13-17
    ("group_range", re.compile(r"^([A-H])(\d{2})([A-Z])(\d+)-(\d+)$")),
    # E01C19, A61K6, H10K85
    ("group", re.compile(r"^([A-H])(\d{2})([A-Z])(\d+)$")),
    # F16J-T, G01B-N, D06L-Q
    ("subclass_range", re.compile(r"^([A-H])(\d{2})([A-Z])-([A-Z])$")),
    # A47B
    ("subclass", re.compile(r"^([A-H])(\d{2})([A-Z])$")),
    # B63-64, E02-04
    ("class_range", re.compile(r"^([A-H])(\d{2})-(\d{2})$")),
    # B23
    ("klass", re.compile(r"^([A-H])(\d{2})$")),
]

# There is deliberately no pattern for a bare section letter. Boards are never
# allocated a whole IPC section, so a stray "G" is a typo, not an allocation --
# in the 2026 scheme board 3.4.03 reads "G09B, F ; G;", where the semicolon
# should be a comma (3.4.01 takes "G09 (exc. B, F, G)", so B, F and G must all
# fall to 3.4.03). Matching it as a section would silently hand 3.4.03 every
# G symbol in the corpus, so it is flagged instead.

# Bare continuation forms, resolved against the preceding token.
BARE_SUBCLASS = re.compile(r"^([A-Z])$")
BARE_SUBCLASS_RANGE = re.compile(r"^([A-Z])-([A-Z])$")
BARE_NUMBER = re.compile(r"^(\d+)$")
BARE_NUMBER_RANGE = re.compile(r"^(\d+)-(\d+)$")
BARE_SUBGROUP = re.compile(r"^(\d+/\w+)$")
BARE_SUBGROUP_RANGE = re.compile(r"^(\d+/\w+-\d+/\w+)$")
# "K67", "F2/00-2/20", "D61-71", "N33" -- a subclass letter plus a group spec.
BARE_WITH_SUBCLASS = re.compile(r"^([A-Z])(\d.*)$")


def split_top_level(text, separator=";"):
    """Split on `separator`, ignoring separators inside parentheses.

    Required because an exclusion list may itself contain a semicolon:
    "B01 (exc. D53/00-53/24; D61-71)" is one rule, not two.
    """
    parts, depth, current = [], 0, []
    for char in text:
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        if char == separator and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
    parts.append("".join(current))
    return [p.strip() for p in parts if p.strip()]


class _Context:
    """The trailing token's coordinates, used to resolve bare continuations."""

    __slots__ = ("section", "klass", "subclass", "had_group")

    def __init__(self, section, klass, subclass=None, had_group=False):
        self.section, self.klass = section, klass
        self.subclass, self.had_group = subclass, had_group


def _qualify(token, ctx, in_exclusion):
    """Expand a possibly-elided token to its fully-qualified form."""
    if ctx is None:
        return token

    stem = f"{ctx.section}{ctx.klass}"

    # Inside an exclusion the stem is always implied, so try it first -- reading
    # "D61-71" standalone would give class D61 instead of B01D 61-71.
    #
    # A single letter is never read standalone while a context exists: the bare
    # "section" pattern would otherwise swallow the "F" of "A61C, F" as section F
    # instead of A61F. A genuine bare section (the "G" allocated to 3.4.03) sits
    # in its own semicolon-delimited part, where the context is reset to None.
    if not in_exclusion and not BARE_SUBCLASS.match(token):
        for _, pattern in PATTERNS:
            if pattern.match(token):
                return token

    match = BARE_WITH_SUBCLASS.match(token)
    if match:
        return f"{stem}{token}"

    if BARE_SUBCLASS.match(token) or BARE_SUBCLASS_RANGE.match(token):
        return f"{stem}{token}"

    if BARE_SUBGROUP.match(token) or BARE_SUBGROUP_RANGE.match(token):
        return f"{stem}{ctx.subclass}{token}" if ctx.subclass else token

    match = BARE_NUMBER.match(token) or BARE_NUMBER_RANGE.match(token)
    if match:
        # Rule 1 and rule 2 from the module docstring.
        as_group = in_exclusion or ctx.had_group
        if as_group and ctx.subclass:
            return f"{stem}{ctx.subclass}{token}"
        return f"{ctx.section}{token}"

    # Fall back to a standalone reading (an exclusion naming a whole class).
    for _, pattern in PATTERNS:
        if pattern.match(token):
            return token
    return token


def _expand(qualified):
    """Turn a fully-qualified token into (prefixes, contested_keys).

    `contested_keys` are main groups whose membership cannot be expressed as a
    prefix; they are excluded from materialisation by the caller.
    """
    for kind, pattern in PATTERNS:
        match = pattern.match(qualified)
        if not match:
            continue
        groups = match.groups()

        if kind == "klass":
            section, klass = groups
            return [f"{section}{klass}"], [], _Context(section, klass)
        if kind == "class_range":
            section, start, end = groups
            if int(start) > int(end):
                return None, None, None
            return (
                [f"{section}{n:02d}" for n in range(int(start), int(end) + 1)],
                [],
                _Context(section, f"{int(end):02d}"),
            )
        if kind == "subclass":
            section, klass, subclass = groups
            return [f"{section}{klass}{subclass}"], [], _Context(section, klass, subclass)
        if kind == "subclass_range":
            section, klass, start, end = groups
            if start > end:
                return None, None, None
            # The IPC skips I and O in subclass letters to avoid confusion with
            # 1 and 0, so a range must not generate them.
            letters = [
                chr(c) for c in range(ord(start), ord(end) + 1) if chr(c) not in "IO"
            ]
            return (
                [f"{section}{klass}{letter}" for letter in letters],
                [],
                _Context(section, klass, end),
            )
        if kind == "group":
            section, klass, subclass, group = groups
            # The space and slash make this exact for the whole main group.
            return (
                [f"{section}{klass}{subclass} {int(group)}/"],
                [],
                _Context(section, klass, subclass, had_group=True),
            )
        if kind == "group_range":
            section, klass, subclass, start, end = groups
            if int(start) > int(end):
                return None, None, None
            return (
                [
                    f"{section}{klass}{subclass} {n}/"
                    for n in range(int(start), int(end) + 1)
                ],
                [],
                _Context(section, klass, subclass, had_group=True),
            )
        if kind == "subgroup":
            section, klass, subclass, group, sub = groups
            return (
                [f"{section}{klass}{subclass} {int(group)}/{sub}"],
                [],
                _Context(section, klass, subclass, had_group=True),
            )
        if kind == "subgroup_range":
            section, klass, subclass, g1, _s1, g2, _s2 = groups
            if int(g1) > int(g2):
                return None, None, None
            # Not expressible as a prefix -- report the main groups as contested.
            contested = [
                f"{section}{klass}{subclass} {n}/" for n in range(int(g1), int(g2) + 1)
            ]
            return [], contested, _Context(section, klass, subclass, had_group=True)

    return None, None, None


def _tokens(text, ctx, in_exclusion):
    """Expand a comma-separated token list, threading context along it."""
    prefixes, contested, ok = [], [], True
    for raw in split_top_level(text, ","):
        token = raw.strip().replace(" ", "").rstrip(".")
        if not token:
            continue
        qualified = _qualify(token, ctx, in_exclusion)
        expanded, contested_keys, new_ctx = _expand(qualified)
        if expanded is None:
            ok = False
            continue
        prefixes.extend(expanded)
        contested.extend(contested_keys)
        if new_ctx is not None:
            ctx = new_ctx
    return prefixes, contested, ctx, ok


EXCLUSION_RE = re.compile(r"\(\s*(?:exc\.?|excl\.?|except)\s*(.*?)\s*\)", re.IGNORECASE | re.S)


def parse_rule(rule_raw):
    """Parse a published allocation string into symbol prefixes.

    Returns includes / excludes / contested prefix lists and a `parseStatus`:

        parsed    every token read, nothing contested
        partial   read, but some main groups dropped as contested
        unparsed  at least one token could not be read

    `contested` main groups are removed from both includes and excludes, so the
    graph never claims an allocation the grammar cannot express exactly.
    """
    includes, excludes, ok = [], [], True
    # Contested main groups are handled differently depending on where the
    # unexpressible range appeared:
    #
    #   include position ("A61K31/00-31/375, 36, ...")  -> drop it from includes
    #   exclude position ("A61 (exc. F2/00-2/20, ...)") -> add it to excludes,
    #                                                      narrowing the broad
    #                                                      include it qualifies
    #
    # Both directions under-claim rather than over-claim, and the second is what
    # stops board 3.2.02's broad "A61" from colliding with 3.2.08's "A61F".
    contested_in, contested_ex = [], []

    for part in split_top_level(rule_raw, ";"):
        # Context resets per semicolon-delimited part, and is threaded across the
        # comma-separated items within it. Walking item by item is what lets an
        # exclusion attach to the token it follows -- "H01B, C, L (exc. 51/00),
        # R, S (exc. 3/14-3/227), T" carries two, each scoped to its own head.
        ctx = None
        for item in split_top_level(part, ","):
            exclusion = EXCLUSION_RE.search(item)
            head = EXCLUSION_RE.sub("", item).strip().strip(",").strip()

            if head:
                expanded, item_contested, new_ctx = _expand(_qualify(head, ctx, False))
                if expanded is None:
                    ok = False
                else:
                    includes.extend(expanded)
                    contested_in.extend(item_contested)
                    if new_ctx is not None:
                        ctx = new_ctx

            if not exclusion:
                continue

            # An exclusion list may be semicolon-separated internally:
            # "B01 (exc. D53/00-53/24; D61-71)".
            exc_text = exclusion.group(1).replace(";", ",")
            exc_prefixes, exc_contested, _, exc_ok = _tokens(exc_text, ctx, True)
            excludes.extend(exc_prefixes)
            contested_ex.extend(exc_contested)
            ok = ok and exc_ok

    contested_in = sorted(set(contested_in))
    contested_ex = sorted(set(contested_ex))
    contested = sorted(set(contested_in) | set(contested_ex))

    def drop_contested(prefixes):
        # Drop only prefixes that fall *inside* a contested main group. A broader
        # include that merely contains one is kept -- dropping "A61" because
        # "A61F 2/" is contested would erase board 3.2.02's entire allocation.
        return sorted({
            p for p in set(prefixes) if not any(p.startswith(c) for c in contested)
        })

    if contested:
        status = "unparsed" if not ok else "partial"
    else:
        status = "parsed" if ok and includes else "unparsed"

    return {
        "includes": drop_contested(includes),
        "excludes": sorted(set(drop_contested(excludes)) | set(contested_ex)),
        "contested": contested,
        "parseStatus": status,
    }
