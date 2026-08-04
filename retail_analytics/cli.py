"""
Pipeline CLI.

    python -m retail_analytics.cli all        # generate -> ETL -> forecast + anomalies (default)
    python -m retail_analytics.cli generate
    python -m retail_analytics.cli etl
    python -m retail_analytics.cli analytics

Outputs a SQLite warehouse + Power BI-ready marts in ./data.
"""
from __future__ import annotations

import argparse
import time

from .analytics import run_anomaly_detection, run_forecast
from .config import config
from .generate import generate_all
from .warehouse import run_etl


def _timed(label, fn):
    t = time.time(); out = fn(); print(f"  [{label}] {time.time()-t:.1f}s -> {out}")
    return out


def cmd_generate(): _timed("generate", lambda: generate_all(config))
def cmd_etl():      _timed("etl", lambda: run_etl(config))


def cmd_analytics():
    _timed("forecast", lambda: run_forecast(config))
    _timed("anomalies", lambda: run_anomaly_detection(config))


def cmd_all():
    config.ensure_dirs()
    print(f"Building retail analytics platform for '{config.retailer_name}'...")
    cmd_generate(); cmd_etl(); cmd_analytics()
    print(f"Done. Warehouse: {config.warehouse_db}")
    print(f"Power BI marts: {config.marts_dir}  (import this folder in Power BI)")


COMMANDS = {"all": cmd_all, "generate": cmd_generate, "etl": cmd_etl,
            "analytics": cmd_analytics}


def main():
    ap = argparse.ArgumentParser(description="Retail analytics pipeline")
    ap.add_argument("command", nargs="?", default="all", choices=list(COMMANDS))
    COMMANDS[ap.parse_args().command]()


if __name__ == "__main__":
    main()
