"""Run the project's verification checks and write figures to ``verification/figures``.

Checks:
  1. Driver math + locking unit tests (mock operator, exact).
  2. Forcing ellipse matches the PDF extent (120E - 165W - 90W), with lat/lon axes.
  3. Vertical heating profiles (Deep / Stratiform / Shallow).
  4. Data-prep sanity: Pangu integrated-TCWV vs FCNv2 TCWV channel agree (RAGASA IC).
  5. Operator one-step is finite & physical (Pangu + FCNv2 on the RAGASA IC).
  6. End-to-end mini run: perturbation vorticity grows in the heating band.

    python verification/run_verification.py [--no_model]

Model checks (5, 6) need the RAGASA IC (scripts/prep_ragasa.py) and take a few
minutes on CPU; pass --no_model to skip them.
"""
import argparse
import os
import subprocess
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
FIG = os.path.join(ROOT, "verification", "figures")
os.makedirs(FIG, exist_ok=True)

from itcz import config as cfgmod                                  # noqa: E402
from itcz.experiment import forcing                               # noqa: E402
from itcz.models.layout import State, get_layout                  # noqa: E402
from itcz.plotting import tracker                                 # noqa: E402

results = {}


def check1_unit_tests():
    print("\n=== CHECK 1: driver math + locking unit tests ===")
    p = subprocess.run([sys.executable, os.path.join(ROOT, "tests", "test_driver_math.py")],
                       capture_output=True, text=True)
    print(p.stdout.strip())
    if p.returncode != 0:
        print(p.stderr.strip())
    results["1_unit_tests"] = "PASS" if p.returncode == 0 else "FAIL"


def check2_ellipse():
    print("\n=== CHECK 2: forcing ellipse vs PDF extent ===")
    cfg = cfgmod.load_config()
    out = tracker.plot_forcing_ellipse(cfg, out=os.path.join(FIG, "02_forcing_ellipse.png"))
    fcfg = cfg["forcing"]
    west = (fcfg["center_lon"] - fcfg["lon_halfwidth"]) % 360
    east = (fcfg["center_lon"] + fcfg["lon_halfwidth"]) % 360
    print(f"center_lon={fcfg['center_lon']} (165W); west edge={west}E (expect 120),"
          f" east edge={east}E (expect 270 = 90W)")
    results["2_ellipse"] = f"west={west:.0f}E east={east:.0f}E -> {os.path.basename(out)}"


def check3_vprofiles():
    print("\n=== CHECK 3: vertical heating profiles ===")
    lev = get_layout("fcnv2").levels  # ascending 50..1000
    fig, ax = plt.subplots(figsize=(4.5, 5))
    for ht in ("Deep", "Stratiform", "Shallow"):
        v = forcing.vertical_profile(ht, lev)
        ax.plot(v, lev, "-o", ms=3, label=ht)
    ax.invert_yaxis()
    ax.set(xlabel="normalized heating V(p)", ylabel="pressure (hPa)",
           title="Vertical heating profiles")
    ax.axvline(0, color="gray", lw=0.6)
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    out = os.path.join(FIG, "03_vertical_profiles.png")
    fig.savefig(out, dpi=130)
    plt.close(fig)
    print(f"[plot] {out}")
    results["3_vprofiles"] = os.path.basename(out)


def check4_tcwv_agreement():
    print("\n=== CHECK 4: TCWV agreement (Pangu integral q vs FCNv2 channel) ===")
    cfg = cfgmod.load_config()
    pa_path = cfgmod.ic_path(cfg, "ragasa", "pangu")
    fc_path = cfgmod.ic_path(cfg, "ragasa", "fcnv2")
    if not (os.path.exists(pa_path) and os.path.exists(fc_path)):
        print("  RAGASA IC missing -> run scripts/prep_ragasa.py; skipping")
        results["4_tcwv"] = "SKIPPED (no IC)"
        return
    pa = get_layout("pangu").tcwv(State.from_npz(pa_path, "pangu"))
    fc = get_layout("fcnv2").tcwv(State.from_npz(fc_path, "fcnv2"))
    diff = pa - fc
    rmse = float(np.sqrt(np.mean(diff ** 2)))
    bias = float(np.mean(diff))
    import cartopy.crs as ccrs
    fig = plt.figure(figsize=(13, 3.2))
    for i, (data, title) in enumerate([(pa, "Pangu  (1/g) integral q dp"),
                                       (fc, "FCNv2  tcwv channel"),
                                       (diff, "difference (Pangu - FCNv2)")]):
        ax = fig.add_subplot(1, 3, i + 1, projection=ccrs.PlateCarree(central_longitude=180))
        ax.coastlines(linewidth=0.4)
        ax.set_extent([100, 300, -20, 40], crs=ccrs.PlateCarree())
        cm = "viridis" if i < 2 else "RdBu_r"
        vlim = dict(vmin=0, vmax=70) if i < 2 else dict(vmin=-5, vmax=5)
        m = ax.pcolormesh(forcing.LON, forcing.LAT, data, cmap=cm, shading="auto",
                          transform=ccrs.PlateCarree(), **vlim)
        ax.set_title(title, fontsize=9)
        plt.colorbar(m, ax=ax, shrink=0.7, label="kg m$^{-2}$")
    fig.suptitle(f"RAGASA TCWV: RMSE={rmse:.2f} kg/m2  bias={bias:.2f} kg/m2", fontsize=10)
    fig.tight_layout()
    out = os.path.join(FIG, "04_tcwv_agreement.png")
    fig.savefig(out, dpi=130)
    plt.close(fig)
    print(f"  RMSE={rmse:.3f} kg/m2  bias={bias:.3f} kg/m2 -> {out}")
    results["4_tcwv"] = f"RMSE={rmse:.2f} bias={bias:.2f} kg/m2"


def check5_operator_step():
    print("\n=== CHECK 5: operator one-step finite & physical ===")
    from itcz.models.operators import load_operator
    import cartopy.crs as ccrs
    cfg = cfgmod.load_config({"background": "ragasa"})
    summary = []
    fig = plt.figure(figsize=(13, 5.5))
    for col, model in enumerate(("pangu", "fcnv2")):
        cfg["model"] = model
        lay = get_layout(model)
        ic = cfgmod.ic_path(cfg, "ragasa", model)
        if not os.path.exists(ic):
            print(f"  {model}: IC missing; skipping")
            continue
        u0 = State.from_npz(ic, model)
        op = load_operator(cfg)
        import time
        t0 = time.time()
        out = op.step(u0)
        dt = time.time() - t0
        finite = all(np.isfinite(a).all() for a in out.arrays.values())
        t0850 = lay.temperature_at(u0, 850)
        t1850 = lay.temperature_at(out, 850)
        summary.append(f"{model}: {dt:.0f}s finite={finite} "
                       f"T850 {t1850.min():.0f}-{t1850.max():.0f}K")
        for row, (data, title) in enumerate([(t0850, f"{model} T850 IC"),
                                             (t1850, f"{model} T850 +6h")]):
            ax = fig.add_subplot(2, 2, row * 2 + col + 1,
                                 projection=ccrs.PlateCarree(central_longitude=180))
            ax.coastlines(linewidth=0.4)
            ax.set_extent([100, 200, 0, 40], crs=ccrs.PlateCarree())
            m = ax.pcolormesh(forcing.LON, forcing.LAT, data, cmap="turbo",
                              vmin=270, vmax=302, shading="auto", transform=ccrs.PlateCarree())
            ax.set_title(title, fontsize=8)
            plt.colorbar(m, ax=ax, shrink=0.6)
    fig.suptitle("One model step on the RAGASA IC (finite, physical T850)", fontsize=10)
    fig.tight_layout()
    out = os.path.join(FIG, "05_operator_step.png")
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print("  " + " | ".join(summary))
    print(f"[plot] {out}")
    results["5_operator"] = " | ".join(summary)


def check6_integration():
    print("\n=== CHECK 6: end-to-end mini run, vorticity growth ===")
    from itcz.experiment import driver
    cfg = cfgmod.load_config({
        "model": "pangu", "background": "ragasa",
        "driver": {"n_days": 0.5, "forcing_days": 0.5, "save_every": 1},
        "plot": {"snapshot_days": [0, 0.25, 0.5]},
    })
    if not os.path.exists(cfgmod.ic_path(cfg, "ragasa", "pangu")):
        print("  RAGASA IC missing; skipping")
        results["6_integration"] = "SKIPPED (no IC)"
        return
    cfg["experiment"] = {"name": "verify_mini_pangu_ragasa", "forcing_type": "heating",
                         "persistent": False, "lock": "none", "seed_npz": None}
    rd = driver.run(cfg)
    d, vm, tm = tracker.timeseries(rd, cfg)
    print(f"  days={d}")
    print(f"  vort_max (1e-5 s^-1)={np.round(vm * 1e5, 3)}")
    print(f"  tcwv_max (kg/m2)={np.round(tm, 3)}")
    tracker.plot_field_panels(rd, cfg, "vort",
                              out=os.path.join(FIG, "06_integration_vort.png"))
    grew = vm[-1] > vm[0]
    results["6_integration"] = (f"vort_max {vm[0]*1e5:.2f}->{vm[-1]*1e5:.2f} 1e-5/s, "
                                f"tcwv {tm[0]:.1f}->{tm[-1]:.1f} kg/m2, grew={grew}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--no_model", action="store_true", help="skip the model-loading checks")
    args = ap.parse_args()

    check1_unit_tests()
    check2_ellipse()
    check3_vprofiles()
    check4_tcwv_agreement()
    if not args.no_model:
        check5_operator_step()
        check6_integration()

    print("\n================ VERIFICATION SUMMARY ================")
    for k, v in results.items():
        print(f"  {k}: {v}")
