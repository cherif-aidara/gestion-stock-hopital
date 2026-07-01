import pandas as pd
import json


def charger_feuille_receptions(chemin_fichier, nom_feuille):
    df = pd.read_excel(chemin_fichier, sheet_name=nom_feuille, header=4)
    df = df[df["Produit"] != "Total général"]
    return df


annees_rec = ["Rec 2019", "Rec 2020", "Rec 2021", "Rec 2022", "Rec 2023", "Rec 2024"]
chemin_rec = "data/raw/Réceptions Famille 11 par jour 2019-2024_20260303.xlsx"

liste_dataframes_rec = []

for nom_feuille in annees_rec:
    df_annee = charger_feuille_receptions(chemin_rec, nom_feuille)
    liste_dataframes_rec.append(df_annee)
    print(nom_feuille, "->", df_annee.shape)

df_complet_rec = pd.concat(liste_dataframes_rec, ignore_index=True)
print("Total combiné réceptions:", df_complet_rec.shape)

with open("data/produits_selectionnes.json", "r", encoding="utf-8") as f:
    selection = json.load(f)

print("Nombre de produits dans la sélection:", len(selection))
print(selection[:3])

df_echantillon_rec = df_complet_rec[df_complet_rec["Produit"].isin(selection)]

print("Lignes dans l'échantillon réceptions:", df_echantillon_rec.shape)
print(
    "Produits distincts dans l'échantillon réceptions:",
    df_echantillon_rec["Produit"].nunique(),
)

df_echantillon_rec.to_csv("data/receptions_echantillon.csv", index=False)
print("Fichier sauvegardé : data/receptions_echantillon.csv")
