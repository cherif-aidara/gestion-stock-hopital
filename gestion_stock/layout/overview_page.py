"""Page Vue d'ensemble enrichie."""

from dash import dcc, html

from gestion_stock.components.card import CardComponent
from gestion_stock.components.charts import ChartBuilder
from gestion_stock.components.kpi import KPIComponent
from gestion_stock.config import AppConfig
from gestion_stock.services.inventory_analytics import InventoryAnalytics


class OverviewPage:
    """Tableau de bord global : KPIs, tendances, alertes."""

    def __init__(
        self,
        analytics: InventoryAnalytics,
        chart_builder: ChartBuilder,
        config: AppConfig | None = None,
    ):
        self.analytics = analytics
        self.chart_builder = chart_builder
        self.config = config or AppConfig()

    @staticmethod
    def _fmt(n: int | float) -> str:
        # Formate un nombre avec espace comme séparateur de milliers (format FR/QC)
        # -> 1 décimale pour les floats, aucune décimale pour les entiers
        if isinstance(n, float):
            return f"{n:,.1f}".replace(",", " ")
        return f"{n:,}".replace(",", " ")

    def _bandeau_resume(self, resume: dict) -> html.Div:
        # Bandeau en haut de page : période analysée + série de mini-statistiques
        # globales (consommation, réquisitions, réceptions, stock, couverture, délai)
        return html.Div(
            [
                html.Div(
                    [
                        html.Span("Période analysée", className="app-overview-eyebrow"),
                        html.H2(
                            f"{resume['date_debut']} → {resume['date_fin']}",
                            className="app-overview-period",
                        ),
                    ],
                    className="app-overview-period-block",
                ),
                html.Div(
                    [
                        self._mini_stat("Consommation totale", self._fmt(resume["consommation_totale"]), "unités"),
                        self._mini_stat("Réquisitions", self._fmt(resume["nb_requisitions"]), "lignes"),
                        self._mini_stat("Réceptions", self._fmt(resume["nb_receptions"]), "lignes"),
                        self._mini_stat("Stock simulé", self._fmt(resume["stock_total_simule"]), "unités"),
                        # Ces deux valeurs sont déjà formatées côté analytics (pas de virgule à gérer)
                        # -> converties directement en str, sans passer par _fmt
                        self._mini_stat("Couverture moy.", str(resume["jours_couverture_moy"]), "jours"),
                        self._mini_stat("Délai réappro moy.", str(resume["delai_reappro_moy"]), "jours"),
                    ],
                    className="app-overview-mini-stats",
                ),
            ],
            className="app-overview-banner",
        )

    @staticmethod
    def _mini_stat(label: str, valeur: str, unite: str) -> html.Div:
        # Bloc compact réutilisable : libellé + valeur + unité
        return html.Div(
            [
                html.Span(label, className="app-mini-stat-label"),
                html.Span(valeur, className="app-mini-stat-value"),
                html.Span(unite, className="app-mini-stat-unit"),
            ],
            className="app-mini-stat",
        )

    def _cartes_risque(self, resume: dict) -> html.Div:
        # Deux cartes mettant en avant les taux globaux de risque
        # (rupture en rouge/"danger", péremption en orange/"warning")
        return html.Div(
            [
                html.Div(
                    [
                        html.Span("Taux de rupture", className="app-risk-card-label"),
                        html.Span(f"{resume['taux_rupture_pct']} %", className="app-risk-card-value app-risk-danger"),
                        html.Span("produits sous le seuil", className="app-risk-card-hint"),
                    ],
                    className="app-risk-card",
                ),
                html.Div(
                    [
                        html.Span("Taux de péremption", className="app-risk-card-label"),
                        html.Span(f"{resume['taux_peremption_pct']} %", className="app-risk-card-value app-risk-warning"),
                        html.Span("stock > durée de vie", className="app-risk-card-hint"),
                    ],
                    className="app-risk-card",
                ),
            ],
            className="app-risk-cards",
        )

    def _liste_alertes(self, alertes) -> html.Div:
        # Liste des produits en alerte de rupture (issue d'un DataFrame)
        # -> état vide si aucune alerte, sinon un item par produit à risque
        if alertes.empty:
            return html.P("Aucune alerte de rupture active.", className="app-empty-state")

        items = []
        for _, row in alertes.iterrows():
            items.append(
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span(row["nom_court"], className="app-alert-name"),
                                # Détail combiné : jours de couverture restants,
                                # stock actuel simulé et seuil (point de commande)
                                # Note : le formatage ",".replace n'agit que sur le seuil
                                # (dernier f-string évalué avant le .replace global de la ligne)
                                html.Span(
                                    f"Couverture : {row['jours_couverture_stock']} j · "
                                    f"Stock : {int(row['stock_actuel_simule']):,} / "
                                    f"Seuil : {int(row['point_commande']):,}".replace(",", " "),
                                    className="app-alert-detail",
                                ),
                            ],
                            className="app-alert-info",
                        ),
                        html.Span("Urgent", className="app-alert-badge"),
                    ],
                    className="app-alert-item",
                )
            )
        return html.Div(items, className="app-alert-list")

    def construire(self) -> html.Div:
        # Récupération de toutes les données nécessaires à la page
        # via le service d'analytics (KPIs, résumé, alertes, top produits)
        kpis = self.analytics.obtenir_kpis()
        resume = self.analytics.obtenir_resume_vue_ensemble()
        alertes = self.analytics.obtenir_alertes_rupture()
        top_produits = self.analytics.obtenir_top_produits_consommation()

        # Construction des 4 graphiques affichés sur la page
        fig_velocite = self.chart_builder.creer_donut_velocite(
            self.analytics.obtenir_repartition_velocite()
        )
        fig_zones = self.chart_builder.creer_graphique_repartition_zones(
            self.analytics.obtenir_repartition_zones()
        )
        fig_tendance = self.chart_builder.creer_graphique_tendance_globale(
            self.analytics.obtenir_consommation_globale_mensuelle()
        )
        fig_top = self.chart_builder.creer_graphique_top_produits(top_produits)

        return html.Div(
            [
                # 1. Bandeau résumé (période + mini-stats)
                self._bandeau_resume(resume),
                # 2. Rangée de KPIs principaux (composant externe dédié)
                KPIComponent.creer_rangée(kpis, self.config.THEME_KPI),
                # 3. Cartes de taux de risque globaux
                self._cartes_risque(resume),
                # 4. Graphique pleine largeur : tendance de consommation globale
                html.Div(
                    [
                        html.Div(
                            CardComponent.construire(
                                dcc.Graph(
                                    figure=fig_tendance,
                                    config={"displayModeBar": False},
                                    style={"height": "300px"},
                                ),
                                titre="Tendance de consommation globale",
                                sous_titre="Volume mensuel toutes réquisitions confondues",
                            ),
                            className="app-overview-wide",
                        ),
                    ],
                    className="app-overview-row-full",
                ),
                # 5. Grille de 3 graphiques côte à côte : vélocité, zones, top produits
                html.Div(
                    [
                        html.Div(
                            CardComponent.construire(
                                dcc.Graph(
                                    figure=fig_velocite,
                                    config={"displayModeBar": False},
                                    style={"height": "300px"},
                                ),
                                titre="Vélocité des produits",
                                sous_titre="Classification ABC",
                            ),
                        ),
                        html.Div(
                            CardComponent.construire(
                                dcc.Graph(
                                    figure=fig_zones,
                                    config={"displayModeBar": False},
                                    style={"height": "300px"},
                                ),
                                titre="Répartition entrepôt",
                                sous_titre="Zones A / B / C suggérées",
                            ),
                        ),
                        html.Div(
                            CardComponent.construire(
                                dcc.Graph(
                                    figure=fig_top,
                                    config={"displayModeBar": False},
                                    style={"height": "300px"},
                                ),
                                titre="Top 5 consommation",
                                sous_titre="Produits les plus demandés",
                            ),
                        ),
                    ],
                    className="app-overview-grid-3",
                ),
                # 6. Liste détaillée des alertes de rupture, en bas de page
                CardComponent.construire(
                    self._liste_alertes(alertes),
                    titre="Alertes rupture de stock",
                    sous_titre="Produits nécessitant un réapprovisionnement prioritaire",
                ),
            ],
            className="app-page-inner",
        )