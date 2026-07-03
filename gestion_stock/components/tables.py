"""Tableau des risques de rupture et de péremption."""

import pandas as pd
from dash import dash_table, html

from gestion_stock.config import AppConfig


class RiskTable:
    """ Affiche le tableau interactif des risques par produit."""

    def __init__(self, config: AppConfig | None = None):
        self.config = config or AppConfig()
        # Thème couleurs/styles spécifique aux tableaux (distinct du thème des graphiques)
        theme = self.config.THEME_TABLEAU

        # Styles réutilisés pour surligner les cellules selon le niveau de risque
        self.STYLE_RISQUE_ELEVE = {
            "backgroundColor": theme["danger_fond"],
            "color": theme["danger_texte"],
            "fontWeight": "600",
            "borderRadius": "6px",
        }
        self.STYLE_RISQUE_FAIBLE = {
            "backgroundColor": theme["success_fond"],
            "color": theme["success_texte"],
            "fontWeight": "500",
            "borderRadius": "6px",
        }

    def _colonnes(self) -> list[dict]:
        # Construit la liste des colonnes du DataTable à partir du mapping
        # {id_colonne: nom_affiché} défini dans la config
        # -> permet de renommer/réordonner les colonnes affichées sans toucher aux données brutes
        return [
            {"name": self.config.NOMS_COLONNES_AFFICHEES[col], "id": col}
            for col in self.config.NOMS_COLONNES_AFFICHEES
        ]

    def _styles_conditionnels(self) -> list[dict]:
        # Règles de style conditionnel du DataTable (style_data_conditional) :
        # applique un fond coloré selon le niveau de risque, colonne par colonne
        return [
            {
                "if": {
                    "filter_query": "{risque_rupture} = 'Élevé'",
                    "column_id": "risque_rupture",
                },
                **self.STYLE_RISQUE_ELEVE,
            },
            {
                "if": {
                    "filter_query": "{risque_rupture} = 'Faible'",
                    "column_id": "risque_rupture",
                },
                **self.STYLE_RISQUE_FAIBLE,
            },
            {
                "if": {
                    "filter_query": "{risque_peremption} = 'Élevé'",
                    "column_id": "risque_peremption",
                },
                **self.STYLE_RISQUE_ELEVE,
            },
            {
                "if": {
                    "filter_query": "{risque_peremption} = 'Faible'",
                    "column_id": "risque_peremption",
                },
                **self.STYLE_RISQUE_FAIBLE,
            },
            # Alternance de couleur de fond une ligne sur deux, pour la lisibilité
            {
                "if": {"row_index": "odd"},
                "backgroundColor": self.config.THEME_TABLEAU["ligne_alternee"],
            },
        ]

    def construire(self, stats_produits: pd.DataFrame) -> html.Div:
        theme = self.config.THEME_TABLEAU
        return html.Div(
            [
                html.H3(
                    "Risques de rupture et de péremption par produit",
                    className="app-table-header",
                ),
                dash_table.DataTable(
                    id="tableau-risques",
                    columns=self._colonnes(),
                    # Conversion du DataFrame en liste de dicts, format attendu par DataTable
                    data=stats_produits.to_dict("records"),
                    page_size=10,           # Pagination : 10 lignes par page
                    sort_action="native",   # Tri géré côté client par Dash (pas de callback custom)
                    filter_action="native", # Filtrage géré côté client par Dash
                    style_cell={
                        "textAlign": "left",
                        "whiteSpace": "normal",  # Permet le retour à la ligne dans les cellules
                        "height": "auto",
                        "fontFamily": "Inter, Segoe UI, sans-serif",
                        "fontSize": "13px",
                        "padding": "12px 14px",
                        "border": "none",
                        "color": theme["texte"],
                    },
                    style_header={
                        "backgroundColor": theme["entete_fond"],
                        "color": theme["entete_texte"],
                        "fontWeight": "600",
                        "fontSize": "12px",
                        "textTransform": "uppercase",
                        "letterSpacing": "0.04em",
                        "border": "none",
                        "borderBottom": f"2px solid {theme['entete_bordure']}",
                    },
                    style_table={
                        "overflowX": "auto",   # Défilement horizontal si le tableau est trop large
                        "borderRadius": "8px",
                        "border": f"1px solid {theme['bordure']}",
                    },
                    style_data={"border": "none"},
                    # Applique le surlignage par niveau de risque + l'alternance de lignes
                    style_data_conditional=self._styles_conditionnels(),
                ),
            ]
        )