"""Cartes conteneurs réutilisables."""

from dash import html


class CardComponent:
    """Enveloppe visuelle pour sections et graphiques."""

    @staticmethod
    def construire(
        contenu,
        titre: str | None = None,
        sous_titre: str | None = None,
        className: str = "",
    ) -> html.Div:
        enfants = []

        if titre:
            header_children = [html.H3(titre, className="app-card-title")]
            if sous_titre:
                header_children.append(
                    html.P(sous_titre, className="app-card-subtitle")
                )
            enfants.append(html.Div(header_children, className="app-card-header"))

        if isinstance(contenu, list):
            enfants.extend(contenu)
        else:
            enfants.append(contenu)

        return html.Div(enfants, className=f"app-card {className}".strip())
