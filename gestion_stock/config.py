"""Configuration centralisée de l'application."""


class AppConfig:
    """Constantes et chemins de l'application."""

    Z_NIVEAU_SERVICE = 1.65  # niveau de service visé ~95%

    CHEMIN_REQUISITIONS = "data/requisitions_echantillon.csv"
    CHEMIN_RECEPTIONS = "data/receptions_echantillon.csv"

    COLONNE_QTE_REQUISITION = "Ligne réquisition - Qté"
    COLONNE_QTE_RECEPTION = "Ligne réception - Qté reçue"

    GRAINES_ALEATOIRES = {"stock": 42, "peremption": 7}

    TITRE = "Stock Hospitalier"
    SOUS_TITRE = "Entrepôt & Approvisionnement"
    NOM_ORGANISATION = "Centre hospitalier"

    NOMS_COLONNES_AFFICHEES = {
        "Produit": "Produit",
        "demande_moyenne": "Demande moy./jour",
        "point_commande": "Seuil de commande",
        "stock_actuel_simule": "Stock actuel (simulé)",
        "risque_rupture": "Risque de rupture",
        "jours_avant_peremption": "Jours avant péremption",
        "risque_peremption": "Risque de péremption",
        "classe_velocite": "Vélocité",
        "zone_suggeree": "Zone suggérée",
    }

    THEME_KPI = {
        "total": {"accent": "#0EA5E9", "fond": "#E0F2FE"},
        "rupture": {"accent": "#EF4444", "fond": "#FEE2E2"},
        "peremption": {"accent": "#F59E0B", "fond": "#FEF3C7"},
        "zone_a": {"accent": "#10B981", "fond": "#D1FAE5"},
    }

    THEME_GRAPHIQUES = {
        "texte": "#0F172A",
        "grille": "#E2E8F0",
        "demande": "#0EA5E9",
        "reception": "#10B981",
    }

    THEME_TABLEAU = {
        "texte": "#0F172A",
        "entete_fond": "#F8FAFC",
        "entete_texte": "#475569",
        "entete_bordure": "#0EA5E9",
        "bordure": "#E2E8F0",
        "ligne_alternee": "#F8FAFC",
        "danger_fond": "#FEE2E2",
        "danger_texte": "#B91C1C",
        "success_fond": "#D1FAE5",
        "success_texte": "#047857",
    }

    PAGES = {
        "/": {
            "id": "overview",
            "label": "Vue d'ensemble",
            "titre": "Vue d'ensemble",
            "sous_titre": "Indicateurs globaux du stock hospitalier",
        },
        "/consommation": {
            "id": "consommation",
            "label": "Consommation",
            "titre": "Consommation par produit",
            "sous_titre": "Analyse détaillée de la demande et des flux",
        },
        "/risques": {
            "id": "risques",
            "label": "Risques & Réappro",
            "titre": "Risques & Réapprovisionnement",
            "sous_titre": "Suivi des ruptures et péremptions",
        },
    }

    PAGE_DEFAUT = "/"
