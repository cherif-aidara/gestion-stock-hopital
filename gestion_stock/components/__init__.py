from gestion_stock.components.card import CardComponent
from gestion_stock.components.charts import ChartBuilder
from gestion_stock.components.header import HeaderComponent
from gestion_stock.components.kpi import KPIComponent
from gestion_stock.components.product_panel import ProductConsumptionPanel
from gestion_stock.components.product_stats import ProductStatsComponent
from gestion_stock.components.sidebar import SidebarComponent
from gestion_stock.components.tables import RiskTable

# Liste explicite des symboles exportés par le package
# -> définit ce qui est accessible via "from gestion_stock.components import *"
# -> sert aussi de documentation rapide sur l'API publique du module
__all__ = [
    "CardComponent",
    "ChartBuilder",
    "HeaderComponent",
    "KPIComponent",
    "ProductConsumptionPanel",
    "ProductStatsComponent",
    "SidebarComponent",
    "RiskTable",
]