"""Self-contained model operators: load Pangu (ONNX) and FourCastNet v2 (torch)
and expose a single ``operator.step(State) -> State`` interface (the M operator).

The FCNv2 network architecture is vendored locally under
``models/vendor/fourcastnetv2`` (no cross-repo import); only the model *weights*
are read, read-only, from their existing location on disk.
"""
from __future__ import annotations

import os
import sys

import numpy as np

from . import layout as _layout
from .layout import State

# make the vendored SFNO package importable as ``fourcastnetv2``
_VENDOR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor")
if _VENDOR not in sys.path:
    sys.path.insert(0, _VENDOR)


def resolve_cpu(cfg: dict) -> int:
    """Resolve ``cpu_num`` (-1/0/None -> all available cores)."""
    n = cfg.get("cpu_num", 0)
    return os.cpu_count() if not n or n < 0 else int(n)


class Operator:
    """Common interface: ``model`` name, a :class:`~layout.Layout`, and ``step``."""

    model: str

    def __init__(self):
        self.layout = _layout.get_layout(self.model)

    def step(self, state: State) -> State:  # pragma: no cover - abstract
        raise NotImplementedError


class PanguOperator(Operator):
    model = "pangu"

    def __init__(self, cfg: dict):
        super().__init__()
        import onnxruntime as ort

        step_hours = cfg.get("step_hours", 6)
        onnx_path = os.path.join(cfg["paths"]["pangu_model_dir"],
                                 f"pangu_weather_{step_hours}.onnx")
        if not os.path.exists(onnx_path):
            raise FileNotFoundError(onnx_path)
        opts = ort.SessionOptions()
        opts.enable_cpu_mem_arena = True
        opts.enable_mem_pattern = True
        opts.enable_mem_reuse = True
        opts.intra_op_num_threads = resolve_cpu(cfg)
        self.session = ort.InferenceSession(
            onnx_path, sess_options=opts, providers=["CPUExecutionProvider"])
        print(f"[operators] Pangu loaded: {onnx_path}")

    def step(self, state: State) -> State:
        surface = np.ascontiguousarray(state.arrays["surface"], dtype=np.float32)
        upper = np.ascontiguousarray(state.arrays["upper"], dtype=np.float32)
        out_upper, out_surface = self.session.run(
            None, {"input": upper, "input_surface": surface})
        return State({"surface": out_surface, "upper": out_upper}, self.model)


class FCNv2Operator(Operator):
    model = "fcnv2"

    def __init__(self, cfg: dict):
        super().__init__()
        import torch
        from fourcastnetv2 import FourierNeuralOperatorNet

        self._torch = torch
        self.device = cfg.get("device", "cpu")
        wdir = cfg["paths"]["fcnv2_weight_dir"]
        self.means = np.load(os.path.join(wdir, "global_means.npy")).astype(np.float32)
        self.stds = np.load(os.path.join(wdir, "global_stds.npy")).astype(np.float32)

        net = FourierNeuralOperatorNet()
        net.zero_grad()
        ckpt = torch.load(os.path.join(wdir, "weights.tar"),
                          map_location=self.device, weights_only=False)
        try:
            sd = {k[7:]: v for k, v in ckpt["model_state"].items() if k[7:] != "ged"}
            net.load_state_dict(sd)
        except Exception:
            net.load_state_dict(ckpt["model_state"])
        net.eval()
        net.to(self.device)
        if self.device == "cpu":
            torch.set_num_threads(resolve_cpu(cfg))
        self.net = net
        print(f"[operators] FCNv2 loaded: {wdir} (device={self.device})")

    def step(self, state: State) -> State:
        torch = self._torch
        x = state.arrays["state"][np.newaxis].astype(np.float32)
        x = (x - self.means) / self.stds
        with torch.no_grad():
            y = self.net(torch.from_numpy(x).to(self.device)).cpu().numpy()
        y = y * self.stds + self.means
        return State({"state": y[0].astype(np.float32)}, self.model)


def load_operator(cfg: dict) -> Operator:
    """Build the operator named by ``cfg['model']``."""
    model = cfg["model"]
    if model == "pangu":
        return PanguOperator(cfg)
    if model == "fcnv2":
        return FCNv2Operator(cfg)
    raise ValueError(f"unknown model {model!r}")
