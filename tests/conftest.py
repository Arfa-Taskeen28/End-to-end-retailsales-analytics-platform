"""Build a small end-to-end run in a temp dir once per test session."""
from __future__ import annotations

import pytest

from retail_analytics.analytics import run_anomaly_detection, run_forecast
from retail_analytics.config import Config
from retail_analytics.generate import generate_all
from retail_analytics.warehouse import run_etl


@pytest.fixture(scope="session")
def cfg(tmp_path_factory) -> Config:
    d = tmp_path_factory.mktemp("run")
    cfg = Config(data_root=d / "data", n_transactions=40000)
    cfg.ensure_dirs()
    generate_all(cfg)
    run_etl(cfg)
    run_forecast(cfg)
    run_anomaly_detection(cfg)
    return cfg
