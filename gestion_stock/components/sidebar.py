"""Barre latérale et navigation."""

from dash import dcc, html

from gestion_stock.config import AppConfig


class SidebarComponent:
    """Navigation latérale avec liens vers les 3 pages."""

    @staticmethod
    def _lien(path: str, page_id: str) -> dcc.Link:
        meta = AppConfig.PAGES[path]
        return dcc.Link(
            html.Div(
                [
                    html.Span(className="app-nav-dot"),
                    meta["label"],
                ],
                id=f"nav-{page_id}",
                className="app-nav-item",
            ),
            href=path,
            className="app-nav-link",
        )

    @classmethod
    def construire(cls, organisation: str) -> html.Aside:
        return html.Aside(
            [
                html.Div(
                    [
                        html.Div("CH", className="app-logo-mark"),
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
                html.Nav(
                    [
                        html.Span("Navigation", className="app-nav-label"),
                        cls._lien("/", "overview"),
                        cls._lien("/consommation", "consommation"),
                        cls._lien("/risques", "risques"),
                    ],
                    className="app-nav",
                ),
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
