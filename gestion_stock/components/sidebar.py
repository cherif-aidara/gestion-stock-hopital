"""Barre latérale et navigation."""

from dash import dcc, html

from gestion_stock.config import AppConfig


class SidebarComponent:
    """Navigation latérale avec liens vers les 3 pages."""

    @staticmethod
    def _lien(path: str, page_id: str) -> dcc.Link:
        # Récupère les métadonnées de la page (label, etc.) depuis la config centralisée
        # -> évite de dupliquer les libellés de navigation à plusieurs endroits
        meta = AppConfig.PAGES[path]
        return dcc.Link(
            html.Div(
                [
                    html.Span(className="app-nav-dot"),  # Puce visuelle (indicateur d'état/actif)
                    meta["label"],
                ],
                # id unique par page -> permet probablement de cibler l'item actif
                # via un callback ou du CSS (ex: surlignage de la page courante)
                id=f"nav-{page_id}",
                className="app-nav-item",
            ),
            href=path,  # Navigation Dash côté client (sans rechargement complet de la page)
            className="app-nav-link",
        )

    @classmethod
    def construire(cls, organisation: str) -> html.Aside:
        return html.Aside(
            [
                # --- Bloc logo / identité de l'organisation ---
                html.Div(
                    [
                        html.Div("CH", className="app-logo-mark"),  # Monogramme (ex: "Centre Hospitalier")
                        html.Div(
                            [
                                html.Span(organisation, className="app-logo-org"),
                                html.Span("Gestion de stock", className="app-logo-app"),
                            ],
                            className="app-logo-text",
                        ),
                    ],
                    className="app-logo",
                ),

                # --- Menu de navigation : les 3 pages principales du dashboard ---
                html.Nav(
                    [
                        html.Span("Navigation", className="app-nav-label"),
                        cls._lien("/", "overview"),
                        cls._lien("/consommation", "consommation"),
                        cls._lien("/risques", "risques"),
                    ],
                    className="app-nav",
                ),

                # --- Pied de sidebar : indicateur d'état du système ---
                # Actuellement en dur ("Système opérationnel" / "Données synchronisées")
                # -> pourrait être rendu dynamique plus tard si besoin d'un vrai statut
                html.Div(
                    [
                        html.Span(className="app-status-dot"),
                        html.Div(
                            [
                                html.Strong("Système opérationnel"),
                                html.Span("Données synchronisées"),
                            ],
                            className="app-sidebar-status-text",
                        ),
                    ],
                    className="app-sidebar-footer",
                ),
            ],
            className="app-sidebar",
        )