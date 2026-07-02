"""Construction des graphiques Plotly."""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from gestion_stock.config import AppConfig


class ChartBuilder:
    """Génère les figures Plotly du tableau de bord."""

    COULEURS_VELOCITE = {
        "Faible": "#94A3B8",
        "Moyenne": "#0EA5E9",
        "Haute": "#0369A1",
    }

    def __init__(self, config: AppConfig | None = None):
        self.config = config or AppConfig()
        self._theme = self.config.THEME_GRAPHIQUES

    def _appliquer_theme(self, fig: go.Figure, titre: str | None = None) -> go.Figure:
        fig.update_layout(
            title=dict(
                text=titre,
                font=dict(
                    family="Inter, Segoe UI, sans-serif",
                    size=15,
                    color=self._theme["texte"],
                ),
                x=0,
                xanchor="left",
            )
            if titre
            else None,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(
                family="Inter, Segoe UI, sans-serif",
                color=self._theme["texte"],
                size=12,
            ),
            margin=dict(l=40, r=20, t=50 if titre else 20, b=40),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor="rgba(0,0,0,0)",
            ),
            hoverlabel=dict(
                bgcolor="white",
                font_size=12,
                font_family="Inter, sans-serif",
            ),
        )
        fig.update_xaxes(
            showgrid=True,
            gridcolor=self._theme["grille"],
            linecolor=self._theme["grille"],
            zeroline=False,
        )
        fig.update_yaxes(
            showgrid=True,
            gridcolor=self._theme["grille"],
            linecolor=self._theme["grille"],
            zeroline=False,
        )
        return fig

    def creer_donut_velocite(self, repartition: pd.DataFrame) -> go.Figure:
        couleurs = [
            self.COULEURS_VELOCITE.get(c, "#0B5EA8")
            for c in repartition["classe_velocite"]
        ]
        fig = px.pie(
            repartition,
            names="classe_velocite",
            values="nombre",
            hole=0.62,
            color="classe_velocite",
            color_discrete_map=self.COULEURS_VELOCITE,
        )
        fig.update_traces(
            textposition="outside",
            textinfo="label+percent",
            marker=dict(line=dict(color="white", width=2)),
            hovertemplate="<b>%{label}</b><br>%{value} produits<br>%{percent}<extra></extra>",
        )
        fig.add_annotation(
            text=f"<b>{repartition['nombre'].sum()}</b><br><span style='font-size:11px'>produits</span>",
            x=0.5,
            y=0.5,
            font=dict(size=18, color=self._theme["texte"], family="Inter"),
            showarrow=False,
        )
        return self._appliquer_theme(fig)

    COULEURS_ZONES = {
        "Zone A - Proche expédition": "#10B981",
        "Zone B - Intermédiaire": "#0EA5E9",
        "Zone C - Éloignée": "#94A3B8",
    }

    def creer_graphique_repartition_zones(self, repartition: pd.DataFrame) -> go.Figure:
        fig = go.Figure()
        couleurs = [
            self.COULEURS_ZONES.get(z, "#64748B") for z in repartition["zone"]
        ]
        fig.add_trace(
            go.Bar(
                x=repartition["zone"],
                y=repartition["nombre"],
                marker=dict(color=couleurs, line=dict(width=0)),
                hovertemplate="%{x}<br><b>%{y}</b> produits<extra></extra>",
            )
        )
        fig.update_layout(bargap=0.3, showlegend=False)
        fig.update_xaxes(tickangle=-15)
        return self._appliquer_theme(fig)

    def creer_graphique_tendance_globale(self, mensuel: pd.DataFrame) -> go.Figure:
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=mensuel["Mois"],
                y=mensuel["consommation"],
                mode="lines+markers",
                name="Consommation",
                line=dict(color=self._theme["demande"], width=2.5),
                marker=dict(size=5),
                fill="tozeroy",
                fillcolor="rgba(14, 165, 233, 0.08)",
                hovertemplate="%{x|%b %Y}<br><b>%{y:,.0f}</b> unités<extra></extra>",
            )
        )
        return self._appliquer_theme(fig)

    def creer_graphique_top_produits(self, top: pd.DataFrame) -> go.Figure:
        top_trie = top.sort_values("consommation_totale", ascending=True)
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=top_trie["consommation_totale"],
                y=top_trie["nom_court"],
                orientation="h",
                marker=dict(
                    color=top_trie["consommation_totale"],
                    colorscale=[[0, "#BAE6FD"], [1, "#0284C7"]],
                    line=dict(width=0),
                ),
                hovertemplate="<b>%{y}</b><br>%{x:,.0f} unités<extra></extra>",
            )
        )
        fig.update_layout(
            bargap=0.25,
            yaxis=dict(autorange="reversed"),
            margin=dict(l=180, r=20, t=20, b=40),
        )
        return self._appliquer_theme(fig)

    def creer_graphique_demande_reception(
        self,
        demande_jour: pd.DataFrame,
        reception_jour: pd.DataFrame,
        produit: str,
    ) -> go.Figure:
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=demande_jour["Date"],
                y=demande_jour[self.config.COLONNE_QTE_REQUISITION],
                mode="lines",
                name="Demande (réquisitions)",
                line=dict(color=self._theme["demande"], width=2.5),
                fill="tozeroy",
                fillcolor="rgba(11, 94, 168, 0.08)",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=reception_jour["Date"],
                y=reception_jour[self.config.COLONNE_QTE_RECEPTION],
                mode="lines+markers",
                name="Réception",
                line=dict(color=self._theme["reception"], width=2),
                marker=dict(size=6, color=self._theme["reception"]),
            )
        )

        return self._appliquer_theme(
            fig, titre=f"Demande vs Réception — {self._nom_court(produit)}"
        )

    @staticmethod
    def _nom_court(produit: str, longueur: int = 45) -> str:
        return produit if len(produit) <= longueur else produit[: longueur - 1] + "…"

    def creer_graphique_consommation_journaliere(
        self, conso_jour: pd.DataFrame, produit: str
    ) -> go.Figure:
        col = self.config.COLONNE_QTE_REQUISITION
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=conso_jour["Date"],
                y=conso_jour[col],
                mode="lines",
                name="Consommation",
                line=dict(color=self._theme["demande"], width=2),
                fill="tozeroy",
                fillcolor="rgba(14, 165, 233, 0.1)",
                hovertemplate="%{x|%d/%m/%Y}<br><b>%{y:,.0f}</b> unités<extra></extra>",
            )
        )
        if len(conso_jour) > 0:
            moyenne = conso_jour[col].mean()
            fig.add_hline(
                y=moyenne,
                line_dash="dash",
                line_color=self._theme["reception"],
                annotation_text=f"Moy. {moyenne:,.0f}/j",
                annotation_position="top right",
                annotation_font_size=11,
            )
        return self._appliquer_theme(
            fig, titre=f"Consommation journalière — {self._nom_court(produit)}"
        )

    def creer_graphique_consommation_mensuelle(
        self, conso_mois: pd.DataFrame, produit: str
    ) -> go.Figure:
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=conso_mois["Mois_label"],
                y=conso_mois["consommation"],
                name="Consommation",
                marker=dict(
                    color=conso_mois["consommation"],
                    colorscale=[[0, "#BAE6FD"], [0.5, "#38BDF8"], [1, "#0284C7"]],
                    line=dict(width=0),
                ),
                hovertemplate="%{x}<br><b>%{y:,.0f}</b> unités<extra></extra>",
            )
        )
        fig.update_layout(bargap=0.25)
        return self._appliquer_theme(
            fig, titre=f"Consommation mensuelle — {self._nom_court(produit)}"
        )
