"""Statistiques de consommation pour un produit sélectionné."""

from dash import html


class ProductStatsComponent:
    """Indicateurs détaillés d'un produit — layout pro."""

    STAT_DEFS = [
        ("consommation_totale", "Consommation totale"),
        ("consommation_moy_jour", "Moyenne / jour"),
        ("consommation_max_jour", "Pic journalier"),
        ("nb_requisitions", "Réquisitions"),
        ("stock_actuel", "Stock actuel"),
        ("jours_couverture", "Jours de couverture"),
        ("seuil_commande", "Seuil de commande"),
        ("classe_velocite", "Vélocité"),
        ("zone_suggeree", "Zone entrepôt"),
    ]

    @classmethod
    def contenu_vide(cls) -> list:
        return [
            html.P(
                "Sélectionnez un produit pour afficher ses statistiques.",
                className="app-empty-state",
            )
        ]

    @classmethod
    def construire_contenu(cls, stats: dict) -> list:
        risque_rupture = stats.get("risque_rupture", "Faible")
        risque_peremption = stats.get("risque_peremption", "Faible")

        return [
            html.Div(
                [
                    html.Div(
                        [
                            html.Span("Fiche produit", className="app-product-eyebrow"),
                            html.H3(
                                stats.get("nom_court", stats["produit"]),
                                className="app-product-name",
                            ),
                            html.P(stats["produit"], className="app-product-fullname"),
                        ],
                        className="app-product-info",
                    ),
                    html.Div(
                        [
                            cls._badge("Rupture", risque_rupture),
                            cls._badge("Péremption", risque_peremption),
                        ],
                        className="app-product-badges",
                    ),
                ],
                className="app-product-header-row",
            ),
            html.Div(
                [cls._metric(cle, label, stats) for cle, label in cls.STAT_DEFS],
                className="app-product-stats-grid",
            ),
        ]

    @staticmethod
    def _metric(cle: str, label: str, stats: dict) -> html.Div:
        valeur = stats.get(cle, "—")
        if isinstance(valeur, float):
            valeur = f"{valeur:,.1f}".replace(",", " ")
        elif isinstance(valeur, int):
            valeur = f"{valeur:,}".replace(",", " ")

        return html.Div(
            [
                html.Span(label, className="app-metric-label"),
                html.Span(str(valeur), className="app-metric-value"),
            ],
            className="app-metric",
        )

    @staticmethod
    def _badge(libelle: str, niveau: str) -> html.Span:
        css = "app-badge app-badge-danger" if niveau == "Élevé" else "app-badge app-badge-success"
        return html.Span([html.Span(className="app-badge-dot"), f"{libelle} · {niveau}"], className=css)
