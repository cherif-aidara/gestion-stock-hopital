"""Point d'entrée de l'application de gestion de stock hospitalier."""

from gestion_stock.dashboard_app import StockDashboardApp

if __name__ == "__main__":
    StockDashboardApp().run(debug=True)
