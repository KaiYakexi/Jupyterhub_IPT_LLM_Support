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

# Default Grey Area band, centered on p=0.5, following "Area 4" from the
# Chounta et al. paper. Kept as a function (not a constant) so a future
# per-student/per-KC personalized band size can replace this without
# touching any call site.
DEFAULT_GREY_AREA = (0.3, 0.7)


def sigmoid(x):
    try:
        return 1.0 / (1.0 + math.exp(-x))
    except OverflowError:
        return 0.0 if x < 0 else 1.0


def get_grey_area_bounds(db, student, kc):
    """Returns (lower, upper) probability bounds for the Grey Area.

    Currently a fixed band for everyone. Replace this function's body to
    plug in a personalized band size later -- every caller in this module
    goes through here, so nothing else needs to change.
    """
    return DEFAULT_GREY_AREA


def get_opportunity_count(db, student, kc):
    """How many times `student` has already attempted `kc`, before now."""
    return db.afmAttempts.count_documents({"user": student, "KC": kc})


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


def evaluate_grey_area(db, student, kc):
    """Runs the full real-time decision for one attempt.

    Returns a dict with everything needed both to decide whether to call
    the LLM and to log the attempt for later fitting:
        opportunityCount, predictedProbability, greyAreaLower,
        greyAreaUpper, inGreyArea, zone

    zone is one of "below", "in", "above" -- being outside the Grey Area
    means two very different things depending on which side you're on, and
    callers (the extension's UI) need to tell them apart:
      - "above": predicted_p > upper bound. The student is doing well
        enough on this KC that this hint mechanism isn't needed -- an
        "you've got this, keep going" message is appropriate.
      - "below": predicted_p < lower bound. The student is far enough
        below the target zone that this specific hint mechanism is judged
        unlikely to help -- telling them "you've got this" here would be
        actively wrong. The appropriate response is pointing them back to
        foundational material (lecture slides/tutorial) rather than
        encouraging them to keep attempting the same exercise unaided.
      - "in": inside the band -- normal hint/example generation proceeds.
    """
    opportunity_count = get_opportunity_count(db, student, kc)
    predicted_p = predict_success_probability(db, student, kc, opportunity_count)
    lower, upper = get_grey_area_bounds(db, student, kc)
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
                     feedback_given=False, timestamp=None):
    """Logs one attempt to the training set used by fit_afm.py's periodic
    full refit (kept for stability/audit -- see update_model_online for
    the immediate, per-attempt live update).

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
        "feedbackGiven": feedback_given,
        "timestamp": timestamp,
    })


# supportTypes that the Grey Area gate applies to. Other support types
# (genericSupport, personalizedSupport, customPrompt, noSupport) keep
# their existing always-on / always-off behavior untouched.
GREY_AREA_SUPPORT_TYPES = {"workedExample", "instructionalText"}


def grey_area_applies(support_type, kc):
    return support_type in GREY_AREA_SUPPORT_TYPES and bool(kc)
