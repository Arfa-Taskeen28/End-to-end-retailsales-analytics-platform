"""Configuration: paths, the simulated retailer, and run parameters."""
from __future__ import annotations

import pathlib
from dataclasses import dataclass, field

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# Italian stores: (city, region, store_type)
STORE_LOCATIONS = [
    ("Milano", "Lombardia", "Flagship"),
    ("Roma", "Lazio", "Flagship"),
    ("Napoli", "Campania", "Standard"),
    ("Torino", "Piemonte", "Standard"),
    ("Firenze", "Toscana", "Standard"),
    ("Bologna", "Emilia-Romagna", "Standard"),
    ("Venezia", "Veneto", "Standard"),
    ("Genova", "Liguria", "Standard"),
    ("Palermo", "Sicilia", "Standard"),
    ("Bari", "Puglia", "Standard"),
    ("Verona", "Veneto", "Standard"),
    ("Catania", "Sicilia", "Outlet"),
    ("Padova", "Veneto", "Standard"),
    ("Bergamo", "Lombardia", "Outlet"),
    ("Cagliari", "Sardegna", "Standard"),
    ("Trieste", "Friuli-Venezia Giulia", "Standard"),
    ("Perugia", "Umbria", "Outlet"),
    ("Bolzano", "Trentino-Alto Adige", "Standard"),
]

# category -> (subcategories, price range EUR, base margin fraction)
CATEGORIES = {
    "Abbigliamento": (["Uomo", "Donna", "Bambino", "Accessori"], (15, 180), 0.55),
    "Elettronica":   (["Smartphone", "Audio", "Computer", "Grandi elettro."], (40, 900), 0.22),
    "Casa & Arredo": (["Cucina", "Arredo", "Tessili", "Illuminazione"], (12, 350), 0.45),
    "Alimentari":    (["Fresco", "Dispensa", "Bevande", "Surgelati"], (2, 40), 0.28),
    "Bellezza":      (["Skincare", "Makeup", "Profumi", "Cura capelli"], (6, 120), 0.50),
    "Sport":         (["Fitness", "Outdoor", "Calcio", "Running"], (18, 260), 0.42),
}


@dataclass
class Config:
    data_root: pathlib.Path = REPO_ROOT / "data"
    seed: int = 42

    start_date: str = "2023-07-01"
    end_date: str = "2026-06-30"          # ~3 years of history

    n_stores: int = len(STORE_LOCATIONS)
    n_products: int = 60
    n_customers: int = 8000
    n_transactions: int = 700_000

    forecast_horizon_days: int = 90

    retailer_name: str = "BellaCasa Retail"
    currency: str = "EUR"

    # --- derived paths -------------------------------------------------------
    @property
    def raw_dir(self) -> pathlib.Path:
        return self.data_root / "raw"

    @property
    def marts_dir(self) -> pathlib.Path:
        return self.data_root / "marts"

    @property
    def warehouse_db(self) -> pathlib.Path:
        return self.data_root / "warehouse.db"

    def ensure_dirs(self) -> None:
        for d in (self.raw_dir, self.marts_dir):
            d.mkdir(parents=True, exist_ok=True)


config = Config()
