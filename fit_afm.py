"""
Fits the Additive Factors Model (AFM) from logged attempts and writes the
result into MongoDB for afm.py to use at request time.

This is a STANDALONE script -- it does not import logService.py (which
requires JUPYTERHUB_API_TOKEN and other Hub-service-only environment
variables at import time and therefore can't be run outside a running
Hub service).

It runs as its OWN persistent JupyterHub service (registered in
jupyterhub_config.py's c.JupyterHub.services, the same way `cull-idle`
is), refitting on a fixed interval for as long as the Hub is up -- no
manual step required. Every logged attempt (from any student, on any
KC) feeds into the next scheduled refit automatically; students' live
Grey Area probabilities move on their own as data accumulates during
class.

The interval is intentionally a periodic BATCH refit, not a per-attempt
online update: refitting a logistic regression after every single new
observation is wasteful and statistically noisy (one data point barely
moves a population-level fit), whereas re-solving the whole regression
every AFM_REFIT_INTERVAL_SECONDS seconds is cheap, stable, and matches
how periodic/temporal AFM refits are done in the literature (t-AFM).
Tune the interval with the AFM_REFIT_INTERVAL_SECONDS env var if you
want faster/slower turnaround; default is 120s.

You can still run it once by hand for debugging:

    docker compose exec jupyterhub python3 /srv/jupyterhub/fit_afm.py --once

What it does (each cycle)
--------------------------
1. Reads every attempt logged so far from `afmAttempts` (written by
   logService.py on every workedExample/instructionalText error or
   success event).
2. Fits AFM as a logistic regression using the classic dummy-coded
   parameterization (Cen, Koedinger & Junker, 2006):
       one indicator column per student  -> theta_i
       one indicator column per KC       -> beta_k
       one (KC indicator * opportunity count) column per KC -> gamma_k
   with NO separate intercept term -- the student columns collectively
   serve as per-student intercepts, which is the standard AFM setup.
3. Writes the fitted theta_i / beta_k / gamma_k, plus how many attempts
   each was fit from (needed for the shrinkage estimate in afm.py), and
   the population-average theta/beta/gamma, into the `afmModel`
   collection.

Requires numpy + scikit-learn (added to the Dockerfile).
"""

import os
import sys
import time
import logging

import numpy as np
from pymongo import MongoClient
from sklearn.linear_model import LogisticRegression

import afm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fit_afm")

# Minimum number of logged attempts before we bother fitting at all --
# below this, a regression is likely to be unstable/meaningless, and
# afm.py's population-average defaults (which start at 0, i.e. p=0.5)
# are a perfectly reasonable stand-in.
MIN_ATTEMPTS_TO_FIT = 20

# How often (seconds) to re-run the fit while this service is up.
REFIT_INTERVAL_SECONDS = int(os.environ.get("AFM_REFIT_INTERVAL_SECONDS", "120"))


def read_secret(name, env_fallback=None):
    """Same convention as logService.py: docker secret file, else env var."""
    secret_path = f"/run/secrets/{name}"
    if os.path.isfile(secret_path):
        with open(secret_path) as f:
            return f.read().strip()
    if env_fallback:
        val = os.environ.get(env_fallback)
        if val:
            return val
    raise RuntimeError(f"Secret {name} not found at {secret_path} or env {env_fallback}")


def get_db():
    mongoClient = MongoClient(
        host="mongodb",
        port=27017,
        username=read_secret("mongo_username", "MONGO_INITDB_ROOT_USERNAME"),
        password=read_secret("mongo_password", "MONGO_INITDB_ROOT_PASSWORD"),
        authSource="admin",
    )
    return mongoClient["loggedData"]


def fit_afm(db):
    attempts = list(db.afmAttempts.find(
        {}, {"user": 1, "KC": 1, "opportunityCount": 1, "outcome": 1}
    ))

    if len(attempts) < MIN_ATTEMPTS_TO_FIT:
        logger.info(
            "Only %d attempts logged (need >= %d) -- skipping fit for now. "
            "Real-time scoring will keep using population defaults (p=0.5).",
            len(attempts), MIN_ATTEMPTS_TO_FIT,
        )
        return

    students = sorted({a["user"] for a in attempts})
    kcs = sorted({a["KC"] for a in attempts})

    if len(students) < 2 or len(kcs) < 1:
        logger.info("Not enough distinct students/KCs yet -- skipping fit.")
        return

    student_index = {s: i for i, s in enumerate(students)}
    kc_index = {k: i for i, k in enumerate(kcs)}

    n_students = len(students)
    n_kcs = len(kcs)
    # Columns: [student one-hots] + [KC one-hots] + [KC * opportunity columns]
    n_cols = n_students + n_kcs + n_kcs
    X = np.zeros((len(attempts), n_cols))
    y = np.zeros(len(attempts))

    for row, a in enumerate(attempts):
        s_i = student_index[a["user"]]
        k_i = kc_index[a["KC"]]
        opp = a.get("opportunityCount", 0) or 0

        X[row, s_i] = 1.0
        X[row, n_students + k_i] = 1.0
        X[row, n_students + n_kcs + k_i] = opp
        y[row] = 1.0 if a.get("outcome") == 1 else 0.0

    if len(set(y.tolist())) < 2:
        logger.info(
            "All logged attempts have the same outcome so far (all correct "
            "or all incorrect) -- logistic regression needs both classes. "
            "Skipping fit until there's a mix."
        )
        return

    # fit_intercept=False: the student dummy columns already act as
    # per-student intercepts (theta_i), matching the AFM formula, which
    # has no separate global intercept term.
    #
    # C=1.0 (moderate L2 regularization), NOT the ~unregularized C=1e6
    # this used to run with. With one column per student, any student
    # whose outcomes so far are all the same class (all-correct or
    # all-incorrect -- routine with the small sample sizes of an early
    # pilot) causes (quasi-)complete separation: without regularization,
    # that student's coefficient has no finite MLE and the optimizer
    # drives it toward +/-infinity, corrupting not just that student's
    # predictions but the population average (and hence every cold-start
    # student's/KC's predictions too, since it's a mean over all of
    # them). L2 regularization is the standard remedy for separation in
    # logistic regression (see e.g. Firth, 1993 on penalized likelihood).
    # clip_param() below is a second, independent safety net regardless
    # of C.
    model = LogisticRegression(fit_intercept=False, C=1.0, solver="lbfgs", max_iter=2000)
    model.fit(X, y)
    coefs = model.coef_[0]

    theta = {s: afm.clip_param(float(coefs[student_index[s]])) for s in students}
    beta = {k: afm.clip_param(float(coefs[n_students + kc_index[k]])) for k in kcs}
    gamma = {k: afm.clip_param(float(coefs[n_students + n_kcs + kc_index[k]])) for k in kcs}

    # How many attempts contributed to each student's / KC's own estimate --
    # needed by afm.py's shrinkage formula.
    n_by_student = {s: 0 for s in students}
    n_by_kc = {k: 0 for k in kcs}
    for a in attempts:
        n_by_student[a["user"]] += 1
        n_by_kc[a["KC"]] += 1

    theta_avg = float(np.mean(list(theta.values())))
    beta_avg = float(np.mean(list(beta.values())))
    gamma_avg = float(np.mean(list(gamma.values())))

    now = __import__("datetime").datetime.now().timestamp()

    db.afmModel.update_one(
        {"type": "population"},
        {"$set": {
            "type": "population",
            "thetaAvg": theta_avg,
            "betaAvg": beta_avg,
            "gammaAvg": gamma_avg,
            "nAttemptsUsed": len(attempts),
            "nStudents": n_students,
            "nKCs": n_kcs,
            "fittedAt": now,
        }},
        upsert=True,
    )

    for s in students:
        db.afmModel.update_one(
            {"type": "student", "student": s},
            {"$set": {
                "type": "student",
                "student": s,
                "theta": theta[s],
                "n": n_by_student[s],
                "fittedAt": now,
            }},
            upsert=True,
        )

    for k in kcs:
        db.afmModel.update_one(
            {"type": "kc", "kc": k},
            {"$set": {
                "type": "kc",
                "kc": k,
                "beta": beta[k],
                "gamma": gamma[k],
                "n": n_by_kc[k],
                "fittedAt": now,
            }},
            upsert=True,
        )

    logger.info(
        "Fit complete: %d attempts, %d students, %d KCs. "
        "theta_avg=%.3f beta_avg=%.3f gamma_avg=%.3f",
        len(attempts), n_students, n_kcs, theta_avg, beta_avg, gamma_avg,
    )


def main():
    db = get_db()

    if "--once" in sys.argv:
        fit_afm(db)
        return

    logger.info(
        "AFM auto-refit service starting: refitting every %ds.",
        REFIT_INTERVAL_SECONDS,
    )
    while True:
        try:
            fit_afm(db)
        except Exception:
            # A transient Mongo hiccup or bad data point should never kill
            # this service -- just log it and try again next cycle. Real-time
            # scoring in afm.py keeps using the last successful fit (or the
            # population/cold-start default) in the meantime.
            logger.exception("AFM refit cycle failed; will retry next interval.")
        time.sleep(REFIT_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
