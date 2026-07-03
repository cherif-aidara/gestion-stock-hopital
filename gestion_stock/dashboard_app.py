"""Application Dash principale."""

from pathlib import Path

from dash import Dash, Input, Output

from gestion_stock.components.charts import ChartBuilder
from gestion_stock.components.product_stats import ProductStatsComponent
from gestion_stock.config import AppConfig
from gestion_stock.data.loader import DataLoader
from gestion_stock.layout.dashboard import DashboardLayout
from gestion_stock.config import AppConfig  # Import en double (voir remarque plus bas)
from gestion_stock.services.inventory_analytics import InventoryAnalytics

# Classes CSS utilisées pour piloter l'état de la navigation
# et l'affichage/masquage des pages via le callback "naviguer"
NAV_ACTIVE = "app-nav-item app-nav-item-active"
NAV_INACTIVE = "app-nav-item"
PAGE_VISIBLE = "app-page"
PAGE_HIDDEN = "app-page app-page-hidden"


class StockDashboardApp:
    """Point d'entrée de l'application de gestion de stock."""

    def __init__(self, config: AppConfig | None = None):
        self.config = config or AppConfig()
        # Charge et prépare toutes les données avant de construire l'app Dash
        self._initialiser_donnees()

        # Dossier des assets statiques (CSS custom, images, etc.)
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
        # Instance unique de ChartBuilder, réutilisée par tous les callbacks
        # qui doivent regénérer des figures dynamiquement
        self.chart_builder = ChartBuilder(self.config)
        self._configurer_application()

    def _initialiser_donnees(self) -> None:
        # Charge les données brutes (réquisitions/réceptions) depuis la source
        # configurée, puis construit le service d'analytics à partir de celles-ci
        loader = DataLoader(self.config)
        df_requisitions, df_receptions = loader.charger_tout()
        self.analytics = InventoryAnalytics(
            df_requisitions, df_receptions, self.config
        )

    def _configurer_application(self) -> None:
        # Construit le layout complet (sidebar, pages, etc.) et l'assigne à Dash
        layout_builder = DashboardLayout(self.analytics, self.config)
        self.app.layout = layout_builder.construire()
        # Enregistre tous les callbacks (navigation + mise à jour produit)
        self._enregistrer_callbacks()

    @staticmethod
    def _resoudre_pathname(pathname: str | None) -> str:
        # Sécurise le routage : si l'URL ne correspond à aucune page connue
        # (ou est vide/None), on retombe sur la page par défaut
        if pathname in AppConfig.PAGES:
            return pathname
        return AppConfig.PAGE_DEFAUT

    def _enregistrer_callbacks(self) -> None:
        # --- Callback de navigation ---
        # Se déclenche à chaque changement d'URL (composant dcc.Location "url")
        # et pilote à la fois :
        # - la visibilité des 3 pages (overview / consommation / risques)
        # - l'état actif du lien de navigation correspondant dans la sidebar
        # - le titre/sous-titre affichés dans la barre du haut (topbar)
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
            # Table de correspondance : pour chaque route, la combinaison exacte
            # de classes CSS à appliquer aux 3 pages + 3 liens de nav
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
            # Récupère titre/sous-titre de la page depuis la config centralisée
            meta = AppConfig.PAGES[path]
            return (*vis, meta["titre"], meta["sous_titre"])

        # --- Callback de mise à jour produit ---
        # Se déclenche quand l'utilisateur change de produit dans le dropdown
        # de la page "Consommation" ; régénère stats + les 3 graphiques associés
        @self.app.callback(
            Output("stats-produit", "children"),
            Output("graphique-consommation-jour", "figure"),
            Output("graphique-consommation-mois", "figure"),
            Output("graphique-demande", "figure"),
            Input("dropdown-produit", "value"),
        )
        def mettre_a_jour_produit(produit_choisi: str):
            # Cas où aucun produit n'est sélectionné : affiche un état vide
            # partout (contenu vide + figures Plotly vides mais transparentes,
            # cohérentes avec le thème du dashboard)
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

            # Cas normal : récupère toutes les données du produit sélectionné
            # et reconstruit les 3 graphiques + le bloc de statistiques
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
        # Lance le serveur de développement Dash
        # (debug=True active le hot-reload et les messages d'erreur détaillés)
        self.app.run(debug=debug)