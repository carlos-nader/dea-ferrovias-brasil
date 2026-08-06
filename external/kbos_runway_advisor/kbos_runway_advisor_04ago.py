"""
KBOS Runway Advisor - a decision-support tool for Boston Logan International
Airport (KBOS) runway configuration, built for flight-sim / virtual ATC use
(e.g. Tower!Simulator 3, IVAO, VATSIM).

STATUS: BETA - RULE SET v2 + LOCKED DESIGN DECISIONS
-------------------------------------------------------------------
Full rewrite (the earlier draft was discarded rather than patched). Single
source of truth for every rule: KBOS_achados.md in this folder, including the
"Atualizacao de 28/07/2026 (rodada da noite)" section with the original locked
design decisions, plus the 2026-07-31 revisions recorded in ACHADO 12/14 and
the Q4 resolution. The rule set was v0 when this engine was first written; it
is v2 as of the published rules PDF (KBOS_Runway_Advisor_Rules_v2.pdf).
Decisions:

  1. WINDSHEAR REMOVED as an input. Windshear does not appear in a routine
     METAR (its real-world source is LLWAS/PIREP), so a player reading the
     sim's METAR could never fill it honestly. Only THUNDERSTORM (METAR
     present-weather group TS/TSRA) + braking action worse than "good"
     trigger the Step 0 safety override. This makes Step 0 narrower than the
     real FAA Order 8400.9 (which also covers windshear) - documented as an
     APP SIMPLIFICATION, not hidden.
  2. ALWAYS-ON RESTRICTIONS are informational only. They are printed in
     EVERY output, in every scenario, color-coded by restriction TYPE
     (noise/time, physical & legal, aircraft class, procedure), and they
     never add/remove runways from the configuration computed by Steps 0-3.
  3. EXIT-FIX / ROUTE-DIRECTION RULE REMOVED (former Step 4b). It was the
     only purely sim-sourced rule that actually decided a runway, and the
     game's strips only show the destination airport - the player would have
     to infer the departure direction geographically. With its removal, no
     purely SIM-ONLY rule decides anything in this engine.
  4. NW flow keeps ALL its arrival runways in every weather category.
     REVISED AGAIN 2026-08-02 - the arrival set was ["27","32"], taken from
     the FAA Capacity Profile, while the departures on the same line already
     came from Massport/the SOP: two sources mixed with no criterion. Massport
     publishes "Arrivals to R 33L, 33R (limited), 32 and 27" (CAC "Logan 101"
     p.16, CY2016 runway use). The sources do not conflict - the Capacity
     Profile models one representative configuration per weather category for
     throughput analysis, Massport reports what actually flew. Runway 33L is
     the one that mattered: 10,083 ft with an ILS CAT III, and the only
     arrival runway aligned with a 330-350 deg wind, where 27 takes 21-24 kt
     of crosswind. Which of the four actually works arrivals shifts with
     traffic through the day, and traffic volume can never be an app input -
     so the app lists the package and leaves the choice to the player.
     REVISED 2026-07-31 - the earlier build dropped 32 below Visual as a
     GUESS extrapolated from the North Flow pattern. That rule was both
     unsourced and too blunt: what actually governs is 14 CFR 91.175 (a
     pilot may not descend below the published minimum for the approach in
     use) applied to each runway's own published minima - runway 27 stays
     legal down to 443 ft / 1.5 SM, runway 32 only down to 801 ft / 1.0 SM.
     So there is a real band (443-801 ft) where 27 works and 32 does not,
     and the whole "Marginal" category (>= 1,000 ft) sits above BOTH. The
     app now leaves the configuration alone and lets the minima-caution
     mechanism it already has (RUNWAY_MINIMA_GENERAL / _minima_ok) flag the
     runway that no longer clears - one mechanism instead of two, and it
     reports the actual limiting number instead of a category guess.
  5. GAME AIRCRAFT CATEGORIES (P/T/B/R/N/W/C) are used ONLY where a source
     supports that granularity - runways 32 and 15L/33R. Everywhere else the
     app stays with the two-line jet / turboprop-light split, because the
     underlying sources (dBA limits, turbojet SID minimums) never subdivide
     further and inventing a split would be unsourced. See ACHADO 14 in
     KBOS_achados.md for the per-restriction audit behind this scope.
  6. NIGHT HEAD-TO-HEAD WINDOW IS 00:00-05:00, and the branch checks BOTH
     wind components. REVISED 2026-08-01 (open question 1 research). The
     window used to be 00:00-06:00, taken from the Boeing noise database.
     Massport's own Fly Quiet Report (2017) tracks this configuration under
     the heading "Runway 33L Arrivals Midnight to 5AM" - that is a metric the
     airport counts and compares quarter over quarter, not a rounded phrase
     in a slide, so it outranks Boeing's "12am-6am" and the sim SOP's
     "2300-0630". Boeing's own wording ("WHEN POSSIBLE runway 15R/33L used in
     head on operations") confirms the config is a preference, never a
     schedule: in reality the switch tracks traffic volume, which no player
     can read off a METAR, so the app arbitrates a fixed window and says so.
     Separately, this branch used to test only the tailwind on runway 33 and
     ignore crosswind - which let a noise PREFERENCE outrank a safety limit,
     inverting the hierarchy Step 0 already encodes. It now tests both
     against the same FAA Order 8400.9 caps used everywhere else.
  7. THE 8400.9 WIND LIMITS ARE CHECKED PER RUNWAY, over the whole active
     configuration, and never change it (added 2026-08-02). The old check ran
     on the flow's primary arrival runway alone and printed one generic
     caution, which was blind to the rest of the package - SW and NW are
     heterogeneous, so the primary does not represent them. The app does NOT
     reassign the flow when a runway is over: that was tested across all 360
     wind directions at 20/25/30/35 kt, dry and slippery, and there is not one
     case where the active package fails and another package works. The
     better-aligned runway is normally already inside the active package.
  8. VISIBILITY BELOW 1 SM DISQUALIFIES THE NIGHT HEAD-TO-HEAD (added
     2026-08-02). Order 8400.9 par. 7b: a runway use program may not govern
     the landing runway below one statute mile. The head-to-head is a pure
     noise preference, so it is exactly what that criterion bites. It is NOT
     wired into the Step 0 override, where a sub-1-SM day needs an ILS runway
     and the best-headwind scan would answer runway 9, which has no approach.

The weather category (Visual / Marginal / Instrument) is never an input: the
player types raw ceiling and visibility straight from the METAR and the
engine derives the category from the official BOS thresholds.

SOURCES AND DISCLAIMER
-----------------------
Unlike the LSZH Runway Advisor (100% based on a simulation training manual),
most of this rule set traces to official/regulatory sources:
  - FAA Airport Capacity Profile, Boston Logan, 2019 - weather categories
    and the runway configuration used in each.
  - FAA Order 8400.9 (1981, still in force, never updated) - wind limits for
    noise-based Runway Use Programs; safety-over-noise hierarchy.
  - FAA JO 7110.65 par. 3-5-1 / AIM 4-3-6 - calm-wind rule (< 5 kt).
  - FAA Chart Supplement remarks + SID charts - one-way runway 14/32,
    jet-eligible departure runways, 15R/33L noise preference, 210-kt rule.
  - FAA IAP index + airport data sheet - ILS category and approach type per
    runway (4R/33L CAT II-III; 15R/22L/27 CAT I; 32/4L RNAV only), runway
    lengths and magnetic headings (confirmed across 3 independent sources).
  - 740 CMR 24.00 (Massachusetts state regulation, in force) - the 4L/22R
    rule at first hand: 24.05 sets the 73/78 dBA caps AND the 23:00-06:00
    prohibition, 24.99 the escalating fines ($50-100 / $150-250 / $300-500).
    Verified 2026-08-01 against the regulation text; the Boeing database had
    been carrying this rule for us as an industry mirror of it.
  - Boeing Airport Noise Regulations database (~2011 data) - corroborates the
    4L/22R rule above; sole source for the "when possible" wording that marks
    the night head-to-head config as a preference rather than a schedule.
  - Massport CAC presentations (2016/2017/2018) - flow names and pairings.
  - Massport Fly Quiet Report (2017) - the head-to-head window, taken from
    the airport's own tracking metric "Runway 33L Arrivals Midnight to 5AM".
  - vZBW SOP (VATSIM Boston ARTCC, 2014) - simulation reference; after the
    2026-07-28 decisions, no purely sim-only rule decides anything here (its
    10-kt night tailwind figure survives only as a divergence note).
This tool is a simulation aid inspired by real-world procedures. It is NOT a
real FAA/Massport operational reference and must not be used for actual
aviation. Scope: all runways/navaids available, normal demand, no closures.

DESIGN, IN ONE PARAGRAPH
--------------------------
A single set of inputs (local time, wind direction/speed/gust, ceiling,
visibility, runway condition, braking action, thunderstorm) decides the
active configuration - one run per METAR/hour change, not per aircraft.
Aircraft type is NOT an input (same philosophy as the LSZH Runway Advisor):
since it never changes which runways are active, the output always shows a
dedicated RUNWAY ELIGIBILITY section with BOTH lines - what jets may use and
what turboprops/light aircraft may use, adjusted to the active configuration
and time of day - and the controller applies the right line per strip. Every
statement carries a confidence tag; the always-on restrictions are
additionally color-coded by restriction type.
"""

import math
import os
import re
import sys
import tkinter as tk
from tkinter import ttk, font as tkfont

APP_TITLE = "KBOS Runway Advisor"
APP_VERSION = "1.0-beta"

# ---------------------------------------------------------------------------
# Confidence tags (render tags double as tkinter Text tag names).
# A [GUESS] tag existed here until 2026-07-31 and was emitted by exactly one
# rule (NW flow below Visual). That rule is gone - 14 CFR 91.175 plus the
# published minima answer it properly now - so the tag went with it rather
# than staying in the legend with nothing to point at. Rule of this project:
# every tag in a legend must appear somewhere in the content.
# ---------------------------------------------------------------------------
OFFICIAL = "[OFFICIAL]"
CORROBORATED = "[CORROBORATED]"
SIM_ONLY = "[SIM-ONLY]"
# RENAMED 2026-08-06, user decision: was "[APP SIMPLIFICATION]" - not every
# entry tagged this way is a simplification of something complex, several are
# just a design choice with no source either way (e.g. the calm test reading
# the gust). Identifier kept as SIMPLIFICATION/tag key "simplification" on
# purpose - internal names, not shown to the player, not worth the churn of
# renaming for their own sake.
SIMPLIFICATION = "[APP DESIGN]"

# ---------------------------------------------------------------------------
# Runway magnetic headings (degrees). Confirmed by 3 independent sources
# (FAA data sheet, AirNav/Globalair aggregation); a 4th table offset by
# exactly -30 deg on every runway was discarded as anomalous - see
# KBOS_achados.md. Parallel runways share their strip's heading.
# ---------------------------------------------------------------------------
RUNWAY_HEADING = {
    4: 35, 22: 215,
    9: 92, 27: 272,
    14: 140, 32: 320,
    15: 150, 33: 330,
}

# One heading per physical direction, used by the best-headwind scan (_fill_role,
# shared by the Step 0 safety override and the par. 7d role fill).
#
# ALL EIGHT SINCE 2026-08-05. Headings 14 and 32 used to be left out entirely,
# on a comment reading "one-way + light-aircraft-only, never a best-headwind pick
# for general traffic". Half of that was already contradicted by this same file:
# ALWAYS_ON records runway 32 taking P/T/B/R on landing ([CORROBORATED] - regional
# jets do land there) and runway 14 taking P/T/B on takeoff, so "light aircraft
# only" was left over from before that research and never revisited. The
# consequence was narrow but real, and it is the mirror image of the runway 9
# defect fixed the day before: there an undocumented runway could WIN the scan,
# here two documented ones could never enter it, so a wind straight down 320 deg
# had the scan answer with something further off the nose than runway 32.
#
# The one-way half of that comment IS true and is enforced, one line below,
# where it belongs - as a per-role restriction with a source, not as silent
# absence from a list.
#
# The same comment also claimed 15L/33R were excluded "for the same reason".
# They never were: headings 15 and 33 carry them (see HEADING_TO_RWYS), and the
# rules PDF has always described it correctly - "heading 15/33 also covers the
# short 15L/33R, the aircraft-type filter at Step 4, not this scan, is what keeps
# jets off". Only the comment was wrong.
OVERRIDE_CANDIDATES = [4, 22, 9, 27, 14, 32, 15, 33]

# Heading -> physical runways, for expanding a best-headwind pick into the
# eligibility filters below.
HEADING_TO_RWYS = {
    4: ["4L", "4R"], 22: ["22L", "22R"],
    9: ["9"], 27: ["27"],
    14: ["14"], 32: ["32"],
    15: ["15R", "15L"], 33: ["33L", "33R"],
}

# Runways a court order allows in ONE role only - the 14/32 strip is one-way,
# over water. Same fact ALWAYS_ON prints to the player ("Runway 14/32 one-way:
# 14 = takeoff only, 32 = landing only", [OFFICIAL]), kept here in the form the
# scan can act on.
#
# This is why the two headings above can be candidates at all. Without it the
# scan would offer runway 32 for departures, which no filter would catch: a
# departure needs no approach and no flow membership, so nothing else in
# _fill_role has any reason to stop it. Runway 14 in the arrival role WOULD be
# caught, by DOCUMENTED_ARRIVAL_RWYS - but for the wrong reason ("no flow lands
# there") when the real one is stronger and older ("landing there is prohibited").
# A restriction with a source beats an accident of another filter.
RUNWAY_ONLY_ROLE = {"14": "dep", "32": "arr"}

# Runways that may JOIN an answer but never BE one (user's rule, 2026-08-05:
# "nunca pode ser a unica pista no result, mas deve constar do result").
#
# Measured, not assumed. Adding headings 14 and 32 to the scan without this made
# them win outright inside a ~29-degree band each, and winning means replacing:
# a 320-degree wind turned "arrivals 33L, 33R" into "arrivals 32" alone - the
# 10,083 ft ILS CAT III runway swapped for a 5,000 x 100 ft RNAV-only one to buy
# 10 degrees of alignment, on 576 input combinations. Runway 14 did the same to
# 15R/15L for departures. That is the runway 9 mistake wearing different clothes:
# alignment arithmetic beating what the airport can actually operate.
#
# Neither runway can serve KBOS by itself, and the file already says why - the
# game-category rows in ALWAYS_ON: runway 32 landing is P/T/B/R (no N/W/C, so no
# mainline jet), runway 14 takeoff is P/T/B with R varying. An airport whose
# traffic is mostly mainline jets cannot run on either alone, however well
# aligned. So they are held back and appended to the first heading that CAN
# stand alone - which for arrivals lands inside Massport's own Northwest package
# (32 joins 33L/33R, or 27, all four of which that package lists together).
NEVER_ALONE_RWYS = {"14", "32"}

# ---------------------------------------------------------------------------
# Runway length in feet (added 2026-08-03 for the per-runway table). Source:
# the FAA detailed runway record plus an aggregator cross-check, both listed
# in KBOS_achados.md. Opposite ends of one physical strip share a length, as
# they must (4L/22R, 4R/22L, 9/27, 14/32, 15L/33R, 15R/33L).
#
# Until this constant existed the same numbers were re-typed inside display
# strings in several places, which is exactly the kind of duplication that
# lets a document and the code drift apart.
# ---------------------------------------------------------------------------
RUNWAY_LENGTH = {
    "4L": 7864, "22R": 7864,
    "4R": 10006, "22L": 10006,
    "9": 7001, "27": 7001,
    "14": 5000, "32": 5000,
    "15L": 2557, "33R": 2557,
    "15R": 10083, "33L": 10083,
}


def _length_ft(rwy):
    """'10,083' for the table/display - never a bare int, so a caller cannot
    accidentally print an unformatted number next to formatted ones."""
    return f"{RUNWAY_LENGTH[rwy]:,}"


# ---------------------------------------------------------------------------
# Published approach type per runway (added 2026-08-03 for the table). This is
# the SHORT display label, not the minima - the numbers live in
# RUNWAY_MINIMA_GENERAL below and are reported by the minima caution, which
# only speaks up when the weather actually approaches a limit.
#
# Two display rules, decided 2026-08-03 (KBOS_achados.md, Pendencia 0 par. 7):
#   - every RNAV variant (LPV, LNAV, LNAV/VNAV, RNP) collapses to plain
#     "RNAV" - the sub-type never changes what the player does;
#   - where a runway has more than one ILS tier on file, only the MOST
#     PRECISE one is shown (4R and 33L have CAT I and CAT II/III published;
#     CAT III is what is named).
# Runways with no published instrument approach at all map to None and render
# as "-" (they are also the VISUAL_ONLY_RWYS set below).
# ---------------------------------------------------------------------------
RUNWAY_APPROACH_TYPE = {
    "4R": "ILS CAT III, RNAV",
    "33L": "ILS CAT III, RNAV",
    "15R": "ILS CAT I, RNAV",
    "22L": "ILS CAT I, RNAV",
    "27": "ILS CAT I, RNAV",
    "4L": "RNAV",
    "32": "RNAV",
    "9": None,
    "14": None,
    "22R": None,
    "15L": None,
    "33R": None,
}

# ---------------------------------------------------------------------------
# Eligibility filters (locked design 2026-07-28 - see KBOS_achados.md).
# TWO DIFFERENT jet filters, each with its own source - never reuse one for
# the other:
#   - departures: positive list from the RNAV turbojet SID takeoff minimums
#     ("NA-ATC" on 4L/14/15L/32/33R). NOTE: the conventional LOGAN FOUR SID
#     (radar vectors, non-RNAV) DOES publish jet headings for 4L/R and 14 -
#     the exclusion of 4L rests independently on the 73 dBA takeoff cap
#     (740 CMR 24.05), which binds regardless of which SID is flown.
#   - arrivals: exclusions - 14 (no landings at all, one-way), 32 and
#     15L/33R (see below), 22R (non-jet, 78 dBA - 740 CMR 24.05).
# CORRECTED 2026-07-31 (ACHADO 12/14): runway 32 was listed here as "light
# aircraft only, court order". The court order is real but it restricts
# DIRECTION (14/32 is one-way, over water only), never aircraft category -
# that half was added at some point without a source. Runway 32 stays out of
# JET_ARRIVAL_RWYS anyway, but for a PHYSICAL reason: 5,000 ft long and only
# 100 ft wide, no ILS, so the airport's own traffic data shows it as
# "wind restricted" and a KBOS controller describes it as "most jets refuse
# to use it... only e170/190s use it to land". Regional jets do land there;
# narrow/wide bodies effectively do not. Same story for 15L/33R, where
# 2,557 ft rules out R/N/W outright on landing-distance alone. Both runways
# carry a game-category breakdown in ALWAYS_ON rather than a false
# "light aircraft only" label.
# Prop arrival bonus per flow: only what Massport CAC documents (slide 10:
# "R22R Dep (& nonjet Arr)" in the SW flow). No documented bonus for the
# other flows - none is invented.
# ---------------------------------------------------------------------------
JET_DEPARTURE_RWYS = {"4R", "9", "15R", "22L", "22R", "27", "33L"}
JET_ARRIVAL_RWYS = {"4L", "4R", "9", "15R", "22L", "27", "33L"}
PROP_ARRIVAL_BONUS = {"SW": ["22R"]}

# Runway preference within an equally-eligible pair, added 2026-08-05 (SS28.1
# of the 05/08 exploratory simulation against Fly Quiet Report Q1 2019, Table
# 4-1, page 47). NOT a defect this engine ever claimed to fix - the app only
# decides which runways are ELIGIBLE, never which one a controller (in the
# game, the player) picks between two equally valid options. Purely
# informational, keyed by flow_key, shown whenever that flow is active -
# unlike the prop-bonus/category-split footnotes above, NOT filtered by
# which of the pair's two runways survived the wind/night/minima filters this
# instant, so the text can outlive one runway of the pair being temporarily
# unusable.
# WORDING STANDARDIZED 2026-08-06, user decision: every entry now opens with
# its role ("Arrivals:"/"Departures:"), states the split in one or two short
# sentences depending on whether jet/non-jet AGREE or DISAGREE on which
# runway to favor, and closes with a bare "Source: Fly Quiet Report Q1 2019."
# - all percentages still direct quotes from Table 4-1, only the surrounding
# prose was condensed (was 3 different shapes of sentence for 5 entries).
RUNWAY_PREF_NOTES = {
    "SW": [
        "Departures: jet and non-jet alike favor 22R over 22L (27.2% vs "
        "1.7% jet; 28.9% vs 0.1% non-jet). Source: Fly Quiet Report Q1 "
        "2019.",
    ],
    "NE": [
        "Arrivals: jets rarely land on 4L, favoring 4R (2.2% vs 20.4%). "
        "Non-jet arrivals lean the other way, slightly favoring 4L over "
        "4R (15.4% vs 8.9%). Source: Fly Quiet Report Q1 2019.",
        "Departures: jet and non-jet alike favor runway 9 over 4R (19.6% "
        "vs 2.8% jet; 9.5% vs 2.7% non-jet). Source: Fly Quiet Report Q1 "
        "2019.",
    ],
    "NW": [
        "Arrivals: jets favor 27 over 33L (29.7% vs 18.6%). Non-jet "
        "arrivals favor 33L instead (12.5% vs 6.9%). Source: Fly Quiet "
        "Report Q1 2019.",
        "Departures: jet and non-jet alike favor 33L over 27 (28.8% vs "
        "16.4% jet; 35.8% vs 7.1% non-jet). Source: Fly Quiet Report Q1 "
        "2019.",
    ],
}

# LAHSO jet exclusion, added 2026-08-02 (Pendencia 14). Runway 27 IS jet-capable
# in general (7,001 ft, ILS CAT I) and rightly sits in JET_ARRIVAL_RWYS - in the
# NW flow it takes jet arrivals with no restriction at all. But that set is
# global and static, so it cannot express "jet-capable here, turboprop-only when
# paired with THAT runway": in SW/Visual the 22L+27 dual arrival runs on LAHSO,
# and the FAA Capacity Profile records only turboprops landing 27 holding short
# of 22L - the available landing distance to the hold-short point (5,650 ft) is
# what binds, not the runway. Keyed on (flow, weather) because SW/Marginal uses
# the SAME pair with NO hold-short point (radar-spaced 2.5 NM instrument
# approaches, each aircraft using the full runway), so jets are fine there.
# Deliberately a one-entry exception, not a general (flow, weather) mechanism:
# every other config was checked for the same class of defect and none has it.
LAHSO_JET_EXCLUSION = {("SW", "Visual"): ["27"]}

# ---------------------------------------------------------------------------
# Why a runway is closed to jets - the short tag for the table's Reason column
# (added 2026-08-03). Deliberately 2-3 words: the full reasoning stays in
# ALWAYS_ON, which the table points to rather than duplicates.
#
# One entry per runway is enough because no runway is excluded for different
# reasons in its two roles: 4L is only ever restricted on DEPARTURE (73 dBA
# takeoff cap) and 22R only on ARRIVAL (78 dBA landing cap), so there is no
# case where the same runway needs two different tags.
# ---------------------------------------------------------------------------
RESTRICTION_REASON = {
    "4L": "noise",
    "22R": "noise",
    "14": "runway size",
    "32": "runway size",
    "15L": "runway size",
    "33R": "runway size",
}
LAHSO_REASON = "LAHSO"

# ---------------------------------------------------------------------------
# Game aircraft categories (P/T/B/R/N/W/C) per runway, for the table's
# "Game Category" column. Applied ONLY where a source supports that
# granularity - four runways today; everything else renders "-" rather than an
# invented breakdown.
#
# Letters: P Prop, T TurboProp, B Business, R Regional jet, N Narrow body,
# W Wide body, C Cargo (Tower!Simulator 3 Start Guide). No legend is printed
# in the app: the categories are the sim's own, players read them off its UI.
#
# Cargo always follows N/W (confirmed 2026-08-03: the game only ever shows
# large jets as Cargo), which is why no entry leaves C as "varies".
#
# These are permanent facts of the runway IN A GIVEN ROLE - true whenever it
# appears in that role, in any flow. The runway 27 case is NOT permanent and
# lives in the separate table below.
# ---------------------------------------------------------------------------
# Split by ROLE since 2026-08-03 (Pendencia 15). Runways 32 and 14 are one-way
# by court order, so each has exactly one role and cannot disagree with itself.
# 15L/33R is the one strip that runs BOTH ways in a single configuration (the
# heading 15/33 safety overrides), and its two roles genuinely differ - which
# is the whole defect Pendencia 15 records: the table used to print the landing
# breakdown while the row also claimed a departure role.
#
# Letters re-derived 2026-08-03 from the sim's own data rather than real-world
# reference aircraft: Airplanes\NyergesDesign\<ICAO>\<ICAO>.csv (category +
# landing/takeoff length in feet) intersected with the aircraft types that
# actually appear in Airports\KBOS\databases\<pack>\schedule.csv. Only the
# active traffic pack counts (NyergesDesign), and only aircraft that really fly
# to KBOS - the generic 149-aircraft catalogue produced ghost exceptions from
# types that never appear here. "yes"/"no" mean the WHOLE category; any
# exception at all, however small, becomes "varies".
GAME_CATEGORY_ARR = {
    # Landing 32: regional jets do land there (KBOS controller testimony);
    # the KBOS schedule only ever flies E145/E170/E175 as regional jets and all
    # three clear 5,000 ft, so R stays a clean "yes". CORROBORATED.
    "32": "P T B R yes / N W C no",
    # Landing 15L/33R: 2,557 ft. R/N/W ruled out on landing distance alone;
    # T and B split inside the category (King Air fits, Dash 8 does not).
    "15L": "P yes / T B varies / R N W C no",
    "33R": "P yes / T B varies / R N W C no",
}

GAME_CATEGORY_DEP = {
    # Takeoff 14: same 5,000 ft strip as 32, but departing needs more runway
    # than landing. R is no longer a flat "no": the E170/E175 do clear 5,000 ft
    # on departure, only the E145 does not - one exception is enough to make
    # the whole letter "varies".
    "14": "P T B yes / R varies / N W C no",
    # Takeoff 15L/33R: 2,557 ft. B drops to a flat "no" here even though two
    # business jets can LAND on it - none of the ones that fly to KBOS can
    # depart from it. T stays "varies" but on a different set than landing.
    "15L": "P yes / T varies / B R N W C no",
    "33R": "P yes / T varies / B R N W C no",
}

# What the Game Category cell says when the runway's two roles disagree. The
# breakdown itself goes under the table, never in the cell: a cell that carried
# one role's answer would be wrong at a glance for the other role, and printing
# it there AND in the note would duplicate content rather than add any.
CATEGORY_SPLIT_CELL = "see note *"

# Runway 27 under LAHSO only (SW/Visual). Keyed exactly like
# LAHSO_JET_EXCLUSION because it is the same one-configuration exception: in
# the NW flow the same runway is a full jet runway with no category limit at
# all, so this can never join GAME_CATEGORY_ARR above without lying about NW.
# Arrival-side only: the restriction is about landing behind a hold-short line.
LAHSO_GAME_CATEGORY = {("SW", "Visual"): {"27": "P T yes / B R N W C no"}}

# Category breakdown for the 22R non-jet arrival bonus (PROP_ARRIVAL_BONUS
# below), added 2026-08-05. NOT derived the same way as LAHSO_GAME_CATEGORY
# above - that one comes from FAA LAHSO documentation naming categories
# directly; this one is a straight reading of Massport's own label for the
# bonus ("R22R Dep (& nonjet Arr)", Logan 101 CAC presentation): P and T are
# the definitionally non-jet categories in the game's own P/T/B/R/N/W/C
# scheme, B/R/N/W/C are all jet by definition, and 22R's 7,864 ft rules out
# any length-based exception among P/T (unlike 14 or 15L/33R, both under
# 5,000 ft). CORROBORATED twice independently: Logan 101 (Massport CAC,
# Aug 2016 radar data) shows "22R, 0.0%" of jet arrivals; the Fly Quiet
# Report Q1 2019 (fqr_combined_2020.pdf) does not list 22R among the top 4
# jet-arrival runways and 22R never appears with a nonzero jet-arrival share.
PROP_BONUS_GAME_CATEGORY = {"22R": "P T yes / B R N W C no"}

# ---------------------------------------------------------------------------
# Published approach minima per runway (added 2026-07-28, from 19 IAP charts
# read one at a time by the user - see KBOS_achados.md for the full source
# list and the reasoning for the "general vs special-certification" split).
#
# Each entry is either one (height_ft, visibility_sm) pair, or a LIST of
# pairs when two approaches at the same runway are both non-dominated (ex.:
# runway 27 - ILS wins on height, RNAV LNAV/VNAV wins on visibility; mixing
# the best of each would invent a combination no real approach offers).
# Only the "general" (no special certification) tier is used for the
# automated check below - CAT III/RNP-AR entries use RVR, which does not
# convert reliably to statute miles at that range and the app has no RVR
# input, so they are shown as an informational note only, never compared
# numerically.
# ---------------------------------------------------------------------------
RUNWAY_MINIMA_GENERAL = {
    "4R": (200, 0.5),
    "15R": (200, 0.5),
    "22L": (200, 0.75),
    "27": [(443, 1.5), (493, 1.375)],
    "33L": (200, 0.5),
    "4L": (304, 0.875),
    "32": (801, 1.0),
}
RUNWAY_SPECIAL_CERT_NOTE = {
    "4R": "ILS CAT III on file (RVR 600 ft, no stated DA) - special aircrew/aircraft "
          "certification required; not compared numerically (no RVR input in this app).",
    "33L": "ILS CAT III on file (RVR 600 ft, no stated DA) - special aircrew/aircraft "
           "certification required; not compared numerically (no RVR input in this app).",
}
# Runways with NO published instrument approach at all (confirmed against the
# FAA IAP index) - these need VMC, full stop; no chart minimum to compare.
#
# DERIVED since 2026-08-04 (2nd round), previously the hand-written literal
# {"9", "14", "22R", "15L", "33R"}. It is the same fact RUNWAY_APPROACH_TYPE
# already states as None - "no approach to name" and "no approach to fly" cannot
# be true of different runways - so keeping both by hand meant one could be
# edited without the other and nothing would say so. Same reasoning that made the
# flow runway sets the single source of truth for the display strings.
VISUAL_ONLY_RWYS = {r for r, kind in RUNWAY_APPROACH_TYPE.items() if kind is None}


def _minima_ok(rwy, ceiling_ft, visibility_mi):
    """True if the given conditions clear at least one published minimum for
    this runway (or the runway has no minima on file to check). None
    ceiling/visibility means "not a factor" - treated as best case, same
    convention as weather_category()."""
    candidates = RUNWAY_MINIMA_GENERAL.get(rwy)
    if candidates is None:
        return True
    if isinstance(candidates, tuple):
        candidates = [candidates]
    for min_h, min_v in candidates:
        h_ok = ceiling_ft is None or ceiling_ft >= min_h
        v_ok = visibility_mi is None or visibility_mi >= min_v
        if h_ok and v_ok:
            return True
    return False


def _minima_caution_notes(rwys, ceiling_ft, visibility_mi):
    """Per-runway caution strings for any arrival/departure runway whose
    conditions clear NO published approach - empty (notes=[], flagged=set())
    if all clear or ceiling/visibility were not provided (best case). Never
    blocks or changes a runway choice, purely informational. Returns
    (notes, flagged_rwys, no_approach) - flagged_rwys is asserted directly by the
    selftest so a wording change can never hide a logic bug.

    THE TWO KINDS ARE SEPARATED AT SOURCE since 2026-08-04 (2nd round), which is what the
    third return value is. They were mixed in one list and every consumer then
    re-derived the split for itself, three times over and three different ways:
    _usable_now intersected flagged with VISUAL_ONLY_RWYS, _no_approach_step did
    the same intersection again, and it then pulled the matching lines back out of
    the note list by testing `text.startswith("RWY {r} has NO published")`. That
    last one was a live trap - rewording the sentence below, an edit nothing warns
    you about, would have silently stopped the filter matching and printed the
    same caution under two different headings.

    `no_approach` maps runway -> the exact note text generated for it, so a caller
    that wants to replace one with better-informed wording can find it by identity
    instead of by guessing how it starts."""
    notes = []
    flagged = set()
    no_approach = {}
    seen = set()
    for rwy in rwys or []:
        if rwy in seen:
            continue
        seen.add(rwy)
        if rwy in VISUAL_ONLY_RWYS:
            cat = weather_category(ceiling_ft, visibility_mi)
            if cat != "Visual":
                text = (
                    f"RWY {rwy} has NO published instrument approach (visual only) and "
                    f"current conditions are {cat}, not Visual - this app cannot confirm "
                    f"{rwy} is usable right now.")
                notes.append((text, "minima_warn"))
                flagged.add(rwy)
                no_approach[rwy] = text
        elif rwy in RUNWAY_MINIMA_GENERAL:
            if not _minima_ok(rwy, ceiling_ft, visibility_mi):
                cands = RUNWAY_MINIMA_GENERAL[rwy]
                cands = [cands] if isinstance(cands, tuple) else cands
                cand_txt = " or ".join(f"{h} ft/{v} SM" for h, v in cands)
                note = (
                    f"RWY {rwy}: conditions may be below every published approach minimum "
                    f"on file (lowest: {cand_txt}) - verify real charts before treating this "
                    "as usable.")
                if rwy in RUNWAY_SPECIAL_CERT_NOTE:
                    note += " " + RUNWAY_SPECIAL_CERT_NOTE[rwy]
                notes.append((note, "minima_warn"))
                flagged.add(rwy)
    return notes, flagged, no_approach


def _rwy_base(rwy):
    """'33L' -> 33, '4R' -> 4. Parallel runways share their strip's heading."""
    return int("".join(ch for ch in rwy if ch.isdigit()))


def _heading_label(rwys):
    """"(heading 33)" when every runway in the list is on heading 33, "" when
    they are not - the override's section-1 suffix.

    Added 2026-08-05 with the one-way runways, which are the first thing able to
    put two headings in one answer: runway 32 joins heading 33's arrivals, and
    the label was being read off the first entry alone, so the screen said
    "33L, 33R, 32 (heading 33)". Rather than name one of the two, it names
    neither - the Wind check line directly below reports both, with the numbers
    that actually differ between them."""
    if not rwys:
        return ""
    heads = {_rwy_base(r) for r in rwys}
    return f"(heading {heads.pop():02d})" if len(heads) == 1 else ""


def _wind_limit_notes(rwys, wind_dir, eff_speed, steady_speed, tailwind_limit,
                      crosswind_limit, gust_in_use=False):
    """FAA Order 8400.9 par. 7d wind limits, checked PER RUNWAY over the whole
    active configuration. Same shape as _minima_caution_notes on purpose -
    (notes, flagged) - so the selftest can assert the structured set and a
    wording change can never hide a logic bug.

    REPLACED, 2026-08-02, a check that ran on the flow's PRIMARY arrival runway
    only and printed one generic "the wind exceeds the limits" caution. That
    was blind to the rest of the package: two of the four flows are
    heterogeneous (SW lands 22L at 215 deg AND 27 at 272 deg; NW lands 27 at
    272 deg, 32 at 320 deg and 33L/33R at 330 deg), so the primary does not
    represent them. Concretely, at 350/25 the old code warned about "the flow"
    when only runway 27 was over - 32, 33L and 33R were all comfortable.

    This NEVER removes a runway and never reassigns the flow. Reassigning was
    checked across all 360 directions at 20/25/30/35 kt, dry and slippery:
    there is NOT ONE case where the active package fails and another package
    works, and switching can even make things worse. The better-aligned runway
    is normally already inside the active package - which is precisely what
    this per-runway note surfaces.

    Tagged OFFICIAL: the numbers and the situation of application are literal text
    of an order still in force.

    THE GUST BELONGS TO THE CROSSWIND ALONE, and the tailwind is measured on the
    STEADY wind. The phrase "(including gust values)" sits in the two CROSSWIND
    clauses of par. 7d - 7d(1)(a) for a clear and dry runway, 7d(2)(a) for one
    that is not - and in none of the three tailwind clauses (7d(1)(b), 7d(1)(c),
    7d(2)(b)). Hence the two speeds: `eff_speed` for the crosswind, `steady_speed`
    for the tailwind.

    CHANGED 2026-08-05 (Pendencia Nova B). Until then the app fed the gust to both
    components and called that "stricter than the order, so it stays" - the reading
    recorded as achado N2 on 2026-08-04 (2nd round). The arithmetic undoes that
    argument. A METAR only reports a gust when the peak runs about 10 kt or more
    above the steady wind, so EVERY reported gust is worth at least 10 kt in
    absolute terms, whatever the wind under it. Against a tailwind cap of 5 kt dry
    (0-3 kt slippery), a 10-kt gust clears the cap at any angle inside roughly 60
    degrees of the tail. That is not a stricter reading biting in a corner case: it
    hands the cap over to the presence of a gust instead of to the steady wind that
    landing and takeoff distance actually run on.

    The never-adopted 2006-2014 revision draft is the corroboration. It proposed
    writing the gust INTO the tailwind clauses - and in the same package doubled
    the cap from 5 kt to 10. Whoever revised the order saw that a gust and a 5-kt
    cap do not live together, and fixed both halves at once rather than loosening
    one. (Those draft numbers - 25/10 kt - are what a web search returns for "8400.9
    limits". They are not the order in force. See the archived FINAL_1981 PDF.)"""
    notes = []
    flagged = set()
    if not rwys:
        return notes, flagged
    if wind_dir is None:
        # Added 2026-08-03. Before this, an unknown direction skipped the
        # check entirely - a 40 kt unknown-direction wind rendered identically
        # to a 2 kt one, silent on a real safety margin (Pendencia 11 gap).
        #
        # First attempt computed a per-runway worst case (tw=cw=eff_speed)
        # and printed one "RWY X: tailwind Y kt..." line per runway - but
        # every runway got the SAME number, because there is only one number
        # (the reported speed) with no direction to split it by. That reads
        # as a per-runway calculation when it is actually one blanket
        # assumption repeated - caught by the user reviewing the live output,
        # not by the selftest, which asserts structure, not honesty of
        # wording. One sentence for the whole configuration says the same
        # thing without pretending to a precision the app does not have.
        #
        # flagged is left EMPTY on purpose, and that emptiness now carries more
        # weight than when it was written: besides suppressing the paragraph in
        # render() that cites a per-runway list, it is what keeps the par. 7d
        # role fill from firing here. With no direction there is nothing to
        # align a replacement runway WITH, so "reassign this side by wind
        # alignment" has no meaning - _apply_role_fill sees no flagged runway,
        # concludes the package still stands, and leaves it alone. _fill_role
        # guards the same case independently (wind_dir is None -> empty).
        # Each component against the speed that governs IT (2026-08-05): with no
        # direction the whole speed is assumed to land on the component, so the
        # steady wind is the tailwind worst case and the gust the crosswind one.
        if steady_speed > tailwind_limit or eff_speed > crosswind_limit:
            notes.append((
                f"Wind direction unknown at {eff_speed:.0f} kt - a tailwind or "
                "crosswind over the FAA 8400.9 runway-use limits cannot be "
                "ruled out on this configuration. Enter a direction for a "
                "precise check.", "wind_warn"))
        return notes, flagged
    seen = set()
    for rwy in rwys:
        if rwy in seen:
            continue
        seen.add(rwy)
        base = _rwy_base(rwy)
        tw = tailwind_component(wind_dir, steady_speed, base)
        cw = crosswind_component(wind_dir, eff_speed, base)
        over = []
        if tw > tailwind_limit:
            over.append(f"tailwind {tw:.1f} kt (limit {tailwind_limit} kt)")
        if cw > crosswind_limit:
            gust_txt = ", gust included" if gust_in_use else ""
            over.append(
                f"crosswind {cw:.1f} kt (limit {crosswind_limit} kt{gust_txt})")
        if over:
            notes.append((
                f"RWY {rwy}: {' and '.join(over)} - over the FAA 8400.9 runway-use "
                "limits.", "wind_warn"))
            flagged.add(rwy)
    # THE [APP SIMPLIFICATION] DISCLAIMER THAT STOOD HERE IS GONE (2026-08-05). It
    # confessed the stricter-than-the-order reading, and there is no longer a
    # stricter reading to confess. What replaces it is not a caution at all - the
    # division of the two speeds is now ordinary correct behaviour - so it belongs
    # on the "Wind check" line that always prints the numbers, next to the figures
    # it explains, and not in a block that only appears when something is wrong.
    # See _wind_readout.
    return notes, flagged


def _wind_limit_step(result, wind_dir, eff_speed, steady_speed, tailwind_limit,
                     crosswind_limit, gust_in_use=False):
    """Runs the per-runway check over arrivals AND departures.

    The escalation that used to live here was REMOVED 2026-08-04. It read "No
    documented KBOS configuration satisfies Order 8400.9 in this wind - the
    usual case is a strong easterly, where the aligned runway is 9... The app
    will not invent a configuration", and every clause of it has since been
    disproved:

      - "the usual case is a strong easterly" was already false in a shipped
        selftest scenario - `Minima: 0/0 override` has wind from 000 and
        printed that sentence anyway. A second dead zone exists at 250-269 deg
        under Instrument weather, which the 2026-08-02 sweep never saw because
        it only tested Visual.
      - "the app will not invent a configuration" described a limitation that
        no longer exists. Par. 7d is a criterion FOR the noise programme, so
        when it empties one side the programme simply stops governing there and
        wind alignment answers - see _fill_role. Nothing is invented: an
        easterly lands on the documented Northeast Flow package, whatever the
        weather. (Until 2026-08-04 (8th round) that was true in IMC only - in
        Visual the scan answered "land 9", which no KBOS configuration does.)

    _apply_role_fill now writes the replacement sentence, right where it knows
    which side was reassigned and to what, and _reassigned_wind_notes measures
    the runway it settled on - this check ran before the fill and so has only
    ever seen the package the fill replaced."""
    rwys = (result["arr_rwys"] or []) + (result["dep_rwys"] or [])
    result["wind_notes"], result["wind_flagged"] = _wind_limit_notes(
        rwys, wind_dir, eff_speed, steady_speed, tailwind_limit, crosswind_limit,
        gust_in_use)


def _fill_role(role, wind_dir, eff_speed, ceiling_ft, visibility_mi, night_block):
    """Best-aligned runways that can actually serve `role` ("arr" or "dep").

    Walks OVERRIDE_CANDIDATES from best headwind down and returns the first
    heading usable for this role. Empty list = nothing at KBOS can serve this
    role at all in these conditions.

    Added 2026-08-04. Par. 7d is a CRITERION FOR the runway use programme, not
    a warning about it - the order lists it beside thunderstorms, braking and
    visibility under "OPERATIONAL SAFETY CRITERIA FOR RUNWAY USE PROGRAMS",
    and its text binds "the selected runway". So a runway over the caps cannot
    be assigned under the programme at all. When that empties one side of a
    documented package, the programme has no runway left to assign THERE, and
    that side alone falls back to pure wind alignment - which is this.

    The other side keeps whatever the package still validly assigns. Replacing
    the whole configuration instead was measured and is worse: across the 6,005
    winds where exactly one side empties, the two agree on 4,491 and on the
    other 1,514 the whole-config version throws away a documented runway that
    passed the check (SE at 090/18 wet keeps departures 9 AND 14 this way; the
    whole-config version answers 9 alone). See KBOS_achados.md 15.3.

    ROLES ARE NOT SYMMETRIC, which is the whole reason this takes a `role`
    instead of picking one heading for both: an arrival needs somewhere the
    airport actually lands, a departure needs none of that. Runway 9 launches
    all day and receives nothing - and that asymmetry is what lets the scan
    answer "arrivals 4L/4R, departures 9", which is the documented Northeast
    Flow rediscovered rather than a configuration invented here.

    THE ARRIVAL SIDE IS RESTRICTED TO DOCUMENTED_ARRIVAL_RWYS since 2026-08-04
    (8th round), and that check runs BEFORE the weather one because it does not
    depend on the weather. The old code only kept runway 9 out of arrivals when
    the weather was below Visual, via the minima check - which reads as the same
    rule but is not: on a clear day it answered "land 9", a runway no KBOS
    configuration lands on and that Massport's own data shows taking 0.0% of
    arrivals. Measured over 360 degrees x 8 speeds x dry/wet x VMC/IMC x with
    and without the safety override, that wrong answer covered 1,402 input
    combinations, every one of them in Visual weather, and it reached the
    player through two different doors - this scan is shared by the par. 7d
    role fill and by the Step 0 safety override.

    THE 8400.9 CAPS ARE DELIBERATELY NOT APPLIED HERE, which is why no limit is
    even a parameter. They are criteria FOR the noise programme; once the
    programme stops governing they stop binding anything, and nothing in the
    order says a wind over them closes the airport. Filtering by them would
    return "no runway" for winds that have an obvious answer - the most-aligned
    one, which is what a controller uses. When that pick is itself over a cap,
    _wind_limit_notes still reports it per runway with the number, so the app
    answers AND says the answer is uncomfortable instead of refusing to answer.

    Sorting by tailwind ascending IS "most nearly aligned": at a fixed speed the
    most negative tailwind is the smallest angle off the nose, which is also the
    smallest crosswind.

    Returns (rwys, passed_over, never_arrival). `passed_over` lists the
    better-aligned arrival runways this walked past because the weather rules
    them out, and `never_arrival` the ones it walked past because the airport
    does not land there at all - two different answers to "why not that one",
    kept apart so the caller can give the right one. Skipping either silently
    would hand the player a runway further off the wind with no explanation -
    the same defect _apply_night_prohibition guards against when it removes 4L
    and says so in the same breath.
    """
    passed_over = []
    never_arrival = []
    supplements = []
    if wind_dir is None:
        return [], passed_over, never_arrival
    # eff_speed AND NOT THE STEADY WIND, and that survived Pendencia Nova B on
    # 2026-08-05 deliberately - do not "fix" it to match the limit checks. This
    # sorts; it never compares against a cap. Every heading is multiplied by the
    # same speed, so the ORDER is identical either way, and at wind_speed 0 with a
    # gust (which the input validation allows) the steady version ties every
    # heading at 0 and hands the pick to list order. Same reasoning as tw_rank in
    # evaluate().
    for heading in sorted(OVERRIDE_CANDIDATES,
                          key=lambda h: tailwind_component(wind_dir, eff_speed, h)):
        rwys = list(HEADING_TO_RWYS[heading])
        # FIRST, because it is the oldest and hardest of the filters here: a
        # court order, not a preference or a weather reading. Added 2026-08-05
        # with headings 14 and 32 themselves - they are candidates now, and each
        # serves exactly one role, unlike every other heading in the list.
        #
        # Skipped SILENTLY, unlike never_arrival: ALWAYS_ON prints "Runway 14/32
        # one-way: 14 = takeoff only, 32 = landing only" in every single output,
        # tagged OFFICIAL, so the answer to "why not 14 for arrivals" is already
        # on screen, permanently, in better words than a note written here could
        # manage. Runway 9 needed its own sentence precisely because nothing
        # else on screen accounted for it.
        rwys = [r for r in rwys if RUNWAY_ONLY_ROLE.get(r, role) == role]
        if night_block:
            # 740 CMR 24.05 outranks this fallback for the same reason it
            # outlives the safety override - it is a full prohibition, not a
            # noise preference. See _apply_night_prohibition.
            rwys = [r for r in rwys if r != ("4L" if role == "dep" else "22R")]
        if role == "arr":
            # BEFORE the weather check, because it does not depend on it: a
            # runway no documented configuration lands on is not a destination
            # this scan may invent, clear skies or not. See
            # DOCUMENTED_ARRIVAL_RWYS for the three facts behind that.
            outside = [r for r in rwys if r not in DOCUMENTED_ARRIVAL_RWYS]
            if outside:
                never_arrival.extend(outside)
                rwys = [r for r in rwys if r in DOCUMENTED_ARRIVAL_RWYS]
            # Both kinds disqualify a runway HERE, and the name says so since
            # 2026-08-04 (2nd round) - this was called `no_approach` while actually holding
            # everything the weather flagged, below-minima runways included. That
            # is deliberate and is NOT the same rule _usable_now applies: this is
            # "which runway do I move arrivals TO", where picking one the weather
            # rules out would be pointless, while _usable_now answers "does this
            # DOCUMENTED runway leave the table", where a below-minima reading is
            # only a proxy and is left in place with a hedged caution. Two
            # questions, two answers; the old name hid that they were different.
            _notes, weather_out, _no_app = _minima_caution_notes(
                rwys, ceiling_ft, visibility_mi)
            passed_over.extend(r for r in rwys if r in weather_out)
            rwys = [r for r in rwys if r not in weather_out]
        if not rwys:
            continue
        # Held back rather than returned: these two cannot serve the airport on
        # their own (see NEVER_ALONE_RWYS), so a heading made up entirely of them
        # does not end the walk. They have already passed every check above by
        # this point - role, night, flow membership, weather - so what is carried
        # forward is a runway genuinely usable now, just not sufficient alone.
        # A heading is all-or-nothing here: 14 and 32 are each the only runway on
        # their heading, so this never splits a pair.
        if all(r in NEVER_ALONE_RWYS for r in rwys):
            supplements.extend(rwys)
            continue
        return rwys + supplements, passed_over, never_arrival
    # Nothing could stand alone. Supplements are deliberately NOT returned here:
    # if the scan found no runway able to carry the role, answering with the one
    # that explicitly cannot is worse than answering nothing, which the caller
    # already knows how to say.
    return [], passed_over, never_arrival


def _never_arrival_note(result, never_arrival):
    """Explain a heading the arrival scan refused outright.

    Separate from _merge_passed_over because the two say different things and
    only one of them is about today: a passed-over runway is one the WEATHER
    rules out right now, this one the airport never lands on at all. Reusing the
    weather wording here would have been wrong in both directions - it would
    read as temporary, and on a clear day it would have had nothing to say.

    Filed under no_approach_notes rather than wind_notes on purpose. The wind
    block is headed "WIND OVER THE FAA 8400.9 RUNWAY-USE LIMITS", and this note
    fires whenever runway 9 is best aligned - including light easterlies where
    nothing is over any limit, which would have printed that heading over a
    screen with no runway near a cap."""
    if not never_arrival:
        return
    rwys = sorted(set(never_arrival))
    result["no_approach_notes"].append((
        f"RWY {_fmt(rwys)} is better aligned with this wind but takes no "
        "arrivals: no documented KBOS configuration lands there and it has no "
        "published approach. Departures are unaffected.", "minima_warn"))


# Massport's own names, always written out (massportcac_operational_overview_
# 2017.pdf pp. 11-17) - never abbreviated, never a single cardinal point. Added
# 2026-08-04 for the par. 7d fallback sentence, which has to name the package it
# could not assign from.
#
# NOTE: result["flow"] is still built as flow_key + " flow" ("SE flow"), so the
# header line and the arrival note two lines below it currently disagree - the
# 2026-08-03 name audit (achados 14) fixed the notes and missed the header.
# Not changed here: that is a visible string with no bearing on this round.
FLOW_FULL_NAME = {
    "NE": "Northeast Flow",
    "SW": "Southwest Flow",
    "NW": "Northwest Flow",
    "SE": "Southeast Flow",
}


def _merge_passed_over(result, passed_over, ceiling_ft, visibility_mi):
    """Explain the runways _fill_role walked past.

    They are better aligned with the wind than the one it settled on, so a
    player who knows the airport will ask why they were not used. The answer is
    the same minima caution the app already produces for a runway inside the
    configuration - reused verbatim rather than reworded, so one runway never
    gets two different explanations for one fact."""
    if not passed_over:
        return
    notes, flagged, no_approach = _minima_caution_notes(
        passed_over, ceiling_ft, visibility_mi)
    known = {text for text, _tag in result["minima_notes"]}
    result["minima_notes"].extend(
        (text, tag) for text, tag in notes if text not in known)
    result["minima_flagged"] = result["minima_flagged"] | flagged
    result["minima_no_approach"].update(no_approach)


def _apply_role_fill(result, wind_dir, eff_speed, ceiling_ft, visibility_mi,
                     night_block):
    """Par. 7d as the criterion it is: when the wind check leaves one side of
    the documented package with no runway at all, the noise programme can no
    longer assign one THERE, so that side alone reverts to wind alignment.

    Runs per side, never on the configuration as a whole - the other side keeps
    whatever the package still validly assigns (see _fill_role for the measured
    reason). The flow label is deliberately left untouched: a half-reassigned
    configuration gets no invented name of its own (user decision, 2026-08-04).
    """
    flagged = result["wind_flagged"]
    for key, role in (("arr_rwys", "arr"), ("dep_rwys", "dep")):
        assigned = result[key]
        if not assigned:
            continue                    # nothing was assigned to begin with
        if [r for r in assigned if r not in flagged]:
            continue                    # this side still has a usable runway
        result[key], passed_over, never_arrival = _fill_role(
            role, wind_dir, eff_speed, ceiling_ft, visibility_mi, night_block)
        result["role_fill"][role] = list(result[key])
        _never_arrival_note(result, never_arrival)
        if result[key]:
            # Only when something WAS chosen: the passed-over notes exist to
            # explain why a better-aligned runway lost to the one on screen. If
            # nothing was chosen there is no comparison to draw, and the
            # sentence below carries the whole message on its own.
            _merge_passed_over(result, passed_over, ceiling_ft, visibility_mi)

        # The sentence goes on wind_notes, next to the per-runway lines that
        # caused it, so render stays dumb. It deliberately repeats NO number:
        # those lines already carry them, one per runway, and the runways of an
        # emptied side do not always share a heading (measured: 2,909 of 12,139
        # such winds), so there is often no single figure to quote anyway.
        side = "arrival" if role == "arr" else "departure"
        package = FLOW_FULL_NAME.get(result["flow_key"], result["flow"])
        if result[key]:
            result["wind_notes"].append((
                f"The {package} package has no eligible {side} runway. Under Order "
                f"8400.9 par. 7d {side}s were reassigned to RWY "
                f"{_fmt(result[key])} by wind alignment.", "wind_warn"))
        else:
            result["wind_notes"].append((
                f"The {package} package has no eligible {side} runway, and no runway "
                f"at KBOS can take a {side} in these conditions - real ATC "
                "improvises here.", "wind_warn"))


def _reassigned_wind_notes(result, wind_dir, eff_speed, steady_speed,
                           tailwind_limit, crosswind_limit, gust_in_use):
    """Report the wind on runways par. 7d has just reassigned to.

    The per-runway check ran before the fill did, so it measured the DOCUMENTED
    package and never the runway the fallback settled on - which can be over a
    cap itself. An easterly at 25 kt is the case that shows it: the Southeast
    pair goes out at 21.7 kt of crosswind, and the 4L/4R pair it falls back to
    sits at 20.5 kt, half a knot over the same limit. Printing the numbers for
    the runways being taken AWAY and none for the one being handed to the player
    hides exactly the figure they need.

    THE RUNWAYS ARE NOT ADDED TO wind_flagged, and that is the whole reason this
    merges notes by hand instead of calling _wind_limit_step again. Flagged means
    "the noise programme may not assign this", which is what takes a runway out
    of the table in _usable_now - and here the programme has already stopped
    governing this side, which is why the fallback ran at all. Flagging would
    delete the only answer left from the table that exists to show it, on the
    authority of a rule that is no longer in play. Same reading of par. 7d that
    exempts the safety override there.
    """
    rwys = [r for role in ("arr", "dep")
            for r in result["role_fill"].get(role, [])]
    if not rwys:
        return
    notes, _flagged = _wind_limit_notes(
        rwys, wind_dir, eff_speed, steady_speed, tailwind_limit, crosswind_limit,
        gust_in_use)
    known = {text for text, _tag in result["wind_notes"]}
    result["wind_notes"].extend(
        (text, tag) for text, tag in notes if text not in known)


def tailwind_component(wind_dir_deg, wind_speed_kt, runway):
    """Positive = tailwind on that runway direction, negative = headwind."""
    heading = RUNWAY_HEADING[runway]
    headwind = wind_speed_kt * math.cos(math.radians(wind_dir_deg - heading))
    return -headwind


def crosswind_component(wind_dir_deg, wind_speed_kt, runway):
    heading = RUNWAY_HEADING[runway]
    return abs(wind_speed_kt * math.sin(math.radians(wind_dir_deg - heading)))


def _wind_readout(label, heading, wind_dir, eff_speed, steady_speed, gust,
                  tailwind_limit, crosswind_limit):
    """The "Wind check:" line, for whichever runway is being reported on.

    Extracted 2026-08-04 (2nd round) from two places that had drifted into being the same
    sentence typed twice - the flow's primary arrival runway, and the runway par.
    7d reassigned arrivals to. They differ in the label alone, and the numbers
    behind them are the same two functions either way, so writing them out twice
    only created a second place to forget the limits, or the gust note, or the
    tag. The safety override keeps its own line: it reports a BEST-HEADWIND pick
    rather than an assigned runway, and says so in different words."""
    gust_note = f" (incl. gust {gust:.0f} kt)" if gust is not None else ""
    split_note = (" - the gust counts on the crosswind only; the tailwind is the "
                  "steady wind" if gust is not None else "")
    return (
        f"On {label} ({heading:02d}): tailwind "
        f"{tailwind_component(wind_dir, steady_speed, heading):.1f} kt, crosswind "
        f"{crosswind_component(wind_dir, eff_speed, heading):.1f} kt{gust_note} - "
        f"limits: tailwind {tailwind_limit} kt, crosswind {crosswind_limit} kt "
        f"({OFFICIAL} FAA 8400.9 par. 7d{split_note})")


def wind_quadrant(wind_dir_deg):
    """Plain 90-degree compass quadrants. The KBOS sources name four flows
    (NE/SE/SW/NW) chosen "by wind" but never publish the exact sector
    boundaries, so this is an APP SIMPLIFICATION."""
    d = wind_dir_deg % 360
    if d < 90:
        return "NE"
    if d < 180:
        return "SE"
    if d < 270:
        return "SW"
    return "NW"


def weather_category(ceiling_ft, visibility_mi):
    """Official BOS thresholds (FAA Capacity Profile 2019). Never an input -
    always derived. Blank ceiling/visibility = not a factor (best case)."""
    if (ceiling_ft is not None and ceiling_ft < 1000) or \
       (visibility_mi is not None and visibility_mi < 3):
        return "Instrument"
    if (ceiling_ft is None or ceiling_ft >= 3000) and \
       (visibility_mi is None or visibility_mi >= 3):
        return "Visual"
    return "Marginal"


# ---------------------------------------------------------------------------
# Flow definitions (arrivals/departures per FAA Capacity Profile + Massport).
# Runway sets are LISTS - the single source of truth: both the display
# strings (section 1) and the eligibility filters (section 2) derive from
# them, so the two sections can never drift apart.
# "primary" = arrival runway heading used for the wind component readout.
# ---------------------------------------------------------------------------
FLOWS = {
    "NE": {"arr": ["4L", "4R"], "dep": ["9", "4L", "4R"], "primary": 4},
    "SW": {"arr": ["22L", "27"], "dep": ["22L", "22R"], "primary": 22},
    # NW arrivals CORRECTED 2026-08-02: were ["27","32"], taken from the FAA
    # Capacity Profile, while the departures on the same line already came from
    # Massport/the vZBW SOP - two sources mixed with no criterion. Massport's
    # own runway-use data (CAC "Logan 101", p.16, CY2016) is explicit:
    # "Arrivals to R 33L, 33R (limited), 32 and 27 - Departures from R 33L and
    # 27". The two official sources are not in conflict: the Capacity Profile
    # models ONE representative configuration per weather category for
    # throughput analysis, Massport reports what actually flew. Runway 33L
    # matters most here - 10,083 ft with an ILS CAT III, and the only arrival
    # runway aligned with a 330-350 deg wind, where runway 27 takes 21-24 kt of
    # crosswind. What varies within the flow is time/traffic driven ("we go
    # from landing 33L in the morning to landing 27 and 32 in the evening"),
    # and traffic volume can never be an app input - so the app lists the
    # available package and leaves the operational refinement to the player.
    # 33R is included for consistency with 15L (same "(limited)" label from the
    # same source, already in the SE package); the jet filter below excludes it
    # automatically, which is exactly what Massport's "Non-Jet" label means.
    "NW": {"arr": ["27", "32", "33L", "33R"], "dep": ["33L", "27"], "primary": 27},
    "SE": {"arr": ["15R", "15L"], "dep": ["9", "14"], "primary": 15},
}

# Every runway some documented configuration lands on, DERIVED from the tables
# above rather than hand-listed - the same single-source rule the display
# strings follow, so a package edited above can never leave a stale copy here.
# Read by _fill_role (defined earlier in the file; module-level names resolve
# when it runs, not when it is written).
#
# Added 2026-08-04 (8th round) to fix an arrival the scan should never have
# offered. At KBOS it evaluates to everything except runways 9 and 14, and 14 is
# already out of OVERRIDE_CANDIDATES, so runway 9 is the whole practical effect.
# Three independent facts say 9 is not an arrival runway: no flow in the table
# above assigns it to arrivals, it has no published approach of any kind, and
# Massport's own quarterly runway-use data records 0.0% of arrivals on it - jet
# AND non-jet, across a full quarter (Fly Quiet Report, Q1 2019, Table 4-1).
#
# Deriving it from FLOWS rather than reusing VISUAL_ONLY_RWYS was the whole
# point, and the difference is not cosmetic: 15L, 22R and 33R have no published
# approach either, but Massport documents all three AS arrival runways (15L in
# the Southeast package, 33R in the Northwest, 22R as the Southwest prop bonus).
# Excluding by "no approach" would have contradicted three documented packages
# to fix one undocumented runway.
DOCUMENTED_ARRIVAL_RWYS = (
    {r for f in FLOWS.values() for r in f["arr"]}
    | {r for v in PROP_ARRIVAL_BONUS.values() for r in v})


def _fmt(rwys, suffix=""):
    """Display string from a runway list (single source of truth)."""
    if not rwys:
        return "none"
    s = ", ".join(rwys)
    return f"{s} {suffix}".strip() if suffix else s

# NO OPEN-QUESTION MACHINERY ANY MORE (removed 2026-08-01).
# There used to be an OPEN_QUESTIONS dict here plus a render block that printed
# "this scenario touches an open community question". Every entry has now been
# either answered or retired:
#   Q3 (generic "anything outdated?") -> document-level disclaimer, 2026-07-31.
#   Q4 (NW below Visual) -> answered by 14 CFR 91.175 + published minima, 07-31.
#   Q7 (go-around mitigation for 27+32) -> answered; nothing the app models.
#   Q1 (night head-to-head window) -> retired 2026-08-01. It was the last one,
#     and the reason it went is worth recording: the residual ("the real switch
#     tracks traffic volume, not the clock") can never change this app, because
#     volume is not readable from a METAR and so can never be an input - the
#     same test that removed windshear. An arbitrated threshold is not an open
#     question; it is a documented engineering choice, which is what the
#     confidence tags are for. The wind-quadrant boundaries, the override
#     candidate set and the NE default for variable wind are all arbitrated the
#     same way and none of them carries a question either. What Q1 knew is not
#     lost: it lives in decision 6 of the module docstring, in the note on the
#     head-to-head branch below, and in section 6 of the rules PDF.
# Q5/Q6 remain open in the rules PDF, but they concern simultaneous-runway
# separation (Step 6), which this build's engine does not implement - the engine
# never touched them, which is why removing the machinery costs nothing.

# ---------------------------------------------------------------------------
# Always-on restrictions - informational ONLY (locked decision 2026-07-28):
# they appear in every output and never modify the computed configuration.
# Each entry: (category render-tag, category label, confidence tag, text).
# The confidence tag became per-entry on 2026-07-31: it used to be hardcoded
# to OFFICIAL for the whole block, which would have mislabelled the two
# game-category breakdowns added that day (they are derived from published
# landing distances and one controller account, not from an FAA document).
# ---------------------------------------------------------------------------
# REWRITTEN 2026-08-03 (Pendencia 0). Four changes, all deliberate:
#   - two entries added (takeoff 14, landing 27 under LAHSO), so all four
#     runways with a sourced category breakdown are stated here;
#   - the two existing breakdowns corrected: 32 gains B (a regional jet fits
#     the landing distance, so a lighter, narrower business jet does too) and
#     C, and 15L/33R loses "C depends" - Cargo always follows N/W, since the
#     game only shows large jets as Cargo;
#   - the "Maximum 210 kt until 520 ft MSL" procedure line REMOVED: the game
#     takes the aircraft after takeoff, so the player can do nothing with it -
#     the same test that kept windshear out of the inputs;
#   - wording trimmed to what a player acts on. The exact dBA figures and the
#     "restricts DIRECTION, not aircraft size" clause were research-audit
#     precision, not player-facing: nobody flies differently knowing 73 vs 78
#     dBA. That reasoning stays in KBOS_achados.md, which is its proper home.
ALWAYS_ON = [
    ("rt_noise", "NOISE/TIME", OFFICIAL,
     "4L takeoffs & 22R landings: non-jet only in practice (noise limits). "
     "From 23:00 to 06:00: fully prohibited for ALL aircraft, even props, "
     "from State regulation 740 CMR 24.05."),
    ("rt_noise", "NOISE/TIME", OFFICIAL,
     "Noise preference (soft, not a full restriction): takeoff 15R, landing "
     "33L - both paths over the water."),
    ("rt_legal", "PHYSICAL & LEGAL", OFFICIAL,
     "Runway 14/32 one-way: 14 = takeoff only, 32 = landing only."),
    ("rt_legal", "PHYSICAL & LEGAL", OFFICIAL,
     "Runway 15L/33R: 2,557 ft - far too short for airline jets in either "
     "direction."),
    ("rt_class", "AIRCRAFT CLASS", OFFICIAL,
     "Jets depart ONLY from: 4R, 9, 15R, 22L, 22R, 27, 33L."),
    ("rt_class", "AIRCRAFT CLASS", CORROBORATED,
     "Landing runway 32 by game category: P / T / B / R yes - regional jets "
     "do land there (a KBOS controller: \"most jets refuse to use it... only "
     "e170/190s use it to land\"). N / W / C, no, anything bigger than a "
     "regional jet was ruled out. Massport's own traffic data marks the "
     "runway \"wind restricted\"."),
    ("rt_class", "AIRCRAFT CLASS", SIMPLIFICATION,
     "Landing runway 15L/33R by game category: P yes; R / N / W / C, ruled "
     "out by landing distance alone; T / B vary with the specific aircraft - "
     "a King Air or PC-12 fits, a Dash 8 or ATR does not. Derived directly "
     "from game logic assigning P/T/B/R/N/W/C letters, not from a "
     "KBOS-specific source."),
    ("rt_class", "AIRCRAFT CLASS", SIMPLIFICATION,
     # Wording fixed 2026-08-04 (2nd round): read "R ,depend", and said "depend" where the
     # table cell for the same fact renders "varies". One vocabulary per fact -
     # the player reads both on the same screen.
     "Takeoff runway 14 by game category: P / T / B, yes - light and business "
     "jets still clear 5,000 ft on departure; R varies; N / W / C, no - "
     "mainline jets typically need MORE runway to depart than to land, "
     "so 5,000 ft is not enough."),
    ("rt_class", "AIRCRAFT CLASS", SIMPLIFICATION,
     "Takeoff runway 15L/33R by game category: P yes; B / R / N / W / C, ruled "
     "out by takeoff distance alone; T varies with the specific aircraft - "
     "a Cessna 402C fits, a Dash 8 does not. Derived directly "
     "from game logic assigning P/T/B/R/N/W/C letters, not from a "
     "KBOS-specific source."),
    ("rt_class", "AIRCRAFT CLASS", OFFICIAL,
     "Landing runway 27 while operating under LAHSO (Southwest Flow, Visual only "
     "- 22L arrivals hold short of 27): P / T yes, B / R / N / W / C, no. The "
     "FAA Capacity Profile states directly that only turboprops land 27 under "
     "this hold-short arrangement."),
]


def _apply_night_prohibition(result, night_block):
    """The 23:00-06:00 ban on 4L takeoffs and 22R landings (740 CMR 24.05) is
    ABSOLUTE - all aircraft, props included - so it is applied to the
    configuration lists themselves, not to a downstream display filter.

    Added 2026-08-02. Until then the removal happened inside
    _eligibility_step, which meant the PRIMARY answer still listed 4L under
    departures at 23:30 and only the eligibility lines below corrected it -
    the most visible defect in the app for anyone flying a night session.

    Called from all three branches that write a configuration (safety
    override, head-to-head, normal flow), always BEFORE the display strings
    are built, so every downstream consumer - display, eligibility, minima
    caution, wind-limit check - sees runways that are actually usable.

    The explanatory note is emitted right here, next to the removal, on
    purpose: removing a runway without saying why would turn a
    wrong-but-explained answer into a right-but-unexplained one, which is the
    same family of defect as an orphan legend entry."""
    if not night_block:
        return
    removed = []
    if result["dep_rwys"] and "4L" in result["dep_rwys"]:
        result["dep_rwys"].remove("4L")
        removed.append("4L takeoffs")
    if result["arr_rwys"] and "22R" in result["arr_rwys"]:
        result["arr_rwys"].remove("22R")
        removed.append("22R landings")
    if removed:
        result["night_notes"].append((
            f"{OFFICIAL} {' and '.join(removed)} REMOVED from the configuration above: "
            "prohibited 23:00-06:00 for ALL aircraft, props included "
            "(740 CMR 24.05, penalties 24.99).", "official"))


# ---------------------------------------------------------------------------
# Main decision engine.
# Steps 0-3 read the inputs below and are the only place the active runway
# configuration is written. Step 4 (runway eligibility by aircraft type,
# see _eligibility_step) only reads that configuration and filters it -
# aircraft type is not a parameter here, it is not an input at all.
# ---------------------------------------------------------------------------
def evaluate(hour, minute, wind_dir, wind_speed, gust,
             ceiling_ft, visibility_mi, runway_condition, braking,
             thunderstorm):
    """`wind_dir` is None for variable/unknown direction (the reported speed
    is then used directly as the worst-case tailwind for every threshold
    check, deterministically). `gust`/`ceiling_ft`/`visibility_mi` are None
    when not a factor. `runway_condition` in {"Dry","Wet","Contaminated"};
    `braking` in {"Good","Fair","Poor","Nil"}. Aircraft type is NOT an
    input - the result always carries an eligibility line for each type.
    Returns a dict describing the active configuration."""

    t = hour * 60 + minute
    slippery = runway_condition in ("Wet", "Contaminated")
    eff_speed = max(wind_speed, gust) if gust is not None else wind_speed
    # TAILWIND LIMIT CHECKS ONLY (2026-08-05, Pendencia Nova B). Par. 7d writes
    # "(including gust values)" into its crosswind clauses and into none of its
    # three tailwind ones, so the two components no longer share one speed. See
    # _wind_limit_notes for the reasoning and for why "stricter is safer" did not
    # survive the arithmetic. This is NOT the speed the flow choice or the calm
    # exemption reads - both of those keep the gust, on purpose, and each says why
    # where it is written.
    steady_speed = wind_speed

    # FAA Order 8400.9 (1981) noise runway-use limits
    tailwind_limit = 0 if slippery else 5
    crosswind_limit = 15 if slippery else 20
    gust_in_use = gust is not None and gust > wind_speed

    # PAR. 7d(2)(b) EXCEPTION, added 2026-08-04 (2nd round). The zero-tailwind rule for a
    # runway that is not clear and dry carries an exception the app had simply
    # never implemented. Verbatim from the archived 1981 order: "No tailwind
    # component may be present EXCEPT the nominal range of winds reported as calm
    # (0-3 knots) may be considered to have no tailwind component."
    #
    # Without it a ONE-KNOT wind put every runway of the package over the limit,
    # and the par. 7d role fill then reassigned both sides - so the app answered a
    # configuration nobody asked for, on a wind nobody would notice. Measured over
    # 0-3 kt x non-dry x 72 directions: 282 of 432 combinations fired the caution
    # and 216 of them reassigned the configuration.
    #
    # WRITTEN AS A 3-KT LIMIT rather than as "force the component to zero" because
    # the two are arithmetically identical here - the exemption requires the whole
    # reported wind to be 0-3 kt, so no component of it can exceed 3 - and a limit
    # is a SINGLE value that every consumer already reads. Forcing the component
    # would have meant editing _wind_limit_notes AND the head-to-head branch
    # separately, which is exactly how two copies of one rule drift apart.
    #
    # THE TRIGGER IS eff_speed, not wind_speed alone. The order says winds
    # "reported as calm", and a METAR reporting a gust is not reporting calm - the
    # gust group only appears at 10 kt or more above the base, so 00003G20KT would
    # otherwise claim an exemption the text plainly does not intend. With no gust
    # the two are the same number, so this is stricter only where it should be.
    if slippery and eff_speed <= 3:
        tailwind_limit = 3

    night_block = t >= 23 * 60 or t < 6 * 60          # 23:00-06:00 [OFFICIAL]
    # 00:00-05:00 [CORROBORATED] - Massport's own metric "Runway 33L Arrivals
    # Midnight to 5AM" (Fly Quiet Report 2017). Narrowed from 00:00-06:00 on
    # 2026-08-01; see decision 6 in the module docstring.
    h2h_window = t < 5 * 60

    result = {
        "flow": None,
        "flow_key": None,       # NE/SW/NW/SE/H2H/OVERRIDE - drives eligibility
        # Always computed, in every branch including the safety override -
        # informational only, does not change the runway choice below. This
        # is what the minima-caution check (see _minima_caution_notes) reads
        # for runways with no chart minima on file.
        "weather": weather_category(ceiling_ft, visibility_mi),
        "arr_rwys": None,       # runway lists - the single source of truth
        "dep_rwys": None,
        "arrivals": None,       # display strings, derived from the lists
        "arrival_note": None,
        "departures": None,
        # No "departure_note" here: it existed from the first rewrite, was never
        # written by any branch, and render() tested it on every single output.
        # Removed 2026-08-04 (2nd round). Everything a departure needs said is already said -
        # the "(limited)" suffix on the SE package, the night removal note, the
        # par. 7d reassignment sentence - so there is nothing to restore, only a
        # slot that looked like a feature.
        "wind_readout": None,
        "reasons": [],
        "night_notes": [],
        "minima_notes": [],     # published-approach-minima caution, informational only
        "minima_flagged": set(),  # runway ids flagged - structured, for assertions
        "wind_notes": [],       # per-runway 8400.9 wind check, informational only
        "wind_flagged": set(),  # runway ids over the limits - structured, asserted
        # CAUTION: NO APPROACH AVAILABLE - split out of minima_notes on
        # 2026-08-04. A runway with no published approach at all is a harder
        # fact than one merely below its minima, and now has a harder
        # consequence (it leaves the table), so the two no longer share a
        # heading. See _no_approach_step.
        "no_approach_notes": [],
        # The subset of minima_flagged that has NO published approach at all,
        # mapped to the note text written for it (2026-08-04 (2nd round)). Separated at source
        # by _minima_caution_notes rather than re-derived by each consumer - see
        # that function for what the three separate re-derivations used to cost.
        "minima_no_approach": {},
        # Which side(s) the par. 7d fallback had to reassign, and to what
        # (2026-08-04). Structured like every other assertion target here:
        # {"arr": ["9"]} or {"dep": []} when nothing can serve that side. Empty
        # dict = the documented package answered both sides on its own.
        "role_fill": {},
        # True when par. 7d emptied BOTH sides, so the header stopped naming the
        # documented package (2026-08-04 (2nd round)). Structured like role_fill and asserted
        # directly by the selftest, so the fact is pinned without pinning the
        # sentence that reports it - a wording change must not be able to hide it.
        "package_dropped": False,
        "eligibility": [],
        "elig": None,
        "rwy_table": None,      # per-runway rows (Pendencia 0) - structured,
                                # asserted by the selftest like elig is
        "override": False,
    }

    def tw(runway):
        # STEADY, since 2026-08-05 - this feeds limit checks (the head-to-head
        # branch tests tw33/tw15 against tailwind_limit) and the figures printed
        # beside them. Ranking wants the other speed; that is tw_rank.
        if wind_dir is None:
            return steady_speed
        return tailwind_component(wind_dir, steady_speed, runway)

    def tw_rank(runway):
        """Ordering only - never compared against a limit.

        SPLIT OUT of tw() on 2026-08-05 rather than following it to the steady
        wind, and the reason is arithmetic, not caution. The component is
        speed * cos(angle), and the speed is the same constant for every heading
        in the list, so sorting by it gives the SAME order at either speed - the
        change would be a no-op almost everywhere.

        Almost. At wind_speed 0 with a gust - which the input validation accepts,
        since it only rejects a gust BELOW the steady wind - the steady ranking
        collapses to 0 for every heading, and min() then returns whichever
        candidate happens to sit first in the list. The runway would come out of
        list order instead of out of the wind. Reading the gust here keeps the
        pick meaningful in that case and identical in every other."""
        if wind_dir is None:
            return eff_speed
        return tailwind_component(wind_dir, eff_speed, runway)

    def cw(runway):
        # Same worst-case convention as tw(): with no direction reported,
        # assume the whole speed lands on this component.
        if wind_dir is None:
            return eff_speed
        return crosswind_component(wind_dir, eff_speed, runway)

    # -----------------------------------------------------------------
    # STEP 0 - safety override (noise rules OFF). Locked decision 1:
    # thunderstorm (METAR TS group) or degraded braking only - windshear is
    # not an input because it does not appear in a routine METAR.
    # -----------------------------------------------------------------
    if thunderstorm or braking != "Good":
        result["override"] = True
        # RENAMED 2026-08-04. "SAFETY OVERRIDE" was this app's own invention
        # with no source behind it - flagged as such in the achados name audit.
        # Order 8400.9 par. 7 is titled "OPERATIONAL SAFETY CRITERIA FOR RUNWAY
        # USE PROGRAMS" and lists exactly these triggers as its criteria, so the
        # order's own words replace the invented ones, and the line now names
        # WHICH criterion fired instead of leaving the reader to hunt for it in
        # the reasoning block.
        triggers = []
        if thunderstorm:
            triggers.append("Thunderstorm")
        if braking != "Good":
            triggers.append("Braking")
        result["flow"] = ("OPERATIONAL SAFETY CRITERIA - "
                          + ", ".join(triggers)
                          + " (no flow - pure wind alignment)")
        result["flow_key"] = "OVERRIDE"
        if thunderstorm:
            result["reasons"].append((
                f"{OFFICIAL} Thunderstorm reported (METAR TS group): FAA 8400.9 - noise "
                "rules stop being a factor, runway choice is pure wind alignment. Note: "
                "the real order also covers windshear (LLWAS/PIREP), which this app "
                f"dropped as an input because it is not in a routine METAR {SIMPLIFICATION}.",
                "official"))
        if braking != "Good":
            result["reasons"].append((
                f"{OFFICIAL} Braking action \"{braking}\" (worse than \"good\"): FAA 8400.9 "
                "- noise rules off; NO tailwind allowed on a slippery/contaminated runway.",
                "official"))
        if wind_dir is None:
            result["arrivals"] = "NOT DETERMINABLE (variable/unknown wind)"
            result["departures"] = result["arrivals"]
            result["arrival_note"] = (
                "The override picks the best-headwind runway - with no wind direction "
                "there is no deterministic answer.")
        else:
            # PER ROLE since 2026-08-04. Both lists used to come from ONE
            # heading - whichever had the best headwind - which quietly assumed
            # a runway that can launch can also receive. Runway 9 is the
            # counter-example and it is the scan's own favourite on an easterly:
            # no published approach at all, so the override answered "land 9" on
            # a runway nothing lands on. Now the departure side still takes the
            # best-aligned heading (a takeoff needs no approach) while the
            # arrival side keeps walking until it finds one the airport actually
            # lands on - on an easterly that is 4L/4R, which together with the 9
            # departure is the documented Northeast Flow.
            # THE FIRST FIX HERE WAS HALF OF ONE (corrected 2026-08-04, 8th
            # round): it rested on the minima check, which only rules runway 9
            # out when the weather is below Visual, so on a clear day this
            # branch went on answering "land 9". _fill_role now keeps it out of
            # arrivals in every weather, from DOCUMENTED_ARRIVAL_RWYS.
            # night_block goes IN, rather than being left to
            # _apply_night_prohibition below: a runway the 23:00-06:00 ban
            # already forbids must never reach the minima check, or it comes
            # back as a caution about a runway that was never a candidate.
            # F11c guards exactly that - 22R is visual-only, so at night in
            # Marginal weather it would otherwise be reported as below minima
            # while the ban had already taken it out. The ban still gets
            # explained here: the override branch prints its own note saying
            # the 4L/22R prohibition outlives the override.
            result["arr_rwys"], arr_passed, arr_never = _fill_role(
                "arr", wind_dir, eff_speed, ceiling_ft, visibility_mi, night_block)
            result["dep_rwys"], _dep_passed, _dep_never = _fill_role(
                "dep", wind_dir, eff_speed, ceiling_ft, visibility_mi, night_block)
            _never_arrival_note(result, arr_never)
            best = min(OVERRIDE_CANDIDATES, key=tw_rank)
            best_tw = tw(best)
            _apply_night_prohibition(result, night_block)
            # ONLY WHEN THE LIST IS ONE HEADING, since 2026-08-05. An answer can
            # now span two - the one-way 14/32 join the heading that carries the
            # role - and this label read off the FIRST runway alone, so it
            # printed "33L, 33R, 32 (heading 33)" over a list whose last entry is
            # heading 320. The Wind check line below names both headings with
            # their own numbers, so nothing is lost by dropping a label that
            # cannot describe the list.
            arr_head = _heading_label(result["arr_rwys"])
            dep_head = _heading_label(result["dep_rwys"])
            result["arrivals"] = _fmt(result["arr_rwys"], arr_head)
            result["departures"] = _fmt(result["dep_rwys"], dep_head)
            result["arrival_note"] = (
                f"{SIMPLIFICATION} Override active: best-headwind runway picked from "
                f"{len(OVERRIDE_CANDIDATES)} usable headings. The one-way 14/32 can join "
                "a configuration but never form one alone - neither takes a mainline jet.")
            result["wind_readout"] = (
                f"Best headwind: runway {best:02d} "
                f"({-best_tw:.1f} kt headwind, {crosswind_component(wind_dir, eff_speed, best):.1f} kt crosswind)")
            # When the two roles ended up on different headings, the line above
            # describes the departure runway only - and the arrival runway is
            # the one carrying the worse numbers, since it was chosen second.
            # Reporting the best heading alone would hide exactly the figure the
            # player needs.
            #
            # THE TEST IS MEMBERSHIP, not equality, since 2026-08-05: with the
            # one-way runways in the scan, the best-aligned heading can be part
            # of the arrival list rather than absent from it (320 deg puts
            # runway 32 first AND in the answer). Comparing against the first
            # entry alone then produced "Best headwind: runway 32; arrivals on
            # 33", which reads as though arrivals were not on 32 - the one thing
            # this clause exists to say.
            if result["arr_rwys"]:
                arr_head = _rwy_base(result["arr_rwys"][0])
                if best not in {_rwy_base(r) for r in result["arr_rwys"]}:
                    result["wind_readout"] += (
                        f"; arrivals on {arr_head:02d} "
                        f"({-tailwind_component(wind_dir, steady_speed, arr_head):.1f} kt "
                        f"headwind, "
                        f"{crosswind_component(wind_dir, eff_speed, arr_head):.1f} kt "
                        "crosswind)")
        if night_block:
            result["night_notes"].append((
                f"{OFFICIAL} The 4L/22R ban is NOT suspended by the safety override: it is a "
                "full prohibition, not a noise preference, so it outlives the rules that the "
                "override switches off.", "official"))
        # Noise rules are off in this branch and the runway was already picked
        # by best headwind - but that pick can still be the least-bad one and
        # be over the limits, so the check runs here too.
        #
        # ORDER CHANGED 2026-08-04: both checks now run BEFORE
        # _eligibility_step, because the table it builds is filtered by what
        # they flag - until then the table was built first and could not have
        # seen either result. Neither check reads anything _eligibility_step
        # writes, so the move is output-neutral on its own.
        (result["minima_notes"], result["minima_flagged"],
         result["minima_no_approach"]) = _minima_caution_notes(
            result["arr_rwys"], ceiling_ft, visibility_mi)
        if wind_dir is not None:
            if result["arr_rwys"]:
                # Why the scan walked past runways better aligned than the one
                # it settled on.
                _merge_passed_over(result, arr_passed, ceiling_ft, visibility_mi)
            else:
                # Nothing anywhere can receive, so per-runway cautions would be
                # ten lines all saying the same thing - the summary says it once.
                # (Reached at 0/0: no ceiling and no visibility clears any
                # published minimum on the field.)
                result["minima_notes"].append((
                    "No runway at KBOS can take an arrival in these conditions - "
                    "every candidate is below its published minimum, or has no "
                    "published approach at all. Departures are unaffected; real "
                    "ATC improvises here.", "minima_warn"))
        _wind_limit_step(result, wind_dir, eff_speed, steady_speed,
                         tailwind_limit, crosswind_limit, gust_in_use)
        _eligibility_step(result, night_block)
        return result

    # -----------------------------------------------------------------
    # STEP 1 - night rules
    # -----------------------------------------------------------------
    if night_block:
        result["night_notes"].append((
            f"{OFFICIAL} 23:00-06:00: 4L takeoffs and 22R landings fully PROHIBITED "
            "(all aircraft, even props) - 740 CMR 24.05, state regulation in force.",
            "official"))

    if h2h_window:
        # BOTH components are tested against the FAA Order 8400.9 caps. The
        # head-to-head config is a noise PREFERENCE, and Step 0 already
        # encodes the hierarchy: safety outranks noise. Testing tailwind
        # alone (the pre-2026-08-01 behaviour) inverted that - a 25-kt
        # crosswind on runway 33 with a 0-kt tailwind would still have been
        # answered "land 33L / depart 15R".
        tw33 = tw(33)
        cw33 = cw(33)
        # Order 8400.9 par. 7b, wired up 2026-08-02: "In order to utilize
        # landing runways associated with a runway use program, the reported
        # visibility shall not be less than one statute mile." The
        # head-to-head is a PURE noise preference, so it is exactly the
        # assignment that criterion governs. Nothing else in the app caught
        # this: at 0.75 SM the minima check waves 33L through (CAT III, general
        # minimum 200 ft / 0.5 SM), so the app used to answer "land 33L /
        # depart 15R" on a night the noise program may not govern at all.
        # NOT wired into Step 0: below 1 SM you need an ILS runway, and the
        # override picks by wind alignment - it would answer runway 9, which
        # has no approach at all.
        vis_ok = visibility_mi is None or visibility_mi >= 1.0
        # THE DEPARTURE END, added 2026-08-04. Until now this branch tested
        # only runway 33 - the ARRIVAL end - and never 15R, which it assigns
        # for departures in the same breath. They are opposite ends of one
        # strip, so the headwind that validates the landing IS the tailwind on
        # the takeoff: tw15 == -tw33 exactly, and a 6-kt headwind on 33L means
        # a 6-kt tailwind on 15R, over the 5-kt cap. Par. 7d applies to "all
        # runway use programs" with no carve-out for which end, and its own
        # par. 7d(1)(c) names takeoffs explicitly ("near the departure end for
        # takeoffs"), so testing one end was the same half-check that the
        # 2026-08-01 crosswind fix closed on the other axis. Computed rather
        # than derived from tw33 so the code says what it checks.
        # (cw15 is not computed: crosswind is |sin| about the strip axis, so
        # it is identical on both ends by construction.)
        tw15 = tw(15)
        if (tw33 <= tailwind_limit and cw33 <= crosswind_limit
                and tw15 <= tailwind_limit and vis_ok):
            # RENAMED 2026-08-04 (3rd round), closing the last item of the name
            # audit. "HEAD-TO-HEAD (night)" was flagged as this app's own label -
            # checking the archived Massport CAC 2017 overview settled it BOTH
            # ways: the configuration is titled "Late Night, Opposite Direction
            # Configuration" (Arrivals R 33L / Departures R 15R), and the SAME
            # document also calls it the "Overnight Head-to-Head Procedure" on
            # its noise-abatement page - so "head-to-head" was never invented,
            # only less formal. The header takes the configuration title, which
            # parallels the flow names; the descriptive texts keep "head-to-head"
            # with Massport now backing the word.
            result["flow"] = ("Late Night, Opposite Direction Configuration "
                              "(Massport; a.k.a. head-to-head)")
            result["flow_key"] = "H2H"
            # No re-derivation of result["weather"] here (removed 2026-08-04 (2nd round)):
            # the dict above already computed it from the same two arguments, and
            # weather_category is pure, so this line could only ever produce the
            # identical string. Three copies of one call invite the day when one
            # of them is passed something slightly different.
            result["arr_rwys"] = ["33L"]
            result["dep_rwys"] = ["15R"]
            # No-op for this branch (neither 4L nor 22R is ever in the
            # head-to-head config) - called anyway so all three branches that
            # write a configuration go through the same single point.
            _apply_night_prohibition(result, night_block)
            result["arrivals"] = _fmt(result["arr_rwys"])
            result["departures"] = _fmt(result["dep_rwys"])
            result["arrival_note"] = (
                f"{OFFICIAL} Noise preference for overnight hours: landing 33L / "
                "departing 15R - opposite ends of the same runway (head-on operation). "
                "All operations occur over water.")
            h2h_gust = (" - the gust counts on the crosswind only; the tailwind is "
                        "the steady wind" if gust_in_use else "")
            result["wind_readout"] = (
                f"On 33L: tailwind {tw33:.1f} kt (limit {tailwind_limit} kt), "
                f"crosswind {cw33:.1f} kt (limit {crosswind_limit} kt)"
                f"{h2h_gust}")
            result["reasons"].append((
                f"{CORROBORATED} Night head-to-head window 00:00-05:00 - Massport's own "
                "tracking metric \"Runway 33L Arrivals Midnight to 5AM\" (Fly Quiet Report "
                f"2017). {OFFICIAL} Both ends are within the in-force FAA 8400.9 limits: "
                f"on 33L tailwind {tw33:.1f}/{tailwind_limit} kt and crosswind "
                f"{cw33:.1f}/{crosswind_limit} kt, on the 15R departure end tailwind "
                f"{tw15:.1f}/{tailwind_limit} kt. {SIM_ONLY} The vZBW SOP quotes 10 kt of "
                "tailwind for this config - not used in the decision, kept only as a "
                "divergence note. The window itself is a fixed stand-in for what is "
                "really a traffic-volume trigger.",
                "corroborated"))
            # Same reorder as the safety-override branch (2026-08-04): the
            # table is filtered by what these two flag, so both run first.
            (result["minima_notes"], result["minima_flagged"],
             result["minima_no_approach"]) = _minima_caution_notes(
                result["arr_rwys"], ceiling_ft, visibility_mi)
            _wind_limit_step(
                result, wind_dir, eff_speed, steady_speed, tailwind_limit,
                crosswind_limit, gust_in_use)
            _eligibility_step(result, night_block)
            return result
        else:
            exceeded = []
            if tw33 > tailwind_limit:
                exceeded.append(
                    f"tailwind {tw33:.1f} kt on 33L > {tailwind_limit} kt (par. 7d)")
            if cw33 > crosswind_limit:
                exceeded.append(
                    f"crosswind {cw33:.1f} kt > {crosswind_limit} kt (par. 7d)")
            if tw15 > tailwind_limit:
                exceeded.append(
                    f"tailwind {tw15:.1f} kt on the 15R departure end > "
                    f"{tailwind_limit} kt (par. 7d)")
            if not vis_ok:
                exceeded.append(
                    f"visibility {visibility_mi:.2f} SM < 1 SM (par. 7b - below that, a "
                    "runway use program may not govern the landing runway)")
            sop_note = (
                f" (The sim SOP's 10-kt tailwind figure would allow it in some of "
                f"these cases {SIM_ONLY} - not used.)"
                if (tw33 > tailwind_limit or tw15 > tailwind_limit) else "")
            result["reasons"].append((
                f"Night window 00:00-05:00 is active but the head-to-head config fails "
                f"the in-force FAA 8400.9 criteria ({'; '.join(exceeded)}) {OFFICIAL}, so "
                f"it is NOT used - safety and visibility outrank the noise "
                f"preference.{sop_note} Falling through to the normal wind/flow logic.",
                # Tag corrected 2026-08-04 (2nd round), was "simonly". What refuses the
                # head-to-head here is the in-force 8400.9 criteria, and the text
                # says so; the SIM-ONLY clause is the optional sop_note, which is
                # explicitly "not used" and is absent whenever no tailwind was the
                # reason. So the whole paragraph was being painted in the colour
                # of a source it does not rely on, and sometimes does not even
                # mention.
                "official"))

    # -----------------------------------------------------------------
    # STEP 2 - wind picks the flow
    # -----------------------------------------------------------------
    # THE CALM TEST READS eff_speed SINCE 2026-08-04 (2nd round), not the bare reported wind.
    # It was the last place in the engine still ignoring the gust, and the two
    # readings collided on one screen: at 22003G20KT the flow was picked off 3 kt
    # ("calm, the wind decides nothing -> NE package") and the par. 7d check was
    # then run at 20 kt, which put every NE runway over its tailwind limit and
    # reassigned both sides. The app declared the wind irrelevant and unusable in
    # the same run, and the improvised answer it landed on (22L + 22R) was WORSE
    # than the documented Southwest package (22L + 27) it would have picked had it
    # read the gust in the first place.
    #
    # NOT A SOURCED CHANGE, and tagged accordingly below. JO 7110.65 par. 3-5-1 and
    # AIM 4-3-6 both say "when 5 knots or more" / "less than 5 knots" and neither
    # mentions gusts at all - checked against the FAA text 2026-08-04 (2nd round), it is
    # silence, not permission. What tips it is the same paragraph's own hierarchy:
    # it lists "A Runway Use Program is in effect" as an EXCEPTION to the calm-wind
    # runway, and its NOTE reads "Tailwind and crosswind considerations take
    # precedence over delay/capacity considerations, and noise abatement
    # operations/procedures". Entering a noise-preferential package on a reading of
    # the wind that the safety check then rejects inverts exactly that order.
    # (User decision, 2026-08-04 (2nd round).)
    if eff_speed < 5:
        flow = "NE"
        result["reasons"].append((
            f"{OFFICIAL} Calm wind (< 5 kt, FAA JO 7110.65 par. 3-5-1 / AIM 4-3-6): "
            "calm-wind runways -> NE flow.", "official"))
    elif wind_dir is None:
        flow = "NE"
        result["reasons"].append((
            f"Variable/unknown wind direction at {wind_speed:.0f} kt: defaulting to the "
            f"NE flow (the calm-wind configuration) {SIMPLIFICATION} - no source covers "
            "this case.", "simplification"))
    else:
        raw_flow = wind_quadrant(wind_dir)
        flow = raw_flow
        # PENDENCIA NOVA C, closed 2026-08-05 (later same day as the Q1 2019
        # exploratory simulation that found it). The SE package's own source
        # ("Strong SE wind", Massport CAC) names wind FORCE as its trigger, but
        # wind_quadrant() above only ever reads direction - measured against 35
        # days of real METAR (mesonet.agron.iastate.edu ASOS), that produced SE
        # in 18.6% of hours versus 4% Massport actually records (Logan101,
        # CY2016). A quadrant-boundary-arbitrage explanation was tested and
        # ruled out: the SE-hour wind directions have a 121 deg median, well
        # inside the sector, not clustered on an edge.
        #
        # FIX: SE stops competing with NE/SW as a quadrant and becomes their
        # FALLBACK - it only fires when neither NE's nor SW's own primary
        # runway clears the same tailwind/crosswind test par. 7d already runs
        # elsewhere in this engine (reusing tailwind_component/
        # crosswind_component, tailwind_limit/crosswind_limit, steady_speed/
        # eff_speed - all already computed above for that same check, including
        # the 0-3 kt calm exception). Validated first in a standalone script
        # (simulacao_estatistica/04_kbos_option_b_teste.py, not part of the
        # app) against the real evaluate(): SE fell from 154 to 1 of 826 hours.
        #
        # NE checked before SW, with no crosswind-based tiebreak: headings 35
        # and 215 are exactly opposite, so crosswind_component is IDENTICAL for
        # both (sin(x) and sin(x-180) share the same absolute value) and
        # tailwind_component on one is always the exact negative of the other.
        # A "lower crosswind wins" comparison would therefore always be an
        # exact tie - the only thing that ever discriminates is which side's
        # tailwind clears the limit, so "NE first, then SW" reproduces the
        # tested script's result with no tiebreak needed.
        se_override_note = None
        if raw_flow == "SE":
            ne_hdg, sw_hdg = FLOWS["NE"]["primary"], FLOWS["SW"]["primary"]
            tw_ne = tailwind_component(wind_dir, steady_speed, ne_hdg)
            cw_ne = crosswind_component(wind_dir, eff_speed, ne_hdg)
            tw_sw = tailwind_component(wind_dir, steady_speed, sw_hdg)
            cw_sw = crosswind_component(wind_dir, eff_speed, sw_hdg)
            if tw_ne <= tailwind_limit and cw_ne <= crosswind_limit:
                flow = "NE"
            elif tw_sw <= tailwind_limit and cw_sw <= crosswind_limit:
                flow = "SW"
            if flow != "SE":
                # SIMPLIFIED 2026-08-06, user decision: the standard
                # "Wind from X -> quadrant -> flow" line below is SKIPPED
                # entirely in this branch (not printed alongside this one) -
                # two REASONING lines for one decision read as clutter. This
                # line carries the same "official" color as that standard
                # line even though its text opens with the APP SIMPLIFICATION
                # bracket, so a fallback case does not look visually
                # different from every other flow pick.
                se_override_note = (
                    f"{SIMPLIFICATION} SE quadrant wind, but, as SE flow is "
                    f"only used when strong SE winds are present ({OFFICIAL} "
                    f"Massport CAC), {flow} flow was used instead, for it "
                    "clears FAA 8400.9 par. 7d tailwind/crosswind limits.")

        if se_override_note:
            result["reasons"].append((se_override_note, "official"))
        else:
            result["reasons"].append((
                f"Wind from {wind_dir:.0f} deg -> {raw_flow} quadrant -> {flow} "
                f"flow. Flow packages are {OFFICIAL} (Massport CAC / Capacity "
                f"Profile). But their boundaries were manually defined "
                f"{SIMPLIFICATION}.",
                "official"))
        # LINE REMOVED 2026-08-05, user decision. It reported which internal
        # branch fired (calm-wind test vs quadrant) rather than anything the
        # player could act on - the flow and the reason for it (wind direction)
        # are already said in full by the reasons entry just above, and the path
        # not taken is never shown for comparison, so "this used the gust to
        # avoid the calm branch" had no consequence a player could read off the
        # screen even when the branch genuinely changed the flow (confirmed with
        # 220/03G10: SW rather than the NE the calm rule alone would have given -
        # still nothing to act on, since NE's package is never displayed either
        # way). Belongs in the player manual, which documents every APP
        # SIMPLIFICATION as a matter of course - not in the live per-query
        # output. The underlying mechanism (K1/K2/K3 below) is untouched.

    fr = FLOWS[flow]
    # FLOW_FULL_NAME since 2026-08-04 (3rd round, user-approved): the header used
    # to print flow_key + " flow" ("SE flow") while the arrival note three lines
    # below already said "Southeast Flow" - the 2026-08-03 name audit fixed the
    # notes against Massport's own wording and missed the header, so one screen
    # carried two names for the same flow.
    result["flow"] = FLOW_FULL_NAME[flow]
    result["flow_key"] = flow

    if wind_dir is not None:
        result["wind_readout"] = _wind_readout(
            f"the {flow} flow's primary arrival runway", fr["primary"],
            wind_dir, eff_speed, steady_speed, gust, tailwind_limit,
            crosswind_limit)
        # The generic "the wind exceeds the limits on this flow" caution that
        # used to live here was REMOVED 2026-08-02. It was computed from the
        # primary arrival runway alone and named neither the runway nor the
        # amount. _wind_limit_step below reports every runway of the
        # configuration, with the number.

    # -----------------------------------------------------------------
    # STEP 3 - weather picks the variant (FAA Capacity Profile 2019).
    # Category is DERIVED from ceiling/visibility, never an input.
    # -----------------------------------------------------------------
    weather = result["weather"]        # derived once, at the top of evaluate()

    arr_suffix = ""
    if flow == "NE":
        result["dep_rwys"] = list(fr["dep"])
        if weather == "Visual":
            result["arr_rwys"] = list(fr["arr"])
            result["arrival_note"] = f"{OFFICIAL} Northeast Flow, Visual: dual arrivals 4L + 4R."
        elif weather == "Marginal":
            result["arr_rwys"] = ["4R"]
            arr_suffix = "only"
            result["arrival_note"] = (
                f"{OFFICIAL} Northeast Flow, Marginal: dual arrival becomes single: using "
                "only 4R (ILS CAT II-III) with reduced 2.5 NM separation authorized. "
                "Note: 4L only has an RNAV (GPS) approach and was dropped.")
        else:
            result["arr_rwys"] = ["4R"]
            arr_suffix = "only"
            result["arrival_note"] = (
                f"{OFFICIAL} Northeast Flow, Instrument: radar separation, arrivals only "
                "on 4R (ILS CAT II-III).")
    elif flow == "SW":
        if weather in ("Visual", "Marginal"):
            result["arr_rwys"] = list(fr["arr"])
            result["dep_rwys"] = list(fr["dep"])
            if weather == "Visual":
                result["arrival_note"] = (
                    f"{OFFICIAL} Southwest Flow, Visual. LAHSO: 22L arrivals hold short of "
                    "27; only turboprops land 27, holding short of 22L.")
            else:
                result["arrival_note"] = (
                    f"{OFFICIAL} Southwest Flow, Marginal: both arrival runways kept "
                    "with reduced 2.5 NM separation authorized on instrument approaches "
                    "to 22L and 27 (Capacity Profile).")
        else:
            result["arr_rwys"] = ["22L"]
            result["dep_rwys"] = ["22R"]
            arr_suffix = "only"
            result["arrival_note"] = (
                f"{OFFICIAL} Southwest Flow, Instrument: radar separation, arrivals only "
                "on 22L (ILS CAT I); 2.5 NM authorized on the ILS 22L.")
    elif flow == "NW":
        # Both arrival runways are kept in EVERY weather category (revised
        # 2026-07-31 - see decision 4 in the module docstring). What limits
        # runway 32 is its own published minimum, not the weather label:
        # 27 stays legal down to 443 ft / 1.5 SM, 32 only to 801 ft / 1.0 SM,
        # so the whole Marginal band (>= 1,000 ft) clears both and only a
        # genuinely low Instrument day takes 32 out. The minima caution
        # (_minima_caution_notes, applied further down) is what reports that,
        # per runway and with the actual number.
        result["dep_rwys"] = list(fr["dep"])
        result["arr_rwys"] = list(fr["arr"])
        result["arrival_note"] = (
            f"{OFFICIAL} Northwest Flow, ~99% VMC use. Four arrival runways: 33L "
            "(10,083 ft, ILS CAT III) and 27 (7,001 ft, ILS CAT I) carry most traffic; "
            "32 is RNAV-only (5,000 x 100 ft) and 33R (2,557 ft) has no published "
            f"approach. {CORROBORATED} Which runways are active could shift through "
            "the day. For instance: 33L for arrivals in the morning, 27+32 in the "
            "evening, freeing 33L for departures.")
    else:  # SE
        result["arr_rwys"] = list(fr["arr"])
        result["dep_rwys"] = list(fr["dep"])
        arr_suffix = "(limited)"
        if weather == "Visual":
            result["arrival_note"] = (
                f"{OFFICIAL} Southeast Flow (rare, strong SE wind): limited throughput "
                "per Massport - arrival runway crosses departure runway 9 (LAHSO "
                "required), which constrains sequencing.")
        else:
            result["arrival_note"] = (
                "NOT DOCUMENTED: no source describes an SE-flow variant below Visual "
                "weather. Consult applicable runways in the next sections.")

    _apply_night_prohibition(result, night_block)

    # Same reorder as the other two branches (2026-08-04). Here it matters most:
    # the display strings below are built from the runway lists, and the role
    # fill (added in the same round) can still REPLACE one of those lists, so
    # nothing may be rendered until both checks have run.
    (result["minima_notes"], result["minima_flagged"],
     result["minima_no_approach"]) = _minima_caution_notes(
        result["arr_rwys"], ceiling_ft, visibility_mi)
    _wind_limit_step(result, wind_dir, eff_speed, steady_speed, tailwind_limit,
                     crosswind_limit, gust_in_use)
    _apply_role_fill(result, wind_dir, eff_speed, ceiling_ft, visibility_mi,
                     night_block)
    _reassigned_wind_notes(result, wind_dir, eff_speed, steady_speed,
                           tailwind_limit, crosswind_limit, gust_in_use)

    dep_suffix = "(limited)" if flow == "SE" else ""
    # Everything built above this line describes the DOCUMENTED package, so a
    # side that the fallback reassigned is no longer described by it. Leaving
    # them attached produced three real contradictions on one screen (found by
    # reading the rendered W2 output, not by the selftest, which asserts
    # structure): "Arrivals: 9 (limited)" pinned the SE package's throughput
    # caveat onto a runway that is not in that package; the arrival note went
    # on describing dual 15R/15L arrivals; and the wind readout still reported
    # "the SE flow's primary arrival runway (15)" when 15 had stopped being an
    # arrival runway at all.
    if "arr" in result["role_fill"]:
        arr_suffix = ""
        # A REPLACEMENT, not a deletion, since 2026-08-04 (8th round). Clearing
        # this to None left section 1 with a runway list and no account of where
        # it came from - the one line under Arrivals that every other
        # configuration prints simply vanished, and the explanation was three
        # blocks further down, inside a CAUTION the player has no reason to
        # expect. The sentence stays short and repeats no number on purpose: the
        # rule, the runway and the figures are all in that block already, which
        # this points at rather than duplicates.
        result["arrival_note"] = (
            f"{FLOW_FULL_NAME.get(result['flow_key'], result['flow'])} standard "
            "arrival runways were reassigned by wind alignment (see the CAUTION "
            "section below).")
        if result["arr_rwys"]:
            result["wind_readout"] = _wind_readout(
                "the reassigned arrival runway", _rwy_base(result["arr_rwys"][0]),
                wind_dir, eff_speed, steady_speed, gust, tailwind_limit,
                crosswind_limit)
    if "dep" in result["role_fill"]:
        dep_suffix = ""

    # BOTH SIDES REASSIGNED, added 2026-08-04 (2nd round). The block above handles a package
    # that lost ONE of its roles - it drops that role's note and suffix and keeps
    # the flow name, which is right there, because the other side genuinely still
    # comes from the documented package.
    #
    # When par. 7d empties BOTH sides, nothing of the package is in use and the
    # header was still naming it. That produced a screen contradicting itself in
    # three places at once - reproducible with no gust and no exotic input, at
    # 000/30 on a wet runway: "Flow: NE flow" over "Arrivals: 33L, 33R /
    # Departures: 33L, 33R", with the REASONING block still explaining why the NE
    # package had been chosen. 52 winds do this in a 360 x 6 speeds x dry/wet
    # sweep; the calm-wind default reaches it on far weaker winds still.
    #
    # NO NAME IS INVENTED for what replaced it - same decision as the half-package
    # case (user, 2026-08-04). The header states that no documented package is in
    # use and points at the rule; the runways themselves are already on screen.
    # flow_key is deliberately LEFT ALONE: it records which package was tried, and
    # the eligibility filters keyed on it are about the airport, not the label.
    #
    # The flow-choice reason is marked superseded rather than deleted. Deleting it
    # would leave the player reading a configuration with no account of how the app
    # got there; the mark keeps the chain and says where it broke.
    if "arr" in result["role_fill"] and "dep" in result["role_fill"]:
        result["package_dropped"] = True
        package = FLOW_FULL_NAME.get(result["flow_key"], result["flow"])
        result["flow"] = ("no documented package in use - Order 8400.9 par. 7d "
                          "emptied both sides (see the wind caution below)")
        result["reasons"].append((
            f"SUPERSEDED: the {package} was selected by the rule above, but par. 7d "
            "then took every one of its runways out of BOTH roles, so none of the "
            "package is in use. What is shown is the best alignment the wind "
            "allows, per role.", "muted"))

    result["arrivals"] = _fmt(result["arr_rwys"], arr_suffix)
    result["departures"] = _fmt(result["dep_rwys"], dep_suffix)

    _eligibility_step(result, night_block, arr_suffix, dep_suffix)
    return result


# Runway 27 added to the exclusion list 2026-08-02 (Pendencia 14), stating the
# FACT only ("turboprop-only LAHSO", FAA Capacity Profile) and NOT the mechanism
# - whether the binding constraint is the 5,650 ft available to the hold-short
# point, operator LAHSO policy, or FAA demand modelling is not established by any
# source held here. It is named in the per-category clause too, because "no jets
# at all" would be as false for it as it was for 32: LAHSO is a clearance a pilot
# may decline, so the real granularity is a game-letter breakdown. Those letters
# are NOT derived yet - to be done together with the runway 14 departure letters
# (Pendencia 13 extension), same method, same published-distance data.
# Shown instead of the table when no configuration could be computed at all
# (safety override + unknown wind direction). REPLACED the former
# ELIGIBILITY_REFERENCE and ELIGIBILITY_FALLBACK on 2026-08-03: both were
# fixed text that repeated, fact for fact, what ALWAYS_ON already prints in
# every single output - so the player read the same rules twice on one screen.
# Section 1 already says the configuration is NOT DETERMINABLE and what to do
# about it; this line only has to say where the general rules are.
NO_CONFIG_MESSAGE = (
    "No specific runway configuration was determined for this input - general "
    "runway rules are listed in ALWAYS-ON RESTRICTIONS below.")

# Pointer printed under the table. One line, on purpose: the table carries the
# short facts, ALWAYS_ON carries the reasoning, and neither repeats the other.
TABLE_FOOTER_POINTER = (
    "See ALWAYS-ON RESTRICTIONS below for the full reasoning behind Jet and "
    "Game Category.")


def _usable_now(result):
    """The two runway lists with everything unusable RIGHT NOW taken out.

    Section 1 keeps showing the documented package - that is a fact about the
    flow and stays true whatever the weather is doing. This is the other
    question: of that package, what can actually be used on this input. The
    table and the eligibility lines below are answers to THAT, so they are
    built from this and not from the raw lists (user decision, 2026-08-04).

    Two filters, deliberately different in reach:

      - WIND (par. 7d) takes a runway out of BOTH roles. The tailwind and
        crosswind on a strip are the same numbers whether you are landing on
        it or taking off from it.
      - NO PUBLISHED APPROACH in non-Visual weather takes it out of ARRIVALS
        ONLY. Nothing needs an approach to depart, which is why runway 9 keeps
        launching in IMC.

    Runways merely BELOW their published minima are NOT filtered. That is a
    softer fact than it looks: 14 CFR 91.175 governs DESCENT below the minimum
    and turns on FLIGHT visibility, while this app compares REPORTED ceiling and
    visibility - a proxy, which is why the app's own caution for it is hedged
    ("may be below... verify real charts"). Filtering on a proxy would also
    reinstate exactly what the 2026-07-31 Q4 decision reversed, having judged
    the old blanket rule "excessively conservative, discarding a runway the law
    still allows".

    THE WIND FILTER IS SKIPPED INSIDE THE SAFETY OVERRIDE, and that is not an
    exception to the rule but the rule read properly. The caps bound a NOISE
    programme; the override exists precisely because thunderstorms or braking
    have switched that programme off, so there is nothing left for them to
    bound. Applying them there produced a straight contradiction on one screen -
    an easterly in IMC had the scan pick 4L/4R as the only runways that can
    receive, and the filter then removed both, so the app named an arrival
    configuration and declared it unusable in the same breath. The caps stay
    visible as a caution (that IS still true and worth knowing), they just no
    longer decide.
    """
    no_approach = set(result["minima_no_approach"])
    wind_out = set() if result["override"] else result["wind_flagged"]
    arr = [r for r in (result["arr_rwys"] or [])
           if r not in wind_out and r not in no_approach]
    dep = [r for r in (result["dep_rwys"] or []) if r not in wind_out]
    return arr, dep


def _package_governs_arrivals(result):
    """True while the arrival side still comes from the documented package.

    Added 2026-08-04 (2nd round) as a guard, not as a fix for anything visible. Two tables are
    keyed on (flow_key, weather) - LAHSO_JET_EXCLUSION and LAHSO_GAME_CATEGORY -
    and one on flow_key alone, PROP_ARRIVAL_BONUS. All three describe an
    ARRANGEMENT BETWEEN THE PACKAGE'S RUNWAYS, not a property of a runway: the
    turboprop-only limit on 27 exists because 22L arrivals are holding short of
    it, and the 22R prop bonus is what Massport documents alongside the Southwest
    arrival pair. flow_key deliberately keeps naming the package that was TRIED
    even after par. 7d reassigns a side (it is what the eligibility filters and
    the header's own explanation are built on), so without this guard those
    lookups would go on describing an arrangement whose other half is gone -
    runway 27 would be marked turboprop-only for a LAHSO with a runway no longer
    taking arrivals.

    THIS IS REACHED, and the first reading of it here was wrong. Checking whether
    the SW arrival side can empty, only the DRY caps were tried - 22L at 215 deg
    and 27 at 272 deg, and no wind in the SW quadrant puts both over 20 kt of
    crosswind at once. On a WET runway the cap is 15, and 180/30 clears it on
    both: 17.2 kt across 22L and 30 kt across 27, which also carries a tailwind.
    The whole package goes, arrivals land on 15R/15L - and the app went on
    printing "+ 22R (noise-runway bonus, Massport CAC)" on the turboprop line,
    naming a runway that was not in the configuration at all. 58 combinations of
    the sweep did this, every one of them SW on a non-dry runway.

    The lesson is the cheaper half of the same mistake this file has recorded
    before: a reachability argument run against one set of limits says nothing
    about the other set, and the slippery caps are exactly the ones that make
    marginal cases reachable."""
    return "arr" not in result["role_fill"]


def _no_approach_step(result, arr, dep):
    """Builds the CAUTION: NO APPROACH AVAILABLE block and takes those lines
    out of the minima caution, which keeps only the softer "below its published
    minimum" cases.

    They were one block until 2026-08-04 and should not have been. "No
    published approach, and it is not Visual" is a fact with no judgement in it,
    and it now REMOVES the runway from the arrival side; "the reported ceiling
    is under the published minimum" is a proxy for a rule about flight
    visibility, stays hedged, and removes nothing. One heading over two
    different consequences was making the app look like it could not tell them
    apart.

    Three wordings, because the same fact lands differently depending on what is
    left. The old single line - "this app cannot confirm 9 is usable right now" -
    was wrong in the case that matters most: it printed while runway 9 was
    actively assigned for departures, hedging about a runway the app had just
    told the player to use."""
    # Reads the set _minima_caution_notes separated at source (2026-08-04 (2nd round)); this
    # used to intersect minima_flagged with VISUAL_ONLY_RWYS all over again.
    flagged_no_approach = result["minima_no_approach"]
    no_approach = [r for r in (result["arr_rwys"] or []) if r in flagged_no_approach]
    # A runway the scan walked past is not in arr_rwys but still deserves the
    # explanation - it is the one the player would otherwise expect to see.
    for r in dep:
        if r in flagged_no_approach and r not in no_approach:
            no_approach.append(r)
    cat = result["weather"]
    for rwy in no_approach:
        head = (f"RWY {rwy} has no published instrument approach and conditions "
                f"are {cat}, not Visual")
        if rwy in dep and arr:
            note = (f"{head}, so it takes departures only. Arrivals move to RWY "
                    f"{_fmt(arr)}, the next alignment with a usable approach.")
        elif rwy in dep:
            note = (f"{head}. It is the only runway this wind allows, so "
                    "departures still work but no arrival runway is left - real "
                    "ATC improvises here.")
        else:
            note = f"{head}, so it is out of the table below."
        result["no_approach_notes"].append((note, "minima_warn"))
    if no_approach:
        # BY IDENTITY since 2026-08-04 (2nd round), not by prefix. This used to read
        # `t.startswith(f"RWY {r} has NO published")`, so the block above and the
        # sentence in _minima_caution_notes were joined by nothing but a shared
        # guess about how that sentence begins - reword it there, an edit nothing
        # warns you about, and the line would quietly have appeared under BOTH
        # headings. The exact text now comes back from the same function that
        # wrote it, so there is no wording to agree on.
        moved = {flagged_no_approach[r] for r in no_approach}
        result["minima_notes"] = [
            (t, g) for t, g in result["minima_notes"] if t not in moved]


def _build_rwy_table(result, arr, dep, arr_suffix="", dep_suffix=""):
    """Per-runway rows for the section-2 table, built from arr_rwys/dep_rwys -
    the same lists section 1 displays, so the two can never disagree.

    Built PER QUERY, never from a fixed flow->runway map. That is what makes
    runway 27 come out right without a special column: it shows the LAHSO
    limit in SW/Visual and nothing at all in the NW flow, because the row
    reflects what was actually computed for this input.

    A physical strip normally shows once even though it can be active in both
    directions - 4L/22R, 14/32 and 15L/33R only ever run one way at a time, so
    dict.fromkeys() on arr+dep never has both ends of one strip to collapse.
    22R is the one runway that appears TWICE regardless (added 2026-08-05,
    see below): once from this loop for its documented role, once as its own
    row for the non-jet arrival bonus that is deliberately NOT part of arr.

    `arr`/`dep` ARE PASSED IN since 2026-08-04, rather than read off `result`:
    they are the usable-now lists from _usable_now(), not the documented package
    that section 1 prints. A runway the wind has ruled out has no business in a
    table the player reads to decide what to use.
    """

    # The documented prop arrival bonus (SW: 22R) is NOT in arr_rwys - it never
    # was, because it is not part of the configuration, and changing that would
    # change the single source of truth every other step reads. It gets its own
    # row instead (below), built straight from PROP_BONUS_GAME_CATEGORY rather
    # than the arr/dep loop's per-role logic, since it never has a departure
    # side to disagree with.
    # Read from elig, which already suppresses it during the night ban.
    prop_bonus = (result.get("elig") or {}).get("prop_bonus") or []

    lahso_key = (result["flow_key"], result["weather"])
    governs = _package_governs_arrivals(result)
    lahso_excluded = LAHSO_JET_EXCLUSION.get(lahso_key, []) if governs else []
    lahso_cats = LAHSO_GAME_CATEGORY.get(lahso_key, {}) if governs else {}

    rows = []
    for rwy in list(dict.fromkeys(list(arr) + list(dep))):
        in_arr, in_dep = rwy in arr, rwy in dep
        if in_arr and in_dep:
            # No suffix here on purpose: "only"/"(limited)" qualify a whole
            # arrival or departure list, and section 1 still prints them
            # there. Pinning a list-level caveat onto one row would be the
            # same category error this table exists to fix.
            role = "Arr+Dep"
        elif in_arr:
            role = f"Arr {arr_suffix}".strip()
        else:
            role = f"Dep {dep_suffix}".strip()

        # Jet eligibility is per ROLE, and the two roles genuinely disagree on
        # two runways: jets land 4L but may not take off from it (73 dBA), and
        # jets take off from 22R but may not land on it (78 dBA). A single
        # Yes/No would be false on both counts, so a mixed answer says which
        # half is allowed - the same lesson Pendencia 14 taught about letting
        # a binary stand in for a per-category truth.
        jet_arr = in_arr and rwy in JET_ARRIVAL_RWYS and rwy not in lahso_excluded
        jet_dep = in_dep and rwy in JET_DEPARTURE_RWYS
        if in_arr and in_dep:
            jet = {(True, True): "Yes", (False, False): "No",
                   (True, False): "Arr only", (False, True): "Dep only"}[(jet_arr, jet_dep)]
        else:
            jet = "Yes" if (jet_arr or jet_dep) else "No"

        if jet == "Yes":
            reason = None
        elif rwy in lahso_excluded:
            reason = LAHSO_REASON
        else:
            reason = RESTRICTION_REASON.get(rwy)

        # Game category is per ROLE for the same reason the Jet column is, and
        # 15L/33R is the only strip that runs both ways at once (the heading
        # 15/33 overrides) while genuinely answering differently in each: a
        # business jet lands there but cannot depart. Printing the landing
        # breakdown on a row that also departs WAS the Pendencia 15 defect.
        #
        # When the two disagree the cell carries NEITHER answer - it points at
        # the note under the table, which gives both. Putting one half in the
        # cell and then repeating both below duplicates content instead of
        # adding any, and picking a half means picking which way to be wrong at
        # a glance. (22R's non-jet arrival bonus used to be exactly this kind
        # of asterisk, hanging off the "Dep" role cell - it is its own row
        # since 2026-08-05 instead, because unlike 15L/33R it never has a
        # departure-side answer to disagree with in the same row.)
        #
        # The "or" fallback below is only ever reached when BOTH are None
        # (4L, 9, 27 outside LAHSO...): every runway that has letters in
        # one role only - 32 landing, 14 takeoff, 27 under LAHSO - is one-way
        # in that configuration and can never show up here as Arr+Dep.
        cat_arr = lahso_cats.get(rwy) or GAME_CATEGORY_ARR.get(rwy)
        cat_dep = GAME_CATEGORY_DEP.get(rwy)
        cat_split = None
        if in_arr and in_dep:
            if cat_arr and cat_dep and cat_arr != cat_dep:
                category = CATEGORY_SPLIT_CELL
                cat_split = (cat_arr, cat_dep)
            else:
                category = cat_arr or cat_dep
        elif in_arr:
            category = cat_arr
        else:
            category = cat_dep

        rows.append({
            "rwy": rwy,
            "role": role,
            "length": _length_ft(rwy),
            "approach": RUNWAY_APPROACH_TYPE.get(rwy),
            "jet": jet,
            "reason": reason,
            "category": category,
            # Not a column (RWY_TABLE_COLUMNS drives rendering) - it feeds the
            # note under the table.
            "category_split": cat_split,
        })

    # Bonus arrival row(s) - added 2026-08-05. `prop_bonus` (read from
    # result["elig"]) is already filtered to runways still present in `dep`
    # by _eligibility_step, the single place that builds it - see the comment
    # there. No re-filtering here on purpose: two independent filters on the
    # same fact are exactly how a table and a footnote drift apart.
    for rwy in prop_bonus:
        jet_arr = rwy in JET_ARRIVAL_RWYS and rwy not in lahso_excluded
        jet = "Yes" if jet_arr else "No"
        if jet == "Yes":
            reason = None
        elif rwy in lahso_excluded:
            reason = LAHSO_REASON
        else:
            reason = RESTRICTION_REASON.get(rwy)
        rows.append({
            "rwy": rwy,
            "role": "Arr*",
            "length": _length_ft(rwy),
            "approach": RUNWAY_APPROACH_TYPE.get(rwy),
            "jet": jet,
            "reason": reason,
            "category": PROP_BONUS_GAME_CATEGORY.get(rwy),
            "category_split": None,
        })
    return rows


# Column order and headers for the table. Kept next to the builder so a column
# can never be added to one and forgotten in the other.
RWY_TABLE_COLUMNS = [
    ("rwy", "Runway"),
    ("role", "Role"),
    ("length", "Length"),
    ("approach", "Approach"),
    ("jet", "Jet"),
    ("reason", "Reason"),
    ("category", "Game Category"),
]


def _render_rwy_table(rows):
    """(text, tag) lines for the table - plain monospace, so the GUI and the
    selftest print exactly the same thing."""
    if not rows:
        return []
    cells = [[h for _k, h in RWY_TABLE_COLUMNS]]
    for row in rows:
        cells.append([(row[k] if row[k] is not None else "-")
                      for k, _h in RWY_TABLE_COLUMNS])
    widths = [max(len(r[i]) for r in cells) for i in range(len(RWY_TABLE_COLUMNS))]

    def line(values):
        return "  ".join(v.ljust(w) for v, w in zip(values, widths)).rstrip()

    out = [(line(cells[0]), "table_head")]
    out.append(("  ".join("-" * w for w in widths), "muted"))
    for row, values in zip(rows, cells[1:]):
        out.append((line(values), "jet" if row["jet"] == "Yes" else "prop"))
    return out


def _eligibility_step(result, night_block, arr_suffix="", dep_suffix=""):
    """STEP 4 - runway eligibility by aircraft type, FILTERED to the active
    configuration (locked design 2026-07-28). Aircraft type is NOT an input
    (one app run per METAR/hour change, never per aircraft): both lines are
    always produced from result["arr_rwys"]/["dep_rwys"] - the same lists
    that build the section-1 display, so the two sections cannot drift.
    This never changes the configuration computed by Steps 0-3 - it only
    reads it. The former Step 4b (exit-fix) was REMOVED entirely.

    Since 2026-08-03 it also builds the per-runway table (Pendencia 0), from
    those same two lists. The two summary lines stay: they answer "where do
    jets go" at a glance, which reading down a column cannot.

    SINCE 2026-08-04 IT READS _usable_now(), NOT THE RAW LISTS. Everything in
    this section answers "what can I use", so a runway the wind has ruled out
    does not belong in any of it. The summary lines are filtered with the table
    on purpose: leaving them on the raw lists would print "JETS - land: 22L"
    directly above a table with no 22L row, which is the same class of defect
    as Pendencia 14 - two parts of one screen disagreeing about one runway."""
    if result["arr_rwys"] is None:
        # Unknown-wind safety override: nothing was computed, so there is no
        # table to build and no configuration to filter.
        result["elig"] = None
        result["eligibility"].append((NO_CONFIG_MESSAGE, "muted"))
        return

    arr, dep = _usable_now(result)
    _no_approach_step(result, arr, dep)

    if not arr and not dep:
        # Newly reachable in 2026-08-04: the filters can empty both sides at
        # once (0/0 weather with the wind over the caps). Rendering nothing
        # would leave the section header sitting above blank space with the
        # footer pointer still under it, so say it outright.
        result["elig"] = None
        result["eligibility"].append((
            "Nothing in this configuration is usable on this input - see the "
            "cautions above. General runway rules are listed in ALWAYS-ON "
            "RESTRICTIONS below.", "muted"))
        return

    jet_land = [r for r in arr if r in JET_ARRIVAL_RWYS]
    # A jet-capable runway can still be turboprop-only in ONE configuration -
    # see LAHSO_JET_EXCLUSION. Applied after the static filter, never to it.
    lahso_excluded = (
        LAHSO_JET_EXCLUSION.get((result["flow_key"], result["weather"]), [])
        if _package_governs_arrivals(result) else [])
    jet_land = [r for r in jet_land if r not in lahso_excluded]
    jet_dep = [r for r in dep if r in JET_DEPARTURE_RWYS]
    prop_land = list(arr)
    prop_dep = list(dep)
    notes = []

    # The 23:00-06:00 removal of 4L departures / 22R arrivals USED to happen
    # here, on the eligibility lines only. It moved upstream to
    # _apply_night_prohibition on 2026-08-02, so by the time this runs the
    # lists no longer contain them and there is nothing left to strip. Doing
    # it here as well would be dead code.

    # Prop arrival bonus - only where Massport documents one (SW: 22R arr),
    # and never during the night prohibition on 22R landings.
    bonus_txt = ""
    # Guarded with the LAHSO lookups (2026-08-04 (2nd round)): this is an ARRIVAL bonus that
    # Massport documents alongside the Southwest arrival pair, so it has nothing
    # left to attach to once par. 7d reassigns arrivals away from that pair.
    bonus = (PROP_ARRIVAL_BONUS.get(result["flow_key"], [])
             if _package_governs_arrivals(result) else [])
    if bonus:
        if night_block:
            notes.append(
                f"{_fmt(bonus)} arrival bonus (Massport CAC) NOT available "
                "23:00-06:00.")
        else:
            bonus_txt = f" + {_fmt(bonus)} (noise-runway bonus, Massport CAC)"

    # Structured copy of the filtered sets - asserted by the selftest, so a
    # rendering change can never silently hide a filtering bug.
    result["elig"] = {
        "jet_land": jet_land, "jet_dep": jet_dep,
        "prop_land": prop_land, "prop_dep": prop_dep,
        # list(...) since 2026-08-04 (2nd round): this stored the module-level list from
        # PROP_ARRIVAL_BONUS itself, so result["elig"]["prop_bonus"] WAS the
        # constant, not a copy of it. Nothing mutates it today, but every other
        # runway list in this engine is copied on the way in (list(fr["arr"]) and
        # so on) precisely so that a future append cannot reach back into the
        # table it came from.
        #
        # Filtered on `r in dep` since 2026-08-05: _package_governs_arrivals
        # only confirms the SW package as a whole is still valid, not that
        # THIS runway survived the wind filter that already built `dep` (a
        # crosswind can push 22R alone over its cap while 22L/27 stay fine).
        # This is the single place the filter happens - _build_rwy_table's
        # bonus row and the footnote below both read this same field, so
        # they can never show the fact for a runway that is not in the table.
        "prop_bonus": ([r for r in bonus if r in dep] if not night_block
                        else []),
    }

    result["rwy_table"] = _build_rwy_table(
        result, arr, dep, arr_suffix, dep_suffix)

    result["eligibility"].append((
        f"{OFFICIAL} JETS            - land: {_fmt(jet_land)} | "
        f"depart: {_fmt(jet_dep)}", "jet"))
    result["eligibility"].append((
        f"{OFFICIAL} TURBOPROP/LIGHT - land: {_fmt(prop_land)}{bonus_txt} | "
        f"depart: {_fmt(prop_dep)}", "prop"))
    result["eligibility"].append(("", None))
    result["eligibility"].extend(_render_rwy_table(result["rwy_table"]))
    if result["elig"]["prop_bonus"]:
        result["eligibility"].append((
            f"* {_fmt(result['elig']['prop_bonus'])} also takes non-jet "
            "ARRIVALS in this flow - noise-runway bonus (Massport CAC). "
            f"{CORROBORATED}: 0% jet arrivals confirmed by Logan 101 Aug "
            "2016 data and Fly Quiet Report Q1 2019.", "muted"))
    # The other asterisk: a runway whose game categories differ between landing
    # and takeoff (15L/33R in the heading 15/33 overrides). It can never clash
    # with the prop-bonus one above - that bonus only exists in the SW flow
    # (PROP_ARRIVAL_BONUS), and a runway is only ever Arr+Dep like this inside
    # an override, where flow_key is "OVERRIDE" - so a bare "*" stays
    # unambiguous in any single output.
    for row in result["rwy_table"] or []:
        if row.get("category_split"):
            cat_arr, cat_dep = row["category_split"]
            result["eligibility"].append((
                f"* {row['rwy']} game categories differ by role. LANDING: "
                f"{cat_arr}. TAKEOFF: {cat_dep}.", "muted"))
    pref_notes = RUNWAY_PREF_NOTES.get(result["flow_key"], [])
    if pref_notes:
        # Blank line before the block AND between entries (added 2026-08-06,
        # user decision) - back-to-back sentences with no gap read as one
        # run-on paragraph instead of two separate facts.
        result["eligibility"].append(("", None))
        for i, text in enumerate(pref_notes):
            if i:
                result["eligibility"].append(("", None))
            result["eligibility"].append((f"{CORROBORATED} {text}", "pref_note"))
    result["eligibility"].append(("", None))
    for n in notes:
        result["eligibility"].append((f"({n})", "muted"))
    result["eligibility"].append((TABLE_FOOTER_POINTER, "muted"))


# ---------------------------------------------------------------------------
# Rendering - a list of (text, tag) lines shared by the GUI and the selftest.
# Tag names map to colors in the GUI; the selftest prints plain text.
# ---------------------------------------------------------------------------
def render(result):
    lines = []

    def add(text="", tag=None):
        lines.append((text, tag))

    add("=== RUNWAY CONFIGURATION ===", "h1")
    add(f"Flow: {result['flow']}")
    if result["weather"]:
        add(f"Weather category (derived from ceiling/visibility, {OFFICIAL} BOS "
            "thresholds): " + result["weather"])
    add()
    add(f"Arrivals:   {result['arrivals']}", "config")
    if result["arrival_note"]:
        add(f"  -> {result['arrival_note']}")
    add(f"Departures: {result['departures']}", "config")
    add()

    # Wind check moved here 2026-08-03 (was printed after section 2). It is the
    # input that PRODUCED the configuration above - the reasoning section even
    # narrates "wind from X deg -> Y flow" - not a note about eligibility, and
    # printing it last meant the CAUTION below fired before the reader ever saw
    # the numbers behind it. Muted, because next to the arrival/departure lines
    # it is context, not the answer.
    if result["wind_readout"]:
        add(f"Wind check: {result['wind_readout']}", "muted")
        add()

    # REASONING moved here 2026-08-03 (was printed after section 2, near the
    # bottom). It explains WHY the configuration above was chosen - reading
    # the CAUTION blocks below before ever seeing that explanation was
    # confusing (found by the user reading a real scenario where an
    # [APP SIMPLIFICATION] wind default preceded its own justification by
    # three sections). Same reasoning that already moved the wind readout
    # here on the same day.
    if result["reasons"]:
        add("=== REASONING ===", "h1")
        for text, tag in result["reasons"]:
            add(f"  - {text}", tag)
        add()

    if result["wind_notes"]:
        add("=== CAUTION: WIND OVER THE FAA 8400.9 RUNWAY-USE LIMITS ===", "wind_warn")
        for text, tag in result["wind_notes"]:
            add(f"  - {text}", tag)
        # This explanation only makes sense against a per-runway breakdown -
        # it says "the better-aligned runway is normally already listed
        # above," which is only true when there IS a per-runway list above.
        # The unknown-direction path (added 2026-08-03) prints one sentence
        # instead, has no such list, and leaves wind_flagged empty on purpose
        # (see _wind_limit_notes) - that emptiness is the signal used here to
        # skip a paragraph that would otherwise reference a list that isn't
        # there. Caught by the user reading the live output, not by the
        # selftest.
        if (result["wind_flagged"] and not result["role_fill"]
                and not result["override"]):
            # REWRITTEN 2026-08-04. The old paragraph ended "the app does not
            # switch configuration: checked across every wind direction, there
            # is no case at KBOS where another package works when the active one
            # does not" - which the same round proved false twice over. It now
            # only prints where it is still true: a side that kept a documented
            # runway. Where a side WAS reassigned, the sentence appended by
            # _apply_role_fill says so instead, and this would contradict it.
            add("  These limits bound a noise-preferential runway assignment (Order "
                "8400.9 par. 7d). Past them the wind outranks the noise preference, "
                "but this side of the configuration still has a documented runway "
                "within the limits, so nothing was reassigned.",
                "muted")
        add()

    if result["no_approach_notes"]:
        # Its own heading since 2026-08-04: this one is a hard fact and it
        # removes the runway from arrivals, unlike the hedged block below, which
        # removes nothing. See _no_approach_step.
        add("=== CAUTION: NO APPROACH AVAILABLE ===", "minima_warn")
        for text, tag in result["no_approach_notes"]:
            add(f"  {text}", tag)
        add()

    if result["minima_notes"]:
        add("=== CAUTION: POSSIBLY BELOW PUBLISHED APPROACH MINIMA ===", "minima_warn")
        for text, tag in result["minima_notes"]:
            add(f"  - {text}", tag)
        add("  This app picks a runway from wind/noise/flow rules only - it does not "
            "confirm the airport is actually operating in these conditions. Apply your "
            "own judgement; see the app manual for the minima on file per runway.",
            "muted")
        add()

    if result["eligibility"]:
        add("=== RUNWAY ELIGIBILITY ===", "h1")
        for text, tag in result["eligibility"]:
            add(f"  {text}" if text else "", tag)
        add()

    if result["night_notes"]:
        add("=== NIGHT RULES ACTIVE ===", "h1")
        for text, tag in result["night_notes"]:
            add(f"  - {text}", tag)
        add()

    add("=== ALWAYS-ON RESTRICTIONS ===", "h1")
    # A blank line between entries, not just after the block (added 2026-08-03,
    # Pendencia 6): color alone did not separate ten back-to-back paragraphs of
    # running text - confirmed once the user had actually read a day's worth of
    # output, not a hypothesis going in. Between entries only, so it reads as
    # ten distinct items rather than N-1 gaps plus one at the end.
    for i, (tag, label, confidence, text) in enumerate(ALWAYS_ON):
        if i:
            add()
        add(f"  [{label}] {confidence} {text}", tag)
    add()

    # PROCEDURE dropped from the category list 2026-08-04 (2nd round). The only entry that
    # ever carried it was the "maximum 210 kt until 520 ft MSL" line, removed on
    # 2026-08-03 because the game takes the aircraft after takeoff and the player
    # can do nothing with it. The category outlived its content by two days,
    # which is precisely the orphan-legend defect this project treats as real:
    # every tag in a legend must appear somewhere in the content.
    add("Tags: [OFFICIAL] FAA/Massport document | [CORROBORATED] multiple sources "
        "agree | [SIM-ONLY] virtual-ATC training document only | "
        "[APP DESIGN] engineering choice, no source. Restriction "
        "categories: NOISE/TIME, PHYSICAL & LEGAL, AIRCRAFT CLASS.",
        "muted")
    add()
    add("Simulation use only (Tower!Simulator 3, VATSIM, IVAO) - not a real "
        "operational reference. Rule set v2 pending community validation.", "muted")
    return lines


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------
HEADER_BG = "#0A3161"  # navy, same as the rules PDF sent to the community

TEXT_TAG_COLORS = {
    "h1": {"foreground": "#0A3161", "font": ("Consolas", 10, "bold")},
    "config": {"font": ("Consolas", 10, "bold")},
    "official": {"foreground": "#1E7A42"},
    "corroborated": {"foreground": "#2B5FA5"},
    "simonly": {"foreground": "#9C6B08"},
    # "guess" removed 2026-08-04 (2nd round). It outlived the [GUESS] confidence tag retired
    # on 2026-07-31 by being quietly reused as the colour of the one error message
    # the GUI had; the input validation rewritten today uses "minima_warn" like
    # every other red block, so nothing referenced it any more. Caught while
    # removing rt_proc for the same reason - a repurposed orphan is still an
    # orphan, and it made the legend's colour vocabulary mean two things.
    "simplification": {"foreground": "#5B5568"},
    "muted": {"foreground": "#777777"},
    "rt_noise": {"foreground": "#A0450F"},
    "rt_legal": {"foreground": "#2E3F80"},
    "rt_class": {"foreground": "#7A2E63"},
    # "rt_proc" (PROCEDURE) removed 2026-08-04 (2nd round) together with the category itself -
    # its last entry went on 2026-08-03 and the colour had been sitting here with
    # nothing to paint. Same rule as the [GUESS] tag retired on 2026-07-31.
    "table_head": {"foreground": "#0A3161", "font": ("Consolas", 10, "bold")},
    "jet": {"foreground": "#4A148C", "font": ("Consolas", 10, "bold")},
    "prop": {"foreground": "#00695C", "font": ("Consolas", 10, "bold")},
    "minima_warn": {"foreground": "#B00020", "font": ("Consolas", 10, "bold")},
    "wind_warn": {"foreground": "#B45309", "font": ("Consolas", 10, "bold")},
    # Added 2026-08-05 (SS28.1) for the 5 runway-preference footnotes. A new
    # color on purpose - it was chosen only after several yellow/gold families
    # failed WCAG contrast on white (or read too close to "simonly"), and a
    # magenta/wine pair risked being read as "minima_warn". #0E7C86 (teal)
    # does not collide with any existing tag's meaning.
    "pref_note": {"foreground": "#0E7C86"},
}


def _icon_path():
    """Ships next to the .py/.exe (essentials\\), same convention as the
    selftest log and the rules PDF - not a PyInstaller --add-data resource.
    Same sys.frozen check as _selftest_output_path: __file__ points into the
    temp extraction dir when frozen, so sys.executable is used instead."""
    if getattr(sys, "frozen", False):
        app_dir = os.path.dirname(sys.executable)
    else:
        app_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(app_dir, "kbos_icon.ico")


class RunwayAdvisorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_TITLE} v{APP_VERSION}")
        icon_path = _icon_path()
        if os.path.isfile(icon_path):
            try:
                self.iconbitmap(icon_path)
            except tk.TclError:
                pass
        self.geometry("860x900")
        # Resizable since 2026-08-03: the per-runway table is the widest thing
        # the app prints, and while it does fit 860px, a player who wants the
        # whole Game Category column on one line can now just widen the window.
        # minsize keeps the layout from being squeezed below what it needs.
        self.resizable(True, True)
        self.minsize(860, 600)
        self.mono_font = tkfont.Font(family="Consolas", size=10)

        self._build_header()
        self._build_inputs()
        self._build_output()
        self._build_footer()

    def _build_header(self):
        header = tk.Frame(self, bg=HEADER_BG)
        header.pack(fill="x")
        tk.Label(
            header, text="KBOS Runway Advisor - Boston Logan International",
            bg=HEADER_BG, fg="white", font=("Segoe UI", 16, "bold"), pady=12,
        ).pack()

    def _build_inputs(self):
        frame = ttk.LabelFrame(
            self,
            text="Time, wind, weather, surface",
            padding=12,
        )
        frame.pack(fill="x", padx=12, pady=6)

        ttk.Label(frame, text="Local time (HH:MM):").grid(row=0, column=0, sticky="w", pady=3)
        self.time_var = tk.StringVar(value="14:30")
        ttk.Entry(frame, textvariable=self.time_var, width=10).grid(row=0, column=1, sticky="w")

        ttk.Label(frame, text="Wind direction (deg, FROM) - blank = variable/unknown:").grid(
            row=1, column=0, sticky="w", pady=3)
        self.wind_dir_var = tk.StringVar(value="40")
        ttk.Entry(frame, textvariable=self.wind_dir_var, width=10).grid(row=1, column=1, sticky="w")

        ttk.Label(frame, text="Wind speed (kt):").grid(row=2, column=0, sticky="w", pady=3)
        self.wind_speed_var = tk.StringVar(value="8")
        ttk.Entry(frame, textvariable=self.wind_speed_var, width=10).grid(row=2, column=1, sticky="w")

        ttk.Label(frame, text="Gust (kt) - blank = no gust:").grid(row=3, column=0, sticky="w", pady=3)
        self.gust_var = tk.StringVar(value="")
        ttk.Entry(frame, textvariable=self.gust_var, width=10).grid(row=3, column=1, sticky="w")

        ttk.Label(frame, text="Ceiling (ft) - blank = not a factor:").grid(row=1, column=2, sticky="w", padx=(24, 0))
        self.ceiling_var = tk.StringVar(value="")
        ttk.Entry(frame, textvariable=self.ceiling_var, width=10).grid(row=1, column=3, sticky="w")

        ttk.Label(frame, text="Visibility (SM) - blank = not a factor:").grid(row=2, column=2, sticky="w", padx=(24, 0))
        self.visibility_var = tk.StringVar(value="")
        ttk.Entry(frame, textvariable=self.visibility_var, width=10).grid(row=2, column=3, sticky="w")

        ttk.Label(frame, text="Runway condition:").grid(row=3, column=2, sticky="w", padx=(24, 0))
        self.condition_var = tk.StringVar(value="Dry")
        ttk.Combobox(
            frame, textvariable=self.condition_var, state="readonly", width=13,
            values=["Dry", "Wet", "Contaminated"],
        ).grid(row=3, column=3, sticky="w")

        ttk.Label(frame, text="Braking action:").grid(row=4, column=2, sticky="w", padx=(24, 0))
        self.braking_var = tk.StringVar(value="Good")
        ttk.Combobox(
            frame, textvariable=self.braking_var, state="readonly", width=13,
            values=["Good", "Fair", "Poor", "Nil"],
        ).grid(row=4, column=3, sticky="w")

        self.ts_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            frame,
            text="Thunderstorm in METAR (TS/TSRA present-weather group)",
            variable=self.ts_var,
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(6, 0))

        ttk.Button(self, text="Evaluate", command=self.on_evaluate).pack(pady=8)

    def _build_output(self):
        frame = ttk.LabelFrame(self, text="Result", padding=12)
        frame.pack(fill="both", expand=True, padx=12, pady=6)
        self.output = tk.Text(frame, wrap="word", font=self.mono_font, height=24)
        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.output.yview)
        self.output.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.output.pack(side="left", fill="both", expand=True)
        for tag, cfg in TEXT_TAG_COLORS.items():
            self.output.tag_configure(tag, **cfg)
        self.output.configure(state="disabled")

    def _build_footer(self):
        tk.Label(
            self,
            text=("Sources: FAA Capacity Profile BOS 2019, FAA Order 8400.9 (1981), "
                  "JO 7110.65/AIM 4-3-6, Chart Supplement + SID charts, FAA IAP index, "
                  "740 CMR 24, Boeing noise DB, Massport CAC + Fly Quiet Report, "
                  "vZBW SOP 2014. Per-rule sourcing: see the app manual. "
                  "Simulation use only."),
            font=("Segoe UI", 7), fg="#888888", wraplength=820, justify="center",
        ).pack(pady=4)

    # INPUT VALIDATION REWRITTEN 2026-08-04 (2nd round). Until then a blank field and a field
    # with rubbish in it produced the SAME answer - None - and None means "not a
    # factor", which is the most permissive reading the engine has. So a typo in
    # Ceiling silently became clear skies, a typo in Visibility became unlimited,
    # and a typo in Wind speed became 0.0, i.e. calm, which also decides the flow.
    # The app answered confidently and never said it had thrown the entry away.
    # Only the time field had ever been validated, and it did so with an `assert`,
    # which `python -O` removes.
    #
    # Every field is now checked and every problem is reported at once, so the
    # player fixes the whole form in one pass instead of one field per click.
    def _parse_float(self, text):
        """(value, ok). ok=False means the field holds something that is not a
        number. value=None with ok=True means it was left blank, which the engine
        reads as "not a factor" - the one case where None is a real answer."""
        text = text.strip()
        if not text:
            return None, True
        try:
            return float(text.replace(",", ".")), True
        except ValueError:
            return None, False

    def _read_number(self, var, label, errors, lo, hi, required=False):
        raw = var.get().strip()
        value, ok = self._parse_float(raw)
        if not ok:
            errors.append(f"{label}: \"{raw}\" is not a number.")
            return None
        if value is None:
            if required:
                errors.append(f"{label}: required - this one has no "
                              "\"not a factor\" reading.")
            return None
        if not lo <= value <= hi:
            errors.append(f"{label}: {value:g} is outside the accepted range "
                          f"{lo:g}-{hi:g}.")
            return None
        return value

    def _read_time(self, errors):
        raw = self.time_var.get().strip()
        parts = raw.split(":")
        if len(parts) != 2 or not all(p.strip().isdigit() for p in parts):
            errors.append(f"Local time: \"{raw}\" is not HH:MM (e.g. 14:30).")
            return None, None
        hour, minute = int(parts[0]), int(parts[1])
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            errors.append(f"Local time: {hour:02d}:{minute:02d} is not a real "
                          "time of day.")
            return None, None
        return hour, minute

    def on_evaluate(self):
        errors = []
        hour, minute = self._read_time(errors)
        # 360 is accepted as well as 0: a METAR reports north as 360.
        wind_dir = self._read_number(
            self.wind_dir_var, "Wind direction", errors, 0, 360)
        # Required: blank wind speed used to become 0.0, which is not "unknown",
        # it is a positive claim of calm - and calm picks the flow on its own.
        wind_speed = self._read_number(
            self.wind_speed_var, "Wind speed", errors, 0, 250, required=True)
        gust = self._read_number(self.gust_var, "Gust", errors, 0, 250)
        ceiling = self._read_number(self.ceiling_var, "Ceiling", errors, 0, 99999)
        visibility = self._read_number(
            self.visibility_var, "Visibility", errors, 0, 99)
        # Contradictory rather than out of range, so it is checked separately: a
        # gust is by definition above the wind it gusts from, and eff_speed would
        # quietly discard the smaller number without a word.
        if gust is not None and wind_speed is not None and gust < wind_speed:
            errors.append(f"Gust: {gust:g} kt is below the {wind_speed:g} kt wind "
                          "speed - a gust is the peak, not a separate wind.")
        if errors:
            lines = [("Nothing was evaluated - fix the input first:", "minima_warn"),
                     ("", None)]
            lines += [(f"  - {e}", "minima_warn") for e in errors]
            lines += [("", None),
                      ("A blank field means \"not a factor\" and is fine; text "
                       "that is not a number is not the same thing, so the app "
                       "will not guess which you meant.", "muted")]
            self._write(lines)
            return

        result = evaluate(
            hour, minute, wind_dir, wind_speed, gust, ceiling, visibility,
            self.condition_var.get(), self.braking_var.get(), self.ts_var.get(),
        )
        self._write(render(result))

    def _write(self, lines):
        self.output.configure(state="normal")
        self.output.delete("1.0", tk.END)
        for text, tag in lines:
            if tag:
                self.output.insert(tk.END, text + "\n", tag)
            else:
                self.output.insert(tk.END, text + "\n")
        self.output.configure(state="disabled")


# ---------------------------------------------------------------------------
# Selftest with ASSERTIONS - covers every one of the 12 configuration
# families the deterministic engine can produce (enumerated in
# KBOS_achados.md), plus night/gust/edge variants. Exit code != 0 on any
# failure. ALWAYS run before building the executable:
#   python kbos_runway_advisor.py --selftest            (compact PASS/FAIL)
#   python kbos_runway_advisor.py --selftest --verbose  (full rendered output)
#
# Each scenario: (name, inputs..., expect) where expect asserts any of:
# flow_key, weather, arr, dep, jet_land, jet_dep, prop_land, prop_dep,
# prop_bonus, elig_fallback.
# ---------------------------------------------------------------------------
SELFTEST_SCENARIOS = [
    # F1 - NE Visual
    ("F1 NE Visual", 14, 30, 40, 8, None, None, None, "Dry", "Good", False,
     {"flow_key": "NE", "weather": "Visual", "arr": ["4L", "4R"],
      "dep": ["9", "4L", "4R"], "jet_land": ["4L", "4R"], "jet_dep": ["9", "4R"],
      "prop_land": ["4L", "4R"], "prop_dep": ["9", "4L", "4R"], "prop_bonus": []}),
    # F2 - NE Marginal
    ("F2 NE Marginal", 14, 30, 40, 8, None, 2000, 5, "Dry", "Good", False,
     {"flow_key": "NE", "weather": "Marginal", "arr": ["4R"],
      "dep": ["9", "4L", "4R"], "jet_land": ["4R"], "jet_dep": ["9", "4R"]}),
    # F3 - NE Instrument
    ("F3 NE Instrument", 14, 30, 40, 8, None, 800, 2, "Dry", "Good", False,
     {"flow_key": "NE", "weather": "Instrument", "arr": ["4R"],
      "jet_land": ["4R"]}),
    # F4 - SW Visual (prop bonus 22R). CORRECTED 2026-08-02 (Pendencia 14):
    # jet_land used to assert ["22L", "27"], which fixed the bug as expected
    # behaviour - the LAHSO on this config is turboprop-only on 27, so the jet
    # line must NOT list it. See LAHSO_JET_EXCLUSION.
    ("F4 SW Visual", 14, 30, 220, 10, None, None, None, "Dry", "Good", False,
     {"flow_key": "SW", "weather": "Visual", "arr": ["22L", "27"],
      "dep": ["22L", "22R"], "jet_land": ["22L"], "jet_dep": ["22L", "22R"],
      "prop_bonus": ["22R"], "prop_land": ["22L", "27"]}),
    # F5 - SW Marginal. jet_land asserted here on purpose (added 2026-08-02):
    # it is the SAME runway pair as F4, and the exclusion must NOT fire, because
    # Marginal spaces two full-length instrument approaches 2.5 NM apart with no
    # hold-short point. This is the guard against over-applying the F4 fix.
    ("F5 SW Marginal", 14, 30, 220, 10, None, 2000, 5, "Dry", "Good", False,
     {"flow_key": "SW", "weather": "Marginal", "arr": ["22L", "27"],
      "dep": ["22L", "22R"], "jet_land": ["22L", "27"]}),
    # F6 - SW Instrument
    ("F6 SW Instrument", 14, 30, 220, 15, None, 800, 2, "Dry", "Good", False,
     {"flow_key": "SW", "weather": "Instrument", "arr": ["22L"], "dep": ["22R"],
      "jet_land": ["22L"], "jet_dep": ["22R"], "prop_bonus": ["22R"]}),
    # F7 - NW Visual. CORRECTED 2026-08-02: the package now carries all four
    # arrival runways Massport documents. The jet line gains 33L (10,083 ft,
    # ILS CAT III - a full jet runway); 32 and 33R stay off it, each for its
    # own reason (32 by runway size, 33R labelled "Non-Jet" by Massport), and
    # the per-category detail for both lives in the always-on restrictions.
    # See ACHADO 12/14 and the 2026-08-02 section of KBOS_achados.md.
    ("F7 NW Visual (jets land 27 + 33L)", 14, 30, 300, 10,
     None, None, None, "Dry", "Good", False,
     {"flow_key": "NW", "weather": "Visual", "arr": ["27", "32", "33L", "33R"],
      "dep": ["33L", "27"], "jet_land": ["27", "33L"], "jet_dep": ["33L", "27"],
      "prop_land": ["27", "32", "33L", "33R"]}),
    # F8 - NW Marginal. Two rules under test at once:
    #  - runway 32 is NOT dropped below Visual (revised 2026-07-31): its
    #    published minimum is 801 ft / 1.0 SM and the whole Marginal band sits
    #    above that. This regresses if the old GUESS rule ever comes back.
    #  - 33R IS flagged (new 2026-08-02): it has no published instrument
    #    approach at all, so any category below Visual triggers the caution.
    #    That is the price of carrying it in the package, and it is correct.
    # UPDATED 2026-08-04: `arr` still holds all four - the package is what
    # Massport documents and section 1 goes on printing it - but prop_land now
    # drops 33R, because the eligibility lines answer "what can I use" and 33R
    # has no approach to use in Marginal weather. The two assertions sitting
    # side by side here are the whole point of the split: the documented
    # package and the usable-now subset are different questions with different
    # answers, and this scenario now pins both.
    ("F8 NW Marginal keeps all four, 33R not usable", 14, 30, 300, 12, None, 2500, 5,
     "Dry", "Good", False,
     {"flow_key": "NW", "weather": "Marginal", "arr": ["27", "32", "33L", "33R"],
      "dep": ["33L", "27"], "jet_land": ["27", "33L"],
      "prop_land": ["27", "32", "33L"], "minima_flagged": {"33R"}}),
    # F8b - NW Instrument at 600 ft: the band where the arrival runways
    # genuinely differ. 27 (443 ft / 1.5 SM) and 33L (200 ft / 0.5 SM) still
    # clear; 32 (801 ft / 1.0 SM) does not, and 33R has no approach at all.
    # The configuration is unchanged - the caution names the two that fail.
    ("F8b NW Instrument 600 ft flags 32 and 33R", 14, 30, 300, 12, None, 600, 2,
     "Dry", "Good", False,
     {"flow_key": "NW", "weather": "Instrument",
      "arr": ["27", "32", "33L", "33R"],
      "dep": ["33L", "27"], "minima_flagged": {"32", "33R"}}),
    # F9 - SE: jets depart 9 only (14 light), land 15R only (15L light).
    # WIND CHANGED 2026-08-05 (Pendencia Nova C) from 150/10 to 125/25: the old
    # wind cleared the new NE/SW fallback test (crosswind 9.1 kt on both
    # primaries, well under the 20-kt cap), so with the fallback in place it no
    # longer reaches SE at all - it would have silently started asserting a
    # flow the fallback overrides. 125/25 sits at the crosswind-limit end of
    # the SE quadrant (25 kt on both NE's and SW's primary, since their
    # headings are exactly opposite and share the same crosswind), which is
    # the case the fallback is meant to leave alone. Verified by hand (same
    # formulas the engine uses) that none of the SE package's own four
    # runways (9/14/15R/15L) get pushed over their own limits at this wind, so
    # the expected eligibility below is unchanged from the old scenario.
    ("F9 SE Visual (survives NE/SW fallback)", 14, 0, 125, 25, None, None, None,
     "Dry", "Good", False,
     {"flow_key": "SE", "weather": "Visual", "arr": ["15R", "15L"],
      "dep": ["9", "14"], "jet_land": ["15R"], "jet_dep": ["9"],
      "prop_land": ["15R", "15L"], "prop_dep": ["9", "14"]}),
    # F9b - Pendencia Nova C fallback, NE side. 121 deg is the real median wind
    # direction found among the 154 baseline-buggy SE hours in the 35-day
    # simulation (simulacao_estatistica/03_kbos_sim_35dias_IEM_FINAL.py) - at
    # 8 kt neither NE's nor SW's primary is anywhere near its limit (tailwind
    # +-0.6 kt, crosswind 8.0 kt on both, since the two primaries are exactly
    # opposite headings), so NE wins on the "checked first" rule with no real
    # tiebreak needed. Same eligibility as F1 (NE Visual) - the fallback
    # reuses the ordinary NE branch once flow is reassigned.
    ("F9b SE quadrant falls back to NE", 14, 0, 121, 8, None, None, None,
     "Dry", "Good", False,
     {"flow_key": "NE", "weather": "Visual", "arr": ["4L", "4R"],
      "dep": ["9", "4L", "4R"], "jet_land": ["4L", "4R"], "jet_dep": ["9", "4R"],
      "prop_land": ["4L", "4R"], "prop_dep": ["9", "4L", "4R"]}),
    # F9c - Pendencia Nova C fallback, SW side (mirrors F9b near the other edge
    # of the SE quadrant, close to 180 deg). At 175/8, NE's primary fails on
    # tailwind alone (6.1 kt > the 5-kt dry limit) while SW's clears (tailwind
    # -6.1 kt, a headwind), so this is the one case where the "NE first" order
    # actually matters rather than being a tie. Same eligibility as F4 (SW
    # Visual).
    ("F9c SE quadrant falls back to SW", 14, 0, 175, 8, None, None, None,
     "Dry", "Good", False,
     {"flow_key": "SW", "weather": "Visual", "arr": ["22L", "27"],
      "dep": ["22L", "22R"], "jet_land": ["22L"], "jet_dep": ["22L", "22R"],
      "prop_bonus": ["22R"], "prop_land": ["22L", "27"]}),
    # F10 - night head-to-head. WIND CHANGED 2026-08-04 from 330/6 to 060/12,
    # and the reason is the whole point of the par. 7d departure-end fix: a
    # headwind on 33L is by definition a tailwind on the 15R it departs from,
    # so ANY wind down the strip above 5 kt now refuses the config. What keeps
    # the head-to-head alive is wind ACROSS the strip - 060 is perpendicular to
    # 330, giving 0.0 kt on both ends and 12 kt of crosswind, well inside the
    # 20-kt cap. 12 rather than 15 on purpose: at 15 the crosswind lands exactly
    # on the 15-kt slippery cap, and a boundary value is a fragile thing to pin
    # a regression test to. The old 330/6 wind now lives in F10c, which locks
    # the refusal.
    ("F10 Night head-to-head", 2, 0, 60, 12, None, None, None, "Dry", "Good", False,
     {"flow_key": "H2H", "arr": ["33L"], "dep": ["15R"],
      "jet_land": ["33L"], "jet_dep": ["15R"], "wind_flagged": set()}),
    # F10c - the departure-end check itself (added 2026-08-04). 330/6 is a
    # 6-kt HEADWIND on 33L, which the old build accepted happily - and a 6-kt
    # tailwind on 15R, over the 5-kt cap. Par. 7d(1)(c) names takeoffs
    # explicitly, so the noise preference cannot govern here and the app falls
    # through to the normal flow. This is the exact scenario F10 used to assert
    # the OPPOSITE of.
    ("F10c Night h2h refused by the 15R departure tailwind -> NW", 2, 0, 330, 6,
     None, None, None, "Dry", "Good", False,
     {"flow_key": "NW", "arr": ["27", "32", "33L", "33R"], "dep": ["33L", "27"],
      "wind_flagged": set()}),
    # F10b - night, tailwind on 33 too high -> falls through to SE flow.
    # SPEED CHANGED 2026-08-05 (Pendencia Nova C) from 10 to 23 kt: at 10 kt
    # the new NE/SW fallback overrides SE (same reason as the old F9), which
    # would have hidden the h2h-refusal path this scenario exists to cover.
    # 23 kt keeps this a genuine SE case - crosswind 20.9 kt on both NE's and
    # SW's primary (over the 20-kt cap), verified by hand - while still
    # failing the h2h tailwind test (33's tailwind only grows with speed).
    ("F10b Night h2h refused -> SE", 2, 0, 150, 23, None, None, None,
     "Dry", "Good", False,
     {"flow_key": "SE", "arr": ["15R", "15L"]}),
    # F10e - the head-to-head window ENDS at 05:00 (Massport's own "Midnight
    # to 5AM" metric, Fly Quiet Report 2017). At 05:30 the 23:00-06:00 noise
    # prohibition is still running but the h2h config is not, so the engine
    # must fall through to the normal wind logic. Returned H2H under the old
    # 00:00-06:00 window - this is the regression guard for decision 6.
    # RENAMED F10c -> F10e on 2026-08-04 (2nd round): the scenario added on 2026-08-04 for the
    # 15R departure-end check took the name F10c, which this one already had, and
    # the shipped selftest log went out with two [PASS] F10c lines.
    ("F10e Night window ends 05:00 -> NW", 5, 30, 330, 6, None, None, None,
     "Dry", "Good", False,
     {"flow_key": "NW", "arr": ["27", "32", "33L", "33R"],
      "dep": ["33L", "27"]}),
    # F10d - crosswind guard on the head-to-head branch. Wind 060/25 puts a
    # 0-kt tailwind on runway 33 (it passes the tailwind test) but a 25-kt
    # crosswind, over the 20-kt dry cap of FAA Order 8400.9. Safety outranks
    # the noise preference, so h2h must be refused. Returned H2H before the
    # 2026-08-01 fix, when the branch tested tailwind only.
    ("F10d Night h2h refused on crosswind -> NE", 2, 0, 60, 25, None, None,
     None, "Dry", "Good", False,
     {"flow_key": "NE", "arr": ["4L", "4R"]}),
    # F11 - safety override, known wind (braking Fair, wind 090). The scan's
    # best alignment is runway 9 and the DEPARTURE side takes it; arrivals do
    # not, in any weather, because no KBOS configuration lands there
    # (DOCUMENTED_ARRIVAL_RWYS). CHANGED 2026-08-04 (8th round) from
    # arr/jet_land ["9"]: this scenario asserted the defect as correct, on a
    # Visual day, which is exactly where the old minima-based guard did nothing.
    ("F11 Override braking Fair", 12, 0, 90, 25, None, None, None,
     "Wet", "Fair", False,
     {"flow_key": "OVERRIDE", "arr": ["4L", "4R"], "dep": ["9"],
      "jet_land": ["4L", "4R"], "jet_dep": ["9"]}),
    # F11b - override + night: heading 22 expands to 22L/22R, then the night
    # ban takes 22R OUT OF THE ARRIVAL CONFIGURATION ITSELF (not just off the
    # eligibility line). CHANGED 2026-08-02 by the night-awareness fix: this
    # asserted arr ["22L","22R"] before, and it is the scenario that proves
    # the removal now reaches the primary answer. Departures keep both - only
    # 4L takeoffs and 22R LANDINGS are banned, so 22R may still depart.
    ("F11b Override TS at night (rwy 22)", 23, 30, 200, 18, None, None, None,
     "Dry", "Good", True,
     {"flow_key": "OVERRIDE", "arr": ["22L"], "dep": ["22L", "22R"],
      "jet_land": ["22L"], "prop_land": ["22L"], "prop_dep": ["22L", "22R"]}),
    # F11c - the same night override, but in Marginal weather. Guards the
    # side effect the night fix has on the minima caution: 22R has no
    # published instrument approach, so while it was still in the arrival list
    # this scenario flagged it. With 22R removed as prohibited, the caution
    # must be SILENT - warning about a runway nobody may use would be noise.
    ("F11c Override at night, Marginal - no 22R minima caution", 23, 30, 200,
     18, None, 2000, 5, "Dry", "Good", True,
     {"flow_key": "OVERRIDE", "weather": "Marginal", "arr": ["22L"],
      "dep": ["22L", "22R"], "minima_flagged": set()}),
    # F12 - override with unknown wind: eligibility falls back to general text
    ("F12 Override, variable wind", 15, 0, None, 12, None, None, None,
     "Wet", "Poor", False,
     {"flow_key": "OVERRIDE", "elig_fallback": True}),
    # Night NE at 23:30: departures lose 4L, arrivals KEEP 4L (only takeoffs
    # are banned there, landings are fine). The `dep` assertion was ADDED
    # 2026-08-02 - without it this scenario never tested the very thing its
    # name promises, since it only checked the eligibility lines.
    ("Night NE 23:30 (4L dep blocked)", 23, 30, 40, 10, None, None, None,
     "Dry", "Good", False,
     {"flow_key": "NE", "arr": ["4L", "4R"], "dep": ["9", "4R"],
      "prop_dep": ["9", "4R"], "prop_land": ["4L", "4R"],
      "jet_dep": ["9", "4R"]}),
    # Night SW at 23:30: 22R prop arrival bonus suppressed
    ("Night SW 23:30 (bonus suppressed)", 23, 30, 220, 10, None, None, None,
     "Dry", "Good", False,
     {"flow_key": "SW", "prop_bonus": [], "prop_land": ["22L", "27"]}),
    # Calm and variable winds default to NE
    ("Calm 2 kt -> NE", 10, 0, 270, 2, None, None, None, "Dry", "Good", False,
     {"flow_key": "NE", "arr": ["4L", "4R"]}),
    ("Variable 12 kt -> NE", 10, 0, None, 12, None, None, None, "Dry", "Good", False,
     {"flow_key": "NE"}),
    # Gust included in limits (NW visual, crosswind CAUTION expected in text)
    ("Gust over crosswind limit (NW)", 14, 0, 350, 15, 25, None, None,
     "Dry", "Good", False,
     {"flow_key": "NW", "weather": "Visual",
      "arr": ["27", "32", "33L", "33R"]}),

    # --- Minima caution (added 2026-07-28, from 19 real IAP charts) ---
    # The original bug report: 0/0 fog + TS + Poor braking -> override picked
    # heading 33 (33L+33R) purely by wind, with no weather check at all, and
    # the minima caution then said both were unusable.
    # REWRITTEN 2026-08-04: the check moved UPSTREAM of the choice. The scan is
    # now per role and will not hand the arrival side a runway that cannot
    # receive, so at 0 ft / 0 SM - where nothing on the field clears any
    # published minimum - it returns NO arrival runway rather than naming two
    # and warning about them afterwards. minima_flagged is empty on purpose:
    # ten identical per-runway cautions would be noise, so one summary sentence
    # replaces them (asserted below by minima_notes_count, not by its wording).
    # The departure side is untouched, because a takeoff needs no approach -
    # which is the asymmetry this whole round is built on.
    ("Minima: 0/0 override - nothing can receive, departures unaffected",
     5, 50, 0, 12, 36, 0, 0, "Wet", "Poor", True,
     {"flow_key": "OVERRIDE", "arr": [], "dep": ["33L", "33R"],
      "minima_flagged": set(), "minima_notes_count": 1}),
    # Same wind/override trigger, but good weather - must NOT flag anything.
    ("Minima: override, good weather -> no caution", 5, 50, 0, 12, 36, 3000, 5,
     "Wet", "Poor", True,
     {"flow_key": "OVERRIDE", "arr": ["33L", "33R"], "minima_flagged": set()}),
    # Normal (non-override) flow: NE + Instrument collapses to 4R only, but
    # conditions are below even 4R's general minimum (200ft/0.5SM) - special
    # cert (CAT III, RVR 600) is the only real answer here. Must flag 4R.
    ("Minima: NE Instrument below 4R's general minimum", 14, 30, 40, 8, None,
     100, 0.1, "Dry", "Good", False,
     {"flow_key": "NE", "weather": "Instrument", "arr": ["4R"],
      "minima_flagged": {"4R"}}),
    # Same flow/weather category, conditions clear the general minimum -
    # must NOT flag (this is the existing F3 scenario's territory: 800ft/2SM
    # clears 4R's 200ft/0.5SM easily).
    ("Minima: NE Instrument, conditions clear 4R -> no caution", 14, 30, 40, 8,
     None, 800, 2, "Dry", "Good", False,
     {"flow_key": "NE", "weather": "Instrument", "arr": ["4R"],
      "minima_flagged": set()}),
    # Blank ceiling/visibility ("not a factor") must never trigger a false
    # caution - same convention as weather_category().
    ("Minima: blank ceiling/visibility -> no caution", 14, 30, 40, 8, None,
     None, None, "Dry", "Good", False,
     {"flow_key": "NE", "minima_flagged": set()}),

    # --- Per-runway 8400.9 wind check (Pendencia 12, added 2026-08-02) ---
    # W1 - the scenario that exposed the old single-runway check. NW flow at
    # 350/25: runway 27 takes 24.5 kt of crosswind (over the 20 kt cap) while
    # 32 (12.5), 33L and 33R (8.6) are all comfortable. The old code printed
    # one generic "the wind exceeds the limits on this flow" caution; it must
    # now name 27 and 27 ONLY. Note 27 is also a departure runway here, so
    # this proves the check covers both lists without double-reporting.
    ("W1 Wind: NW 350/25 flags runway 27 only", 14, 0, 350, 25, None, None,
     None, "Dry", "Good", False,
     {"flow_key": "NW", "arr": ["27", "32", "33L", "33R"],
      "dep": ["33L", "27"], "wind_flagged": {"27"}}),
    # W2 - the easterly band, and now the textbook par. 7d role fill.
    # Both SE arrival runways (15R/15L, both 150 deg) are over the crosswind
    # cap, so the noise programme has no arrival runway left to assign and that
    # SIDE ALONE reverts to wind alignment: runway 9 at 92 deg, all but on the
    # nose. The departure side is untouched (9 nearly aligned; 14 at 140 deg
    # just under at 19.2 kt), which is the whole point of filling per role -
    # runway 14 is documented, it passed, and it stays.
    # UPDATED 2026-08-04: until then this asserted arr == the flagged runways
    # themselves, because the app had no answer for this wind and left them in
    # place with a caution.
    # CHANGED 2026-08-04 (8th round), arr/role_fill were ["9"]. wind_flagged
    # stays {15R, 15L}: the 4L/4R pair the fill lands on is over the crosswind
    # cap too (20.5 kt against 20), and _reassigned_wind_notes now says so in
    # the caution - but flagging it would take the replacement out of the table
    # in _usable_now, deleting the only answer left. Notes yes, flag no.
    ("W2 Wind: east 090/25 refills SE arrivals by alignment, keeps departures",
     14, 0, 90, 25, None, None, None, "Dry", "Good", False,
     {"flow_key": "SE", "arr": ["4L", "4R"], "dep": ["9", "14"],
      "wind_flagged": {"15R", "15L"}, "role_fill": {"arr": ["4L", "4R"]}}),
    # W2b - same wind, same flow, but Instrument: runway 9 has no published
    # approach, so the fill must SKIP it for arrivals and keep walking - while
    # the departure side still uses it, because a takeoff needs no approach.
    # This is the asymmetry _fill_role exists for, and the two runways it lands
    # on (4L/4R + 9) are the documented Northeast Flow package, rediscovered
    # rather than invented.
    ("W2b Wind: east 090/25 in IMC - arrivals skip rwy 9, departures do not",
     14, 0, 90, 25, None, 500, 1.0, "Dry", "Good", False,
     {"flow_key": "SE", "arr": ["4L", "4R"], "dep": ["9", "14"],
      "role_fill": {"arr": ["4L", "4R"]}}),
    # W3 - no false positives on an ordinary day (same inputs as F1).
    ("W3 Wind: NE 040/08 flags nothing", 14, 30, 40, 8, None, None, None,
     "Dry", "Good", False,
     {"flow_key": "NE", "wind_flagged": set()}),
    # W4 - a slippery runway drops the caps to 15 kt crosswind / 0 kt
    # tailwind, so a wind that is harmless when dry starts flagging. Same
    # 350/20 wind, dry vs slippery, is the cleanest way to lock that in.
    ("W4 Wind: 350/20 dry flags nothing", 14, 0, 350, 20, None, None, None,
     "Dry", "Good", False,
     {"flow_key": "NW", "wind_flagged": set()}),
    ("W4b Wind: 350/20 on a wet runway flags 27", 14, 0, 350, 20, None, None,
     None, "Wet", "Good", False,
     {"flow_key": "NW", "wind_flagged": {"27"}}),

    # --- Unknown wind direction, Step 2 (added 2026-08-03) ---
    # Closes a real gap found while mapping today's fix: W1-W4b all use a
    # known wind direction, so none of them ever exercised this branch of
    # _wind_limit_notes - the original bug (any speed, unknown direction,
    # silently produced zero notes) could have shipped again with 47/47
    # still green. wind_notes_count checks the STRUCTURE (how many notes),
    # never the wording, same principle as every other check in this suite.
    #
    # W5 - below the tailwind limit even under the worst-case assumption:
    # must NOT fire. Guards against a fix that flags every non-zero wind.
    ("W5 Wind: 2 kt unknown direction -> no caution", 14, 30, None, 2, None,
     None, None, "Dry", "Good", False,
     {"flow_key": "NE", "wind_notes_count": 0, "wind_flagged": set()}),
    # W6 - the original bug report: unknown direction, moderate speed. Must
    # fire, and wind_flagged must stay EMPTY (2026-08-03 decision: naming
    # specific runways here would be the same "fake per-runway calculation"
    # problem the single-sentence rewrite exists to avoid).
    ("W6 Wind: 10 kt unknown direction -> caution fires", 14, 30, None, 10,
     None, None, None, "Dry", "Good", False,
     {"flow_key": "NE", "wind_notes_count": 1, "wind_flagged": set()}),
    # W7 - Step 0 override with unknown direction: arr_rwys/dep_rwys stay
    # None (no configuration is ever named - see "NOT DETERMINABLE" in the
    # arrival note), so there is nothing for the wind check to run against.
    # Zero notes here is the CORRECT behaviour, not a gap - this scenario
    # exists so a future change can't quietly start firing a caution that
    # would reference a configuration the app never actually named.
    ("W7 Wind: override + unknown direction -> no caution (no config)", 14,
     0, None, 15, None, None, None, "Dry", "Good", True,
     {"flow_key": "OVERRIDE", "arr": None, "dep": None,
      "wind_notes_count": 0, "wind_flagged": set()}),
    # W8/W8b - same dry-vs-slippery pair as W4/W4b, but for unknown
    # direction: the wet runway must keep inheriting the slippery limits instead
    # of the code hard-coding the dry threshold.
    # W8b RENUMBERED 2026-08-04 (2nd round), from 3 kt to 4 kt. At 3 kt this pair stopped
    # testing anything the day the par. 7d(2)(b) calm exemption went in: 0-3 kt on
    # a non-dry runway is now exempt, so the wet half fired nothing and the pair
    # read dry-no / wet-no. Moving it to 4 kt - the first speed above the
    # exemption - keeps it testing the thing it was written for. Simply flipping
    # its expectation to 0 would have left a scenario whose name promises a
    # caution and whose assertion promises none.
    ("W8 Wind: 3 kt unknown direction, dry -> no caution", 14, 30, None, 3,
     None, None, None, "Dry", "Good", False,
     {"flow_key": "NE", "wind_notes_count": 0, "wind_flagged": set()}),
    ("W8b Wind: 4 kt unknown direction, wet -> caution fires", 14, 30, None,
     4, None, None, None, "Wet", "Good", False,
     {"flow_key": "NE", "wind_notes_count": 1, "wind_flagged": set()}),

    # --- Runway 9 is never an arrival (added 2026-08-04, 8th round) ------------
    # The bug this closes reached the player through THREE doors, and the suite
    # only ever watched one of them. W2/P2 cover the par. 7d fill on the SE side
    # of the 90-degree boundary and F11/R4b the safety override; nothing covered
    # the NE side, where the same wind picks the same wrong runway through the
    # same shared scan. Measured over the full sweep, the NE half was 201 of the
    # 1,402 affected combinations - a sixth of the defect, invisible to 74 tests.
    #
    # N1 - the NE half. 080/30 puts 24.5 kt of crosswind on 4L/4R, over the 20 kt
    # dry cap, so the arrival side empties and the fill runs. Best alignment is
    # runway 9; the airport does not land there, so arrivals come back to the
    # very pair that just failed - the least-bad real answer, carrying its number
    # on screen, rather than a runway nothing lands on. Note what is NOT flagged:
    # runway 9 sits 12 degrees off this wind and is comfortably inside both caps,
    # so nothing about the wind was ever what ruled it out for arrivals.
    ("N1 rwy 9 is never an arrival: NE 080/30 falls back to 4L/4R",
     14, 0, 80, 30, None, None, None, "Dry", "Good", False,
     {"flow_key": "NE", "arr": ["4L", "4R"], "role_fill": {"arr": ["4L", "4R"]},
      "wind_flagged": {"4L", "4R"}}),
    # N2 - the departure side must come through untouched. Runway 9 is a real
    # departure runway in two documented flows, and the rule added here is about
    # LANDING there; a guard written one line too wide would take a working
    # runway away from takeoffs too. The assertion is that the documented NE
    # departure package survives whole and that only "arr" appears in role_fill -
    # the arrival side was reassigned, the departure side was never in question.
    ("N2 rwy 9 still departs: NE 080/30 leaves the departure package whole",
     14, 0, 80, 30, None, None, None, "Dry", "Good", False,
     {"flow_key": "NE", "dep": ["9", "4L", "4R"],
      "role_fill": {"arr": ["4L", "4R"]}, "package_dropped": False}),

    # --- The one-way 14/32 join the scan (added 2026-08-05) -------------------
    # Headings 14 and 32 are candidates now, under two restrictions that have to
    # hold together: one role each (court order), and never alone (neither can
    # serve the airport by itself). Both are asserted here, because dropping
    # either produces a plausible-looking answer that is wrong in a different
    # way - and the first cut of this change dropped the second, replacing
    # "arrivals 33L, 33R" with "arrivals 32" on 576 combinations.
    #
    # O1 - a wind straight down 320. Runway 32 is the best-aligned arrival at
    # 0 kt of crosswind and joins the answer instead of becoming it; the result,
    # 33L + 33R + 32, is a subset of Massport's own Northwest arrival package.
    # The departure side of the same run is the role restriction: 32 is
    # landing-only, so it is absent there however well aligned it is.
    ("O1 one-way 32 joins the arrival answer, never replaces it",
     14, 0, 320, 25, None, None, None, "Dry", "Good", True,
     {"flow_key": "OVERRIDE", "arr": ["33L", "33R", "32"], "dep": ["33L", "33R"]}),
    # O2 - the same wind with a 200 ft ceiling. Runway 32's own published minimum
    # is 801 ft / 1.0 SM, so it drops out; 33R has no approach at all and goes
    # too, leaving 33L. Held-back runways go through every check the others do -
    # a supplement that skipped the weather test would be the older
    # "conditions are Visual, so anything goes" bug in a new place.
    ("O2 one-way 32 is dropped by its own minima like any other runway",
     14, 0, 320, 25, None, 200, 0.5, "Dry", "Good", True,
     {"flow_key": "OVERRIDE", "arr": ["33L"]}),
    # O3 - the departure mirror, and the strongest evidence the pair of rules is
    # right rather than merely safe: at 118 degrees departures come out as
    # 9 + 14, which IS the documented Southeast departure package, rediscovered
    # by alignment alone. The band is narrow and had to be measured rather than
    # guessed - runway 14 must out-align runway 9 (wind past 116) while runway 9
    # still out-aligns runway 15 (wind before 122). Arrivals in the same run stay
    # off 14 (takeoff-only) AND off 9 (no flow lands there), landing on 15R/15L:
    # both arrival guards firing at once, on one input.
    ("O3 one-way 14 joins departures: 9 + 14 is the documented SE package",
     14, 0, 118, 25, None, None, None, "Dry", "Good", True,
     {"flow_key": "OVERRIDE", "dep": ["9", "14"], "arr": ["15R", "15L"]}),

    # --- Par. 7d(2)(b), the 0-3 kt calm exemption (added 2026-08-04 (2nd round)) ------
    # The order's own words: "No tailwind component may be present EXCEPT the
    # nominal range of winds reported as calm (0-3 knots) may be considered to
    # have no tailwind component." The app implemented the rule and not the
    # exception, so ONE KNOT on a wet runway put the whole package over the limit
    # and the par. 7d role fill reassigned BOTH sides. Measured before the fix:
    # 282 of 432 combinations of 0-3 kt on a non-dry runway fired, 216 reassigned.
    #
    # C1/C2 - the boundary, from both sides. 3 kt is the last exempt speed, 4 kt
    # the first that is not. Asserting role_fill on both is the point: the damage
    # was never the caution text, it was the configuration being thrown away.
    ("C1 par.7d(2)(b): 3 kt on a wet runway is exempt, nothing reassigned",
     14, 30, 220, 3, None, None, None, "Wet", "Good", False,
     {"flow_key": "NE", "arr": ["4L", "4R"], "dep": ["9", "4L", "4R"],
      "wind_flagged": set(), "role_fill": {}, "wind_notes_count": 0}),
    ("C2 par.7d(2)(b): 4 kt on a wet runway is NOT exempt",
     14, 30, 220, 4, None, None, None, "Wet", "Good", False,
     {"flow_key": "NE", "wind_flagged": {"4L", "4R", "9"}}),
    # C3 - the exemption is for a runway NOT clear and dry. On a dry runway the
    # limit is 5 kt and the exception does not exist in the order at all, so 3 kt
    # must stay silent for the ordinary reason, not the new one. Guards against a
    # fix that raised the dry limit too.
    ("C3 par.7d(2)(b): dry runway unaffected by the exemption",
     14, 30, 220, 3, None, None, None, "Dry", "Good", False,
     {"flow_key": "NE", "wind_flagged": set(), "role_fill": {}}),
    # C4 - a gust disqualifies the exemption. The order exempts winds "REPORTED as
    # calm", and a wind carrying a gust is not reported as calm, so the exemption
    # keys on eff_speed and 02G04 falls outside it while a bare 02 does not.
    # 220/02G04 rather than the 02G18 first written here: since the calm test
    # itself started reading the gust (N3), an 18-kt gust no longer lands in the
    # NE package at all, and the scenario would have been testing the flow choice
    # instead of the exemption. At G04 both readings still call it calm, so the
    # ONLY thing separating this from C1 is the gust - which is the whole point.
    ("C4 par.7d(2)(b): a gust disqualifies the calm exemption",
     14, 30, 220, 2, 4, None, None, "Wet", "Good", False,
     {"flow_key": "NE", "wind_flagged": {"4L", "4R", "9"}}),

    # --- Par. 7d, gust attribution (N2 2026-08-04, REVERSED 2026-08-05) --------------
    # "(including gust values)" is written into the CROSSWIND clauses of the order
    # (7d(1)(a), 7d(2)(a)) and into none of the three tailwind clauses. Until
    # 2026-08-05 the app counted the gust on both and an [APP SIMPLIFICATION] line
    # owned up to it; Pendencia Nova B took the gust out of the tailwind, so the
    # tailwind now runs on the steady wind and the disclaimer is gone.
    #
    # G1/G2 STILL a matched pair with the same effective wind - 4 kt either way -
    # differing in nothing but whether a gust produced it. That used to make them
    # differ by exactly one note (the disclaimer). Now they must be IDENTICAL: the
    # gust no longer reaches the tailwind, and at 270 deg nothing here is near the
    # crosswind cap, so the gust has nowhere left to bite. G1 asserting the same
    # count as G2 is the whole point of the pair after the change - if a future
    # edit lets the gust back into the tailwind, these two separate again.
    ("G1 par.7d: a gust no longer moves the tailwind (matches G2 exactly)",
     14, 30, 270, 2, 4, None, None, "Wet", "Good", False,
     {"flow_key": "NE", "wind_notes_count": 5}),
    ("G2 par.7d: same effective wind without a gust -> identical result",
     14, 30, 270, 4, None, None, None, "Wet", "Good", False,
     {"flow_key": "NE", "wind_notes_count": 5}),
    # G3 - the half of the rule that did NOT change, and the reason the split has
    # to be per component rather than a blanket switch to the steady wind. A gust
    # over the CROSSWIND still flags the runway, because there the order's own text
    # does include gust values. 350/15G25 puts 24.5 kt across runway 27 and no
    # tailwind anywhere. If someone "simplifies" the two speeds back into one by
    # taking the STEADY side everywhere, this scenario is what breaks.
    ("G3 par.7d: the crosswind still reads the gust -> 27 stays flagged",
     14, 0, 350, 15, 25, None, None, "Dry", "Good", False,
     {"flow_key": "NW", "wind_flagged": {"27"}, "wind_notes_count": 1}),
    # G4/G5 - Pendencia Nova B measured over a sweep of 171,720 combinations:
    # 4,404 differences, in two shapes, and the two are worth separate scenarios
    # because they sit at opposite ends of how much the cap matters.
    #
    # THE FOUR DOCUMENTED FLOWS BARELY FEEL IT (G4, 64 of the 4,404). A flow is
    # chosen to point INTO the wind, so a runway it makes active is never far off
    # the nose - the largest positive tailwind geometry measured on an active
    # package runway is 3.5% of the wind speed, about 1 kt even under a 30-kt gust,
    # nowhere near the 5-kt dry cap. Only the 0-kt slippery cap can be cleared by a
    # figure that small, and since both components scale from the same direction
    # the SIGN cannot differ between steady and gust - so "steady at or under 0,
    # gust over it" forces a steady wind of exactly 0. Hence every one of these 64
    # is a 00000Gxx input. 000/00G10 wet, 14:00: runway 9 (heading 092) takes
    # 0.35 kt of tailwind from the gust and 0.00 from the steady wind, and that
    # 0.35 used to strike it off the departure list.
    ("G4 Pendencia Nova B: 000/00G10 wet keeps runway 9 available to depart",
     14, 0, 0, 0, 10, None, None, "Wet", "Good", False,
     {"flow_key": "NE", "wind_flagged": set(), "role_fill": {}}),
    # G5 - WHERE IT ACTUALLY BITES (4,340 of the 4,404), and the scenario that had
    # to exist: the overnight head-to-head is the ONE branch that assigns runways
    # AGAINST the wind - 33L arrivals and 15R departures are forced by the noise
    # procedure whatever the wind is doing - so it is the one place the tailwind
    # cap is the real gate rather than a formality. 2,585 of these carry a steady
    # wind of 2 kt or more, i.e. ordinary METARs and not the 00000G degenerate.
    #
    # THIS SCENARIO EXISTS BECAUSE THE FIRST SWEEP MISSED IT ENTIRELY. That sweep
    # sampled 14:00 and 23:00, and the h2h window is 00:00-05:00 - a DIFFERENT
    # range from night_block (23:00-06:00), which is what made 23:00 look like it
    # covered the night. It reported 64 differences, all with a zero steady wind,
    # and the conclusion drawn from that ("no realistic METAR is affected") was
    # exactly wrong. The user's own question - "the order says 5 kt, so 150/05G10
    # ought to pass" - is what exposed it. 150/05G10 puts 5.0 kt of steady tailwind
    # on runway 33 against a 5-kt cap (passes) and 10.0 kt of gust tailwind (used
    # to fail), which is the whole rule in one input.
    ("G5 Pendencia Nova B: 150/05G10 at 02:00 lets the head-to-head stand",
     2, 0, 150, 5, 10, None, None, "Dry", "Good", False,
     {"flow_key": "H2H", "arr_rwys": ["33L"], "dep_rwys": ["15R"]}),

    # --- Par. 7d as a criterion, not a warning (added 2026-08-04) -------
    # The three levels of the same rule, applied per role. See KBOS_achados.md
    # 15.3. Each asserts the STRUCTURED result - which side was reassigned and
    # to what - never the sentence that reports it.
    #
    # R1 - LEVEL 1, the common case: one runway of the package is over the cap,
    # the rest of that side is not. Nothing is reassigned; the runway simply
    # stops being offered. Runway 27 is Arr+Dep in the NW package, so this also
    # pins that the wind filter takes a runway out of BOTH roles - unlike the
    # no-approach filter, which is arrivals-only (see R4).
    ("R1 par.7d L1: NW 350/25 drops 27 from the table, keeps the package",
     14, 0, 350, 25, None, None, None, "Dry", "Good", False,
     {"flow_key": "NW", "arr": ["27", "32", "33L", "33R"], "dep": ["33L", "27"],
      "wind_flagged": {"27"}, "role_fill": {},
      "table": {("32", "Arr"): ("No", "runway size", "P T B R yes / N W C no"),
                ("33L", "Arr+Dep"): ("Yes", None, None),
                ("33R", "Arr"): ("No", "runway size",
                                 "P yes / T B varies / R N W C no")}}),
    # R2 - LEVEL 2 on the DEPARTURE side, which W2 does not cover. At 269/25 the
    # SW package's departures are 22L and 22R, both on heading 215 and both over
    # the 20-kt cap, while arrival runway 27 (272 deg) is barely touched. So
    # departures alone are reassigned - to 27, which then works both ways - and
    # the arrival side keeps the documented pair. If this ever comes back with
    # arr == ["27"] the fill has gone back to replacing whole configurations.
    # prop_bonus asserted empty too (added 2026-08-05): _package_governs_arrivals
    # alone would say True here (arrivals untouched), but 22R itself is gone
    # from dep - this is the one reachable way to isolate 22R from the bonus
    # guard added the same day, since 22L and 22R share one heading and can
    # never diverge on wind alone (so "22R excluded, 22L fine" cannot happen;
    # this scenario, "both excluded, dep reassigned away from 22R entirely",
    # is the real-world version of the same edge case).
    ("R2 par.7d L2: SW 269/25 refills departures only",
     14, 0, 269, 25, None, 5000, 10.0, "Dry", "Good", False,
     {"flow_key": "SW", "arr": ["22L", "27"], "dep": ["27"],
      "wind_flagged": {"22L", "22R"}, "role_fill": {"dep": ["27"]},
      "prop_bonus": []}),
    # R3 - the control the other three need: an ordinary day must reassign
    # NOTHING. Guards against a fill that fires whenever anything is flagged
    # rather than only when a side is actually empty.
    ("R3 par.7d: ordinary day reassigns nothing", 14, 30, 40, 8, None, None,
     None, "Dry", "Good", False,
     {"flow_key": "NE", "role_fill": {}, "wind_flagged": set()}),
    # R4 - the safety override, per role (the "case A" of KBOS_achados 15.3.1).
    # An easterly picks runway 9 on alignment, but the airport does not land
    # there, so it can only depart. The scan keeps walking for the arrival side
    # and lands on 4L/4R. The pair it ends up with - land 4, depart 9 - IS the
    # documented Northeast Flow, which is the strongest evidence that the scan
    # rediscovers real configurations instead of inventing them.
    # minima_flagged WAS {"9"} until 2026-08-04 (8th round). Runway 9 no longer
    # reaches the weather check at all - _fill_role drops it from arrivals
    # before that, on a fact that does not depend on the weather - so the
    # explanation moved to _never_arrival_note and says the same thing on every
    # kind of day instead of only on bad ones.
    ("R4 override per role: easterly in IMC lands 4, departs 9",
     14, 0, 90, 30, None, 500, 1.0, "Dry", "Good", True,
     {"flow_key": "OVERRIDE", "arr": ["4L", "4R"], "dep": ["9"],
      "minima_flagged": set()}),
    # R4b - same wind, Visual. REVERSED 2026-08-04 (8th round): this used to
    # assert arr ["9"] with the comment "runway 9 CAN receive now, so both roles
    # must land on it" - the defect written down as the expected result. Weather
    # was never what made 9 unusable for arrivals; no documented configuration
    # lands there at all. The split must happen in EVERY weather, and this is
    # now the control that proves the guard is not weather-dependent.
    ("R4b override per role: same easterly in VMC still splits the roles",
     14, 0, 90, 30, None, 5000, 10.0, "Dry", "Good", True,
     {"flow_key": "OVERRIDE", "arr": ["4L", "4R"], "dep": ["9"],
      "minima_flagged": set()}),

    # --- The calm test reads the gust (N3, added 2026-08-04 (2nd round)) --------------
    # K1 - the case that exposed it. 22003G20KT used to be "calm" on its 3 kt of
    # reported wind, which sent the app into the NE package; par. 7d then found a
    # 19.9-kt tailwind on every NE runway (under the tailwind formula THEN in
    # force, which read the gust) and reassigned both sides, landing on 22L + 22R.
    # STALE NUMBER, corrected 2026-08-06: Pendencia Nova B (2026-08-05) moved the
    # tailwind check to the steady wind only, so replaying this exact wind today
    # finds just 3 kt of tailwind - no longer a reassignment trigger by itself.
    # The underlying phenomenon this scenario guards against (a wrongly-calm flow
    # pick, then torn apart by par. 7d two steps later) is UNCHANGED and still
    # real - measured at 22,094 wind/speed combinations - it now fires through the
    # CROSSWIND check (which still reads the gust), not the tailwind one. Reading
    # the gust puts 220/03G20 straight into the documented Southwest package -
    # 22L + 27, with its LAHSO note - and reassigns NOTHING. role_fill empty is
    # the real assertion here: it says the app no longer builds a configuration
    # only to take it apart two steps later.
    ("K1 N3: 220/03G20 uses the gust -> SW package, nothing reassigned",
     14, 30, 220, 3, 20, None, None, "Dry", "Good", False,
     {"flow_key": "SW", "arr": ["22L", "27"], "dep": ["22L", "22R"],
      "role_fill": {}, "package_dropped": False, "wind_flagged": set()}),
    # K2 - the control: same wind, no gust. 3 kt really is calm, so the calm rule
    # must still fire and still answer NE. Guards against a change that simply
    # deleted the calm branch.
    ("K2 N3: 220/03 without a gust is still calm -> NE", 14, 30, 220, 3, None,
     None, None, "Dry", "Good", False,
     {"flow_key": "NE", "arr": ["4L", "4R"], "role_fill": {}}),
    # K3 - a gust that stays under the threshold changes nothing. 02G04 is calm on
    # either reading, so the flow must still be NE - the test is "5 kt or more",
    # not "has a gust".
    ("K3 N3: 220/02G04 is calm on both readings -> NE", 14, 30, 220, 2, 4,
     None, None, "Dry", "Good", False,
     {"flow_key": "NE", "arr": ["4L", "4R"], "role_fill": {}}),

    # --- Par. 7d emptying BOTH sides (added 2026-08-04 (2nd round)) -------------------
    # P1 - the defect itself, and it needs no gust and no unusual input: 000/30 on
    # a wet runway picks the NE package, then par. 7d takes 4L, 4R and 9 out of
    # both roles. Before the fix the header still read "NE flow" over an
    # all-33L/33R configuration, with the REASONING block still explaining the NE
    # choice - three statements on one screen contradicting the two lines between
    # them. The assertion is the structured flag, not the sentence.
    ("P1 par.7d: both sides emptied -> header stops naming the package",
     14, 30, 0, 30, None, None, None, "Wet", "Good", False,
     {"flow_key": "NE", "arr": ["33L", "33R"], "dep": ["33L", "33R"],
      "role_fill": {"arr": ["33L", "33R"], "dep": ["33L", "33R"]},
      "package_dropped": True}),
    # P2 - the control that matters most: ONE side reassigned must NOT drop the
    # package name, because the other side still genuinely comes from it. This is
    # the 2026-08-04 decision and P1 must not have overrun it. Same wind as W2.
    ("P2 par.7d: one side reassigned keeps the package name",
     14, 0, 90, 25, None, None, None, "Dry", "Good", False,
     {"flow_key": "SE", "role_fill": {"arr": ["4L", "4R"]},
      "package_dropped": False}),
    # P3 - an ordinary day drops nothing at all.
    ("P3 par.7d: ordinary day keeps its package", 14, 30, 40, 8, None, None,
     None, "Dry", "Good", False,
     {"flow_key": "NE", "role_fill": {}, "package_dropped": False}),

    # --- Package-level arrangements stop when the package does (2026-08-04 (2nd round)) --
    # B1 - the 22R prop arrival bonus is something Massport documents ALONGSIDE
    # the Southwest arrival pair, not a standing property of runway 22R. At 180/30
    # on a wet runway the 15-kt slippery crosswind cap takes out both 22L (17.2
    # kt) and 27 (30 kt plus a tailwind), so par. 7d reassigns arrivals to 15R/15L
    # and the SW package is gone - but flow_key still reads "SW", by design, and
    # the app went on printing "land: 15R, 15L + 22R (noise-runway bonus)" for a
    # runway not in the configuration at all. The same guard covers the LAHSO
    # tables, which describe the 22L/27 hold-short arrangement.
    ("B1 the 22R prop bonus dies with the SW arrival package",
     14, 30, 180, 30, None, None, None, "Wet", "Good", False,
     {"flow_key": "SW", "arr": ["15R", "15L"], "prop_bonus": [],
      "role_fill": {"arr": ["15R", "15L"], "dep": ["15R", "15L"]}}),
    # B2 - the control: the ordinary SW flow must still carry the bonus, or the
    # guard has simply deleted the feature. Same pair as F4.
    ("B2 the bonus survives an ordinary SW day", 14, 30, 220, 10, None, None,
     None, "Dry", "Good", False,
     {"flow_key": "SW", "prop_bonus": ["22R"], "role_fill": {}}),

    # --- Order 8400.9 par. 7b, visibility (added 2026-08-02) ---
    # V1/V1b isolate the VISIBILITY criterion, so the pair must differ in
    # nothing but visibility. WIND CHANGED 2026-08-04 from 330/6 to 060/12 for
    # the reason given in F10: 330/6 now fails on par. 7d at the departure end,
    # which would have made this pair pass and fail for the wrong reason - both
    # sides refused, neither of them by visibility. 060/12 is across the strip:
    # 0.0 kt on both ends, so par. 7d is silent and visibility is the only
    # variable left.
    ("V1 par.7b: h2h holds at 5 SM", 2, 0, 60, 12, None, None, 5,
     "Dry", "Good", False,
     {"flow_key": "H2H", "arr": ["33L"], "dep": ["15R"]}),
    # V1b - identical, but 0.75 SM. The head-to-head is a pure noise
    # preference and par. 7b forbids a runway use program from governing the
    # landing runway below 1 SM, so it must fall through to the wind logic.
    # Before this was wired up the app answered H2H here, and nothing else
    # objected: 33L is CAT III, so the minima check clears 0.75 SM easily.
    # Lands in NE rather than the old NW simply because 060 is the NE quadrant -
    # where it falls is incidental, the assertion is that it fell.
    ("V1b par.7b: h2h refused at 0.75 SM -> NE", 2, 0, 60, 12, None, None,
     0.75, "Dry", "Good", False,
     {"flow_key": "NE", "weather": "Instrument"}),

    # -----------------------------------------------------------------
    # T-series - the per-runway table (Pendencia 0, added 2026-08-03).
    # Asserted against the STRUCTURED rows, never the rendered text, for the
    # same reason minima_flagged is: a wording change must not be able to hide
    # a logic bug, and a logic bug must not be able to hide behind wording.
    # "table" maps (runway, role) -> (jet, reason, category). Runway alone
    # stopped being unique 2026-08-05: 22R's non-jet arrival bonus is a
    # second row for a runway that already has a "Dep" row (see T2/T2b).
    # -----------------------------------------------------------------
    # T1 - NW, the worst case: four arrival runways, two of them jet-capable,
    # two restricted for different reasons at different granularity.
    ("T1 Table: NW Visual, 4 runways", 14, 0, 320, 15, None, 3000, 10,
     "Dry", "Good", False,
     {"flow_key": "NW", "table": {
         ("27", "Arr+Dep"): ("Yes", None, None),
         ("32", "Arr"): ("No", "runway size", "P T B R yes / N W C no"),
         ("33L", "Arr+Dep"): ("Yes", None, None),
         ("33R", "Arr"): ("No", "runway size", "P yes / T B varies / R N W C no"),
     }}),
    # T2 - the LAHSO case, and the whole reason the table is built per query:
    # runway 27 must carry the restriction HERE...
    # 22R gets its own extra row here (added 2026-08-05): it is a departure
    # runway in this configuration, but non-jet aircraft also land on it
    # (Massport CAC) as a bonus outside the documented package - two rows,
    # not a suffix on the "Dep" row, since it genuinely has two answers now.
    ("T2 Table: SW Visual, 27 under LAHSO", 14, 0, 215, 15, None, 3000, 10,
     "Dry", "Good", False,
     {"flow_key": "SW", "prop_bonus": ["22R"], "table": {
         ("22L", "Arr+Dep"): ("Yes", None, None),
         ("27", "Arr"): ("No", "LAHSO", "P T yes / B R N W C no"),
         ("22R", "Dep"): ("Yes", None, None),
         ("22R", "Arr*"): ("No", "noise", "P T yes / B R N W C no"),
     }}),
    # T2b - the same flow at night: the 22R prop arrival bonus is suspended
    # (23:00-06:00 landing ban), so the extra "Arr*" row must be GONE
    # entirely, not just its asterisk. prop_bonus asserted empty directly -
    # the row-injection loop in _build_rwy_table iterates exactly that list,
    # so this is the exact guard against the row surviving into the night.
    ("T2b Table: SW at night, prop bonus row gone", 23, 30, 215, 15, None,
     3000, 10, "Dry", "Good", False,
     {"flow_key": "SW", "prop_bonus": [], "table": {
         ("22R", "Dep"): ("Yes", None, None),
     }}),
    # T3 - ...and NOT here. Same runway, same table, no restriction at all:
    # SW/Marginal drops the hold-short, so 27 is a full jet runway again.
    # If this ever comes back "No", the exception leaked out of its one config.
    ("T3 Table: SW Marginal, 27 unrestricted", 14, 0, 215, 15, None, 2000, 5,
     "Dry", "Good", False,
     {"flow_key": "SW", "weather": "Marginal", "table": {
         ("27", "Arr"): ("Yes", None, None),
     }}),
    # T4 - NE: runway 4L is arrival AND departure, and jets may do only one of
    # them (they land 4L, they may not take off from it - 73 dBA). A plain
    # Yes/No would be false either way; the mixed answer is the point.
    ("T4 Table: NE Visual, 4L jet arrival only", 14, 0, 35, 15, None, 3000, 10,
     "Dry", "Good", False,
     {"flow_key": "NE", "table": {
         ("4L", "Arr+Dep"): ("Arr only", "noise", None),
         ("4R", "Arr+Dep"): ("Yes", None, None),
         ("9", "Dep"): ("Yes", None, None),
     }}),
    # T5 - SE: the only flow with a suffix that survives into the Role column
    # (arrivals and departures share no runway here, so nothing collides), and
    # the only flow where runway 14 appears at all.
    # SPEED CHANGED 2026-08-05 (Pendencia Nova C) from 20 to 23 kt: 20 kt
    # cleared the new NE/SW fallback (crosswind 18.1 kt on both primaries,
    # under the 20-kt cap), so the scenario stopped reaching SE at all. 23 kt
    # keeps SE genuine (crosswind 20.9 kt on both primaries) while staying
    # under runway 9's own crosswind cap (19.5 kt) - picked by hand-checking
    # the narrow window where both hold, since going much higher would have
    # flagged 9 too and broken the "Dep (limited): Yes" row below.
    ("T5 Table: SE Visual, limited suffix + rwy 14", 14, 0, 150, 23, None,
     3000, 10, "Dry", "Good", False,
     {"flow_key": "SE", "table": {
         ("15R", "Arr (limited)"): ("Yes", None, None),
         ("15L", "Arr (limited)"): ("No", "runway size",
                                     "P yes / T B varies / R N W C no"),
         ("9", "Dep (limited)"): ("Yes", None, None),
         ("14", "Dep (limited)"): ("No", "runway size",
                                    "P T B yes / R varies / N W C no"),
     }}),
    # T6 - the mirror of T4 on the other noise runway: in the override the
    # heading-22 pair runs both ways, and 22R is the reverse mixed case (jets
    # depart it, jets may not land on it - 78 dBA).
    ("T6 Table: override heading 22, 22R jet departure only", 12, 0, 200, 25,
     None, None, None, "Wet", "Fair", False,
     {"flow_key": "OVERRIDE", "table": {
         ("22L", "Arr+Dep"): ("Yes", None, None),
         ("22R", "Arr+Dep"): ("Dep only", "noise", None),
     }}),
    # T7 - the guard: safety override with unknown wind computes no
    # configuration, so there must be NO table at all (not an empty one, not a
    # half-built one) and the single no-config line takes its place.
    ("T7 Table: no config -> no table", 15, 0, None, 12, None, None, None,
     "Dry", "Poor", False,
     {"flow_key": "OVERRIDE", "elig_fallback": True, "table": None}),
    # T8 - the night ban reaches the table too: at 23:30 runway 4L must not
    # appear as a departure row at all (it is out of dep_rwys), and 22R must
    # not appear as an arrival row. Guards against the table being rebuilt
    # from a static flow map instead of the computed lists.
    ("T8 Table: night ban removes 4L departure row", 23, 30, 35, 15, None,
     3000, 10, "Dry", "Good", False,
     {"flow_key": "NE", "table": {
         ("4L", "Arr"): ("Yes", None, None),
         ("4R", "Arr+Dep"): ("Yes", None, None),
     }}),
    # --- Pendencia 15 (2026-08-03): game category is per ROLE ---------
    # T9 - the defect itself. The heading-15 override runs 15L both ways at
    # once, and its two answers really differ (a business jet lands there but
    # cannot depart). The cell must carry NEITHER breakdown - the old build
    # printed the landing one on a row that also departs, which errs on the
    # permissive side, and printing the takeoff one instead would just pick the
    # other way to be wrong at a glance.
    ("T9 Table: override heading 15, 15L category split by role", 12, 0, 150,
     20, None, 3000, 10, "Wet", "Fair", False,
     {"flow_key": "OVERRIDE", "table": {
         ("15R", "Arr+Dep"): ("Yes", None, None),
         ("15L", "Arr+Dep"): ("No", "runway size", "see note *"),
     }}),
    # T10 - the same strip from the other end, so a fix that only ever keyed on
    # "15L" would fail here.
    ("T10 Table: override heading 33, 33R category split by role", 12, 0, 330,
     20, None, 3000, 10, "Wet", "Fair", False,
     {"flow_key": "OVERRIDE", "table": {
         ("33L", "Arr+Dep"): ("Yes", None, None),
         ("33R", "Arr+Dep"): ("No", "runway size", "see note *"),
     }}),
    # T11 - the control for T9/T10: in the SE flow 15L ARRIVES ONLY, so the
    # landing breakdown is the whole truth and there must be NO asterisk. This
    # is what stops the split from becoming a static label on the runway
    # instead of a per-query fact about its role - the same trap T2b guards for
    # the prop-bonus asterisk.
    # SPEED CHANGED 2026-08-05 (Pendencia Nova C), same reason and same value
    # as T5 just above - 20 kt no longer reaches SE once the NE/SW fallback is
    # in place.
    ("T11 Table: SE flow, 15L arrival only -> landing letters, no asterisk", 14,
     0, 150, 23, None, 3000, 10, "Dry", "Good", False,
     {"flow_key": "SE", "table": {
         ("15L", "Arr (limited)"): ("No", "runway size",
                                     "P yes / T B varies / R N W C no"),
     }}),
]


def _selftest_output_path():
    """Where the full-text selftest log is written (added 2026-08-03, so the
    community gets a plain-text artifact of what the app actually prints, not
    just a pass/fail count). Name mirrors whatever this build is currently
    called - "kbos_runway_advisor_03ago.py" writes
    "KBOS_Runway_Advisor_selftest_03ago.txt" next to itself; after the
    Pendencia 0 promotion (name drops the date) the same code writes
    "KBOS_Runway_Advisor_selftest.txt" with no extra step. Works from the
    frozen .exe too: sys.frozen means __file__ points into a temp extraction
    directory, not the real install folder, so sys.executable is used instead.
    """
    if getattr(sys, "frozen", False):
        own_path, app_dir = sys.executable, os.path.dirname(sys.executable)
    else:
        own_path, app_dir = __file__, os.path.dirname(os.path.abspath(__file__))
    stem = os.path.splitext(os.path.basename(own_path))[0]
    suffix = re.sub(r"^kbos_runway_advisor", "", stem, flags=re.IGNORECASE)
    return os.path.join(app_dir, f"KBOS_Runway_Advisor_selftest{suffix}.txt")


def _tailwind_rule_check():
    """Par. 7d's two speeds, asserted AT THE RULE and not through evaluate().

    WHY THIS EXISTS, and why the 81 scenarios above could not replace it. Every
    one of them drives the whole engine, so the flow selection runs first - and a
    flow is chosen to face the wind, which means it hands _wind_limit_notes
    runways that are already pointed into it. The largest positive tailwind
    geometry reachable on an active package runway is 3.5% of the wind speed. An
    end-to-end scenario therefore measures whether the app can REACH the tailwind
    cap, which is a different question from whether the cap is RIGHT, and the
    answer to the first is "almost never, outside the overnight head-to-head".
    That gap is how the gust attribution sat unexamined through several audits.

    So this drives the rule directly, on a wind the flow logic would never send
    it: for each of the 12 runways, wind straight down the reciprocal (perfect
    tailwind, and exactly 0 crosswind, so the two components cannot mask each
    other). The assertion is that the cut follows the STEADY wind alone and the
    gust changes nothing - INCLUDING the cases where it must still cut, which is
    the half that stops this from being satisfied by a rule that just never fires.

    The second block is the mirror: wind straight across (perfect crosswind, 0
    tailwind), where the gust MUST count, because that is where the order writes
    "(including gust values)". Together they pin the split in both directions - a
    future edit that collapses the two speeds back into one breaks one block or
    the other, whichever direction it collapses in."""
    errors = []
    rwys = [r for group in HEADING_TO_RWYS.values() for r in group]
    # (steady, gust) either side of both caps. 6G16 and 5G10 are the load-bearing
    # pair on a dry runway: same gust story, but 6 kt of steady wind is over the
    # 5-kt cap on its own and must still cut.
    pairs = [(5, 10), (4, 20), (3, 15), (2, 12), (0, 10),
             (5, None), (6, 16), (7, None), (12, 25)]
    for tw_cap, cw_cap, surface in ((5, 20, "dry"), (0, 15, "slippery")):
        for rwy in rwys:
            base = _rwy_base(rwy)
            tail_dir = (RUNWAY_HEADING[base] + 180) % 360
            for steady, gust in pairs:
                eff = max(steady, gust) if gust is not None else steady
                giu = gust is not None and gust > steady
                _n, flagged = _wind_limit_notes(
                    [rwy], tail_dir, eff, steady, tw_cap, cw_cap, giu)
                want = steady > tw_cap
                if (rwy in flagged) != want:
                    errors.append(
                        f"tailwind/{surface} RWY {rwy} {steady}G{gust}: "
                        f"cut={rwy in flagged}, expected {want} "
                        f"(steady {steady} vs cap {tw_cap} - the gust must not "
                        f"reach the tailwind)")
    # The other half: the gust DOES count across the runway.
    for cw_cap, surface in ((20, "dry"), (15, "slippery")):
        tw_cap = 5 if cw_cap == 20 else 0
        for rwy in rwys:
            base = _rwy_base(rwy)
            cross_dir = (RUNWAY_HEADING[base] + 90) % 360
            for steady, gust in ((10, 25), (10, 18), (14, 16), (22, None)):
                eff = max(steady, gust) if gust is not None else steady
                giu = gust is not None and gust > steady
                _n, flagged = _wind_limit_notes(
                    [rwy], cross_dir, eff, steady, tw_cap, cw_cap, giu)
                want = eff > cw_cap
                if (rwy in flagged) != want:
                    errors.append(
                        f"crosswind/{surface} RWY {rwy} {steady}G{gust}: "
                        f"cut={rwy in flagged}, expected {want} "
                        f"(gust {eff} vs cap {cw_cap} - the gust MUST reach the "
                        f"crosswind)")
    return errors


def selftest(verbose=False):
    failures = []
    full_log = []  # every scenario, full render - independent of `verbose`,
                    # which only controls what ALSO prints to the console
    for name, *rest in SELFTEST_SCENARIOS:
        args, expect = rest[:-1], rest[-1]
        result = evaluate(*args)
        errors = []

        def check(label, got, want):
            if got != want:
                errors.append(f"{label}: expected {want!r}, got {got!r}")

        if "flow_key" in expect:
            check("flow_key", result["flow_key"], expect["flow_key"])
        if "weather" in expect:
            check("weather", result["weather"], expect["weather"])
        if "arr" in expect:
            check("arr_rwys", result["arr_rwys"], expect["arr"])
        if "dep" in expect:
            check("dep_rwys", result["dep_rwys"], expect["dep"])
        if expect.get("elig_fallback"):
            check("elig (fallback => None)", result["elig"], None)
        else:
            for key in ("jet_land", "jet_dep", "prop_land", "prop_dep", "prop_bonus"):
                if key in expect:
                    got = result["elig"][key] if result["elig"] else None
                    check(key, got, expect[key])
        if "table" in expect:
            want = expect["table"]
            rows = result["rwy_table"]
            if want is None:
                check("rwy_table (no config => None)", rows, None)
            elif rows is None:
                errors.append("rwy_table: expected rows, got None")
            else:
                # Keyed on (rwy, role) since 2026-08-05, not rwy alone: 22R's
                # non-jet arrival bonus is a second row for a runway that
                # already has a "Dep" row, and a plain rwy key would silently
                # collapse the two (dict comprehension keeps only the last),
                # hiding either row from every check below without an error.
                got = {(r["rwy"], r["role"]): (r["jet"], r["reason"], r["category"])
                       for r in rows}
                # Every expected runway must match, and the row set must be
                # exactly the runways USABLE on this input - a row for a
                # runway that is not active would be the "static map" bug.
                # REVISED 2026-08-04: this used to compare against the raw
                # arr_rwys|dep_rwys. It now compares against _usable_now(), the
                # same helper the table itself is built from - so the invariant
                # still catches a table built from a fixed map, while allowing
                # the wind and no-approach filters to remove rows. Recomputing
                # it here rather than reading result["rwy_table"] keeps it an
                # independent statement about what SHOULD be there.
                # Runway NAMES only (not (rwy, role) pairs) since 2026-08-05:
                # 22R's bonus row shares its runway name with its own "Dep"
                # row, so the name-only set is still exactly want_arr|want_dep
                # - this invariant is about which RUNWAYS are usable, not how
                # many rows each contributes.
                want_arr, want_dep = _usable_now(result)
                check("rwy_table runways", sorted({rwy for rwy, _role in got}),
                      sorted(set(want_arr) | set(want_dep)))
                for key, want_row in want.items():
                    check(f"rwy_table[{key}]", got.get(key), want_row)
        if "minima_flagged" in expect:
            check("minima_flagged", result["minima_flagged"], expect["minima_flagged"])
        if "minima_notes_count" in expect:
            # Count, never text - same principle as wind_notes_count. Exists for
            # the cases where the caution is a single summary sentence rather
            # than one line per runway, so minima_flagged is legitimately empty
            # and would not catch a regression on its own.
            check("minima_notes_count", len(result["minima_notes"]),
                  expect["minima_notes_count"])
        if "wind_flagged" in expect:
            check("wind_flagged", result["wind_flagged"], expect["wind_flagged"])
        if "package_dropped" in expect:
            # The structured fact, never the header sentence: True means par. 7d
            # emptied both sides and the header stopped naming the package.
            check("package_dropped", result["package_dropped"],
                  expect["package_dropped"])
        if "role_fill" in expect:
            # Structured, like every other assertion here: WHICH side the par.
            # 7d fallback had to reassign and to what, never the sentence that
            # reports it. {} asserts that the documented package answered both
            # sides on its own, which is what most scenarios must keep doing.
            check("role_fill", result["role_fill"], expect["role_fill"])
        if "wind_notes_count" in expect:
            # Count, not text (same principle as every other check here) - a
            # wording change must not be able to hide a logic bug. Added
            # 2026-08-03: closes a real gap found while mapping the unknown-
            # direction wind fix - the W1-W4b scenarios all use a known wind
            # direction, so none of them ever exercised this code path.
            check("wind_notes_count", len(result["wind_notes"]),
                  expect["wind_notes_count"])

        status = "FAIL" if errors else "PASS"
        print(f"[{status}] {name}")
        for e in errors:
            print(f"       {e}")
        if errors or verbose:
            for text, _tag in render(result):
                print(f"    | {text}")
            print()
        if errors:
            failures.append(name)

        full_log.append(f"[{status}] {name}")
        full_log.extend(f"       {e}" for e in errors)
        full_log.extend(f"    | {text}" for text, _tag in render(result))
        full_log.append("")

    # RULE-LEVEL BLOCK, added 2026-08-05, counted alongside the scenarios so a
    # failure here cannot be read as "81/81 passed" with a warning above it.
    # It is one entry rather than 264 because it asserts ONE rule; the message
    # names the runway, the wind and the cap that disagreed.
    rule_name = "R0 par.7d two speeds, asserted at the rule (all 12 runways)"
    rule_errors = _tailwind_rule_check()
    status = "FAIL" if rule_errors else "PASS"
    print(f"[{status}] {rule_name}")
    for e in rule_errors:
        print(f"       {e}")
    if rule_errors:
        failures.append(rule_name)
    full_log.append(f"[{status}] {rule_name}")
    full_log.extend(f"       {e}" for e in rule_errors)
    full_log.append("")

    total = len(SELFTEST_SCENARIOS) + 1
    summary = f"{total - len(failures)}/{total} checks passed."
    print("-" * 78)
    print(summary)
    full_log.append("-" * 78)
    full_log.append(summary)
    if failures:
        full_log.append("FAILED: " + "; ".join(failures))

    # Written every run, overwriting the previous one - always the current
    # build's actual output, never a stale artifact from an earlier session.
    # This file (not the terminal) is what ships with the .exe on Discord.
    try:
        with open(_selftest_output_path(), "w", encoding="utf-8") as f:
            f.write("\n".join(full_log) + "\n")
    except OSError as e:
        print(f"(could not write selftest log: {e})")

    if failures:
        print("FAILED: " + "; ".join(failures))
        sys.exit(1)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest(verbose="--verbose" in sys.argv)
    else:
        app = RunwayAdvisorApp()
        app.mainloop()
