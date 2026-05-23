import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
from statsmodels.stats.multitest import multipletests

st.set_page_config(page_title="Media Representation Dashboard", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("encoded_annotated_final.csv", dtype=str)
    df["billing_order"] = pd.to_numeric(df["billing_order"], errors="coerce")
    df["prominence_score"] = pd.to_numeric(df["prominence_score"], errors="coerce")
    df["start_year"] = pd.to_numeric(df["start_year"], errors="coerce")
    df["end_year"] = pd.to_numeric(df["end_year"], errors="coerce")

    named = df[df["is_named_character"] == "True"].copy()
    named["decade"] = (named["start_year"] // 10 * 10).astype("Int64").astype(str) + "s"
    named = named[named["decade"] != "<NA>s"].copy()
    named["ethnicity_simple"] = named["actor_ethnicity"].apply(
        lambda x: "White" if x == "White" else ("Unknown" if pd.isna(x) or x == "Unknown" else "Non-white")
    )
    named["genre_primary"] = named["genres"].str.split("|").str[0]
    return named

named = load_data()

# sidebar filters
st.sidebar.header("Filters")

media_options = ["All"] + sorted(named["media_type"].dropna().unique().tolist())
media_filter = st.sidebar.selectbox("Media type", media_options)

genre_options = ["All"] + sorted(named["genre_primary"].dropna().unique().tolist())
genre_filter = st.sidebar.selectbox("Genre", genre_options)

decade_options = ["All"] + sorted(named["decade"].dropna().unique().tolist())
decade_filter = st.sidebar.selectbox("Decade", decade_options)

role_options = ["All", "lead", "supporting", "minor"]
role_filter = st.sidebar.selectbox("Role type", role_options)

gender_options = ["All", "female", "male"]
gender_filter = st.sidebar.selectbox("Gender", gender_options)

ethnicity_options = ["All", "White", "Non-white"]
ethnicity_filter = st.sidebar.selectbox("Ethnicity", ethnicity_options)

# apply filters
filtered = named.copy()
if media_filter != "All":
    filtered = filtered[filtered["media_type"] == media_filter]
if genre_filter != "All":
    filtered = filtered[filtered["genre_primary"] == genre_filter]
if decade_filter != "All":
    filtered = filtered[filtered["decade"] == decade_filter]
if role_filter != "All":
    filtered = filtered[filtered["role_type"] == role_filter]
if gender_filter != "All":
    filtered = filtered[filtered["actor_gender"] == gender_filter]
if ethnicity_filter != "All":
    if ethnicity_filter == "Non-white":
        filtered = filtered[filtered["ethnicity_simple"] == "Non-white"]
    else:
        filtered = filtered[filtered["ethnicity_simple"] == "White"]

st.title("Media Representation Dashboard")
st.caption(f"{len(filtered):,} cast entries · {filtered['title'].nunique()} titles")

tab1, tab2 = st.tabs(["Explore", "Statistics"])


with tab1:
    # headline metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Cast entries", f"{len(filtered):,}")
    col2.metric("Titles", filtered["title"].nunique())
    col3.metric("% Female", f"{(filtered['actor_gender'] == 'female').mean()*100:.1f}%")
    col4.metric("% Non-white", f"{(filtered['ethnicity_simple'] == 'Non-white').mean()*100:.1f}%")

    st.divider()

    # chart selector
    chart = st.selectbox("What do you want to explore?", [
        "Gender by role type",
        "Ethnicity by role type",
        "Gender over time",
        "Ethnicity over time",
        "Prominence by gender",
        "Prominence by ethnicity",
        "Gender × Ethnicity in lead roles",
        "Prominence: gender × ethnicity",
        "Gender by genre",
        "Ethnicity by genre",
        "Sympathy coding",
        "Arc presence",
        "Sympathy by gender",
        "Sympathy by ethnicity",
        "Arc by gender",
    ])

    ROLE_ORDER = ["lead", "supporting", "minor"]

    if chart == "Gender by role type":
        gender_role = filtered.groupby("role_type").apply(
            lambda x: (x["actor_gender"] == "female").mean() * 100
        ).reset_index()
        gender_role.columns = ["role_type", "pct_female"]
        gender_role = gender_role[gender_role["role_type"].isin(ROLE_ORDER)]
        fig = px.bar(gender_role, x="role_type", y="pct_female",
                     title="% Female by role type",
                     category_orders={"role_type": ROLE_ORDER},
                     color_discrete_sequence=["#E07B9A"])
        fig.add_hline(y=50, line_dash="dash", line_color="gray", annotation_text="50% parity")
        fig.update_layout(transition={"duration": 500}, yaxis_title="% Female", xaxis_title="Role type")
        st.plotly_chart(fig, use_container_width=True)

    elif chart == "Ethnicity by role type":
        eth_role = filtered.groupby("role_type").apply(
            lambda x: (x["ethnicity_simple"] == "Non-white").mean() * 100
        ).reset_index()
        eth_role.columns = ["role_type", "pct_nonwhite"]
        eth_role = eth_role[eth_role["role_type"].isin(ROLE_ORDER)]
        fig = px.bar(eth_role, x="role_type", y="pct_nonwhite",
                     title="% Non-white by role type",
                     category_orders={"role_type": ROLE_ORDER},
                     color_discrete_sequence=["#E8A838"])
        fig.update_layout(transition={"duration": 500}, yaxis_title="% Non-white", xaxis_title="Role type")
        st.plotly_chart(fig, use_container_width=True)

    elif chart == "Gender over time":
        gender_decade = filtered.groupby("decade").apply(
            lambda x: (x["actor_gender"] == "female").mean() * 100
        ).reset_index()
        gender_decade.columns = ["decade", "pct_female"]
        fig = px.line(gender_decade, x="decade", y="pct_female",
                      title="% Female cast members over time",
                      markers=True, color_discrete_sequence=["#E07B9A"])
        fig.add_hline(y=50, line_dash="dash", line_color="gray", annotation_text="50% parity")
        fig.update_layout(transition={"duration": 500}, yaxis_title="% Female", xaxis_title="Decade")
        st.plotly_chart(fig, use_container_width=True)

    elif chart == "Ethnicity over time":
        eth_decade = filtered.groupby("decade").apply(lambda x: pd.Series({
            "White": (x["ethnicity_simple"] == "White").mean() * 100,
            "Non-white": (x["ethnicity_simple"] == "Non-white").mean() * 100,
        })).reset_index()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=eth_decade["decade"], y=eth_decade["White"],
                                 mode="lines+markers", name="White", line=dict(color="#5B8DB8")))
        fig.add_trace(go.Scatter(x=eth_decade["decade"], y=eth_decade["Non-white"],
                                 mode="lines+markers", name="Non-white", line=dict(color="#E8A838")))
        fig.update_layout(title="Ethnicity distribution over time",
                          xaxis_title="Decade", yaxis_title="%", transition={"duration": 500})
        st.plotly_chart(fig, use_container_width=True)

    elif chart == "Prominence by gender":
        prom = filtered.groupby("actor_gender")["prominence_score"].mean().reset_index()
        prom.columns = ["gender", "avg_prominence"]
        fig = px.bar(prom, x="gender", y="avg_prominence",
                     title="Average prominence score by gender",
                     color="gender",
                     color_discrete_map={"female": "#E07B9A", "male": "#5B8DB8", "unspecified": "#B0B0B0"})
        fig.update_layout(transition={"duration": 500}, yaxis_title="Avg prominence score")
        st.plotly_chart(fig, use_container_width=True)

    elif chart == "Prominence by ethnicity":
        prom = filtered.groupby("ethnicity_simple")["prominence_score"].mean().reset_index()
        prom.columns = ["ethnicity", "avg_prominence"]
        fig = px.bar(prom, x="ethnicity", y="avg_prominence",
                     title="Average prominence score by ethnicity",
                     color="ethnicity",
                     color_discrete_map={"White": "#5B8DB8", "Non-white": "#E8A838", "Unknown": "#B0B0B0"})
        fig.update_layout(transition={"duration": 500}, yaxis_title="Avg prominence score")
        st.plotly_chart(fig, use_container_width=True)

    elif chart == "Gender × Ethnicity in lead roles":
        leads = filtered[filtered["role_type"] == "lead"]
        intersect = leads.groupby(["actor_gender", "actor_ethnicity"]).size().reset_index(name="count")
        intersect = intersect[intersect["actor_gender"].isin(["female", "male"])]
        fig = px.bar(intersect, x="actor_ethnicity", y="count", color="actor_gender",
                     barmode="group", title="Lead role counts: gender × ethnicity",
                     color_discrete_map={"female": "#E07B9A", "male": "#5B8DB8"})
        fig.update_layout(transition={"duration": 500}, xaxis_title="Ethnicity", yaxis_title="Count")
        st.plotly_chart(fig, use_container_width=True)

    elif chart == "Prominence: gender × ethnicity":
        prom = filtered[filtered["actor_gender"].isin(["female", "male"])].groupby(
            ["actor_gender", "ethnicity_simple"]
        )["prominence_score"].mean().reset_index()
        prom.columns = ["gender", "ethnicity", "avg_prominence"]
        fig = px.bar(prom, x="gender", y="avg_prominence", color="ethnicity",
                     barmode="group", title="Avg prominence: gender × ethnicity",
                     color_discrete_map={"White": "#5B8DB8", "Non-white": "#E8A838", "Unknown": "#B0B0B0"})
        fig.update_layout(transition={"duration": 500}, yaxis_title="Avg prominence score")
        st.plotly_chart(fig, use_container_width=True)

    elif chart == "Gender by genre":
        genre_gender = filtered.groupby("genre_primary").apply(
            lambda x: (x["actor_gender"] == "female").mean() * 100 if len(x) >= 10 else None
        ).dropna().reset_index()
        genre_gender.columns = ["genre", "pct_female"]
        genre_gender = genre_gender.sort_values("pct_female")
        fig = px.bar(genre_gender, x="pct_female", y="genre", orientation="h",
                     title="% Female by genre", color_discrete_sequence=["#E07B9A"])
        fig.add_vline(x=50, line_dash="dash", line_color="gray", annotation_text="50% parity")
        fig.update_layout(transition={"duration": 500}, xaxis_title="% Female", height=500)
        st.plotly_chart(fig, use_container_width=True)

    elif chart == "Ethnicity by genre":
        genre_eth = filtered.groupby("genre_primary").apply(
            lambda x: (x["ethnicity_simple"] == "Non-white").mean() * 100 if len(x) >= 10 else None
        ).dropna().reset_index()
        genre_eth.columns = ["genre", "pct_nonwhite"]
        genre_eth = genre_eth.sort_values("pct_nonwhite")
        fig = px.bar(genre_eth, x="pct_nonwhite", y="genre", orientation="h",
                     title="% Non-white by genre", color_discrete_sequence=["#E8A838"])
        fig.update_layout(transition={"duration": 500}, xaxis_title="% Non-white", height=500)
        st.plotly_chart(fig, use_container_width=True)

    elif chart == "Sympathy coding":
        if "sympathy_coding" in filtered.columns and filtered["sympathy_coding"].notna().sum() > 0:
            symp = filtered["sympathy_coding"].value_counts(normalize=True).mul(100).reset_index()
            symp.columns = ["category", "pct"]
            fig = px.bar(symp, x="category", y="pct",
                        title="Sympathy coding distribution (%)",
                        color_discrete_sequence=["#9B59B6"])
            fig.update_layout(transition={"duration": 500}, yaxis_title="% of characters")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sympathy coding not yet available in this dataset.")

    elif chart == "Arc presence":
        if "arc_presence" in filtered.columns and filtered["arc_presence"].notna().sum() > 0:
            arc = filtered["arc_presence"].value_counts(normalize=True).mul(100).reset_index()
            arc.columns = ["arc", "pct"]
            fig = px.bar(arc, x="arc", y="pct",
                        title="Arc presence distribution (%)",
                        color_discrete_sequence=["#1ABC9C"])
            fig.update_layout(transition={"duration": 500}, yaxis_title="% of characters")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Arc data not yet available in this dataset.")

    elif chart == "Sympathy by gender":
        if "sympathy_coding" in filtered.columns and filtered["sympathy_coding"].notna().sum() > 0:
            symp = filtered[filtered["actor_gender"].isin(["female", "male"])].groupby(
                ["actor_gender", "sympathy_coding"]
            ).size().reset_index(name="count")
            symp["pct"] = symp.groupby("actor_gender")["count"].transform(lambda x: x / x.sum() * 100)
            fig = px.bar(symp, x="sympathy_coding", y="pct", color="actor_gender",
                        barmode="group", title="Sympathy coding by gender (% within gender)",
                        color_discrete_map={"female": "#E07B9A", "male": "#5B8DB8"})
            fig.update_layout(transition={"duration": 500}, yaxis_title="% within gender group")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sympathy coding not yet available in this dataset.")

    elif chart == "Sympathy by ethnicity":
        if "sympathy_coding" in filtered.columns and filtered["sympathy_coding"].notna().sum() > 0:
            symp = filtered[filtered["ethnicity_simple"].isin(["White", "Non-white"])].groupby(
                ["ethnicity_simple", "sympathy_coding"]
            ).size().reset_index(name="count")
            symp["pct"] = symp.groupby("ethnicity_simple")["count"].transform(lambda x: x / x.sum() * 100)
            fig = px.bar(symp, x="sympathy_coding", y="pct", color="ethnicity_simple",
                        barmode="group", title="Sympathy coding by ethnicity (% within ethnicity)",
                        color_discrete_map={"White": "#5B8DB8", "Non-white": "#E8A838"})
            fig.update_layout(transition={"duration": 500}, yaxis_title="% within ethnicity group")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sympathy coding not yet available in this dataset.")

    elif chart == "Arc by gender":
        if "arc_presence" in filtered.columns and filtered["arc_presence"].notna().sum() > 0:
            arc = filtered[filtered["actor_gender"].isin(["female", "male"])].groupby(
                ["actor_gender", "arc_presence"]
            ).size().reset_index(name="count")
            arc["pct"] = arc.groupby("actor_gender")["count"].transform(lambda x: x / x.sum() * 100)
            fig = px.bar(arc, x="arc_presence", y="pct", color="actor_gender",
                        barmode="group", title="Arc presence by gender (% within gender)",
                        color_discrete_map={"female": "#E07B9A", "male": "#5B8DB8"})
            fig.update_layout(transition={"duration": 500}, yaxis_title="% within gender group")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Arc data not yet available in this dataset.")


with tab2:
    st.subheader("Statistical tests")
    st.markdown("All tests use independent samples t-tests (or ANOVA for genre), corrected with **Benjamini-Hochberg** at FDR = 0.05. Cohen's d: small ≈ 0.2, medium ≈ 0.5, large ≈ 0.8.")

    def cohens_d(a, b):
        pooled = np.sqrt((a.std()**2 + b.std()**2) / 2)
        return (a.mean() - b.mean()) / pooled if pooled > 0 else 0

    def fmt_p(p):
        return f"{p:.2e}" if p < 0.0001 else f"{p:.4f}"

    def add_test(name, a, b, tests, anova=False):
        if anova:
            _, p = stats.f_oneway(*a)
            d, comp = None, "ANOVA"
        else:
            _, p = stats.ttest_ind(a, b)
            d = abs(cohens_d(a, b))
            comp = f"{a.mean()*100:.1f}% vs {b.mean()*100:.1f}%" if a.max() <= 1 else f"{a.mean():.4f} vs {b.mean():.4f}"
        tests.append((name, p, d, comp))

    f = filtered
    tests = []

    add_test("Female: leads vs non-leads",
        (f[f["role_type"] == "lead"]["actor_gender"] == "female").astype(float),
        (f[f["role_type"] != "lead"]["actor_gender"] == "female").astype(float), tests)

    add_test("Non-white: leads vs non-leads",
        (f[f["role_type"] == "lead"]["ethnicity_simple"] == "Non-white").astype(float),
        (f[f["role_type"] != "lead"]["ethnicity_simple"] == "Non-white").astype(float), tests)

    add_test("Prominence: male vs female",
        f[f["actor_gender"] == "male"]["prominence_score"].dropna(),
        f[f["actor_gender"] == "female"]["prominence_score"].dropna(), tests)

    add_test("Prominence: White vs non-white",
        f[f["ethnicity_simple"] == "White"]["prominence_score"].dropna(),
        f[f["ethnicity_simple"] == "Non-white"]["prominence_score"].dropna(), tests)

    tv_f  = (f[f["media_type"] == "tv"]["actor_gender"] == "female").astype(float)
    mov_f = (f[f["media_type"] == "movie"]["actor_gender"] == "female").astype(float)
    if len(tv_f) > 0 and len(mov_f) > 0:
        add_test("Female: TV vs film", tv_f, mov_f, tests)

    tv_nw  = (f[f["media_type"] == "tv"]["ethnicity_simple"] == "Non-white").astype(float)
    mov_nw = (f[f["media_type"] == "movie"]["ethnicity_simple"] == "Non-white").astype(float)
    if len(tv_nw) > 0 and len(mov_nw) > 0:
        add_test("Non-white: TV vs film", tv_nw, mov_nw, tests)

    w_f  = f[(f["actor_gender"] == "female") & (f["ethnicity_simple"] == "White")]["prominence_score"].dropna()
    nw_f = f[(f["actor_gender"] == "female") & (f["ethnicity_simple"] == "Non-white")]["prominence_score"].dropna()
    if len(w_f) > 0 and len(nw_f) > 0:
        add_test("Prominence: white female vs non-white female", w_f, nw_f, tests)

    w_m  = f[(f["actor_gender"] == "male") & (f["ethnicity_simple"] == "White")]["prominence_score"].dropna()
    nw_m = f[(f["actor_gender"] == "male") & (f["ethnicity_simple"] == "Non-white")]["prominence_score"].dropna()
    if len(w_m) > 0 and len(nw_m) > 0:
        add_test("Prominence: white male vs non-white male", w_m, nw_m, tests)

    genre_g = [(f[f["genre_primary"] == g]["actor_gender"] == "female").astype(float)
               for g in f["genre_primary"].dropna().unique() if len(f[f["genre_primary"] == g]) >= 10]
    if len(genre_g) >= 2:
        add_test("Gender differs across genres (ANOVA)", genre_g, None, tests, anova=True)

    genre_e = [(f[f["genre_primary"] == g]["ethnicity_simple"] == "Non-white").astype(float)
               for g in f["genre_primary"].dropna().unique() if len(f[f["genre_primary"] == g]) >= 10]
    if len(genre_e) >= 2:
        add_test("Ethnicity differs across genres (ANOVA)", genre_e, None, tests, anova=True)

    if len(tests) > 0:
        names, pvals, ds, comps = zip(*tests)
        reject, p_corr, _, _ = multipletests(pvals, method="fdr_bh")

        results = pd.DataFrame({
            "Test": names,
            "p-raw": [fmt_p(p) for p in pvals],
            "p-corrected": [fmt_p(p) for p in p_corr],
            "Cohen's d": [f"{d:.3f}" if d is not None else "—" for d in ds],
            "Values": comps,
            "Significant": ["YES" if r else "no" for r in reject]
        })
        st.dataframe(results, use_container_width=True, hide_index=True)

        p_display = [-np.log10(max(p, 1e-300)) for p in p_corr]
        colors = ["#2ecc71" if r else "#e74c3c" for r in reject]
        fig = go.Figure(go.Bar(
            x=p_display, y=list(names), orientation="h", marker_color=colors
        ))
        fig.add_vline(x=-np.log10(0.05), line_dash="dash", line_color="black", annotation_text="p = 0.05")
        fig.update_layout(
            title="-log10(corrected p-value) — green = significant, red = not significant",
            xaxis_title="-log10(p)", height=400, transition={"duration": 500}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough data with current filters to run statistical tests.")
