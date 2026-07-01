import pandas as pd
import plotly.graph_objects as go
from dash import Dash, html, dcc, Input, Output, dash_table
import numpy as np
import plotly.express as px

Z = 1.65  # niveau de service visé ~95%


df = pd.read_csv("data/requisitions_echantillon.csv", low_memory=False)
df["Date"] = pd.to_datetime(df["Date"])

df_rec = pd.read_csv("data/receptions_echantillon.csv", low_memory=False)
df_rec["Date"] = pd.to_datetime(df_rec["Date"])

# Demande moyenne et variabilité par produit
stats_demande = (
    df.groupby("Produit")["Ligne réquisition - Qté"].agg(["mean", "std"]).reset_index()
)
stats_demande.columns = ["Produit", "demande_moyenne", "demande_ecart_type"]

df_rec_trie = df_rec.sort_values(["Produit", "Date"])
df_rec_trie["jours_depuis_derniere_reception"] = (
    df_rec_trie.groupby("Produit")["Date"].diff().dt.days
)

delai_reappro = (
    df_rec_trie.groupby("Produit")["jours_depuis_derniere_reception"]
    .median()
    .reset_index()
)
delai_reappro.columns = ["Produit", "delai_reappro_jours"]

stats_produits = stats_demande.merge(delai_reappro, on="Produit")

stats_produits["stock_securite"] = (
    Z
    * stats_produits["demande_ecart_type"]
    * np.sqrt(stats_produits["delai_reappro_jours"])
)
stats_produits["point_commande"] = (
    stats_produits["demande_moyenne"] * stats_produits["delai_reappro_jours"]
    + stats_produits["stock_securite"]
)

np.random.seed(42)

stats_produits["stock_actuel_simule"] = (
    stats_produits["point_commande"] * np.random.uniform(0.4, 1.8, len(stats_produits))
).round(0)

stats_produits["risque_rupture"] = np.where(
    stats_produits["stock_actuel_simule"] < stats_produits["point_commande"],
    "Élevé",
    "Faible",
)

np.random.seed(7)

stats_produits["jours_couverture_stock"] = (
    stats_produits["stock_actuel_simule"] / stats_produits["demande_moyenne"]
).round(1)

stats_produits["jours_avant_peremption"] = np.random.randint(
    15, 400, size=len(stats_produits)
)

stats_produits["risque_peremption"] = np.where(
    stats_produits["jours_avant_peremption"] < stats_produits["jours_couverture_stock"],
    "Élevé",
    "Faible",
)

stats_produits["classe_velocite"] = pd.qcut(
    stats_produits["demande_moyenne"], q=3, labels=["Faible", "Moyenne", "Haute"]
)


def assigner_zone(classe):
    if classe == "Haute":
        return "Zone A - Proche expédition"
    elif classe == "Moyenne":
        return "Zone B - Intermédiaire"
    else:
        return "Zone C - Éloignée"


stats_produits["zone_suggeree"] = stats_produits["classe_velocite"].apply(assigner_zone)

nb_produits_total = len(stats_produits)
nb_risque_rupture_eleve = (stats_produits["risque_rupture"] == "Élevé").sum()
nb_risque_peremption_eleve = (stats_produits["risque_peremption"] == "Élevé").sum()
nb_zone_a = (stats_produits["zone_suggeree"] == "Zone A - Proche expédition").sum()

repartition_velocite = stats_produits["classe_velocite"].value_counts().reset_index()
repartition_velocite.columns = ["classe_velocite", "nombre"]

fig_donut_velocite = px.pie(
    repartition_velocite,
    names="classe_velocite",
    values="nombre",
    hole=0.5,
    title="Répartition des produits par vélocité",
)


def creer_carte_kpi(valeur, libelle, couleur="#4a90d9"):
    return html.Div(
        [
            html.H2(
                str(valeur), style={"margin": "0", "color": "white", "fontSize": "32px"}
            ),
            html.P(
                libelle, style={"margin": "0", "color": "white", "fontSize": "14px"}
            ),
        ],
        style={
            "backgroundColor": couleur,
            "padding": "20px",
            "borderRadius": "8px",
            "textAlign": "center",
            "flex": "1",
            "margin": "5px",
        },
    )


noms_colonnes_affichees = {
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


liste_produits = sorted(df["Produit"].unique())

app = Dash(__name__)

app.layout = html.Div(
    [
        html.H1("Tableau de bord - Entrepôt hospitalier"),
        html.Div(
            [
                creer_carte_kpi(nb_produits_total, "Total produits suivis", "#4a90d9"),
                creer_carte_kpi(
                    nb_risque_rupture_eleve, "Risque rupture élevé", "#e74c3c"
                ),
                creer_carte_kpi(
                    nb_risque_peremption_eleve, "Risque péremption élevé", "#e67e22"
                ),
                creer_carte_kpi(nb_zone_a, "Produits en Zone A", "#27ae60"),
            ],
            style={"display": "flex", "marginBottom": "20px"},
        ),
        dcc.Graph(figure=fig_donut_velocite),
        dcc.Tabs(
            [
                dcc.Tab(
                    label="Prévisions de demande",
                    children=[
                        dcc.Dropdown(
                            id="dropdown-produit",
                            options=liste_produits,
                            value=liste_produits[0],
                        ),
                        dcc.Graph(id="graphique-demande"),
                    ],
                ),
                dcc.Tab(
                    label="Risques & Réapprovisionnement",
                    children=[
                        html.H2("Risques de rupture et de péremption par produit"),
                        dash_table.DataTable(
                            id="tableau-risques",
                            columns=[
                                {"name": noms_colonnes_affichees[col], "id": col}
                                for col in noms_colonnes_affichees
                            ],
                            data=stats_produits.to_dict("records"),
                            page_size=10,
                            sort_action="native",
                            filter_action="native",
                            style_cell={
                                "textAlign": "left",
                                "whiteSpace": "normal",
                                "height": "auto",
                                "fontFamily": "Arial",
                                "fontSize": "13px",
                                "padding": "5px",
                            },
                            style_table={"overflowX": "auto"},
                            style_data_conditional=[
                                {
                                    "if": {
                                        "filter_query": "{risque_rupture} = 'Élevé'",
                                        "column_id": "risque_rupture",
                                    },
                                    "backgroundColor": "#ffcccc",
                                    "color": "darkred",
                                    "fontWeight": "bold",
                                },
                                {
                                    "if": {
                                        "filter_query": "{risque_rupture} = 'Faible'",
                                        "column_id": "risque_rupture",
                                    },
                                    "backgroundColor": "#ccffcc",
                                    "color": "darkgreen",
                                },
                                {
                                    "if": {
                                        "filter_query": "{risque_peremption} = 'Élevé'",
                                        "column_id": "risque_peremption",
                                    },
                                    "backgroundColor": "#ffcccc",
                                    "color": "darkred",
                                    "fontWeight": "bold",
                                },
                                {
                                    "if": {
                                        "filter_query": "{risque_peremption} = 'Faible'",
                                        "column_id": "risque_peremption",
                                    },
                                    "backgroundColor": "#ccffcc",
                                    "color": "darkgreen",
                                },
                            ],
                        ),
                    ],
                ),
            ]
        ),
    ],
    style={
        "maxWidth": "1200px",
        "margin": "0 auto",
        "padding": "20px",
        "fontFamily": "Arial",
    },
)


@app.callback(Output("graphique-demande", "figure"), Input("dropdown-produit", "value"))
def mettre_a_jour_graphique(produit_choisi):
    df_produit = df[df["Produit"] == produit_choisi]
    demande_jour = df_produit.groupby("Date", as_index=False)[
        "Ligne réquisition - Qté"
    ].sum()

    df_produit_rec = df_rec[df_rec["Produit"] == produit_choisi]
    reception_jour = df_produit_rec.groupby("Date", as_index=False)[
        "Ligne réception - Qté reçue"
    ].sum()

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=demande_jour["Date"],
            y=demande_jour["Ligne réquisition - Qté"],
            mode="lines",
            name="Demande (réquisitions)",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=reception_jour["Date"],
            y=reception_jour["Ligne réception - Qté reçue"],
            mode="lines+markers",
            name="Réception",
        )
    )

    fig.update_layout(title=f"Demande vs Réception — {produit_choisi}")

    return fig


if __name__ == "__main__":
    app.run(debug=True)
