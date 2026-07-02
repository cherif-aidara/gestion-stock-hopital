"""Application Dash principale."""

from pathlib import Path

from dash import Dash, Input, Output

from gestion_stock.components.charts import ChartBuilder
from gestion_stock.components.product_stats import ProductStatsComponent
from gestion_stock.config import AppConfig
from gestion_stock.data.loader import DataLoader
from gestion_stock.layout.dashboard import DashboardLayout
from gestion_stock.config import AppConfig
from gestion_stock.services.inventory_analytics import InventoryAnalytics

NAV_ACTIVE = "app-nav-item app-nav-item-active"
NAV_INACTIVE = "app-nav-item"
PAGE_VISIBLE = "app-page"
PAGE_HIDDEN = "app-page app-page-hidden"


class StockDashboardApp:
    """Point d'entrée de l'application de gestion de stock."""

    def __init__(self, config: AppConfig | None = None):
        self.config = config or AppConfig()
        self._initialiser_donnees()
        assets_path = Path(__file__).parent / "assets"
        self.app = Dash(
            __name__,
            assets_folder=str(assets_path),
            title="Gestion Stock Hospitalier",
            meta_tags=[
                {"name": "viewport", "content": "width=device-width, initial-scale=1"},
                {
                    "name": "description",
                    "content": "Tableau de bord de gestion de stock hospitalier",
                },
            ],
        )
        self.chart_builder = ChartBuilder(self.config)
        self._configurer_application()

    def _initialiser_donnees(self) -> None:
        loader = DataLoader(self.config)
        df_requisitions, df_receptions = loader.charger_tout()
        self.analytics = InventoryAnalytics(
            df_requisitions, df_receptions, self.config
        )

    def _configurer_application(self) -> None:
        layout_builder = DashboardLayout(self.analytics, self.config)
        self.app.layout = layout_builder.construire()
        self._enregistrer_callbacks()

    @staticmethod
    def _resoudre_pathname(pathname: str | None) -> str:
        if pathname in AppConfig.PAGES:
            return pathname
        return AppConfig.PAGE_DEFAUT

    def _enregistrer_callbacks(self) -> None:
        @self.app.callback(
            Output("page-overview", "className"),
            Output("page-consommation", "className"),
            Output("page-risques", "className"),
            Output("nav-overview", "className"),
            Output("nav-consommation", "className"),
            Output("nav-risques", "className"),
            Output("topbar-title", "children"),
            Output("topbar-subtitle", "children"),
            Input("url", "pathname"),
        )
        def naviguer(pathname: str | None):
            path = self._resoudre_pathname(pathname)
            pages_cls = {
                "/": (
                    PAGE_VISIBLE,
                    PAGE_HIDDEN,
                    PAGE_HIDDEN,
                    NAV_ACTIVE,
                    NAV_INACTIVE,
                    NAV_INACTIVE,
                ),
                "/consommation": (
                    PAGE_HIDDEN,
                    PAGE_VISIBLE,
                    PAGE_HIDDEN,
                    NAV_INACTIVE,
                    NAV_ACTIVE,
                    NAV_INACTIVE,
                ),
                "/risques": (
                    PAGE_HIDDEN,
                    PAGE_HIDDEN,
                    PAGE_VISIBLE,
                    NAV_INACTIVE,
                    NAV_INACTIVE,
                    NAV_ACTIVE,
                ),
            }
            vis = pages_cls[path]
            meta = AppConfig.PAGES[path]
            return (*vis, meta["titre"], meta["sous_titre"])

        @self.app.callback(
            Output("stats-produit", "children"),
            Output("graphique-consommation-jour", "figure"),
            Output("graphique-consommation-mois", "figure"),
            Output("graphique-demande", "figure"),
            Input("dropdown-produit", "value"),
        )
        def mettre_a_jour_produit(produit_choisi: str):
            if not produit_choisi:
                from plotly.graph_objects import Figure

                fig_vide = Figure()
                fig_vide.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                )
                return (
                    ProductStatsComponent.contenu_vide(),
                    fig_vide,
                    fig_vide,
                    fig_vide,
                )

            stats = self.analytics.obtenir_stats_produit(produit_choisi)
            conso_jour = self.analytics.obtenir_consommation_journaliere(produit_choisi)
            conso_mois = self.analytics.obtenir_consommation_mensuelle(produit_choisi)
            demande_jour, reception_jour = (
                self.analytics.obtenir_series_demande_reception(produit_choisi)
            )

            return (
                ProductStatsComponent.construire_contenu(stats),
                self.chart_builder.creer_graphique_consommation_journaliere(
                    conso_jour, produit_choisi
                ),
                self.chart_builder.creer_graphique_consommation_mensuelle(
                    conso_mois, produit_choisi
                ),
                self.chart_builder.creer_graphique_demande_reception(
                    demande_jour, reception_jour, produit_choisi
                ),
            )

    def run(self, debug: bool = True) -> None:
        self.app.run(debug=debug)
