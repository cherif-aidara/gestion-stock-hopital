"""Statistiques de consommation pour un produit sélectionné."""

from dash import html


class ProductStatsComponent:
    """Indicateurs détaillés d'un produit — layout pro."""

    # Liste ordonnée des statistiques à afficher : (clé dans le dict "stats", libellé affiché)
    # -> pilote à la fois l'ordre et le contenu de la grille de métriques
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
        # État par défaut affiché quand aucun produit n'est encore sélectionné
        # (ex: au premier chargement si la liste de produits est vide)
        return [
            html.P(
                "Sélectionnez un produit pour afficher ses statistiques.",
                className="app-empty-state",
            )
        ]

    @classmethod
    def construire_contenu(cls, stats: dict) -> list:
        # Niveaux de risque avec valeur par défaut "Faible" si absents du dict
        risque_rupture = stats.get("risque_rupture", "Faible")
        risque_peremption = stats.get("risque_peremption", "Faible")

        return [
            # --- Ligne d'en-tête : identité du produit + badges de risque ---
            html.Div(
                [
                    html.Div(
                        [
                            html.Span("Fiche produit", className="app-product-eyebrow"),
                            # Nom court utilisé si disponible, sinon le nom complet en repli
                            html.H3(
                                stats.get("nom_court", stats["produit"]),
                                className="app-product-name",
                            ),
                            # Nom complet toujours affiché en dessous (pour contexte/vérification)
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
            # --- Grille de métriques générée dynamiquement à partir de STAT_DEFS ---
            html.Div(
                [cls._metric(cle, label, stats) for cle, label in cls.STAT_DEFS],
                className="app-product-stats-grid",
            ),
        ]

    @staticmethod
    def _metric(cle: str, label: str, stats: dict) -> html.Div:
        # Récupère la valeur associée à la clé, "—" par défaut si absente
        valeur = stats.get(cle, "—")

        # Formatage des nombres avec séparateur de milliers (espace, format FR/QC)
        # -> f"{x:,.1f}" produit un séparateur "," par défaut, qu'on remplace par un espace
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
        # Badge rouge ("danger") si le niveau de risque est "Élevé",
        # vert ("success") pour tout autre niveau (Faible, Moyen, etc.)
        css = "app-badge app-badge-danger" if niveau == "Élevé" else "app-badge app-badge-success"
        return html.Span([html.Span(className="app-badge-dot"), f"{libelle} · {niveau}"], className=css)