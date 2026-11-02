"""Convert Rules Reference v1.4.6-1 through APPENDIX: EXAMPLES (physical pages 2–29)."""

import argparse
from dataclasses import dataclass, field
from itertools import groupby
from html import escape
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.parse import quote

import pymupdf
import markdown

from pdf_artwork import render_figure


SOURCE = Path("Rules Reference v1.4.6-1.pdf")
TEXT_FLAGS = pymupdf.TEXTFLAGS_DICT & ~pymupdf.TEXT_PRESERVE_IMAGES
REFERENCE_COLOR = 0x0F864C
APPENDIX_SECTION = "APPENDIX: EXAMPLES"
STOP_SECTION = "ERRATA"
SYMBOLS = {
    "\U000f2040": "[focus]", "\U000f2041": "[lock]",
    "\U000f2042": "[barrel-roll]", "\U000f2043": "[boost]",
    "\U000f2044": "[evade]", "\U000f2045": "[cloak]",
    "\U000f2047": "[reinforce]", "\U000f2048": "[coordinate]",
    "\U000f2049": "[jam]", "\U000f204a": "[slam]",
    "\U000f204b": "[talent]", "\U000f204c": "[sensor]",
    "\U000f204d": "[cannon]", "\U000f204e": "[turret]",
    "\U000f204f": "[torpedo]", "\U000f2050": "[missile]",
    "\U000f2052": "[crew]", "\U000f2054": "[astromech]",
    "\U000f2056": "[payload]", "\U000f2058": "[illicit]",
    "\U000f2059": "[modification]", "\U000f205a": "[title]",
    "\U000f205b": "[tech]", "\U000f205c": "[turn-left]",
    "\U000f205d": "[bank-left]", "\U000f205e": "[straight]",
    "\U000f205f": "[bank-right]", "\U000f2060": "[turn-right]",
    "\U000f2061": "[stationary]", "\U000f2062": "[tallon-roll-left]",
    "\U000f2063": "[segnors-loop-left]", "\U000f2064": "[koiogran-turn]",
    "\U000f2065": "[segnors-loop-right]", "\U000f2066": "[tallon-roll-right]",
    "\U000f2067": "[hit]", "\U000f2068": "[critical-hit]",
    "\U000f206a": "[energy]", "\U000f206b": "[rotate]",
    "\U000f206c": "[reverse-straight]", "\U000f206d": "[reverse-bank-right]",
    "\U000f206e": "[reverse-bank-left]", "\U000f2221": "[configuration]",
    "\U000f2222": "[force-power]", "\U000f2223": "[reload]",
    "\U000f2224": "[linked-action]", "\U000f2225": "[calculate]",
    "\U000f2226": "[gunner]", "\U000f2227": "[full-front-arc]",
    "\U000f2228": "[full-rear-arc]", "\U000f2229": "[bullseye-arc]",
    "\U000f222a": "[rear-arc]", "\U000f222b": "[front-arc]",
    "\U000f222c": "[double-turret-arc]", "\U000f222d": "[turret-arc]",
    "\U000f222e": "[charge]", "\U000f222f": "[force]",
    "\U000f2400": "[left-arc]", "\U000f2401": "[right-arc]",
    "\U000f2402": "[tactical-relay]", "\U000f2408": "[shield]",
    "\U000f25c0": "[attack]", "\U000f2409": "[threat]", "\U000f2500": "[hyperdrive]",
}

# Crop bounds include captions; embedded image bounds ignore PDF clipping masks.
# Entries contain (rectangle, description, insertion y). Side artwork follows its heading.
FIGURES = {
    2: [((312, 288, 576, 405), "Pilot and ship abilities", 288)],
    3: [((528, 561, 576, 627), "Agility value on a ship card", 589)],
    4: [((110, 273, 217, 377), "Standard arcs", 273),
        ((110, 505, 218, 609), "Bullseye arc", 505),
        ((392, 56, 485, 153), "Full front and rear arcs", 56),
        ((380, 372, 506, 506), "Single turret arc indicator and ID tokens", 372),
        ((520, 543, 589, 617), "Double turret arc indicator", 612)],
    6: [((30, 180, 305, 259), "Small ship barrel roll positions", 180),
        ((30, 279, 305, 359), "Medium or large ship barrel roll", 279)],
    7: [((33, 185, 107, 269), "Blazer Bomb", 185),
        ((310, 149, 581, 273), "Boost positions", 149),
        ((528, 610, 581, 666), "Calculate token", 630)],
    8: [((235, 630, 291, 676), "Recurring charge symbol", 630),
        ((231, 688, 297, 738), "Negative recurring charge symbol", 688)],
    9: [((253, 31, 305, 86), "Cloak token", 47.5)],
    10: [((231, 78, 306, 170), "Damage cards", 78),
         ((252, 616, 305, 674), "Deplete token", 632)],
    11: [((175, 281, 305, 388), "X-wing dials front and back", 302),
         ((531, 376, 584, 430), "Disarm token", 394)],
    12: [((258, 703, 309, 760), "Evade token", 719.5),
         ((535, 626, 588, 680), "Focus token", 644)],
    13: [((257, 275, 309, 337), "Fuse marker", 292),
         ((542, 33, 581, 98), "Hull value on a ship card", 47.5),
         ((534, 259, 590, 321), "Ion token", 273)],
    14: [((253, 159, 305, 214), "Jam token", 175.2)],
    16: [((94, 431, 284, 518), "Obstructed attack", 431)],
    17: [((31, 168, 161, 247), "Player markers", 168),
         ((242, 258, 307, 335), "First player marker", 264),
         ((253, 434, 310, 504), "Position marker", 450),
         ((247, 510, 312, 575), "Primary weapon on a ship card", 521),
         ((359, 75, 531, 233), "Within and beyond range 1", 75)],
    18: [((253, 89, 301, 138), "Ordnance icon", 47.5),
         ((241, 168, 304, 222), "Fore reinforce token", 186.5),
         ((241, 222, 304, 274), "Aft reinforce token", 222),
         ((34, 316, 264, 473), "Reinforce example", 316)],
    19: [((69, 167, 267, 310), "Relocating a remote forward", 167)],
    20: [((449, 236, 584, 332), "A left sideslip", 236),
         ((323, 397, 590, 510), "Correct and incorrect sideslip placement", 397)],
    21: [((40, 81, 305, 264), "Bank compared with sideslip", 81),
         ((253, 690, 306, 738), "Ordnance icon", 699),
         ((533, 640, 586, 696), "Strain token", 656)],
    22: [((257, 31, 309, 84), "Stress token", 47.5),
         ((531, 567, 584, 632), "Tractor token", 588)],
    23: [((300, 68, 388, 133), "Victory counters", 47.5)],
}

# These callout diagrams mix labels with artwork rather than captions below it.
COMPOSITE_FIGURES = {(2, "Pilot and ship abilities"),
                     (4, "Single turret arc indicator and ID tokens")}

# Source MCIDs in FIGURES order, including embedded labels in composite diagrams.
# Include the page 20 check/cross text groups as part of their diagram, not captions.
FIGURE_GROUPS = {
    (page, description): mcids
    for page, groups in {
        2: [(84, 85, 86, 87, 88)],
        3: [(296,)],
        4: [(599,), (600,), (494,), tuple(range(495, 503)), (503,)],
        6: [(1061, 1062, 1063), (1064, 1065, 1066)],
        7: [(1216,), tuple(range(1177, 1189)), (1189,)],
        8: [(1556,), (1559,)],
        9: [(1778,)],
        10: [(1970,), (1971,)],
        11: [(2205, 2206, 2207, 2210), (2101,)],
        12: [(2481,), (2354,)],
        13: [(2699,), (2586,), (2590,)],
        14: [(2936,)],
        16: [(3423,)],
        17: [(3523, 3524), (3586,), (3587,), (3590,), (3498, 3503)],
        18: [(3789,), (3791,), (3793,), (3800,)],
        19: [(4012, 4013, 4014, 4015)],
        20: [(4105, 4106, 4107, 4108), (4115, 4116, 4117, 4118, 4122, 4123, 4124, 4125)],
        21: [tuple(range(4448, 4454)), (4460,), (4345,)],
        22: [(4668,), (4568,)],
        23: [(4675,)],
    }.items()
    for (_, description, _), mcids in zip(FIGURES[page], groups, strict=True) if mcids
}

APPENDIX_GROUPS = {
    24: "Examples",
    25: "Objects: Bombs and Mines",
    26: "Objects: Bombs and Mines",
    27: "Objects: Obstacles",
    28: "Objects: Remotes",
    29: "Device and Deploying Examples",
}

# Appendix cards remain in column order; each rectangle becomes one indexed rule.
APPENDIX_CARDS = {
    25: [("Bomblet", (36, 56, 300, 258)),
         ("Concussion Bomb", (36, 258, 300, 467)),
         ("Electro-Proton Bomb", (36, 467, 300, 705)),
         ("Cluster Mine", (312, 56, 576, 316)),
         ("Conner Net", (312, 316, 576, 516)),
         ("Ion Bomb", (312, 516, 576, 719))],
    26: [("Proton Bomb", (36, 50, 300, 249)),
         ("Seismic Charge", (36, 256, 300, 456)),
         ("Proximity Mine", (36, 464, 300, 660)),
         ("Thermal Detonator", (312, 50, 576, 249)),
         ("Blazer Bomb", (312, 256, 576, 706))],
    27: [("Asteroids", (36, 50, 300, 299)),
         ("Debris Clouds", (36, 307, 300, 558)),
         ("Loose Cargo", (36, 568, 300, 740)),
         ("Cargo Drift", (312, 50, 576, 240)),
         ("Gas Clouds", (312, 260, 576, 523)),
         ("Spare Parts", (312, 537, 576, 730))],
    28: [("Buzz Droid Swarm", (36, 56, 300, 424)),
         ("Sensor Buoy", (36, 433, 300, 611)),
         ("Dark Eye Probe Droid", (312, 34, 576, 348)),
         ("Commando Team", (312, 354, 576, 744))],
    29: [("Deploy Example", (90, 60, 234, 283)),
         ("Dropping Bomb Example", (280, 60, 378, 270)),
         ("Launching Bomb Example", (420, 48, 526, 302)),
         ("Ship Cards", (28, 337, 305, 701)),
         ("Upgrade Cards", (312, 337, 584, 750))],
}

# Appendix artwork excludes decorative card borders. Remote stat bars keep their labels.
APPENDIX_FIGURES = {
    24: [((100, 198, 234, 222), "Jake ability queue", 198, tuple(range(4870, 4872))),
         ((70, 314, 270, 340), "Jake repeated ability queue", 314, tuple(range(4872, 4875))),
         ((52, 385, 285, 418), "Phoenix Squadron ability queue", 385, tuple(range(4875, 4879))),
         ((350, 146, 550, 171), "Chopper ability queue", 146, tuple(range(4907, 4910)))],
    25: [((46, 84, 294, 191), "Bomblet token", 84, (4926,)),
         ((46, 284, 294, 391), "Concussion Bomb token", 284, (5003,)),
         ((46, 494, 294, 601), "Electro-Proton Bomb token", 494, (4960,)),
         ((322, 92, 572, 198), "Cluster Mine set", 92, tuple(range(4987, 4993))),
         ((322, 344, 572, 451), "Conner Net token", 344, (4937,)),
         ((322, 544, 572, 650), "Ion Bomb token", 544, (4970,))],
    26: [((46, 75, 294, 182), "Proton Bomb token", 75, (5057,)),
         ((46, 283, 294, 389), "Seismic Charge token", 283, (5030,)),
         ((46, 492, 294, 599), "Proximity Mine token", 492, (5017,)),
         ((322, 75, 572, 182), "Thermal Detonator token", 75, (5046,)),
         ((354, 298, 546, 410), "Blazer Bomb and Blaze", 298, (5076, 5077, 5082, 5083)),
         ((354, 493, 524, 646), "Placing Blaze", 493, (5078, 5079, 5080, 5081))],
    27: [((46, 78, 294, 262), "Asteroid examples", 78, (5123, 5124, 5125)),
         ((46, 336, 294, 519), "Debris Cloud examples", 336, (5126, 5127, 5128)),
         ((46, 594, 294, 716), "Loose Cargo token", 594, (5092,)),
         ((322, 78, 572, 198), "Cargo Drift token", 78, (5104,)),
         ((322, 287, 572, 482), "Gas Cloud examples", 287, (5120, 5121, 5122)),
         ((322, 565, 572, 685), "Spare Parts token", 565, (5098,))],
    28: [((46, 84, 288, 177), "Buzz Droid Swarm token and stats", 84, tuple(range(5211, 5218))),
         ((210, 239, 294, 334), "Buzz Droid Swarm placement", 239, tuple(range(5197, 5203))),
         ((172, 340, 294, 420), "Buzz Droid Swarm blocked placement", 340, tuple(range(5203, 5211))),
         ((46, 439, 288, 526), "Sensor Buoy token and stats", 439, tuple(range(5228, 5235))),
         ((324, 60, 554, 153), "Dark Eye Probe Droid token and stats", 60, tuple(range(5160, 5167))),
         ((390, 389, 502, 471), "Commando Team token", 389, (5292,)),
         ((352, 481, 532, 524), "Commando Team stats", 481, tuple(range(5236, 5249)))],
    29: [((94, 82, 233, 254), "Deploy diagram", 82, (5355,)),
         ((282, 92, 376, 234), "Dropping Bomb diagram", 92, (5365,)),
         ((425, 82, 518, 265), "Launching Bomb diagram", 82, (5374,)),
         ((28, 357, 305, 701), "Ship card anatomy", 357, tuple(range(5299, 5326)) + (5296,)),
         ((312, 357, 584, 750), "Upgrade card anatomy", 357, tuple(range(5326, 5355)) + (5297,))],
}
for page, figures in APPENDIX_FIGURES.items():
    FIGURES[page] = [(box, description, anchor) for box, description, anchor, _ in figures]
    FIGURE_GROUPS.update({(page, description): mcids for _, description, _, mcids in figures})
COMPOSITE_FIGURES.update({
    (24, description) for _, description, _, _ in APPENDIX_FIGURES[24]
})
COMPOSITE_FIGURES.update({
    (28, description) for _, description, _, _ in APPENDIX_FIGURES[28]
})
COMPOSITE_FIGURES.update({(29, "Ship card anatomy"), (29, "Upgrade card anatomy")})


# Printed cross-references include inflections and descriptive phrases, not only headings.
RULE_ALIASES = {}
for destination, variants in {
    "abilities": ["ability"], "actions": ["action"],
    "arc": ["arcs"], "attack": ["attacks"], "attack range": ["attack ranges"],
    "barrel roll": ["barrel rolls", "barrel rolling"],
    "boost": ["boosts", "boosting"], "cancel": ["canceling"],
    "charges": ["charge", "charge limit"], "force charge": ["force capacity"],
    "condition cards": ["condition"], "coordinate": ["coordinates"],
    "decloak": ["decloaking", "decloaks"], "deplete": ["deplete token"],
    "destroying ships": ["destroyed"], "device": ["devices", "dropping and launching devices"],
    "dock": ["docked"], "deploy": ["deploys"], "disarmed": ["disarm"],
    "drop": ["dropped"], "engagement phase": ["engagement phases"],
    "fail": ["fails"], "flee": ["flees", "fled"], "hit": ["hits"],
    "id marker": ["id markers"], "initiative": ["initiative order"],
    "jam": ["jams"], "launch": ["launched"], "linked action": ["linked actions"],
    "lock": ["locks"], "maneuver": ["maneuvers"], "miss": ["misses"],
    "dice modification": ["modifying dice"], "move": ["moves"],
    "move through": ["moving through", "moved through"], "objects": ["object"],
    "obstacles": ["obstacle"], "overlap": ["overlapped", "overlapping"],
    "partially execute": ["partially executing", "partially executes", "partially executes a maneuver"],
    "primary weapon": ["primary"], "range": ["range 0", "range 4–5"],
    "recurring charges": ["recurring charge icon"],
    "negative recurring charges": ["negative recurring charge icon"],
    "removed from the game": ["removed"], "upgrade cards": ["restriction", "upgrade"],
    "ship": ["ships"], "ship sizes": ["size", "medium or large ship"],
    "ship type": ["ship’s type"], "slam": ["slams"],
    "special weapon": ["special", "special weapons"], "strain": ["strain token"],
    "stress": ["stress token", "stressed"], "suffer damage": ["suffers damage"],
    "system phase": ["system"], "tokens": ["token"], "winning the game": ["wins"],
}.items():
    RULE_ALIASES.update(dict.fromkeys(variants, destination))
EXTERNAL_RULES = {
    "appendix: huge ships": 44,
    "appendix: environment cards": 49, "squad building": 43,

}


@dataclass
class Block:
    kind: str
    spans: list = field(default_factory=list)
    page: int = 0
    prefix: str = ""
    figure: tuple | None = None

    @property
    def text(self):
        return "".join(s["text"] for s in self.spans).replace("\ufffc", "").strip()


def heading_level(spans):
    """Use the source's three heading styles, not capitalization."""
    if any(s["font"] == "KimberleyBl-Regular" and s["size"] >= 17 for s in spans):
        return 1
    if any(s["font"] == "EurostileLTStd-Bold" and s["size"] >= 10.5 for s in spans):
        return 2
    letters = [s for s in spans if s["font"] != "X-WingIcons" and s["text"].strip()]
    if letters and all(s["font"] == "EurostileLTStd-Bold-SC70" for s in letters) and max(s["size"] for s in letters) >= 9.5:
        return 3
    if letters and all(s["font"] == "EurostileLTStd-Bold" for s in letters):
        text = "".join(s["text"] for s in letters)
        if text.isupper() and re.fullmatch(r"[A-Z ]+", text):
            return 3
    return 0


def title_key(text):
    return text.split("(")[0].replace("\ufffc", "").strip().rstrip(".").casefold()


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.casefold().replace("’", "")).strip("-")


def translated(span):
    text = span["text"].replace("\u00ad", "").replace("\ufffc", "").replace("\x07", "")
    if span["font"] == "X-WingIcons":
        unknown = set(text) - SYMBOLS.keys() - set(" ")
        if unknown:
            codes = ", ".join(f"U+{ord(c):04X}" for c in sorted(unknown))
            raise ValueError(f"Unmapped X-WingIcons character(s): {codes}")
        return "".join(SYMBOLS.get(c, c) for c in text)
    if any(0xE000 <= ord(c) <= 0xF8FF or 0xF0000 <= ord(c) <= 0x10FFFD or c == "\ufffd" for c in text):
        raise ValueError(f"Unmapped character in font {span['font']}")
    return text


def body_line(spans):
    return any(s["font"] == "EurostileLTStd-Cn" and 8.2 <= s["size"] <= 8.6 for s in spans)


def figure_content(page, box, description):
    """Separate source-sized captions from artwork, retaining printed card text."""
    if (page.number + 1, description) in COMPOSITE_FIGURES:
        return box, []
    clip = pymupdf.Rect(box)
    lines = [line for block in page.get_text("dict", flags=TEXT_FLAGS)["blocks"]
             for line in block.get("lines", [])
             if clip.contains((pymupdf.Rect(line["bbox"]).tl + pymupdf.Rect(line["bbox"]).br) / 2)
             and any(s["font"] == "EurostileLTStd-Cn" and 7 <= s["size"] <= 8.1
                     for s in line["spans"])]
    if not lines:
        return box, []
    # Centered wrapped lines can occupy separate PDF blocks; keep paired captions separate.
    groups = []
    for line in sorted(lines, key=lambda line: (round(line["bbox"][1]), line["bbox"][0])):
        rect = pymupdf.Rect(line["bbox"])
        center = (rect.x0 + rect.x1) / 2
        group = next((g for g in reversed(groups)
                      if abs(g[0] - center) < 20 and -1 <= rect.y0 - g[1] <= 4), None)
        if group is None:
            group = [center, rect.y1, []]
            groups.append(group)
        elif group[2]:
            group[2][-1]["text"] = group[2][-1]["text"].rstrip() + " "
        group[1] = rect.y1
        group[2].extend(dict(s, text=s["text"].replace("\n", "")) for s in line["spans"])
    return box, [g[2] for g in groups]


def relative_url(target, current):
    path, _, anchor = target.partition("#")
    relative = Path(os.path.relpath(path, Path(current).parent)).as_posix()
    return quote(relative) + ("#" + anchor if anchor else "")


def inline_text(spans, targets, current, source, html=False):
    """Merge font runs and wrapped references before emitting Markdown."""
    runs = []
    for span in spans:
        text = translated(span)
        style = "bold" if "Bold" in span["font"] else "italic" if "Oblique" in span["font"] else ""
        if html and "Demi" in span["font"]:
            style = "bold"
        runs.append((text, style, span["color"] == REFERENCE_COLOR, span["color"] if html else None))
    output = []
    for (style, reference, color), group in groupby(runs, key=lambda r: r[1:]):
        text = "".join(r[0] for r in group)
        core = text.strip()
        if not core:
            output.append(text)
            continue
        if reference and any(c.isalpha() for c in core):
            # Keep surrounding punctuation outside the link and preserve the printed wording.
            match = re.fullmatch(r'([“"(]*)(.*?)([.,;:”)"!]*)', core)
            before, label, after = match.groups()
            name = RULE_ALIASES.get(label.casefold(), label.casefold())
            if name in targets:
                url = relative_url(str(targets[name]), current)
            elif name in EXTERNAL_RULES:
                url = relative_url(str(source) + f"#page={EXTERNAL_RULES[name]}", current)
            else:
                raise ValueError(f"Cannot resolve rule reference: {core!r}")
            formatted = (f'{escape(before)}<a href="{escape(url, quote=True)}">{escape(label)}</a>{escape(after)}'
                         if html else f"{before}[{label}]({url}){after}")
        elif style:
            marker = "**" if style == "bold" else "*"
            tag = "strong" if style == "bold" else "em"
            formatted = f"<{tag}>{escape(core)}</{tag}>" if html else marker + core + marker
        else:
            formatted = escape(core) if html else core
        if html and color != 0x231F20 and not reference:
            formatted = f'<span style="color: #{color:06x}">{formatted}</span>'
        output.append(text[:len(text) - len(text.lstrip())] + formatted + text[len(text.rstrip()):])
    return "".join(output).strip()


def appendix_events(page):
    """Read each calibrated panel independently, ignoring its border and original title."""
    number = page.number + 1
    lines = [line for block in page.get_text("dict", flags=TEXT_FLAGS)["blocks"]
             for line in block.get("lines", [])]
    events = []
    for panel, (title, bounds) in enumerate(APPENDIX_CARDS[number]):
        rect = pymupdf.Rect(bounds)
        heading = {"bbox": (rect.x0, rect.y0, rect.x1, rect.y0), "level": 2,
                   "spans": [{"text": title, "font": "EurostileLTStd-Bold", "size": 11,
                              "color": 0x231F20}]}
        events.append((number, panel, rect.y0, heading))
        figures = [(box, description, anchor) for box, description, anchor in FIGURES[number]
                   if rect.contains(pymupdf.Point((box[0] + box[2]) / 2, anchor))]
        for line in lines:
            box = pymupdf.Rect(line["bbox"])
            if not rect.contains((box.tl + box.br) / 2):
                continue
            if any(s["font"] == "EurostileLTStd-Bold" and s["size"] >= 9 for s in line["spans"]):
                continue
            if any(pymupdf.Rect(figure).contains((box.tl + box.br) / 2) for figure, _, _ in figures):
                continue
            spans = [dict(span, text=span["text"].replace("\n", "")) for span in line["spans"]]
            if not "".join(span["text"] for span in spans).strip():
                continue
            events.append((number, panel, box.y0, dict(line, spans=spans, level=0,
                           paragraph_start=("Bold" in spans[0]["font"]
                                            and spans[0]["text"].strip().endswith(":")))))
        for box, description, anchor in figures:
            artwork, captions = figure_content(page, box, description)
            events.append((number, panel, anchor, (artwork, description, captions)))
    return events


def extract_blocks(document):
    """Keep paragraphs and list items intact across page and column boundaries."""
    events = []
    found_stop = False
    for page in document:
        if page.number == 0:
            continue
        if STOP_SECTION in page.get_text().splitlines():
            found_stop = True
            break
        if page.number + 1 in APPENDIX_CARDS:
            events.extend(appendix_events(page))
            continue
        figures = FIGURES.get(page.number + 1, [])
        for block in page.get_text("dict", flags=TEXT_FLAGS)["blocks"]:
            for line in block.get("lines", []):
                rect = pymupdf.Rect(line["bbox"])
                if rect.x0 < 30 or rect.x0 > 590 or rect.y0 < 30 or rect.y0 > 759:
                    continue
                if not "".join(s["text"] for s in line["spans"]).strip():
                    continue
                if not body_line(line["spans"]) and any(pymupdf.Rect(box).contains((rect.tl + rect.br) / 2) for box, _, _ in figures):
                    continue
                events.append((page.number + 1, int(rect.x0 >= 306), rect.y0, line))
        for box, description, anchor in figures:
            # Crop margins can cross the gutter; use the center to identify the column.
            artwork, captions = figure_content(page, box, description)
            events.append((page.number + 1, int((box[0] + box[2]) / 2 >= 306), anchor,
                           (artwork, description, captions)))
    if not found_stop:
        raise ValueError(f"Missing conversion boundary: {STOP_SECTION}")
    events.sort(key=lambda e: e[:3])
    result, paragraph = [], None
    pending_figures = []
    numbered_list = False
    previous_stream, previous_bottom = None, 0
    for page, column, top, item in events:
        stream = page, column
        if isinstance(item, tuple):
            figure = Block("figure", page=page, figure=item)
            if paragraph:
                pending_figures.append(figure)
            else:
                result.append(figure)
            continue
        spans = [dict(s) for s in item["spans"]]
        text = "".join(s["text"] for s in spans)
        level = item.get("level", heading_level(spans))
        if level == 1 and text.strip() == STOP_SECTION:
            break
        bullet = None if page in APPENDIX_CARDS else re.match(r"^([•◊]|[a-z]\.|\d+\.)\s+", text)
        # Across pages/columns, a return to the body margin ends an indented list item.
        list_ended = (stream != previous_stream and paragraph and paragraph.prefix
                      and item["bbox"][0] <= (312 if column else 36) + 1)
        if paragraph and (level or bullet or list_ended or item.get("paragraph_start") or (stream == previous_stream and top - previous_bottom > (3 if page in APPENDIX_CARDS else 4))):
            result.append(paragraph)
            result.extend(pending_figures)
            pending_figures.clear()
            paragraph = None
        if level:
            numbered_list = False
            result.append(Block({1: "section", 2: "rule", 3: "subsection"}[level], spans, page))
        else:
            prefix = ""
            if bullet:
                marker = bullet[1]
                if marker[0].isdigit():
                    numbered_list = True
                prefix = "    - " if marker == "◊" else "- " if marker == "•" else (
                    f"    - **{marker}** " if marker[0].isalpha() else marker + " ")
                # Bullet markers in this source share the first text span.
                remaining = bullet.end()
                for span in spans:
                    amount = min(remaining, len(span["text"]))
                    span["text"] = span["text"][amount:]
                    remaining -= amount
                    if remaining == 0:
                        break
            elif paragraph is None:
                # Unmarked paragraphs at the substep margin still belong to the numbered step.
                numbered_list = numbered_list and item["bbox"][0] >= (312 if column else 36) + 12.5
                if numbered_list:
                    prefix = "    "
            if paragraph is None:
                paragraph = Block("paragraph", spans, page, prefix)
            else:
                last = paragraph.spans[-1]["text"].rstrip()
                paragraph.spans[-1]["text"] = last + ("" if last.endswith("-") else " ")
                paragraph.spans.extend(spans)
        previous_stream = stream
        previous_bottom = item["bbox"][3]
    if paragraph:
        result.append(paragraph)
    result.extend(pending_figures)
    return result


def organize(blocks, output, extension=".md"):
    sections, targets = [], {}
    section = rule = None
    for block in blocks:
        if block.kind == "section":
            section = {"title": block.text, "slug": slug(block.text), "intro": [], "rules": []}
            sections.append(section)
            rule = None
        elif block.kind == "rule":
            if section is None:
                raise ValueError("Rule encountered before a document section")
            name = title_key(block.text)
            path = output / section["slug"] / f"{section['slug']}-{slug(name)}{extension}"
            if isinstance(targets.get(name), Path) and section["title"] != APPENDIX_SECTION:
                raise ValueError(f"Duplicate rule: {name}")
            if section["title"] != APPENDIX_SECTION or name not in targets:
                targets[name] = path
            rule = {"title": block, "path": path, "blocks": []}
            if section["title"] == APPENDIX_SECTION:
                rule["group"] = ("Card Anatomies" if block.page == 29 and name in {"ship cards", "upgrade cards"}
                                 else APPENDIX_GROUPS[block.page])
            section["rules"].append(rule)
        else:
            if section is None:
                raise ValueError("Text encountered before a document section")
            (rule["blocks"] if rule else section["intro"]).append(block)
            if block.kind == "subsection" and rule:
                targets.setdefault(title_key(block.text), str(rule["path"]) + "#" + slug(title_key(block.text)))
    if [s["title"] for s in sections] != ["INTRODUCTION", "GLOSSARY", APPENDIX_SECTION]:
        raise ValueError("Expected Introduction, Glossary, and Appendix: Examples")
    targets["appendix"] = str(output / ("index" + extension)) + "#appendix-examples"
    targets["individual entries"] = targets["appendix"]
    return sections, targets


def render_blocks(blocks, targets, current, source, root, assets, html=False, image_sizes=None):
    rendered = []
    list_parent = False
    for index, block in enumerate(blocks):
        if block.kind == "figure":
            box, description, captions = block.figure
            name = f"page-{block.page:02d}-{slug(description)}.png"
            asset = root.parent / "markdown" / "assets" / name
            assets[asset] = block.page, box, description, captions
            linked_asset = root / "assets" / name
            url = relative_url(str(linked_asset), current)
            caption_text = [inline_text(spans, targets, current, source, html=html) for spans in captions]
            if html:
                caption = "".join(f"<p>{text}</p>" for text in caption_text)
                size = image_sizes[name] if image_sizes else None
                small = size is not None and max(size) < 155
                attributes = f' class="figure-right" style="--figure-width: {size[0]}px"' if small else ""
                figure = (f'<figure{attributes}><img src="{escape(url, quote=True)}" alt="{escape(description, quote=True)}">'
                          + (f'<figcaption>{caption}</figcaption>' if captions else "") + '</figure>')
                # Deferred side artwork must precede its paragraph for text to wrap around it.
                position = len(rendered)
                if small and index and blocks[index - 1].kind == "paragraph" and not blocks[index - 1].prefix:
                    position -= 1
                rendered.insert(position, figure)
            else:
                rendered.append("\n\n".join([f"![{description}]({url})", *(f"*{text}*" for text in caption_text)]))
        else:
            text = inline_text(block.spans, targets, current, source, html=html)
            if block.kind == "subsection":
                title = text if html else "".join(translated(s) for s in block.spans).strip()
                text = f'<a id="{slug(title_key(block.text))}"></a>\n\n## ' + title
            prefix = block.prefix
            if html:
                # Standalone lettered substeps have no parent list to supply Markdown indentation.
                if prefix.startswith("    ") and not list_parent:
                    prefix = prefix[4:]
                if not block.prefix.startswith("    "):
                    list_parent = bool(block.prefix)
            rendered.append(prefix + text)
    return "\n\n".join(rendered)


def html_document(text, title, current, root):
    body = markdown.markdown(text, extensions=["sane_lists"])
    # Keep subsection targets on headings rather than empty paragraphs that add spacing.
    body = re.sub(r'<p><a id="([^"]+)"></a></p>\s*<h2>', r'<h2 id="\1">', body)
    # Replace symbols only in text, never inside link destinations or attributes.
    parts = re.split(r'(<[^>]+>)', body)
    for i in range(0, len(parts), 2):
        parts[i] = re.sub(r'\[([a-z-]+)\]', html_icon, parts[i])
    stylesheet = relative_url(str(root / "style.css"), current)
    index = relative_url(str(root / "index.html"), current)
    manifest = relative_url(str(root / "manifest.webmanifest"), current)
    favicon = relative_url(str(root / "favicon.ico"), current)
    icon = relative_url(str(root / "icons/icon.svg"), current)
    touch_icon = relative_url(str(root / "icons/apple-touch-icon.png"), current)
    script = relative_url(str(root / "pwa.js"), current)
    return (f'<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<meta name="theme-color" content="#004761">\n'
            f'<link rel="manifest" href="{manifest}">\n'
            f'<link rel="icon" href="{favicon}" sizes="32x32">\n'
            f'<link rel="icon" href="{icon}" type="image/svg+xml">\n'
            f'<link rel="apple-touch-icon" href="{touch_icon}">\n'
            f'<script src="{script}" defer></script>\n'
            f'<title>{escape(title)}</title>\n<link rel="stylesheet" href="{stylesheet}">\n'
            f'</head>\n<body>\n<div class="page-content" tabindex="0" role="region" aria-label="Scrollable rules">\n'
            f'<nav aria-label="Rules navigation"><a href="{index}">Rules Reference</a></nav>\n'
            f'<main>{"".join(parts)}</main>\n'
            f'<footer>© &amp; ™ Lucasfilm Ltd. The AMG logo is a ® of Atomic Mass Games.</footer>\n'
            f'</div>\n</body>\n</html>\n')


ICON_ALIASES = {
    "critical-hit": "crit", "payload": "device", "configuration": "config",
    "force": "forcecharge", "linked-action": "linked", "rotate": "rotatearc",
    "stationary": "stop", "koiogran-turn": "kturn", "turret-arc": "singleturretarc",
    "segnors-loop-left": "sloopleft", "segnors-loop-right": "sloopright",
    "tallon-roll-left": "trollleft", "tallon-roll-right": "trollright",
}
WEB = Path(__file__).resolve().parent / "web"


def html_icon(match):
    name = match[1]
    # shortcut: upstream lacks these glyphs; retain labels until the font adds them.
    if f"[{name}]" not in SYMBOLS.values() or name in {"hyperdrive", "threat"}:
        return match[0]
    icon = ICON_ALIASES.get(name, name.replace("-", ""))
    return (f'<i class="xwing-miniatures-font xwing-miniatures-font-{icon}" '
            f'role="img" aria-label="{name}" title="{name}"></i>')


def extract_page_frame(document):
    """Render the page-sized background form without its footer or rule content."""
    with pymupdf.open() as artwork:
        artwork.insert_pdf(document, from_page=2, to_page=2)
        page = artwork[0]
        for xref, name, parent, bbox in page.get_xobjects():
            if parent != 0 or not pymupdf.Rect(bbox).contains(page.rect):
                continue
            background, marker, _ = artwork.xref_stream(xref).partition(b"EMC")
            if not marker or b"/Im0 Do" not in background or b"BT" in background:
                continue
            # The first artifact contains only the frame; the next form adds copyright text.
            artwork.update_stream(xref, background + marker)
            contents = page.get_contents()[0]
            artwork.update_stream(contents, f"q /GS0 gs /{name} Do Q".encode("ascii"))
            page.set_contents(contents)
            # insert_pdf omits the source page's CMYK transparency group.
            artwork.xref_set_key(page.xref, "Group", "<</CS /DeviceCMYK /S /Transparency /Type /Group>>")
            return page.get_pixmap(matrix=pymupdf.Matrix(3, 3)).tobytes("png")
    raise ValueError("Missing full-page margin artwork on physical page 3")


def convert(source, output):
    source, output = Path(source), Path(output)
    if output.suffix.lower() == ".md":
        raise ValueError("Output must be a directory; use -o output")
    with pymupdf.open(source) as document:
        if len(document) != 49 or document[1].rect != pymupdf.Rect(0, 0, 612, 792):
            raise ValueError("Expected the 49-page US Letter Rules Reference v1.4.6-1 PDF")
        blocks = extract_blocks(document)
        files, assets, illustrations, image_sizes = {}, {}, {}, {}
        for format, extension in (("markdown", ".md"), ("docs", ".html")):
            root = output / format
            html = extension == ".html"
            linked_source = root / source.name
            sections, targets = organize(blocks, root, extension)
            index = root / ("index" + extension)
            toc = ["# Rules Reference v1.4.6-1"]
            for section in sections:
                if section["title"] == APPENDIX_SECTION:
                    toc.append('<a id="appendix-examples"></a>')
                toc.append("## " + ("Appendix" if section["title"] == APPENDIX_SECTION else section["title"].title()))
                intro = render_blocks(section["intro"], targets, index, linked_source, root, assets, html=html, image_sizes=image_sizes)
                if intro:
                    toc.append(intro)
                links = []
                previous_group = None
                for rule in section["rules"]:
                    group = rule.get("group")
                    if group != previous_group:
                        if links:
                            toc.append("\n".join(links))
                            links = []
                        toc.append("### " + group)
                        previous_group = group
                    title = "".join(translated(s) for s in rule["title"].spans).strip()
                    heading = inline_text(rule["title"].spans, targets, rule["path"], linked_source, html=True) if html else title
                    text = "# " + heading + "\n\n" + render_blocks(rule["blocks"], targets, rule["path"], linked_source, root, assets, html=html, image_sizes=image_sizes) + "\n"
                    files[rule["path"]] = html_document(text, title, rule["path"], root) if html else text
                    links.append(f"- [{escape(title) if html else title}]({relative_url(str(rule['path']), index)})")
                toc.append("\n".join(links))
            text = "\n\n".join(toc) + "\n"
            files[index] = html_document(text, "Rules Reference v1.4.6-1", index, root) if html else text
            if not html:
                # Render only after text validation, so unmapped symbols cannot replace a good output.
                # Render after Markdown text validation, before HTML needs trimmed PNG dimensions.
                for asset, (page, box, description, captions) in assets.items():
                    data = render_figure(document, page, FIGURE_GROUPS[page, description], box,
                                         [s["bbox"] for spans in captions for s in spans],
                                         unmarked=(page == 24))
                    illustrations[asset] = data
                    image = pymupdf.Pixmap(data)
                    image_sizes[asset.name] = image.width, image.height
        # Read web resources before replacing any generated content.
        web_assets = {p.relative_to(WEB): p.read_bytes() for p in WEB.rglob("*") if p.is_file()}
        web_assets[Path("assets/page-frame.png")] = extract_page_frame(document)
        web_assets[Path(source.name)] = source.read_bytes()
        for asset, data in illustrations.items():
            web_assets[Path("assets") / asset.name] = data
        # Version the offline bundle by content so each deployment installs atomically.
        offline = {p.relative_to(output / "docs").as_posix(): text.encode("utf-8")
                   for p, text in files.items() if p.suffix == ".html"}
        offline.update({p.as_posix(): data for p, data in web_assets.items()
                        if p.suffix != ".pdf" and p.name != "sw.js"})
        digest = hashlib.sha256()
        for name, data in sorted(offline.items()):
            digest.update(name.encode("utf-8") + b"\0" + data)
        digest.update(web_assets[Path("sw.js")])
        worker = web_assets[Path("sw.js")].decode("utf-8")
        worker = worker.replace("__VERSION__", digest.hexdigest()[:16])
        worker = worker.replace("__PRECACHE__", json.dumps(sorted(offline)))
        web_assets[Path("sw.js")] = worker.encode("utf-8")
        for path, text in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        for asset, data in illustrations.items():
            asset.parent.mkdir(parents=True, exist_ok=True)
            asset.write_bytes(data)
        for relative, data in web_assets.items():
            path = output / "docs" / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        (output / "markdown" / source.name).write_bytes(web_assets[Path(source.name)])
    return output / "markdown" / "index.md"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", type=Path, default=SOURCE)
    parser.add_argument("-o", "--output", type=Path, default=Path("."), help="parent directory for docs/ and markdown/ (default: current directory)")
    args = parser.parse_args()
    try:
        result = convert(args.source, args.output)
    except (OSError, ValueError, pymupdf.FileDataError) as error:
        parser.exit(1, f"Conversion failed: {error}\n")
    print(f"Converted Introduction, Glossary, and Appendix: Examples: {result} and {args.output / 'docs' / 'index.html'}")


if __name__ == "__main__":
    main()
