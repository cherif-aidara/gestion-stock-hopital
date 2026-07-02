"""En-tête principal du contenu."""

from datetime import date

from dash import html


class HeaderComponent:
    """Barre supérieure du contenu principal."""

    @staticmethod
    def construire() -> html.Header:
        return html.Header(
            [
                html.Div(
                    [
                        html.H1(id="topbar-title", className="app-topbar-title"),
                        html.P(id="topbar-subtitle", className="app-topbar-subtitle"),
                    ],
                    className="app-topbar-left",
                ),
                html.Div(
                    html.Span(
                        date.today().strftime("%d %B %Y"),
                        className="app-topbar-date",
                    ),
                    className="app-topbar-right",
                ),
            ],
            className="app-topbar",
        )
