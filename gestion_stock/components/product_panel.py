"""Panneau de consommation par produit."""

from dash import dcc, html

from gestion_stock.components.card import CardComponent
from gestion_stock.components.charts import ChartBuilder
from gestion_stock.components.product_stats import ProductStatsComponent
from gestion_stock.config import AppConfig
from gestion_stock.services.inventory_analytics import InventoryAnalytics


class ProductConsumptionPanel:
    """Section principale : sélection produit + stats + graphiques."""

    def __init__(
        self,
        analytics: InventoryAnalytics,
        chart_builder: ChartBuilder,
        config: AppConfig | None = None,
    ):
        self.analytics = analytics
        self.chart_builder = chart_builder
        self.config = config or AppConfig()
        self.options = analytics.obtenir_options_produits()
        self.produit_defaut = self.options[0]["value"] if self.options else None
        self._figs_initiales = self._generer_figures_initiales()

    def _generer_figures_initiales(self) -> dict:
        if not self.produit_defaut:
            return {}
        produit = self.produit_defaut
        return {
            "stats": self.analytics.obtenir_stats_produit(produit),
            "conso_jour": self.chart_builder.creer_graphique_consommation_journaliere(
                self.analytics.obtenir_consommation_journaliere(produit), produit
            ),
            "conso_mois": self.chart_builder.creer_graphique_consommation_mensuelle(
                self.analytics.obtenir_consommation_mensuelle(produit), produit
            ),
            "demande": self._fig_demande(produit),
        }

    def _fig_demande(self, produit: str):
        demande, reception = self.analytics.obtenir_series_demande_reception(produit)
        return self.chart_builder.creer_graphique_demande_reception(
            demande, reception, produit
        )

    def construire(self) -> html.Div:
        stats_init = self._figs_initiales.get("stats")
        contenu_stats = (
            ProductStatsComponent.construire_contenu(stats_init)
            if stats_init
            else ProductStatsComponent.contenu_vide()
        )

        return html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span("Produit à analyser", className="app-selector-eyebrow"),
                                html.H2(
                                    "Sélectionnez un produit",
                                    className="app-selector-title",
                                ),
                                html.P(
                                    "Recherchez par code ou nom pour afficher "
                                    "la consommation et les statistiques détaillées.",
                                    className="app-selector-desc",
                                ),
                            ],
                            className="app-selector-header",
                        ),
                        html.Div(
                            dcc.Dropdown(
                                id="dropdown-produit",
                                options=self.options,
                                value=self.produit_defaut,
                                className="app-dropdown app-dropdown-prominent",
                                clearable=False,
                                searchable=True,
                                placeholder="Rechercher par code ou nom…",
                            ),
                            className="app-selector-input-wrap",
                        ),
                    ],
                    className="app-product-selector-hero",
                ),
                html.Div(
                    contenu_stats,
                    id="stats-produit",
                    className="app-product-panel",
                ),
                html.Div(
                    [
                        html.Div(
                            CardComponent.construire(
                                dcc.Graph(
                                    id="graphique-consommation-jour",
                                    figure=self._figs_initiales.get("conso_jour"),
                                    config={"displayModeBar": False},
                                    style={"height": "340px"},
                                ),
                                titre="Consommation journalière",
                                sous_titre="Évolution dans le temps",
                            ),
                            className="app-chart-col",
                        ),
                        html.Div(
                            CardComponent.construire(
                                dcc.Graph(
                                    id="graphique-consommation-mois",
                                    figure=self._figs_initiales.get("conso_mois"),
                                    config={"displayModeBar": False},
                                    style={"height": "340px"},
                                ),
                                titre="Consommation mensuelle",
                                sous_titre="Volumes agrégés par mois",
                            ),
                            className="app-chart-col",
                        ),
                    ],
                    className="app-charts-row",
                ),
                CardComponent.construire(
                    dcc.Graph(
                        id="graphique-demande",
                        figure=self._figs_initiales.get("demande"),
                        config={
                            "displayModeBar": True,
                            "modeBarButtonsToRemove": ["lasso2d", "select2d"],
                        },
                        style={"height": "360px"},
                    ),
                    titre="Demande vs réception",
                    sous_titre="Comparaison des flux d'approvisionnement",
                ),
            ],
            className="app-tab-panel",
        )
