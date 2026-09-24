# Nuclear Sentinel — Experiment 3
# Adaptive Calibration, Drift Awareness, State-Aware Digital Twin,
# and B3/M1 Gated Hybrid Decision Support

from pathlib import Path
import re, json, warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.cluster import MiniBatchKMeans
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix, average_precision_score

warnings.filterwarnings("ignore")
SEED=42
DATA_DIR=Path("/content")
OUT=Path("/content/Nuclear_Sentinel_Adaptive_Results"); OUT.mkdir(parents=True,exist_ok=True)
PRIMARY_Q=.995
CANDIDATE_Q=[.995,.999,.9995,.9999]
TARGET_NORMAL_FPR=.005  # predeclared 0.5% normal false-alarm budget
MAX_DT=12
N_STATES=2
MIN_STATE_CAL_ROWS=500
N_BOOT=1000
BLOCK=300

def locate(names):
    """Locate exact filenames or numbered copies such as ...(1).csv / ...(2).csv."""
    for n in names:
        p = DATA_DIR / n
        if p.exists():
            return p

    for n in names:
        stem = Path(n).stem
        suffix = Path(n).suffix
        patterns = [f"{stem}(*){suffix}", f"{stem}*{suffix}"]
        for pattern in patterns:
            hits = sorted(DATA_DIR.rglob(pattern))
            if hits:
                return hits[-1]
    return None

def load(p):
    """Load SWaT and repair Normal-v1's embedded real header row."""
    if p.suffix.lower() in [".xlsx", ".xls"]:
        df = pd.read_excel(p)
    else:
        df = pd.read_csv(p, low_memory=False)

    df.columns = [re.sub(r"\s+", " ", str(c).strip()) for c in df.columns]

    if len(df):
        first = [re.sub(r"\s+", " ", str(v).strip()) for v in df.iloc[0].tolist()]
        first_upper = [v.upper() for v in first]

        if "TIMESTAMP" in first_upper and "FIT101" in first_upper and "LIT101" in first_upper:
            df = df.iloc[1:].copy().reset_index(drop=True)
            df.columns = first
            print(f"Repaired embedded SWaT header: {p.name}")

    df.columns = [re.sub(r"\s+", " ", str(c).strip()) for c in df.columns]
    return df

def tidy(df):
    df = df.copy()
    df.columns = [re.sub(r"\s+", " ", str(c).strip()) for c in df.columns]
    return df

def label_col(df):
    for c in df.columns:
        s=c.lower().strip()
        if s in ["normal/attack","label","attack","class","target"] or ("normal" in s and "attack" in s): return c
    return None

def labels(s):
    if pd.api.types.is_numeric_dtype(s):
        x=pd.to_numeric(s,errors="coerce").fillna(0).to_numpy()
        return (x!=0).astype(int)
    x=s.astype(str).str.strip().str.lower()
    return (~x.isin({"normal","0","false","benign","none"})).astype(int).to_numpy()

def taxonomy(df):
    ctrl=[]; phys=[]
    for c in df.columns:
        u=c.upper().replace(" ","")
        if "TIMESTAMP" in u or "NORMAL/ATTACK" in u: continue
        isp=any(u.startswith(z) for z in ["FIT","LIT","AIT","DPIT","PIT"])
        isc=(u.startswith("MV") or re.match(r"^P\d+",u) is not None or u.startswith("UV")) and not u.startswith("PIT")
        if isp: phys.append(c)
        elif isc: ctrl.append(c)
    return sorted(set(ctrl)),sorted(set(phys))

def X(df,cols):
    z=df[cols].copy()
    for c in cols: z[c]=pd.to_numeric(z[c],errors="coerce")
    return z.replace([np.inf,-np.inf],np.nan).ffill().bfill().fillna(0)

def score(model,x): return -model.score_samples(x)

def met(y,p,s=None):
    tn,fp,fn,tp=confusion_matrix(y,p,labels=[0,1]).ravel()
    d=dict(macro_f1=f1_score(y,p,average="macro",zero_division=0),
           precision_attack=precision_score(y,p,zero_division=0),
           recall_attack=recall_score(y,p,zero_division=0),
           f1_attack=f1_score(y,p,zero_division=0),
           fpr=fp/(fp+tn) if fp+tn else np.nan,tn=int(tn),fp=int(fp),fn=int(fn),tp=int(tp))
    d["average_precision"]=average_precision_score(y,s) if s is not None and len(np.unique(y))>1 else np.nan
    return d

def save(df,name): df.to_csv(OUT/name,index=False)

normal_p=locate(["SWaT_Dataset_Normal_v1.xlsx","SWaT_Dataset_Normal_v1.csv"])
attack_p=locate(["SWaT_Dataset_Attack_v0.xlsx","SWaT_Dataset_Attack_v0.csv"])
attack_log_p=locate(["List_of_attacks_Final.xlsx","List_of_attacks_Final.csv"])
if normal_p is None or attack_p is None:
    raise FileNotFoundError("Upload SWaT_Dataset_Normal_v1 and SWaT_Dataset_Attack_v0 to /content or change DATA_DIR.")

normal=tidy(load(normal_p)); attack=tidy(load(attack_p))
print("\nNORMAL first columns:", normal.columns.tolist()[:12])
print("ATTACK first columns:", attack.columns.tolist()[:12])

# IMPORTANT: preserve the attack label BEFORE aligning common feature columns.
lc = label_col(attack)
if lc is None:
    raise ValueError(
        "Could not detect the SWaT attack label column after header repair. "
        f"Attack columns begin with: {attack.columns.tolist()[:15]}"
    )

attack_y = labels(attack[lc])

# Exclude labels/metadata from feature alignment.
normal_label = label_col(normal)
excluded = {lc, "_y"}
if normal_label is not None:
    excluded.add(normal_label)

common = [
    c for c in normal.columns
    if c in attack.columns and c not in excluded
]

# Preserve timestamp for optional reporting, but it will not enter the model taxonomy.
timestamp_candidates = [c for c in common if "timestamp" in c.lower()]
timestamp_col = timestamp_candidates[0] if timestamp_candidates else None

normal = normal[common].copy()
attack_features = attack[common].copy()

normal["_y"] = 0
attack = attack_features.copy()
attack["_y"] = attack_y

print("Detected attack label:", lc)
print("Common aligned columns:", len(common))
print("Normal rows:", len(normal))
print("Attack-file rows:", len(attack))
print("Labeled attack rows:", int(attack["_y"].sum()))

ctrl,phys=taxonomy(normal); b3=ctrl+phys
if not ctrl or not phys: raise ValueError("SWaT feature taxonomy failed; inspect column names.")

# Normal-only chronological train/calibration/development/test split
n=len(normal); a=int(.45*n); b=int(.65*n); c=int(.80*n)
tr=normal.iloc[:a].reset_index(drop=True)
cal=normal.iloc[a:b].reset_index(drop=True)
dev=normal.iloc[b:c].reset_index(drop=True)
nt=normal.iloc[c:].reset_index(drop=True)
save(pd.DataFrame({"partition":["train","calibration","development","normal_test","attack_file"],
                   "n_rows":[len(tr),len(cal),len(dev),len(nt),len(attack)]}),"R00_Data_Partitions.csv")

source_audit = pd.DataFrame({
    "item": ["normal_file", "attack_file", "attack_log", "attack_label", "timestamp_column",
             "control_features", "physical_features", "combined_B3_features"],
    "value": [str(normal_p), str(attack_p), str(attack_log_p) if attack_log_p else "not found",
              lc, timestamp_col if timestamp_col else "not found",
              len(ctrl), len(phys), len(b3)]
})
save(source_audit, "R00B_Input_Audit.csv")

# A0 B3 baseline
b3m=IsolationForest(n_estimators=300,contamination="auto",random_state=SEED,n_jobs=-1).fit(X(tr,b3))
b3cal=score(b3m,X(cal,b3)); b3nt=score(b3m,X(nt,b3)); b3att=score(b3m,X(attack,b3))
b3th=float(np.quantile(b3cal,PRIMARY_Q))

# Digital-twin residuals: normal-only RF expected-state models
targets=X(tr,phys).var().sort_values(ascending=False).head(min(MAX_DT,len(phys))).index.tolist()
dtm={}; scales={}
for t in targets:
    pred=[c for c in b3 if c!=t]; xx=X(tr,pred); yy=X(tr,[t])[t].to_numpy()
    m=RandomForestRegressor(n_estimators=120,max_features="sqrt",min_samples_leaf=2,random_state=SEED,n_jobs=-1).fit(xx,yy)
    r=np.abs(yy-m.predict(xx)); sc=np.median(np.abs(r-np.median(r)))*1.4826
    scales[t]=float(sc if np.isfinite(sc) and sc>1e-8 else max(np.std(r),1.0)); dtm[t]=m

def residuals(df):
    q={}
    for t in targets:
        pred=[c for c in b3 if c!=t]
        actual=X(df,[t])[t].to_numpy()
        q["DT_"+t]=np.abs(actual-dtm[t].predict(X(df,pred)))/(scales[t]+1e-8)
    return pd.DataFrame(q)

dtr,dtc,dtd,dtn,dta=[residuals(z) for z in [tr,cal,dev,nt,attack]]
def M(df,dt): return pd.concat([X(df,b3).reset_index(drop=True),dt.reset_index(drop=True)],axis=1)
m1=IsolationForest(n_estimators=300,contamination="auto",random_state=SEED,n_jobs=-1).fit(M(tr,dtr))
m1cal=score(m1,M(cal,dtc)); m1dev=score(m1,M(dev,dtd)); m1nt=score(m1,M(nt,dtn)); m1att=score(m1,M(attack,dta))
m1th=float(np.quantile(m1cal,PRIMARY_Q))

# Locked evaluation: untouched normal test + labeled attack file
y=np.r_[np.zeros(len(nt),dtype=int),attack["_y"].to_numpy(int)]
sb3=np.r_[b3nt,b3att]; sm1=np.r_[m1nt,m1att]
edt=pd.concat([dtn,dta],ignore_index=True)
A0=(sb3>b3th).astype(int); A1=(sm1>m1th).astype(int)

# A2 adaptive calibration — FIX v4
# ------------------------------------------------------------
# The previous version selected the quantile with the smallest normal-tail
# calibration error, which selected q=.9999 and became too conservative.
#
# v4 uses a PREDECLARED NORMAL FALSE-ALARM BUDGET of 0.5% (q=.995).
# Calibration and development NORMAL scores are pooled to estimate the
# threshold. No attack/test labels are used to choose it.
normal_design_scores = np.r_[m1cal, m1dev]
adaptive_q = 1.0 - TARGET_NORMAL_FPR
ath = float(np.quantile(normal_design_scores, adaptive_q))
aq = adaptive_q
A2 = (sm1 > ath).astype(int)

rows=[]
for q in CANDIDATE_Q:
    th=float(np.quantile(normal_design_scores,q))
    cal_fpr=float(np.mean(m1cal>th))
    dev_fpr=float(np.mean(m1dev>th))
    rows.append(dict(
        quantile=q,
        threshold=th,
        calibration_normal_fpr=cal_fpr,
        development_normal_fpr=dev_fpr,
        nominal_tail_rate=1-q,
        selected_for_A2=bool(abs(q-adaptive_q)<1e-12)
    ))
qt=pd.DataFrame(rows)
save(qt,"R02_Fixed_vs_Adaptive_Thresholds.csv")

# A3 drift-aware M1 — FIX v4
# ------------------------------------------------------------
# Drift is detected against the normal design reference. Unlike v3, a drift
# flag MUST change the decision threshold. We use a predeclared conservative
# q=.999 threshold during drift; otherwise A2's q=.995 threshold is used.
def wd(a,b):
    q=np.linspace(0,1,max(len(a),len(b)))
    return float(np.mean(np.abs(np.quantile(a,q)-np.quantile(b,q))))

def ks(a,b):
    a=np.sort(a); b=np.sort(b); v=np.sort(np.unique(np.r_[a,b]))
    return float(np.max(np.abs(
        np.searchsorted(a,v,side="right")/len(a) -
        np.searchsorted(b,v,side="right")/len(b)
    )))

DW=2000
DS=500
ref = normal_design_scores

# Estimate drift limits from NORMAL design blocks only.
wr=[]; kr=[]
for st in range(0,max(1,len(ref)-DW+1),DS):
    w=ref[st:st+DW]
    if len(w)>=500:
        wr.append(wd(ref,w))
        kr.append(ks(ref,w))

wlim=float(np.quantile(wr,.99)) if wr else np.inf
klim=float(np.quantile(kr,.99)) if kr else np.inf

drift_q=.999
drift_threshold=float(np.quantile(ref,drift_q))
if drift_threshold <= ath:
    # Hard guard: drift response must be distinct from the normal adaptive rule.
    drift_threshold=float(np.nextafter(ath, np.inf))

A3=np.zeros(len(y),int)
drift=np.zeros(len(y),int)
thist=np.full(len(y),ath,float)
dr=[]

for st in range(0,len(y),DS):
    en=min(len(y),st+DW)
    w=sm1[st:en]
    wdist=wd(ref,w)
    kstat=ks(ref,w)
    flag=int(wdist>wlim or kstat>klim)
    th=drift_threshold if flag else ath

    drift[st:en]=flag
    thist[st:en]=th
    A3[st:en]=(sm1[st:en]>th).astype(int)

    dr.append(dict(
        start_row=st,end_row=en-1,
        wasserstein=wdist,ks_statistic=kstat,
        wasserstein_limit=wlim,ks_limit=klim,
        drift_flag=flag,
        threshold_used=th,
        baseline_adaptive_threshold=ath,
        drift_threshold=drift_threshold
    ))

save(pd.DataFrame(dr),"R03_Distribution_Shift_Results.csv")

# A4 state-aware M1 — FIX v4
# ------------------------------------------------------------
# v3 used four states and produced states with zero calibration observations.
# v4 starts with TWO operating states derived from CONTROL variables only.
# The clustering model is fitted on normal TRAIN+CALIBRATION data.
# If either state has too few calibration observations, the experiment falls
# back to one global state rather than pretending an uncalibrated state exists.
state_fit_df = pd.concat([tr, cal], ignore_index=True)
state_model = make_pipeline(
    StandardScaler(),
    MiniBatchKMeans(
        n_clusters=N_STATES,
        random_state=SEED,
        batch_size=2048,
        n_init=20
    )
)
state_model.fit(X(state_fit_df,ctrl))

scal=state_model.predict(X(cal,ctrl))
sdev=state_model.predict(X(dev,ctrl))
seval=np.r_[state_model.predict(X(nt,ctrl)),state_model.predict(X(attack,ctrl))]

cal_counts=pd.Series(scal).value_counts().to_dict()
valid_two_state = all(cal_counts.get(s,0) >= MIN_STATE_CAL_ROWS for s in range(N_STATES))

if not valid_two_state:
    print("Operating-state calibration was sparse; falling back to one calibrated state.")
    scal=np.zeros(len(cal),dtype=int)
    sdev=np.zeros(len(dev),dtype=int)
    seval=np.zeros(len(y),dtype=int)
    effective_states=1
else:
    effective_states=N_STATES

# State thresholds use NORMAL calibration+development scores belonging to the
# same state. The false-alarm budget remains the predeclared 0.5%.
sth={}
sr=[]
for s in range(effective_states):
    z=np.r_[m1cal[scal==s],m1dev[sdev==s]]
    if len(z) < MIN_STATE_CAL_ROWS:
        th=ath
        fallback=True
    else:
        th=float(np.quantile(z,adaptive_q))
        fallback=False
    sth[s]=th
    sr.append(dict(
        state=s,
        n_normal_design_rows=int(len(z)),
        target_normal_fpr=TARGET_NORMAL_FPR,
        state_threshold=th,
        fallback_to_global=fallback
    ))

save(pd.DataFrame(sr),"R14_Operating_State_Definitions.csv")
stv=np.array([sth.get(int(s),ath) for s in seval])
A4=(sm1>stv).astype(int)

# DT residual evidence — TARGET-NORMAL CALIBRATION v5
# ------------------------------------------------------------
# v5 directly tests the residual-transfer problem found in v4.
#
# IMPORTANT ASSUMPTION:
# Target calibration assumes access to a known-normal commissioning/reference
# period in the target environment. Attack labels are NOT used to choose the
# quantile, residual-count rule, or optimize final performance.
DT_RESIDUAL_Q = .995
TARGET_CAL_FRACTION = .20
MIN_TARGET_NORMAL_CAL = 1000
MIN_EXTREME_RESIDUALS = 2 if edt.shape[1] >= 2 else 1

# Source-normal residual thresholds retained as the transfer baseline.
dt_source_design = pd.concat([dtc, dtd], ignore_index=True)
source_residual_thresholds = dt_source_design.quantile(DT_RESIDUAL_Q)

# Chronological target calibration / locked evaluation split.
n_external = len(y)
target_cut = int(np.floor(n_external * TARGET_CAL_FRACTION))
target_cut = max(1, min(target_cut, n_external - 1))
target_cal_idx = np.arange(target_cut)
locked_eval_idx = np.arange(target_cut, n_external)

# Use known-normal observations from the target commissioning/reference segment.
# Labels are used only to identify the known-normal reference subset, not to tune
# q=.995 or MIN_EXTREME_RESIDUALS.
target_normal_idx = target_cal_idx[y[target_cal_idx] == 0]
if len(target_normal_idx) < MIN_TARGET_NORMAL_CAL:
    raise ValueError(
        f"Only {len(target_normal_idx)} known-normal target calibration rows; "
        f"need at least {MIN_TARGET_NORMAL_CAL}."
    )

dt_target_cal = edt.iloc[target_normal_idx].reset_index(drop=True)
target_residual_thresholds = dt_target_cal.quantile(DT_RESIDUAL_Q)

# Apply BOTH threshold systems to the same external stream.
source_exceed = edt.gt(source_residual_thresholds, axis=1)
target_exceed = edt.gt(target_residual_thresholds, axis=1)

source_exceed_count = source_exceed.sum(axis=1).to_numpy()
target_exceed_count = target_exceed.sum(axis=1).to_numpy()

source_elevated_dt = (source_exceed_count >= MIN_EXTREME_RESIDUALS).astype(int)
target_elevated_dt = (target_exceed_count >= MIN_EXTREME_RESIDUALS).astype(int)

# A5 uses target-calibrated DT deviation.
exceed_count = target_exceed_count
elevated_dt_deviation = target_elevated_dt
hdt = elevated_dt_deviation  # backward-compatible variable name only

# Descriptive residual weights remain for analysis; they do not define the gate.
arr = dt_source_design.to_numpy(float)
disp = np.nanmedian(np.abs(arr - np.nanmedian(arr, axis=0)), axis=0)
rw = 1 / (disp + 1e-6)
rw = np.clip(rw, 0, np.nanpercentile(rw, 95))
rw = rw / rw.sum()

residual_audit = pd.DataFrame({
    "dt_feature": dt_source_design.columns,
    "source_normal_dispersion": disp,
    "analysis_weight": rw,
    "source_normal_threshold": source_residual_thresholds.values,
    "target_normal_threshold": target_residual_thresholds.values,
    "threshold_quantile": DT_RESIDUAL_Q,
    "target_minus_source_threshold":
        target_residual_thresholds.values - source_residual_thresholds.values
})
save(residual_audit, "R13_Residual_Weighting.csv")

# Locked source-vs-target transfer audit.
locked_y = y[locked_eval_idx]
transfer_rows = []
for threshold_system, counts, flags in [
    ("source_normal", source_exceed_count, source_elevated_dt),
    ("target_normal", target_exceed_count, target_elevated_dt),
]:
    c = counts[locked_eval_idx]
    f = flags[locked_eval_idx]
    for label_value, label_name in [(0, "normal"), (1, "attack")]:
        mask = locked_y == label_value
        if mask.sum() == 0:
            continue
        transfer_rows.append({
            "threshold_system": threshold_system,
            "evaluation_class": label_name,
            "n": int(mask.sum()),
            "mean_extreme_residual_count": float(np.mean(c[mask])),
            "median_extreme_residual_count": float(np.median(c[mask])),
            "elevated_dt_deviation_rate": float(np.mean(f[mask])),
            "min_extreme_residuals_rule": MIN_EXTREME_RESIDUALS,
            "residual_threshold_quantile": DT_RESIDUAL_Q
        })
save(pd.DataFrame(transfer_rows), "R13B_DT_Evidence_Audit.csv")

# Per-feature locked transfer audit.
feature_rows = []
for feature in edt.columns:
    src_flag = source_exceed.loc[locked_eval_idx, feature].to_numpy()
    tgt_flag = target_exceed.loc[locked_eval_idx, feature].to_numpy()
    for label_value, label_name in [(0, "normal"), (1, "attack")]:
        mask = locked_y == label_value
        if mask.sum() == 0:
            continue
        feature_rows.append({
            "dt_feature": feature,
            "evaluation_class": label_name,
            "source_threshold_exceedance_rate": float(np.mean(src_flag[mask])),
            "target_threshold_exceedance_rate": float(np.mean(tgt_flag[mask]))
        })
save(pd.DataFrame(feature_rows), "R13C_DT_Per_Feature_Transfer_Audit.csv")

save(pd.DataFrame([{
    "external_rows_total": n_external,
    "target_calibration_rows_total": len(target_cal_idx),
    "target_calibration_normal_rows": len(target_normal_idx),
    "locked_evaluation_rows": len(locked_eval_idx),
    "target_calibration_fraction": TARGET_CAL_FRACTION,
    "residual_threshold_quantile": DT_RESIDUAL_Q,
    "min_extreme_residuals_rule": MIN_EXTREME_RESIDUALS,
    "calibration_assumption":
        "known-normal target-environment commissioning/reference period"
}]), "R13D_DT_Target_Calibration_Provenance.csv")

# A5 B3/M1 gated hybrid — FIX v4
# ------------------------------------------------------------
# Preserve B3 alerts. For M1-only alerts, escalation requires:
#   1) state-aware M1 abnormality,
#   2) target-calibrated elevated DT deviation (multiple residual channels),
#   3) no detected distribution-shift flag.
#
# This prevents DT residual evidence from acting as an unconditional attack
# detector and makes disagreement handling explicit.
A5=np.zeros(len(y),int)
states=[]

for i,(bb,mm) in enumerate(zip(A0,A4)):
    if bb==0 and mm==0:
        st="B3_normal__M1_normal"
        final=0
    elif bb==1 and mm==1:
        st="B3_abnormal__M1_abnormal"
        final=1
    elif bb==1 and mm==0:
        st="B3_abnormal__M1_normal"
        final=1
    else:
        st="B3_normal__M1_abnormal"
        final=int(elevated_dt_deviation[i]==1 and drift[i]==0)

    states.append(st)
    A5[i]=final

agree=pd.DataFrame({
    "true_label":y,
    "B3_alert":A0,
    "M1_state_aware_alert":A4,
    "agreement_state":states,
    "extreme_dt_residual_count":exceed_count,
    "elevated_dt_deviation":elevated_dt_deviation,
    "drift_flag":drift,
    "hybrid_alert":A5
})

agreement_summary=agree.groupby("agreement_state").agg(
    n=("true_label","size"),
    actual_attack_rate=("true_label","mean"),
    hybrid_alert_rate=("hybrid_alert","mean"),
    mean_extreme_dt_residuals=("extreme_dt_residual_count","mean"),
    elevated_dt_deviation_rate=("elevated_dt_deviation","mean"),
    drift_rate=("drift_flag","mean")
).reset_index()

save(agreement_summary,"R05_B3_M1_Agreement_Disagreement.csv")

# Evidence-confidence score — FIX v4
# ------------------------------------------------------------
# Experimental evidence score only; NOT a probability of cyberattack.
def pct(v,ref):
    r=np.sort(np.asarray(ref))
    return np.searchsorted(r,v,side="right")/max(len(r),1)

pb=pct(sb3,b3cal)
pm=pct(sm1,normal_design_scores)

# DT evidence is based on the fraction of DT channels exceeding their
# predeclared normal threshold, rather than the unstable weighted aggregate.
dt_fraction = exceed_count / max(dt_design.shape[1],1)
ag=(A0==A4).astype(float)

conf=np.clip(
    (.30*pb + .30*pm + .30*dt_fraction + .10*ag) *
    np.where(drift==1,.80,1.0),
    0,1
)

save(pd.DataFrame({
    "true_label":y,
    "B3_score_percentile":pb,
    "M1_score_percentile":pm,
    "DT_extreme_fraction_target_calibrated":dt_fraction,
    "extreme_dt_residual_count":exceed_count,
    "B3_M1_agreement":ag,
    "drift_flag":drift,
    "evidence_confidence":conf,
    "hybrid_alert":A5
}),"R10_Confidence_Evidence_Analysis.csv")

configs={"A0_B3_Fixed":(A0,sb3),"A1_M1_Fixed":(A1,sm1),"A2_M1_Adaptive":(A2,sm1),
         "A3_M1_DriftAware":(A3,sm1),"A4_M1_StateAware":(A4,sm1),"A5_B3_M1_Hybrid":(A5,conf)}
perf=[]
for name,(p,s) in configs.items():
    r={"configuration":name}; r.update(met(y,p,s)); perf.append(r)
perf=pd.DataFrame(perf); save(perf,"R01_Adaptive_Model_Performance.csv")
save(perf[perf.configuration.isin(["A2_M1_Adaptive","A3_M1_DriftAware","A4_M1_StateAware","A5_B3_M1_Hybrid"])],
     "R06_Hybrid_Gating_Performance.csv")

# State-specific performance
spr=[]
for state in range(effective_states):
    mask=seval==state
    for name in ["A0_B3_Fixed","A1_M1_Fixed","A4_M1_StateAware","A5_B3_M1_Hybrid"]:
        p,s=configs[name]; r={"state":state,"configuration":name,"n":int(mask.sum())}
        r.update(met(y[mask],p[mask],s[mask])); spr.append(r)
save(pd.DataFrame(spr),"R04_State_Aware_Performance.csv")

# False-positive analysis
normalmask=y==0
save(pd.DataFrame([{"configuration":k,"normal_rows":int(normalmask.sum()),
                    "false_positives":int(np.sum((v[0]==1)&normalmask)),
                    "false_positive_rate":float(np.mean(v[0][normalmask]==1))}
                   for k,v in configs.items()]),"R09_False_Positive_Analysis.csv")

save(pd.DataFrame({
    "row":np.arange(len(y)),
    "adaptive_threshold":ath,
    "drift_threshold":drift_threshold,
    "threshold_used_drift_aware":thist,
    "operating_state":seval,
    "state_threshold":stv,
    "drift_flag":drift,
    "m1_score":sm1,
    "true_label":y
}),"R11_Threshold_History.csv")

# Paired block bootstrap of Macro-F1 differences
def boot(pa,pb):
    rng=np.random.default_rng(SEED); starts=np.arange(0,len(y),BLOCK); ds=[]
    for _ in range(N_BOOT):
        parts=[]
        while sum(map(len,parts))<len(y):
            s=int(rng.choice(starts)); parts.append(np.arange(s,min(s+BLOCK,len(y))))
        ix=np.concatenate(parts)[:len(y)]
        ds.append(f1_score(y[ix],pb[ix],average="macro",zero_division=0)-f1_score(y[ix],pa[ix],average="macro",zero_division=0))
    return np.mean(ds),np.quantile(ds,.025),np.quantile(ds,.975)
pairs=[("A1_M1_Fixed","A2_M1_Adaptive"),("A2_M1_Adaptive","A3_M1_DriftAware"),
       ("A3_M1_DriftAware","A4_M1_StateAware"),("A0_B3_Fixed","A5_B3_M1_Hybrid"),
       ("A1_M1_Fixed","A5_B3_M1_Hybrid")]
br=[]
for a,b in pairs:
    m,l,h=boot(configs[a][0],configs[b][0])
    br.append(dict(comparison=f"{b} - {a}",metric="macro_f1",mean_difference=m,ci95_low=l,ci95_high=h,
                   n_bootstraps=N_BOOT,block_size=BLOCK))
save(pd.DataFrame(br),"R12_Statistical_Comparisons.csv")

# Figures
def figbar(col,name,title,ylabel):
    plt.figure(figsize=(10,5)); plt.bar(perf.configuration,perf[col]); plt.xticks(rotation=35,ha="right")
    plt.ylabel(ylabel); plt.title(title); plt.tight_layout(); plt.savefig(OUT/name,dpi=300,bbox_inches="tight"); plt.close()
figbar("macro_f1","Figure_01_Fixed_vs_Adaptive_Performance.png","Fixed vs Adaptive Performance","Macro-F1")
figbar("fpr","Figure_02_False_Positive_Reduction.png","False-Positive Rate","FPR")
plt.figure(figsize=(7,6)); plt.scatter(perf.fpr,perf.recall_attack)
for _,r in perf.iterrows(): plt.annotate(r["configuration"],(r["fpr"],r["recall_attack"]),fontsize=8)
plt.xlabel("FPR"); plt.ylabel("Attack Recall"); plt.title("Recall–False-Alarm Tradeoff"); plt.tight_layout()
plt.savefig(OUT/"Figure_03_Recall_FPR_Tradeoff.png",dpi=300,bbox_inches="tight"); plt.close()

plt.figure(figsize=(10,5)); plt.bar(pd.Series(states).value_counts().index,pd.Series(states).value_counts().values)
plt.xticks(rotation=30,ha="right"); plt.ylabel("Rows"); plt.title("B3/M1 Agreement and Disagreement"); plt.tight_layout()
plt.savefig(OUT/"Figure_08_B3_M1_Agreement.png",dpi=300,bbox_inches="tight"); plt.close()

meta={"experiment":"Nuclear Sentinel Experiment 3","seed":SEED,"primary_quantile":PRIMARY_Q,
      "selected_adaptive_quantile":aq,
      "target_normal_fpr":TARGET_NORMAL_FPR,"b3_threshold":b3th,"m1_fixed_threshold":m1th,
      "adaptive_threshold":ath,"drift_threshold":drift_threshold,
      "dt_targets":targets,"n_operating_states_requested":N_STATES,
      "n_operating_states_effective":effective_states,
      "interpretation":"Evidence-confidence is an experimental evidence score, not a probability of cyberattack. DT residuals indicate deviation from expected behavior and do not independently prove a cyberattack."}
(OUT/"Experiment_3_Metadata.json").write_text(json.dumps(meta,indent=2))

print("\nNUCLEAR SENTINEL EXPERIMENT 3 COMPLETE")
print("Results:",OUT)
print(perf.to_string(index=False))
