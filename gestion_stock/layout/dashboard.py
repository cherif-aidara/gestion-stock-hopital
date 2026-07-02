"""Assemblage de la mise en page du tableau de bord."""

from dash import dcc, html

from gestion_stock.components.header import HeaderComponent
from gestion_stock.components.product_panel import ProductConsumptionPanel
from gestion_stock.components.sidebar import SidebarComponent
from gestion_stock.config import AppConfig
from gestion_stock.layout.overview_page import OverviewPage
from gestion_stock.layout.risks_page import RisksPage
from gestion_stock.components.charts import ChartBuilder
from gestion_stock.services.inventory_analytics import InventoryAnalytics


class DashboardLayout:
    """Construit la structure HTML avec navigation multi-pages."""

    def __init__(
        self,
        analytics: InventoryAnalytics,
        config: AppConfig | None = None,
    ):
        self.analytics = analytics
        self.config = config or AppConfig()
        self.chart_builder = ChartBuilder(self.config)

    def construire(self) -> html.Div:
        overview = OverviewPage(
            self.analytics, self.chart_builder, self.config
        ).construire()
        consommation = ProductConsumptionPanel(
            self.analytics, self.chart_builder, self.config
        ).construire()
        risques = RisksPage(self.analytics, self.config).construire()

        return html.Div(
            [
                dcc.Location(id="url", refresh=False),
                SidebarComponent.construire(self.config.NOM_ORGANISATION),
                html.Div(
                    [
                        HeaderComponent.construire(),
                        html.Div(
                            [
                                html.Div(
                                    overview,
                                    id="page-overview",
                                    className="app-page",
                                ),
                                html.Div(
                                    consommation,
                                    id="page-consommation",
                                    className="app-page app-page-hidden",
                                ),
                                html.Div(
                                    risques,
                                    id="page-risques",
                                    className="app-page app-page-hidden",
                                ),
                            ],
                            className="app-content",
                        ),
                    ],
                    className="app-main",
                ),
            ],
            className="app-shell",
        )
