"""Configuration centralisée de l'application."""


class AppConfig:
    """Constantes et chemins de l'application."""

    # Niveau de service visé pour le calcul du stock de sécurité
    # -> z = 1.65 correspond à ~95% de niveau de service (loi normale)
    # Utilisé dans InventoryAnalytics._calculer_stats_produits
    Z_NIVEAU_SERVICE = 1.65  # niveau de service visé ~95%

    # Chemins vers les fichiers sources de données (relatifs à la racine du projet)
    CHEMIN_REQUISITIONS = "data/requisitions_echantillon.csv"
    CHEMIN_RECEPTIONS = "data/receptions_echantillon.csv"

    # Noms exacts des colonnes de quantité dans les fichiers sources
    # -> centralisés ici pour éviter de répéter/désynchroniser ces chaînes
    # dans tout le code (ChartBuilder, InventoryAnalytics, etc.)
    COLONNE_QTE_REQUISITION = "Ligne réquisition - Qté"
    COLONNE_QTE_RECEPTION = "Ligne réception - Qté reçue"

    # Graines aléatoires fixes pour les simulations (stock actuel, péremption)
    # -> garantit des résultats reproductibles à chaque exécution
    GRAINES_ALEATOIRES = {"stock": 42, "peremption": 7}

    # Textes d'identité de l'application, utilisés dans le logo/sidebar
    TITRE = "Stock Hospitalier"
    SOUS_TITRE = "Entrepôt & Approvisionnement"
    NOM_ORGANISATION = "Centre hospitalier"

    # Mapping {nom technique de colonne -> libellé affiché}
    # -> pilote les en-têtes du RiskTable (dash_table.DataTable)
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

    # Couleurs d'accent + fond pour chaque carte KPI de la page Vue d'ensemble
    # (clé = type de KPI, utilisé par KPIComponent)
    THEME_KPI = {
        "total": {"accent": "#0EA5E9", "fond": "#E0F2FE"},
        "rupture": {"accent": "#EF4444", "fond": "#FEE2E2"},
        "peremption": {"accent": "#F59E0B", "fond": "#FEF3C7"},
        "zone_a": {"accent": "#10B981", "fond": "#D1FAE5"},
    }

    # Palette commune utilisée par ChartBuilder pour styliser tous les graphiques
    # Plotly (texte, grille, et couleurs des séries demande/réception)
    THEME_GRAPHIQUES = {
        "texte": "#0F172A",
        "grille": "#E2E8F0",
        "demande": "#0EA5E9",
        "reception": "#10B981",
    }

    # Palette dédiée au tableau des risques (RiskTable) :
    # couleurs d'en-tête, bordures, lignes alternées, et styles danger/succès
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

    # Définition centralisée des 3 pages du dashboard : route -> métadonnées
    # -> utilisé à la fois par SidebarComponent (liens de nav), StockDashboardApp
    # (routage/callback de navigation) et DashboardLayout (structure des pages)
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

    # Route de repli si l'URL ne correspond à aucune page connue
    # (utilisée par StockDashboardApp._resoudre_pathname)
    PAGE_DEFAUT = "/"