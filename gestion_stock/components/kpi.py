"""Composants de cartes KPI."""

from dash import html


class KPIComponent:
    """Indicateurs clés — style enterprise minimal."""

    KPI_DEFS = [
        ("nb_produits_total", "Produits suivis", "total"),
        ("nb_risque_rupture_eleve", "Ruptures élevées", "rupture"),
        ("nb_risque_peremption_eleve", "Péremptions élevées", "peremption"),
        ("nb_zone_a", "Zone A (priorité)", "zone_a"),
    ]

    @staticmethod
    def creer_carte(valeur, libelle: str, accent: str) -> html.Div:
        return html.Div(
            [
                html.Span(libelle, className="app-kpi-label"),
                html.Span(str(valeur), className="app-kpi-value"),
            ],
            className="app-kpi-card",
            style={"--kpi-accent": accent},
        )

    @classmethod
    def creer_rangée(cls, kpis: dict[str, int], theme: dict[str, dict]) -> html.Div:
        cartes = [
            cls.creer_carte(kpis[cle], libelle, theme[couleur]["accent"])
            for cle, libelle, couleur in cls.KPI_DEFS
        ]
        return html.Div(cartes, className="app-kpi-grid")
