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
        # Service d'analyse qui fournit les données (stats, séries temporelles, etc.)
        self.analytics = analytics
        # Générateur de figures Plotly, réutilisé pour tous les graphiques du panneau
        self.chart_builder = chart_builder
        self.config = config or AppConfig()
        # Liste des produits disponibles pour le dropdown (format {label, value})
        self.options = analytics.obtenir_options_produits()
        # Produit sélectionné par défaut au premier chargement (le premier de la liste)
        self.produit_defaut = self.options[0]["value"] if self.options else None
        # Pré-calcule les figures/stats du produit par défaut pour un affichage
        # immédiat au chargement de la page (avant toute interaction utilisateur)
        self._figs_initiales = self._generer_figures_initiales()

    def _generer_figures_initiales(self) -> dict:
        # Si aucun produit n'est disponible, on retourne un dict vide
        # (évite les erreurs plus loin lors de la construction du layout)
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
        # Récupère séparément les séries de demande et de réception
        # puis construit le graphique combiné des deux
        demande, reception = self.analytics.obtenir_series_demande_reception(produit)
        return self.chart_builder.creer_graphique_demande_reception(
            demande, reception, produit
        )

    def construire(self) -> html.Div:
        # Récupère les stats initiales calculées dans __init__
        stats_init = self._figs_initiales.get("stats")
        # Affiche le contenu réel si des stats existent, sinon un état vide
        # (utile si la liste de produits est vide au démarrage)
        contenu_stats = (
            ProductStatsComponent.construire_contenu(stats_init)
            if stats_init
            else ProductStatsComponent.contenu_vide()
        )

        return html.Div(
            [
                # --- Section "hero" : titre + sélecteur de produit (dropdown) ---
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
                                id="dropdown-produit",  # Utilisé comme Input dans les callbacks
                                options=self.options,
                                value=self.produit_defaut,  # Valeur initiale sélectionnée
                                className="app-dropdown app-dropdown-prominent",
                                clearable=False,  # Empêche de désélectionner sans remplacer
                                searchable=True,  # Permet la recherche par frappe
                                placeholder="Rechercher par code ou nom…",
                            ),
                            className="app-selector-input-wrap",
                        ),
                    ],
                    className="app-product-selector-hero",
                ),

                # --- Bloc de statistiques du produit sélectionné ---
                # id="stats-produit" -> cible d'un callback qui met à jour
                # le contenu quand le produit change dans le dropdown
                html.Div(
                    contenu_stats,
                    id="stats-produit",
                    className="app-product-panel",
                ),

                # --- Rangée de deux graphiques côte à côte : consommation jour / mois ---
                html.Div(
                    [
                        html.Div(
                            CardComponent.construire(
                                dcc.Graph(
                                    id="graphique-consommation-jour",
                                    figure=self._figs_initiales.get("conso_jour"),
                                    config={"displayModeBar": False},  # Masque la barre d'outils Plotly
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

                # --- Graphique combiné demande vs réception (pleine largeur) ---
                CardComponent.construire(
                    dcc.Graph(
                        id="graphique-demande",
                        figure=self._figs_initiales.get("demande"),
                        config={
                            "displayModeBar": True,  # Barre d'outils visible ici
                            # Retire les outils de sélection peu utiles pour ce graphique
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