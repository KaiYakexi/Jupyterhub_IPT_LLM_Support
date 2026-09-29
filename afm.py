"""
Additive Factors Model (AFM) scoring + Grey Area gating.

Implements the "Grey Area" approach (Chounta, Albacete et al., ECTEL 2017,
"The 'Grey Area': A Computational Approach to Model the Zone of Proximal
Development") for deciding whether a student should receive an LLM hint.

Model
-----
AFM predicts, in log-odds form:

    ln(p / (1-p)) = theta_i + beta_k + gamma_k * N_ik

    theta_i  = ability of student i
    beta_k   = difficulty of knowledge component (KC) k
    gamma_k  = learning rate of KC k
    N_ik     = number of times student i has already practiced KC k
               ("opportunity count"), BEFORE the current attempt

Fitting (learning theta/beta/gamma from data) happens in two layers:

1. update_model_online() -- runs INLINE, on every single attempt, right
   here in this module. It takes one stochastic-gradient step on theta_i
   (and beta_k/gamma_k) using only that one attempt's outcome, so the very
   next request already sees an updated probability. This is what makes
   feedback decisions track a student's live performance in real time,
   with no delay.
2. fit_afm.py -- runs periodically (default every 120s, as its own
   JupyterHub service) and re-solves the exact logistic-regression MLE
   from every attempt logged so far. This doesn't make things "more live"
   (the online updates already are live) -- it corrects any drift the
   incremental updates accumulate over a long session, keeping the model
   anchored to the full dataset.

Both layers write into the same `afmModel` collection; evaluate_grey_area()
below always reads whatever is currently there, so it automatically
reflects the latest of either.

Cold start
----------
A student or KC with no fitted parameters yet (new student, new KC, or no
attempt has ever been logged) falls back to population-average values via
a shrinkage estimate:

    theta_hat = (n * theta_observed + K * theta_population) / (n + K)

As n -> 0 (no data), theta_hat -> theta_population. As n grows, theta_hat
-> the student/KC's own value. With no population value set either (e.g.
day one, before any attempt has ever been logged), everything defaults to
0, which makes p = sigmoid(0) = 0.5 -- i.e. every brand-new student/KC
combination starts out exactly inside any Grey Area band, so feedback is
never blocked for lack of data.
"""

import math

# Number of "pseudo-observations" the population average is worth when
# shrinking a student/KC's own estimate toward it. Same role as the
# regularization used in online/temporal AFM variants (t-AFM). Higher =
# trusts the population average longer before an individual's own data
# takes over.
SHRINKAGE_K = 5

# Hard bound on any single fitted parameter's magnitude, in log-odds units.
# +/-6 already corresponds to p in [~0.0025, ~0.9975] -- comfortably wide
# for any real decision. This guards against degenerate near-0/near-1
# predictions, whichever of two ways they could arise: (1) fit_afm.py's
# batch MLE hitting (quasi-)complete separation -- a well-known failure
# mode of fixed-effects logistic regression when a student's outcomes so
# far are all one class, which is common with the small sample sizes of
# an early pilot (see e.g. Firth, 1993, on penalized likelihood as the
# standard remedy -- fit_afm.py additionally uses a much smaller C for
# the same reason); or (2) runaway accumulation of online updates over an
# unusually long session. Every write path (update_model_online here, and
# fit_afm.py's batch fit) clips through this before storing.
PARAM_CLIP = 6.0


def clip_param(value):
    return max(-PARAM_CLIP, min(PARAM_CLIP, value))

# ── Personalized Grey Area (P-GA) ────────────────────────────────────────
# Sheng & Chounta, "Beyond One-Size-Fits-All: Personalizing Computational
# Proxies of the Zone of Proximal Development Through Help-Seeking
# Behaviors" -- replaces the original fixed (0.3, 0.7) band (which was
# centered on p=0.5, following "Area 4" of Chounta et al., ECTEL 2017)
# with a center and width that both adapt per student+KC. See
# get_grey_area_bounds for how the pieces below combine.
#
# NOTE on the constants: the paper's full text sits behind a paywall we
# don't have access to, so PGA_ALPHA/PGA_BASE_HALF_WIDTH/PGA_GROWTH_RATE/
# PGA_MAX_HINTS/PGA_MAX_SHIFT below were carried over from an earlier,
# UNVERIFIED reading of it -- they should not be cited as "the paper's
# values" until someone checks them against the actual equations.
#
# Two real bugs have been found and fixed in how the width was built, both
# from logged data, both in the same underlying spot (how delta_upper/
# delta_lower combined with the base half-width):
#
# 1. (2026-09-29, first pass) The original delta_upper/delta_lower were
#    h_k/(PGA_MAX_HINTS+1) and (PGA_MAX_HINTS-h_k)/(PGA_MAX_HINTS+1) --
#    these summed to a CONSTANT (PGA_MAX_HINTS/(PGA_MAX_HINTS+1) =~ 0.83)
#    regardless of h_k, added on top of 2*PGA_BASE_HALF_WIDTH=0.4, for a
#    pre-clamp w_upper+w_lower of 1.233 -- strictly more than the [0,1]
#    budget available around ANY center. That guaranteed at least one
#    bound clamped to 0/1 on literally every attempt (confirmed: 138/138
#    real logged attempts did).
# 2. (2026-09-29, second pass) Scaling that same additive delta down
#    (PGA_DELTA_SCALE) stopped the guaranteed-saturation problem, but the
#    deeper issue was structural, not just a matter of size: delta_upper
#    and delta_lower were two INDEPENDENTLY-ADDED terms rather than a
#    proper skew, so their (scaled) sum was still a nonzero constant added
#    on top of the base every time -- the band was ALWAYS wider than
#    2*PGA_BASE_HALF_WIDTH, never just reallocated between the two sides.
#    Deployed and tested (2026-09-29, 37 fresh attempts): average width
#    0.565 (vs. the intended 0.4, i.e. the original non-personalized
#    band's width) and 37/37 attempts landed "in" the zone -- confirming
#    this as the reason feedback was skewing almost entirely to
#    instructional-text hints instead of a real below/in/above split.
#
# The fix: hint_skew below is a proper zero-sum trade-off between the two
# sides (added to upper, subtracted from lower -- the same pattern
# _signed_shift already used correctly), bounded by PGA_HINT_SKEW_FRACTION
# * PGA_BASE_HALF_WIDTH, so absent any incorrect-streak shift,
# w_upper + w_lower == 2*PGA_BASE_HALF_WIDTH exactly, no matter what h_k
# is -- h_k only decides how that fixed budget splits between the two
# sides, never how much total budget there is. Simulated against 523 real
# logged attempts (combining both exports so far): at the unchanged
# PGA_BASE_HALF_WIDTH=0.20, this alone drops "in zone" from the observed
# 100% to roughly 56%, with ~20% below and ~24% above -- see chat for the
# full table across narrower PGA_BASE_HALF_WIDTH candidates if 56% "in"
# still feels too high once more real data comes in.
PGA_ALPHA = 0.4
# weight on the GLOBAL threshold in the center blend (Eq. 1) -- 0.4
# global / 0.6 local, giving individual performance history the larger
# say in a student's own personalized center.
PGA_BASE_HALF_WIDTH = 0.20
# w0: base half-width on each side of the center, before any adjustment
# -- same magnitude as the original fixed band's +/-0.2 around 0.5. This
# is now genuinely the TOTAL typical width budget (2*w0), not just a
# floor that hint_skew/shift get added on top of -- see the note above.
PGA_GROWTH_RATE = 0.20
# r: how fast the incorrect-streak shift f(L) grows per consecutive
# wrong-first-attempt opportunity.
PGA_MAX_HINTS = 5
# n: hint count cap per opportunity (Rachatasumrit & Koedinger, 2021's
# assistance-score convention, adopted by the P-GA paper).
PGA_MAX_SHIFT = 0.5 * (1 - PGA_BASE_HALF_WIDTH)
# w_max: cap on f(L) itself, preventing a long struggle streak from
# expanding/contracting a boundary without bound.
PGA_HINT_SKEW_FRACTION = 0.75
# Our own addition (not from the paper): how much of PGA_BASE_HALF_WIDTH
# hint usage on the current cell can shift from one side to the other.
# At h_k=0 (no hints yet), the lower side shrinks to (1-0.75)=25% of
# PGA_BASE_HALF_WIDTH while the upper side grows to 175% of it, and it's
# exactly mirrored at h_k=PGA_MAX_HINTS -- always trading between the two
# sides, never adding to their sum. 0.75 leaves a floor (a side never
# fully collapses to 0 from hint_skew alone) while still letting hint
# count meaningfully swing which side of center is more permissive.


def sigmoid(x):
    try:
        return 1.0 / (1.0 + math.exp(-x))
    except OverflowError:
        return 0.0 if x < 0 else 1.0


def _get_global_threshold(db):
    """Population-wide classification threshold (t_global in the P-GA
    paper) -- the ROC-optimal cutoff for predicting outcome from
    predictedProbability, fit periodically across ALL students'
    opportunity-defining attempts by fit_afm.py (Youden's J: tpr - fpr,
    maximized). Falls back to 0.5 (i.e. "no information yet, split the
    difference") before the first successful fit -- which also matches
    the original fixed band's center, so cold start behaves the same as
    before this change.
    """
    doc = db.afmModel.find_one({"type": "population"}) or {}
    return doc.get("tGlobal", 0.5)


def _get_local_threshold(db, student, kc):
    """This student's own average predicted-correctness on this KC so far
    (t_i,j^local in the P-GA paper) -- the mean predictedProbability
    across their own opportunity-defining attempts on this KC. Falls back
    to the global threshold when they have no opportunities on this KC
    yet, so a brand-new KC for them doesn't pull their personalized
    center toward an arbitrary default.
    """
    pipeline = [
        {"$match": {"user": student, "KC": kc, "countsAsOpportunity": True}},
        {"$group": {"_id": None, "avg": {"$avg": "$predictedProbability"}}},
    ]
    result = list(db.afmAttempts.aggregate(pipeline))
    if not result or result[0].get("avg") is None:
        return _get_global_threshold(db)
    return result[0]["avg"]


def get_personalized_center(db, student, kc):
    """P-GA center (Eq. 1): a weighted blend of the population-wide
    ROC-optimal threshold and this student's own average performance on
    this KC -- the personalized classification threshold that separates
    "predicted correct" from "predicted incorrect" for this student+KC.
    """
    t_global = _get_global_threshold(db)
    t_local = _get_local_threshold(db, student, kc)
    return PGA_ALPHA * t_global + (1 - PGA_ALPHA) * t_local


def _get_hint_count_this_opportunity(db, student, kc, cell_identifier):
    """h_k in the P-GA paper: how many of this student's attempts SO FAR
    on this specific cell (i.e. within the CURRENT opportunity, across
    any retries already made on it) actually produced a hint -- capped at
    PGA_MAX_HINTS, using hint count alone rather than hint-plus-incorrect
    (Rachatasumrit & Koedinger, 2021's convention, adopted by the P-GA
    paper). "Produced a hint" means afmAttempts.feedbackGiven=True, which
    logService.py only sets when a real hint (workedExample or
    instructionalText content) was actually shown -- not for a plain
    success, the "above zone" no-hint-needed message, or a capped-silent
    attempt.

    In this system students don't explicitly REQUEST hints -- they get
    one automatically right after an error, whenever the zone calls for
    it (per your mapping: no feedback = correct or "above" = doing well
    enough; a hint given = the below/in-zone response to an error). h_k
    here is simply how many of those automatic hints have already landed
    on THIS attempt at THIS cell, since that's the direct analogue of
    "how many times has this student already asked for help on this
    problem" in the paper's own hint-seeking framing.
    """
    count = db.afmAttempts.count_documents({
        "user": student, "KC": kc, "cellIdentifier": cell_identifier,
        "feedbackGiven": True,
    })
    return min(count, PGA_MAX_HINTS)


def _get_consecutive_incorrect_streak(db, student, kc):
    """L in the P-GA paper: how many opportunities IN A ROW this
    student's FIRST attempt has been incorrect on this KC, walking
    backwards from the most recent opportunity and stopping at the last
    correct first attempt (or the start of their history on this KC).
    Only opportunity-defining rows are considered, since only those carry
    a "first attempt" outcome at all -- retries within an opportunity
    don't extend or break this streak.
    """
    rows = db.afmAttempts.find(
        {"user": student, "KC": kc, "countsAsOpportunity": True},
        {"outcome": 1, "_id": 0},
    ).sort("timestamp", -1)
    streak = 0
    for row in rows:
        if row.get("outcome") == 0:
            streak += 1
        else:
            break
    return streak


def _signed_shift(streak_length):
    """f(L) in the P-GA paper: grows linearly with the incorrect-streak
    length at PGA_GROWTH_RATE, capped at PGA_MAX_SHIFT. Always added to
    the upper width and subtracted from the lower width (Eq. 2) -- a
    sustained streak of wrong first attempts makes the band skew more
    permissive above center (easier to be seen as needing a hint rather
    than "independent") and stricter below center (easier to be
    classified fully "below" -- genuinely beyond this hint mechanism --
    rather than lingering in the hint-eligible band indefinitely).
    """
    return min(PGA_GROWTH_RATE * streak_length, PGA_MAX_SHIFT)


def get_grey_area_bounds(db, student, kc, cell_identifier):
    """Returns (lower, upper) probability bounds for the Personalized
    Grey Area (P-GA), per Sheng & Chounta, "Beyond One-Size-Fits-All:
    Personalizing Computational Proxies of the Zone of Proximal
    Development Through Help-Seeking Behaviors" (Eq. 1-2).

    Unlike the original fixed (0.3, 0.7) band, both the CENTER and the
    WIDTH are personalized:
      - center blends a population-wide ROC-optimal threshold with this
        student's own average performance on this KC
        (get_personalized_center).
      - width is asymmetric and reacts to two behavioral signals: hint
        usage on the CURRENT cell (more hints so far this opportunity =>
        more benefit of the doubt above center, less below), and a run of
        consecutive wrong first attempts on this KC (the longer the
        streak, the more the same asymmetric skew is reinforced). Both
        signals SKEW the band (trade width from one side to the other);
        neither one inflates its total size -- see the PGA_HINT_SKEW_
        FRACTION comment above for why that distinction matters.
    """
    center = get_personalized_center(db, student, kc)

    h_k = _get_hint_count_this_opportunity(db, student, kc, cell_identifier)
    # hint_skew ranges from -PGA_HINT_SKEW_FRACTION*PGA_BASE_HALF_WIDTH (at
    # h_k=0) to +that same amount (at h_k=PGA_MAX_HINTS), and is added to
    # the upper width / subtracted from the lower width below -- the same
    # zero-sum pattern _signed_shift already uses, so more hints so far
    # this opportunity move width FROM the lower side TO the upper side
    # (more benefit of the doubt above center) rather than adding width
    # to both.
    hint_skew_max = PGA_HINT_SKEW_FRACTION * PGA_BASE_HALF_WIDTH
    hint_skew = hint_skew_max * (2 * h_k / PGA_MAX_HINTS - 1)

    streak = _get_consecutive_incorrect_streak(db, student, kc)
    shift = _signed_shift(streak)

    w_upper = min(PGA_BASE_HALF_WIDTH + hint_skew + shift, 1.0)
    w_lower = max(PGA_BASE_HALF_WIDTH - hint_skew - shift, 0.0)

    upper = min(center + w_upper, 1.0)
    lower = max(center - w_lower, 0.0)
    # Degenerate-edge safety net: extreme personalization inputs
    # shouldn't ever be able to invert the band.
    if lower > upper:
        lower, upper = upper, lower
    return lower, upper


def get_opportunity_count(db, student, kc, cell_identifier):
    """How many opportunities `student` has already had at `kc`, before now
    -- NOT counting `cell_identifier` itself, regardless of whether it has
    already been attempted.

    Classic AFM (Cen, Koedinger & Junker, 2006) defines one opportunity per
    PROBLEM/STEP a KC appears in, not per raw attempt at that problem --
    retrying the same cell five times before succeeding is still ONE
    opportunity, not five (this matches the standard "Correct First
    Attempt" convention from the PSLC DataShop tooling AFM was originally
    fit against). Every individual attempt is still logged as its own row
    in afmAttempts (see log_afm_attempt/is_new_opportunity below), but
    retries on an already-seen cellIdentifier share it with the attempt
    that first created the opportunity, so counting DISTINCT
    cellIdentifiers -- rather than raw afmAttempts rows -- gives the
    correct opportunity count.

    The cell_identifier exclusion matters for that same reason: the very
    FIRST attempt at a cell correctly doesn't count itself (it isn't in
    afmAttempts yet), but without excluding it explicitly, any RETRY on
    that same cell would see a count one higher than the first attempt
    did -- simply because, by then, that first attempt has already been
    logged and its cellIdentifier now shows up in the distinct count. That
    off-by-one isn't real progress on the student's part, but it still
    shifts predict_success_probability's N_ik term, which could silently
    move a retry into a different predicted probability -- and even a
    different Grey Area zone -- than the attempt that originally defined
    this opportunity. Excluding cell_identifier keeps every attempt within
    one opportunity (the first one, and every retry after it) looking at
    the exact same N_ik.
    """
    return len(db.afmAttempts.distinct(
        "cellIdentifier",
        {"user": student, "KC": kc, "cellIdentifier": {"$ne": cell_identifier}},
    ))


def is_new_opportunity(db, student, kc, cell_identifier):
    """True the first time `student` attempts `cell_identifier` for `kc` --
    i.e. this is the attempt that DEFINES this opportunity's outcome
    (Correct First Attempt). False for any later retry on the same cell:
    those still get logged as their own row (see log_afm_attempt), but
    they don't create a new opportunity and shouldn't feed
    update_model_online again -- the opportunity's outcome was already
    fixed by the first attempt, exactly as fit_afm.py's batch refit
    should also only train on opportunity-defining rows.
    """
    return db.afmAttempts.count_documents(
        {"user": student, "KC": kc, "cellIdentifier": cell_identifier}
    ) == 0


ONLINE_LEARNING_RATE = 0.15


def update_model_online(db, student, kc, opportunity_count, outcome):
    """Nudges this student's theta_i and this KC's beta_k/gamma_k by one
    stochastic-gradient step, immediately, using only this single attempt.

    This is what makes probabilities move in real time: every attempt
    updates the model right here, synchronously, instead of waiting for
    fit_afm.py's periodic batch refit. It's the online-learning counterpart
    of the same AFM logistic model fit_afm.py fits in batch -- a single
    step of gradient ascent on the same log-likelihood, which is a standard
    way to do online/incremental logistic regression (and matches how
    "online AFM" / t-AFM variants keep parameters current between full
    refits).

    fit_afm.py's periodic full refit still runs on top of this (see
    jupyterhub_config.py's afm-refit service) and periodically re-solves
    the *exact* MLE from all logged attempts -- that keeps these
    per-attempt nudges from drifting over a long session, while this
    function is what makes each individual attempt visible immediately.

    Step size, and why gamma is normalized
    ---------------------------------------
    theta_i and beta_k each move by at most +/- ONLINE_LEARNING_RATE per
    attempt (the raw gradient of the log-likelihood w.r.t. either is just
    `error = outcome - predicted_p`, which is already bounded in [-1, 1]).
    gamma_k's raw gradient is `error * opportunity_count` instead -- with
    NO cap, since opportunity_count grows over a session. Left unnormalized,
    a single lucky/unlucky attempt late in a session (large opportunity_count)
    can swing gamma_k by several log-odds units in one step, which is exactly
    what produced a 0.09->0.99 jump in one attempt during testing. Dividing
    by (1 + opportunity_count) keeps gamma_k's step bounded the same way
    theta_i/beta_k already are, regardless of how far into the session a
    student is -- this is a standard stabilization technique for online
    gradient methods with differently-scaled features (see e.g. Bottou,
    2010, on the importance of feature scaling in SGD).
    """
    pop = _get_population_params(db)

    student_doc = db.afmModel.find_one({"type": "student", "student": student}) or {}
    theta = student_doc.get("theta", pop["theta"])
    n_student = student_doc.get("n", 0)

    kc_doc = db.afmModel.find_one({"type": "kc", "kc": kc}) or {}
    beta = kc_doc.get("beta", pop["beta"])
    gamma = kc_doc.get("gamma", pop["gamma"])
    n_kc = kc_doc.get("n", 0)

    predicted_p = sigmoid(theta + beta + gamma * opportunity_count)
    error = outcome - predicted_p  # >0 if student did better than predicted

    theta_new = clip_param(theta + ONLINE_LEARNING_RATE * error)
    beta_new = clip_param(beta + ONLINE_LEARNING_RATE * error)
    # Normalized so |gamma step| < ONLINE_LEARNING_RATE regardless of how
    # large opportunity_count gets (see docstring above).
    gamma_new = clip_param(gamma + ONLINE_LEARNING_RATE * error * (
        opportunity_count / (1 + opportunity_count)
    ))

    now = __import__("datetime").datetime.now().timestamp()

    db.afmModel.update_one(
        {"type": "student", "student": student},
        {"$set": {
            "type": "student", "student": student,
            "theta": theta_new, "n": n_student + 1, "updatedAt": now,
        }},
        upsert=True,
    )
    db.afmModel.update_one(
        {"type": "kc", "kc": kc},
        {"$set": {
            "type": "kc", "kc": kc,
            "beta": beta_new, "gamma": gamma_new, "n": n_kc + 1, "updatedAt": now,
        }},
        upsert=True,
    )


def _get_population_params(db):
    doc = db.afmModel.find_one({"type": "population"}) or {}
    return {
        "theta": doc.get("thetaAvg", 0.0),
        "beta": doc.get("betaAvg", 0.0),
        "gamma": doc.get("gammaAvg", 0.0),
    }


def get_student_theta(db, student):
    pop = _get_population_params(db)
    doc = db.afmModel.find_one({"type": "student", "student": student})
    if not doc:
        return pop["theta"]
    n = doc.get("n", 0)
    theta_observed = doc.get("theta", pop["theta"])
    return (n * theta_observed + SHRINKAGE_K * pop["theta"]) / (n + SHRINKAGE_K)


def get_kc_params(db, kc):
    pop = _get_population_params(db)
    doc = db.afmModel.find_one({"type": "kc", "kc": kc})
    if not doc:
        return pop["beta"], pop["gamma"]
    n = doc.get("n", 0)
    beta_observed = doc.get("beta", pop["beta"])
    gamma_observed = doc.get("gamma", pop["gamma"])
    beta = (n * beta_observed + SHRINKAGE_K * pop["beta"]) / (n + SHRINKAGE_K)
    gamma = (n * gamma_observed + SHRINKAGE_K * pop["gamma"]) / (n + SHRINKAGE_K)
    return beta, gamma


def predict_success_probability(db, student, kc, opportunity_count):
    """Real-time AFM prediction: p(student gets this KC's step right)."""
    theta = get_student_theta(db, student)
    beta, gamma = get_kc_params(db, kc)
    z = theta + beta + gamma * opportunity_count
    return sigmoid(z)


def evaluate_grey_area(db, student, kc, cell_identifier):
    """Runs the full real-time decision for one attempt: is THIS student,
    right now, above/in/below their own Personalized Grey Area for this
    KC (get_grey_area_bounds) -- computed fresh per student+KC+cell every
    time this is called, never cached, so it always reflects whatever the
    model and this student's own recent history currently say.

    cell_identifier is used twice here, for two different reasons:
      - get_opportunity_count excludes the current cell from its distinct
        count, so every attempt WITHIN one opportunity (the first attempt
        on a cell, and any retries after it) looks at the same N_ik
        instead of a retry silently drifting to a different N_ik (and
        potentially a different zone) than the attempt that defined the
        opportunity.
      - get_grey_area_bounds needs it too, since the P-GA band's WIDTH
        reacts to hint usage on the specific cell currently being
        attempted (_get_hint_count_this_opportunity).

    Returns a dict with everything needed both to decide whether to call
    the LLM and to log the attempt for later fitting:
        opportunityCount, predictedProbability, greyAreaLower,
        greyAreaUpper, inGreyArea, zone

    zone is one of "below", "in", "above" -- each means a different kind of
    feedback for an "adaptiveSupport" cell (see logService.py's askLLM):
      - "above": predicted_p > upper bound. The student is doing well
        enough on this KC that no hint is given at all -- just a plain
        "you don't need a hint" text message, not counted against either
        hint cap.
      - "in": inside the band -- the student receives instructional-text-
        style hints (up to 3 per cell).
      - "below": predicted_p < lower bound. The student receives
        worked-example-style hints instead (up to 3 per cell) -- a fuller
        worked-through example, since the gap suggests they need more
        scaffolding than an explanation alone.
    """
    opportunity_count = get_opportunity_count(db, student, kc, cell_identifier)
    predicted_p = predict_success_probability(db, student, kc, opportunity_count)
    lower, upper = get_grey_area_bounds(db, student, kc, cell_identifier)
    in_grey_area = lower <= predicted_p <= upper
    if predicted_p > upper:
        zone = "above"
    elif predicted_p < lower:
        zone = "below"
    else:
        zone = "in"
    return {
        "opportunityCount": opportunity_count,
        "predictedProbability": predicted_p,
        "greyAreaLower": lower,
        "greyAreaUpper": upper,
        "inGreyArea": in_grey_area,
        "zone": zone,
    }


def log_afm_attempt(db, student, kc, cell_identifier, opportunity_count,
                     outcome, predicted_probability=None, in_grey_area=None,
                     feedback_given=False, timestamp=None,
                     counts_as_opportunity=True,
                     grey_area_lower=None, grey_area_upper=None):
    """Logs one attempt -- EVERY attempt, including retries on a cell
    that's already had its opportunity scored -- to afmAttempts, so
    nothing about what a student actually did is lost.

    Only rows with counts_as_opportunity=True are opportunity-defining
    (the first attempt on this cellIdentifier for this KC): those are
    what fit_afm.py's batch refit trains on, and what get_opportunity_count
    counts. Retries (counts_as_opportunity=False, see is_new_opportunity)
    are kept in this same collection purely for visibility into everything
    a student tried within one opportunity -- they're never double-counted
    by the model, since caller logService.py only calls
    update_model_online for opportunity-defining rows.

    grey_area_lower/grey_area_upper: the actual Personalized Grey Area
    bounds this attempt was judged against (evaluate_grey_area's
    greyAreaLower/greyAreaUpper). Unlike the old fixed (0.3, 0.7) band,
    these move per student+KC+cell, so without logging them here there's
    no way to later tell WHAT band a given predictedProbability/zone was
    actually compared against -- only inGreyArea (in-or-not) survived
    before this. None for any row logged before this field existed.

    outcome: 1 for a successful run, 0 for a failed/erroring run.
    """
    db.afmAttempts.insert_one({
        "user": student,
        "KC": kc,
        "cellIdentifier": cell_identifier,
        "opportunityCount": opportunity_count,
        "outcome": outcome,
        "predictedProbability": predicted_probability,
        "inGreyArea": in_grey_area,
        "greyAreaLower": grey_area_lower,
        "greyAreaUpper": grey_area_upper,
        "feedbackGiven": feedback_given,
        "timestamp": timestamp,
        "countsAsOpportunity": counts_as_opportunity,
    })


# supportTypes that the Grey Area gate applies to. Other support types
# (genericSupport, personalizedSupport, customPrompt, noSupport) keep
# their existing always-on / always-off behavior untouched.
#
# "adaptiveSupport" is the single cell-metadata value course authors use
# for Grey-Area-driven cells: which of workedExample/instructionalText a
# given attempt actually gets (or neither) is decided per-attempt in
# logService.py's askLLM route, based on this student's live zone -- it is
# no longer a fixed, per-cell choice.
GREY_AREA_SUPPORT_TYPES = {"adaptiveSupport"}


def grey_area_applies(support_type, kc):
    return support_type in GREY_AREA_SUPPORT_TYPES and bool(kc)
