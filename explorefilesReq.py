import pandas as pd
import json

""" Extractions Requisitions to csv """

annees = ["Req 2019", "Req 2020", "Req 2021", "Req 2022", "Req 2023", "Req 2024"]
chemin = "data/raw/Requisitions Famille 11 par jour 2019-2024_20260303.xlsx"


def charger_feuille_requisitions(chemin_fichier, nom_feuille):
    df = pd.read_excel(chemin_fichier, sheet_name=nom_feuille, header=4)

    # Enlever la ligne "Total général"
    df = df[df["Produit"] != "Total général"]

    # Corriger la colonne Date seulement si elle est en texte
    if df["Date"].dtype == "object" or df["Date"].dtype == "str":
        df["Date"] = pd.to_datetime(df["Date"], format="%y/%m/%d")

    return df


liste_dataframes = []

for nom_feuille in annees:
    df_annee = charger_feuille_requisitions(chemin, nom_feuille)
    liste_dataframes.append(df_annee)
    print(nom_feuille, "->", df_annee.shape)

df_complet = pd.concat(liste_dataframes, ignore_index=True)
print("Total combiné:", df_complet.shape)

# Pour chaque produit, on liste les années financières où il apparaît
annees_par_produit = df_complet.groupby("Produit")["Année financière"].nunique()
print(annees_par_produit.head(10))

produits_continus = annees_par_produit[annees_par_produit == 6].index

print("Nombre de produits présents sur les 6 années:", len(produits_continus))

# Quantité totale demandée par produit, sur toute la période
volume_par_produit = df_complet.groupby("Produit")["Ligne réquisition - Qté"].sum()

# On garde seulement les produits présents sur les 6 années
volume_par_produit = volume_par_produit[produits_continus]

# On trie du plus gros volume au plus petit
volume_par_produit = volume_par_produit.sort_values(ascending=False)

print(volume_par_produit.head(15))

# Liste ordonnée des produits, du plus gros volume au plus petit
produits_classes = volume_par_produit.index.tolist()
n = len(produits_classes)

# Découpage en 3 tranches
haute_velocite = produits_classes[:12]
moyenne_velocite = produits_classes[int(n * 0.15) : int(n * 0.15) + 12]
faible_velocite = produits_classes[int(n * 0.55) : int(n * 0.55) + 12]

selection = haute_velocite + moyenne_velocite + faible_velocite

print("Haute vélocité:", len(haute_velocite))
print("Moyenne vélocité:", len(moyenne_velocite))
print("Faible vélocité:", len(faible_velocite))
print("Total sélectionné:", len(selection))

df_echantillon = df_complet[df_complet["Produit"].isin(selection)]

print("Lignes dans l'échantillon final:", df_echantillon.shape)
print("Produits distincts dans l'échantillon:", df_echantillon["Produit"].nunique())


df_echantillon.to_csv("data/requisitions_echantillon.csv", index=False)
print("Fichier sauvegardé : data/requisitions_echantillon.csv")


with open("data/produits_selectionnes.json", "w", encoding="utf-8") as f:
    json.dump(selection, f, ensure_ascii=False, indent=2)

print("Liste des produits sauvegardée dans data/produits_selectionnes.json")
