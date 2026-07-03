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
        # Calcule et met en cache toutes les statistiques par produit dès
        # l'initialisation, pour éviter de recalculer à chaque appel de méthode
        self.stats_produits = self._calculer_stats_produits()

    def _calculer_stats_demande(self) -> pd.DataFrame:
        # Moyenne et écart-type de la demande (quantité réquisitionnée) par produit
        # -> base du calcul de stock de sécurité (formule de type Wilson/service level)
        stats = (
            self.df_requisitions.groupby("Produit")[self.config.COLONNE_QTE_REQUISITION]
            .agg(["mean", "std"])
            .reset_index()
        )
        stats.columns = ["Produit", "demande_moyenne", "demande_ecart_type"]
        return stats

    def _calculer_delai_reappro(self) -> pd.DataFrame:
        # Estime le délai de réapprovisionnement par produit à partir de
        # l'historique des réceptions : calcule le nombre de jours écoulés
        # entre deux réceptions consécutives, puis prend la médiane
        # (médiane plutôt que moyenne pour limiter l'effet des valeurs extrêmes)
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
        # Règle métier : plus un produit tourne vite (vélocité "Haute"),
        # plus il doit être stocké près de la zone d'expédition (Zone A)
        if classe == "Haute":
            return "Zone A - Proche expédition"
        if classe == "Moyenne":
            return "Zone B - Intermédiaire"
        return "Zone C - Éloignée"

    def _calculer_stats_produits(self) -> pd.DataFrame:
        # Assemble le tableau central de statistiques par produit,
        # combinant demande, délais, stock de sécurité, risques et classification
        stats = self._calculer_stats_demande().merge(
            self._calculer_delai_reappro(), on="Produit"
        )

        # --- Stock de sécurité et point de commande (formules classiques de gestion de stock) ---
        # stock_securite = z * écart-type de la demande * racine(délai de réappro)
        # -> plus le niveau de service visé (z) est élevé, plus le stock de sécurité augmente
        z = self.config.Z_NIVEAU_SERVICE
        stats["stock_securite"] = (
            z * stats["demande_ecart_type"] * np.sqrt(stats["delai_reappro_jours"])
        )
        # point_commande = demande moyenne pendant le délai de réappro + stock de sécurité
        # -> seuil sous lequel il faut recommander le produit
        stats["point_commande"] = (
            stats["demande_moyenne"] * stats["delai_reappro_jours"]
            + stats["stock_securite"]
        )

        # --- Simulation du stock actuel ---
        # Pas de données réelles de niveau de stock disponibles :
        # on simule une valeur plausible autour du point de commande
        # (graine fixée pour que le résultat soit reproductible d'un lancement à l'autre)
        np.random.seed(self.config.GRAINES_ALEATOIRES["stock"])
        stats["stock_actuel_simule"] = (
            stats["point_commande"]
            * np.random.uniform(0.4, 1.8, len(stats))
        ).round(0)

        # Risque de rupture : élevé si le stock simulé est sous le point de commande
        stats["risque_rupture"] = np.where(
            stats["stock_actuel_simule"] < stats["point_commande"],
            "Élevé",
            "Faible",
        )

        # Nombre de jours que le stock actuel peut couvrir, au rythme de la demande moyenne
        stats["jours_couverture_stock"] = (
            stats["stock_actuel_simule"] / stats["demande_moyenne"]
        ).round(1)

        # --- Simulation de la durée de vie restante avant péremption ---
        # Même logique : pas de données réelles de péremption, donc simulation
        # avec une graine dédiée pour rester reproductible mais indépendante
        # de la simulation de stock ci-dessus
        np.random.seed(self.config.GRAINES_ALEATOIRES["peremption"])
        stats["jours_avant_peremption"] = np.random.randint(15, 400, size=len(stats))

        # Risque de péremption : élevé si le produit périme avant d'avoir
        # eu le temps d'être consommé (couverture stock > durée de vie restante)
        stats["risque_peremption"] = np.where(
            stats["jours_avant_peremption"] < stats["jours_couverture_stock"],
            "Élevé",
            "Faible",
        )

        # Classification ABC simplifiée en 3 tranches égales (tertiles) selon
        # la demande moyenne -> segmente les produits par "vélocité"
        stats["classe_velocite"] = pd.qcut(
            stats["demande_moyenne"], q=3, labels=["Faible", "Moyenne", "Haute"]
        )
        # Zone d'entreposage suggérée, dérivée directement de la vélocité
        stats["zone_suggeree"] = stats["classe_velocite"].apply(self._assigner_zone)

        return stats

    def obtenir_kpis(self) -> dict[str, int]:
        # Indicateurs clés agrégés, affichés en haut du dashboard (page Vue d'ensemble)
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
        # Nombre de produits par classe de vélocité -> alimente le donut de charts.py
        repartition = (
            self.stats_produits["classe_velocite"].value_counts().reset_index()
        )
        repartition.columns = ["classe_velocite", "nombre"]
        return repartition

    def obtenir_repartition_zones(self) -> pd.DataFrame:
        # Nombre de produits par zone d'entrepôt -> alimente le bar chart des zones
        repartition = (
            self.stats_produits["zone_suggeree"].value_counts().reset_index()
        )
        repartition.columns = ["zone", "nombre"]
        return repartition

    def obtenir_consommation_globale_mensuelle(self) -> pd.DataFrame:
        # Agrège la consommation (toutes réquisitions confondues) mois par mois
        # -> alimente le graphique de tendance globale
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
        # Classement des produits les plus consommés (par défaut : top 5)
        col = self.config.COLONNE_QTE_REQUISITION
        top = (
            self.df_requisitions.groupby("Produit")[col]
            .sum()
            .reset_index()
            .rename(columns={col: "consommation_totale"})
            .sort_values("consommation_totale", ascending=False)
            .head(n)
        )
        # Nom raccourci pour l'affichage dans le graphique (évite de déborder)
        top["nom_court"] = top["Produit"].apply(
            lambda p: self._nom_court(p, 40)
        )
        return top

    def obtenir_alertes_rupture(self, n: int = 5) -> pd.DataFrame:
        # Sélectionne les produits à risque de rupture élevé, triés par
        # couverture de stock croissante (les plus urgents en premier)
        alertes = (
            self.stats_produits[self.stats_produits["risque_rupture"] == "Élevé"]
            .sort_values("jours_couverture_stock")
            .head(n)
        )
        # .copy() pour éviter un SettingWithCopyWarning lors de l'ajout de colonne
        # sur ce qui est une vue filtrée du DataFrame d'origine
        alertes = alertes.copy()
        alertes["nom_court"] = alertes["Produit"].apply(
            lambda p: self._nom_court(p, 45)
        )
        return alertes

    def obtenir_resume_vue_ensemble(self) -> dict:
        # Construit le dict de résumé global utilisé dans le bandeau
        # en haut de la page Vue d'ensemble (période, totaux, taux de risque, etc.)
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
        # Liste triée alphabétiquement des produits distincts (à partir des réquisitions)
        return sorted(self.df_requisitions["Produit"].unique())

    def obtenir_options_produits(self) -> list[dict]:
        # Formate la liste de produits au format attendu par dcc.Dropdown
        # (liste de {"label": ..., "value": ...})
        return [
            {"label": produit, "value": produit}
            for produit in self.lister_produits()
        ]

    @staticmethod
    def _nom_court(produit: str, longueur: int = 55) -> str:
        # Tronque un nom de produit trop long, avec ellipse "…"
        # (longueur par défaut différente de celle de ChartBuilder.__nom_court,
        # car utilisée dans des contextes d'affichage différents)
        return produit if len(produit) <= longueur else produit[: longueur - 1] + "…"

    def obtenir_stats_produit(self, produit: str) -> dict:
        # Rassemble toutes les statistiques d'un produit spécifique,
        # utilisées pour la fiche produit détaillée (ProductStatsComponent)
        col = self.config.COLONNE_QTE_REQUISITION
        df_prod = self.df_requisitions[self.df_requisitions["Produit"] == produit]
        conso_jour = df_prod.groupby("Date", as_index=False)[col].sum()

        # Récupère la ligne de stats précalculées correspondant à ce produit
        # (.iloc[0] car groupby("Produit") garantit l'unicité)
        stats_row = self.stats_produits[
            self.stats_produits["Produit"] == produit
        ].iloc[0]

        return {
            "produit": produit,
            "nom_court": self._nom_court(produit),
            "consommation_totale": int(df_prod[col].sum()),
            "consommation_moy_jour": round(conso_jour[col].mean(), 1),
            # Garde contre une division/erreur si le produit n'a aucune donnée journalière
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
        # Série temporelle jour par jour de la consommation d'un produit
        # -> alimente le graphique "Consommation journalière"
        col = self.config.COLONNE_QTE_REQUISITION
        df_prod = self.df_requisitions[self.df_requisitions["Produit"] == produit]
        return df_prod.groupby("Date", as_index=False)[col].sum()

    def obtenir_consommation_mensuelle(self, produit: str) -> pd.DataFrame:
        # Série mensuelle agrégée pour un produit -> alimente le graphique
        # "Consommation mensuelle"
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
        # Retourne deux séries journalières distinctes pour un produit :
        # la demande (réquisitions) et les réceptions
        # -> alimente le graphique combiné "Demande vs réception"
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