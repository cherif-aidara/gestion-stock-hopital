"""Calculs statistiques et indicateurs de stock."""

import numpy as np
import pandas as pd

from gestion_stock.config import AppConfig


class InventoryAnalytics:
    """Analyse la demande, les délais et les risques par produit."""

    def __init__(
        self,
        df_requisitions: pd.DataFrame,
        df_receptions: pd.DataFrame,
        config: AppConfig | None = None,
    ):
        self.config = config or AppConfig()
        self.df_requisitions = df_requisitions
        self.df_receptions = df_receptions
        self.stats_produits = self._calculer_stats_produits()

    def _calculer_stats_demande(self) -> pd.DataFrame:
        stats = (
            self.df_requisitions.groupby("Produit")[self.config.COLONNE_QTE_REQUISITION]
            .agg(["mean", "std"])
            .reset_index()
        )
        stats.columns = ["Produit", "demande_moyenne", "demande_ecart_type"]
        return stats

    def _calculer_delai_reappro(self) -> pd.DataFrame:
        df_trie = self.df_receptions.sort_values(["Produit", "Date"])
        df_trie["jours_depuis_derniere_reception"] = (
            df_trie.groupby("Produit")["Date"].diff().dt.days
        )
        delai = (
            df_trie.groupby("Produit")["jours_depuis_derniere_reception"]
            .median()
            .reset_index()
        )
        delai.columns = ["Produit", "delai_reappro_jours"]
        return delai

    @staticmethod
    def _assigner_zone(classe: str) -> str:
        if classe == "Haute":
            return "Zone A - Proche expédition"
        if classe == "Moyenne":
            return "Zone B - Intermédiaire"
        return "Zone C - Éloignée"

    def _calculer_stats_produits(self) -> pd.DataFrame:
        stats = self._calculer_stats_demande().merge(
            self._calculer_delai_reappro(), on="Produit"
        )

        z = self.config.Z_NIVEAU_SERVICE
        stats["stock_securite"] = (
            z * stats["demande_ecart_type"] * np.sqrt(stats["delai_reappro_jours"])
        )
        stats["point_commande"] = (
            stats["demande_moyenne"] * stats["delai_reappro_jours"]
            + stats["stock_securite"]
        )

        np.random.seed(self.config.GRAINES_ALEATOIRES["stock"])
        stats["stock_actuel_simule"] = (
            stats["point_commande"]
            * np.random.uniform(0.4, 1.8, len(stats))
        ).round(0)

        stats["risque_rupture"] = np.where(
            stats["stock_actuel_simule"] < stats["point_commande"],
            "Élevé",
            "Faible",
        )

        stats["jours_couverture_stock"] = (
            stats["stock_actuel_simule"] / stats["demande_moyenne"]
        ).round(1)

        np.random.seed(self.config.GRAINES_ALEATOIRES["peremption"])
        stats["jours_avant_peremption"] = np.random.randint(15, 400, size=len(stats))

        stats["risque_peremption"] = np.where(
            stats["jours_avant_peremption"] < stats["jours_couverture_stock"],
            "Élevé",
            "Faible",
        )

        stats["classe_velocite"] = pd.qcut(
            stats["demande_moyenne"], q=3, labels=["Faible", "Moyenne", "Haute"]
        )
        stats["zone_suggeree"] = stats["classe_velocite"].apply(self._assigner_zone)

        return stats

    def obtenir_kpis(self) -> dict[str, int]:
        stats = self.stats_produits
        return {
            "nb_produits_total": len(stats),
            "nb_risque_rupture_eleve": int((stats["risque_rupture"] == "Élevé").sum()),
            "nb_risque_peremption_eleve": int(
                (stats["risque_peremption"] == "Élevé").sum()
            ),
            "nb_zone_a": int(
                (stats["zone_suggeree"] == "Zone A - Proche expédition").sum()
            ),
        }

    def obtenir_repartition_velocite(self) -> pd.DataFrame:
        repartition = (
            self.stats_produits["classe_velocite"].value_counts().reset_index()
        )
        repartition.columns = ["classe_velocite", "nombre"]
        return repartition

    def obtenir_repartition_zones(self) -> pd.DataFrame:
        repartition = (
            self.stats_produits["zone_suggeree"].value_counts().reset_index()
        )
        repartition.columns = ["zone", "nombre"]
        return repartition

    def obtenir_consommation_globale_mensuelle(self) -> pd.DataFrame:
        col = self.config.COLONNE_QTE_REQUISITION
        df = self.df_requisitions.copy()
        df["Mois"] = df["Date"].dt.to_period("M").dt.to_timestamp()
        mensuel = (
            df.groupby("Mois", as_index=False)[col]
            .sum()
            .rename(columns={col: "consommation"})
        )
        mensuel["Mois_label"] = mensuel["Mois"].dt.strftime("%b %Y")
        return mensuel

    def obtenir_top_produits_consommation(self, n: int = 5) -> pd.DataFrame:
        col = self.config.COLONNE_QTE_REQUISITION
        top = (
            self.df_requisitions.groupby("Produit")[col]
            .sum()
            .reset_index()
            .rename(columns={col: "consommation_totale"})
            .sort_values("consommation_totale", ascending=False)
            .head(n)
        )
        top["nom_court"] = top["Produit"].apply(
            lambda p: self._nom_court(p, 40)
        )
        return top

    def obtenir_alertes_rupture(self, n: int = 5) -> pd.DataFrame:
        alertes = (
            self.stats_produits[self.stats_produits["risque_rupture"] == "Élevé"]
            .sort_values("jours_couverture_stock")
            .head(n)
        )
        alertes = alertes.copy()
        alertes["nom_court"] = alertes["Produit"].apply(
            lambda p: self._nom_court(p, 45)
        )
        return alertes

    def obtenir_resume_vue_ensemble(self) -> dict:
        col_req = self.config.COLONNE_QTE_REQUISITION
        col_rec = self.config.COLONNE_QTE_RECEPTION
        stats = self.stats_produits
        nb_total = len(stats)

        return {
            "consommation_totale": int(self.df_requisitions[col_req].sum()),
            "nb_requisitions": len(self.df_requisitions),
            "nb_receptions": len(self.df_receptions),
            "date_debut": self.df_requisitions["Date"].min().strftime("%d/%m/%Y"),
            "date_fin": self.df_requisitions["Date"].max().strftime("%d/%m/%Y"),
            "jours_couverture_moy": float(round(stats["jours_couverture_stock"].mean(), 1)),
            "taux_rupture_pct": float(
                round((stats["risque_rupture"] == "Élevé").sum() / nb_total * 100, 1)
            ),
            "taux_peremption_pct": float(
                round((stats["risque_peremption"] == "Élevé").sum() / nb_total * 100, 1)
            ),
            "stock_total_simule": int(stats["stock_actuel_simule"].sum()),
            "delai_reappro_moy": float(round(stats["delai_reappro_jours"].median(), 1)),
        }

    def lister_produits(self) -> list:
        return sorted(self.df_requisitions["Produit"].unique())

    def obtenir_options_produits(self) -> list[dict]:
        return [
            {"label": produit, "value": produit}
            for produit in self.lister_produits()
        ]

    @staticmethod
    def _nom_court(produit: str, longueur: int = 55) -> str:
        return produit if len(produit) <= longueur else produit[: longueur - 1] + "…"

    def obtenir_stats_produit(self, produit: str) -> dict:
        col = self.config.COLONNE_QTE_REQUISITION
        df_prod = self.df_requisitions[self.df_requisitions["Produit"] == produit]
        conso_jour = df_prod.groupby("Date", as_index=False)[col].sum()

        stats_row = self.stats_produits[
            self.stats_produits["Produit"] == produit
        ].iloc[0]

        return {
            "produit": produit,
            "nom_court": self._nom_court(produit),
            "consommation_totale": int(df_prod[col].sum()),
            "consommation_moy_jour": round(conso_jour[col].mean(), 1),
            "consommation_max_jour": int(conso_jour[col].max()) if len(conso_jour) else 0,
            "nb_requisitions": len(df_prod),
            "stock_actuel": int(stats_row["stock_actuel_simule"]),
            "jours_couverture": float(stats_row["jours_couverture_stock"]),
            "seuil_commande": int(stats_row["point_commande"]),
            "classe_velocite": str(stats_row["classe_velocite"]),
            "zone_suggeree": stats_row["zone_suggeree"],
            "risque_rupture": stats_row["risque_rupture"],
            "risque_peremption": stats_row["risque_peremption"],
            "jours_avant_peremption": int(stats_row["jours_avant_peremption"]),
        }

    def obtenir_consommation_journaliere(self, produit: str) -> pd.DataFrame:
        col = self.config.COLONNE_QTE_REQUISITION
        df_prod = self.df_requisitions[self.df_requisitions["Produit"] == produit]
        return df_prod.groupby("Date", as_index=False)[col].sum()

    def obtenir_consommation_mensuelle(self, produit: str) -> pd.DataFrame:
        col = self.config.COLONNE_QTE_REQUISITION
        df_prod = self.df_requisitions[self.df_requisitions["Produit"] == produit].copy()
        df_prod["Mois"] = df_prod["Date"].dt.to_period("M").dt.to_timestamp()
        mensuel = (
            df_prod.groupby("Mois", as_index=False)[col]
            .sum()
            .rename(columns={col: "consommation"})
        )
        mensuel["Mois_label"] = mensuel["Mois"].dt.strftime("%b %Y")
        return mensuel

    def obtenir_series_demande_reception(
        self, produit: str
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        df_produit = self.df_requisitions[self.df_requisitions["Produit"] == produit]
        demande_jour = df_produit.groupby("Date", as_index=False)[
            self.config.COLONNE_QTE_REQUISITION
        ].sum()

        df_rec_produit = self.df_receptions[
            self.df_receptions["Produit"] == produit
        ]
        reception_jour = df_rec_produit.groupby("Date", as_index=False)[
            self.config.COLONNE_QTE_RECEPTION
        ].sum()

        return demande_jour, reception_jour
