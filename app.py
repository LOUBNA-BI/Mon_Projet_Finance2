from pathlib import Path
import io
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(page_title="Dashboard | Dossiers administratifs", page_icon="📊", layout="wide")

st.title("📊 Tableau de bord — Traitement des dossiers administratifs")
st.caption("Service administratif fictif · Janvier–août 2026")

DEFAULT_FILE = "04_Finance_Administration_Juridique(1).xlsx"

@st.cache_data
def load_data(file_bytes):
    raw = pd.read_excel(io.BytesIO(file_bytes), sheet_name="Données", header=None)
    # The workbook contains a title row, a subtitle row, then column headers.
    df = raw.iloc[2:].copy()
    df.columns = df.iloc[0].astype(str).str.strip()
    df = df.iloc[1:].reset_index(drop=True)
    df = df.loc[:, ~df.columns.astype(str).str.startswith("Unnamed")]
    expected = ["ID dossier", "Date réception", "Ville", "Service", "Type dossier",
                "Canal", "Priorité", "Pièces complètes", "Statut",
                "Traitement (jours)", "Objectif (jours)", "Coût traitement (MAD)"]
    missing = [c for c in expected if c not in df.columns]
    if missing:
        raise ValueError("Colonnes manquantes : " + ", ".join(missing))
    df["Date réception"] = pd.to_datetime(df["Date réception"], errors="coerce")
    for c in ["Traitement (jours)", "Objectif (jours)", "Coût traitement (MAD)"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ["Ville", "Service", "Type dossier", "Canal", "Priorité", "Pièces complètes", "Statut"]:
        df[c] = df[c].astype("string").str.strip()
    df = df.dropna(subset=["ID dossier", "Date réception"])
    df["Mois"] = df["Date réception"].dt.to_period("M").dt.to_timestamp()
    df["Retard"] = (df["Statut"].eq("Clôturé") &
                    df["Traitement (jours)"].notna() &
                    df["Objectif (jours)"].notna() &
                    (df["Traitement (jours)"] > df["Objectif (jours)"]))
    return df

uploaded = st.sidebar.file_uploader("Importer le fichier Excel", type=["xlsx"])
local_path = Path(__file__).with_name(DEFAULT_FILE)
try:
    if uploaded:
        data = load_data(uploaded.getvalue())
    elif local_path.exists():
        data = load_data(local_path.read_bytes())
    else:
        st.info("Importez le fichier Excel d'origine dans la barre latérale pour afficher le tableau de bord.")
        st.stop()
except Exception as exc:
    st.error(f"Impossible de lire le fichier : {exc}")
    st.stop()

st.sidebar.header("Filtres")
def options(col):
    return sorted(data[col].dropna().astype(str).unique().tolist())
cities = st.sidebar.multiselect("Ville", options("Ville"), default=options("Ville"))
services = st.sidebar.multiselect("Service", options("Service"), default=options("Service"))
types = st.sidebar.multiselect("Type de dossier", options("Type dossier"), default=options("Type dossier"))
min_date, max_date = data["Date réception"].min().date(), data["Date réception"].max().date()
date_range = st.sidebar.date_input("Période de réception", value=(min_date, max_date), min_value=min_date, max_value=max_date)

filtered = data[data["Ville"].isin(cities) & data["Service"].isin(services) & data["Type dossier"].isin(types)].copy()
if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    filtered = filtered[filtered["Date réception"].dt.date.between(date_range[0], date_range[1])]

# ── Page 1: direct answers to all six questions ──
st.header("Réponses aux six questions")
total = len(filtered)
closed = filtered[filtered["Statut"].eq("Clôturé")]
open_cases = filtered[filtered["Statut"].eq("En cours")]
late_count = int(closed["Retard"].sum())
late_rate = late_count / len(closed) * 100 if len(closed) else 0
closure_rate = len(closed) / total * 100 if total else 0
avg_days = closed["Traitement (jours)"].mean()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Dossiers reçus", f"{total:,}".replace(",", " "))
k2.metric("Taux de clôture", f"{closure_rate:.1f}%")
k3.metric("Clôturés hors délai", f"{late_rate:.1f}%", f"{late_count} dossier(s)")
k4.metric("Durée moyenne clôturés", f"{avg_days:.1f} j" if pd.notna(avg_days) else "—")

st.subheader("1. Quels types concentrent le plus de demandes ?")
type_counts = filtered["Type dossier"].value_counts().sort_values(ascending=False)
if not type_counts.empty:
    st.write(f"Le type le plus fréquent est **{type_counts.index[0]}** avec **{type_counts.iloc[0]} dossiers** ({type_counts.iloc[0]/total*100:.1f}% du volume filtré).")
    fig, ax = plt.subplots(figsize=(8, 3.8))
    type_counts.sort_values().plot(kind="barh", ax=ax, color="#3B82F6")
    ax.set_xlabel("Nombre de dossiers"); ax.set_ylabel(""); ax.set_title("Volume par type de dossier")
    ax.grid(axis="x", alpha=.2); fig.tight_layout(); st.pyplot(fig); plt.close(fig)
else:
    st.info("Aucune donnée avec les filtres sélectionnés.")

st.subheader("2. Quelle part des dossiers clôturés dépasse l’objectif ?")
st.write(f"**{late_count} / {len(closed)} dossiers clôturés ({late_rate:.1f}%)** dépassent le délai cible. Le retard est défini par Traitement > Objectif; les dossiers encore ouverts sont exclus.")

st.subheader("3. Les pièces incomplètes sont-elles associées à un délai plus long ?")
completed = closed[closed["Pièces complètes"].eq("Oui")]["Traitement (jours)"].dropna()
incomplete = closed[closed["Pièces complètes"].eq("Non")]["Traitement (jours)"].dropna()
c1, c2, c3 = st.columns(3)
c1.metric("Pièces complètes", f"{completed.mean():.1f} j" if len(completed) else "—", f"n={len(completed)}")
c2.metric("Pièces incomplètes", f"{incomplete.mean():.1f} j" if len(incomplete) else "—", f"n={len(incomplete)}")
delta = incomplete.mean() - completed.mean() if len(incomplete) and len(completed) else float("nan")
c3.metric("Écart moyen", f"{delta:+.1f} j" if pd.notna(delta) else "—")
if pd.notna(delta):
    st.write("Les dossiers incomplets ont une durée moyenne supérieure." if delta > 0 else "Les dossiers incomplets n’ont pas une durée moyenne supérieure dans la sélection.")
st.caption("Interprétation : association descriptive, pas preuve de causalité. Les groupes peuvent différer par type, priorité ou service.")

st.subheader("4. Quels services ont le plus de dossiers en cours ?")
open_by_service = open_cases.groupby("Service").size().sort_values(ascending=False)
if not open_by_service.empty:
    st.write(f"Le service avec le plus de dossiers en cours est **{open_by_service.index[0]}** ({open_by_service.iloc[0]}).")
    fig, ax = plt.subplots(figsize=(8, 3.5))
    open_by_service.sort_values().plot(kind="barh", ax=ax, color="#F59E0B")
    ax.set_xlabel("Dossiers en cours"); ax.set_ylabel(""); ax.set_title("Dossiers ouverts par service")
    ax.grid(axis="x", alpha=.2); fig.tight_layout(); st.pyplot(fig); plt.close(fig)
else:
    st.info("Aucun dossier en cours dans la sélection.")
st.caption("Un nombre élevé peut aussi refléter un volume entrant élevé ou des dossiers plus complexes; comparer aussi les volumes reçus et l’ancienneté.")

st.subheader("5. Comment évoluent le volume reçu et le coût mensuel ?")
monthly = filtered.groupby("Mois").agg(Dossiers=("ID dossier", "count"), Cout_MAD=("Coût traitement (MAD)", "sum")).sort_index()
if not monthly.empty:
    monthly.index = monthly.index.strftime("%b %Y")
    fig, ax1 = plt.subplots(figsize=(9, 4))
    monthly["Dossiers"].plot(kind="bar", ax=ax1, color="#3B82F6", alpha=.85, width=.65)
    ax1.set_ylabel("Dossiers reçus"); ax1.set_xlabel(""); ax1.tick_params(axis="x", rotation=35)
    ax2 = ax1.twinx()
    ax2.plot(range(len(monthly)), monthly["Cout_MAD"].values, color="#DC6B19", marker="o", linewidth=2)
    ax2.set_ylabel("Coût estimé (MAD)")
    ax1.set_title("Volume reçu et coût total par mois"); ax1.grid(axis="y", alpha=.2)
    fig.tight_layout(); st.pyplot(fig); plt.close(fig)
    st.dataframe(monthly.rename(columns={"Cout_MAD":"Coût (MAD)"}), use_container_width=True)
st.caption("Le coût est renseigné sur les dossiers clôturés; la somme mensuelle est donc le coût observé des dossiers dont le coût est disponible.")

st.subheader("6. Quelle amélioration proposer ?")
if pd.notna(delta) and delta > 0 and len(incomplete):
    st.write(f"**Action proposée :** mettre en place une vérification des pièces dès la réception, avec une liste de contrôle et une notification rapide des pièces manquantes. Dans la sélection, l’écart descriptif est de {delta:.1f} jours en moyenne. Suivre ensuite le délai médian et le taux de retard par statut de complétude pour évaluer l’effet.")
else:
    st.write("**Action proposée :** piloter chaque mois les retards et les dossiers en cours par service, puis examiner les causes des retards avant de déployer une action ciblée. Réévaluer l’action avec les mêmes indicateurs après mise en œuvre.")

with st.expander("Voir les données filtrées"):
    st.dataframe(filtered, use_container_width=True)
    st.download_button("Télécharger les données filtrées (CSV)", filtered.to_csv(index=False).encode("utf-8-sig"), "dossiers_filtres.csv", "text/csv")

st.caption("Source : fichier pédagogique fictif. Les valeurs manquantes de durée et de coût des dossiers ouverts sont conservées comme manquantes, jamais remplacées par zéro.")
