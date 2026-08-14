from .common import LocalTaskDescriptor

TASK = LocalTaskDescriptor(
    "denoise", "Signal denoising research profile", "evolve a signal denoising filter",
    ("fixed synthetic signal", "measured SNR objective", "no network"),
    {"samples": 2048, "noise_stddev": 0.15},
)
