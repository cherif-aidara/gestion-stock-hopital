"""Chargement des fichiers CSV de réquisitions et réceptions."""

import pandas as pd

from gestion_stock.config import AppConfig


class DataLoader:
    """Charge et prépare les données brutes depuis les fichiers CSV."""

    def __init__(self, config: AppConfig | None = None):
        self.config = config or AppConfig()

    def charger_requisitions(self) -> pd.DataFrame:
        df = pd.read_csv(self.config.CHEMIN_REQUISITIONS, low_memory=False)
        df["Date"] = pd.to_datetime(df["Date"])
        return df

    def charger_receptions(self) -> pd.DataFrame:
        df = pd.read_csv(self.config.CHEMIN_RECEPTIONS, low_memory=False)
        df["Date"] = pd.to_datetime(df["Date"])
        return df

    def charger_tout(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        return self.charger_requisitions(), self.charger_receptions()
