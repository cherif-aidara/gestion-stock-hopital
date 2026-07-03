"""Page Risques & Réapprovisionnement."""

from dash import html

from gestion_stock.components.tables import RiskTable
from gestion_stock.config import AppConfig
from gestion_stock.services.inventory_analytics import InventoryAnalytics


class RisksPage:
    """Tableau des risques par produit."""

    def __init__(
        self,
        analytics: InventoryAnalytics,
        config: AppConfig | None = None,
    ):
        self.analytics = analytics
        self.config = config or AppConfig()
        # Instancie le composant tableau une seule fois, avec la config partagée
        # (thème, styles conditionnels, etc.) — voir gestion_stock.components.tables.RiskTable
        self.risk_table = RiskTable(self.config)

    def construire(self) -> html.Div:
        # Page volontairement minimale : délègue tout l'affichage au RiskTable,
        # en lui passant le DataFrame de statistiques par produit déjà calculé
        # par le service d'analytics
        return html.Div(
            self.risk_table.construire(self.analytics.stats_produits),
            className="app-page-inner",
        )