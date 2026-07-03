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
        # Liste qui contiendra tous les éléments enfants de la carte
        # (en-tête optionnel + contenu passé en paramètre)
        enfants = []

        # Si un titre est fourni, on construit un bloc d'en-tête
        if titre:
            header_children = [html.H3(titre, className="app-card-title")]

            # Le sous-titre est optionnel et ne s'ajoute que si le titre existe
            if sous_titre:
                header_children.append(
                    html.P(sous_titre, className="app-card-subtitle")
                )

            # On regroupe titre + sous-titre dans un conteneur d'en-tête
            enfants.append(html.Div(header_children, className="app-card-header"))

        # Le contenu peut être soit une liste de composants Dash,
        # soit un composant unique : on gère les deux cas
        if isinstance(contenu, list):
            # Si c'est une liste, on l'étale directement dans "enfants"
            enfants.extend(contenu)
        else:
            # Sinon, on l'ajoute comme élément unique
            enfants.append(contenu)

        # Construction finale de la carte :
        # - className combine la classe de base "app-card" et une classe
        #   personnalisée optionnelle passée en paramètre
        # - .strip() évite un espace superflu si className est vide
        return html.Div(enfants, className=f"app-card {className}".strip())