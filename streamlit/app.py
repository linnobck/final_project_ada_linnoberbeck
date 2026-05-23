import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
from statsmodels.stats.multitest import multipletests

st.set_page_config(page_title="Media Representation Dashboard - ADA Final Project", layout="wide")

# load data
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

st.title("Media Representation Dashboard")
st.markdown(f"Showing **{len(filtered):,}** cast entries across **{filtered['title'].nunique()}** titles")

# tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Overview", "Gender", "Ethnicity", "Intersectionality", "Arc & Sympathy", "Statistics"
])


# overview tab
with tab1:
    st.subheader("Dataset overview")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total cast entries", f"{len(filtered):,}")
    col2.metric("Titles", filtered["title"].nunique())
    col3.metric("% Female", f"{(filtered['actor_gender'] == 'female').mean()*100:.1f}%")
    col4.metric("% Non-white", f"{(filtered['actor_ethnicity'] != 'White').mean()*100:.1f}%")

    col1, col2 = st.columns(2)

    with col1:
        gender_counts = filtered["actor_gender"].value_counts().reset_index()
        gender_counts.columns = ["gender", "count"]
        fig = px.pie(gender_counts, names="gender", values="count",
                     title="Gender breakdown",
                     color="gender",
                     color_discrete_map={"female": "#E07B9A", "male": "#5B8DB8", "unspecified": "#B0B0B0"})
        fig.update_traces(textinfo="percent+label")
        fig.update_layout(transition={"duration": 500})
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        eth_counts = filtered["ethnicity_simple"].value_counts().reset_index()
        eth_counts.columns = ["ethnicity", "count"]
        fig = px.pie(eth_counts, names="ethnicity", values="count",
                     title="Ethnicity breakdown (simplified)",
                     color="ethnicity",
                     color_discrete_map={"White": "#5B8DB8", "Non-white": "#E8A838", "Unknown": "#B0B0B0"})
        fig.update_traces(textinfo="percent+label")
        fig.update_layout(transition={"duration": 500})
        st.plotly_chart(fig, use_container_width=True)

    # role type breakdown
    role_gender = filtered.groupby(["role_type", "actor_gender"]).size().reset_index(name="count")
    fig = px.bar(role_gender, x="role_type", y="count", color="actor_gender",
                 barmode="group", title="Cast count by role type and gender",
                 category_orders={"role_type": ["lead", "supporting", "minor"]},
                 color_discrete_map={"female": "#E07B9A", "male": "#5B8DB8", "unspecified": "#B0B0B0"})
    fig.update_layout(transition={"duration": 500}, xaxis_title="Role type", yaxis_title="Count")
    st.plotly_chart(fig, use_container_width=True)


# gender tab
with tab2:
    st.subheader("Gender representation")

    col1, col2 = st.columns(2)

    with col1:
        # gender by role type as %
        gender_role = filtered.groupby("role_type").apply(
            lambda x: (x["actor_gender"] == "female").mean() * 100
        ).reset_index()
        gender_role.columns = ["role_type", "pct_female"]
        gender_role = gender_role[gender_role["role_type"].isin(["lead", "supporting", "minor"])]
        fig = px.bar(gender_role, x="role_type", y="pct_female",
                     title="% Female by role type",
                     category_orders={"role_type": ["lead", "supporting", "minor"]},
                     color_discrete_sequence=["#E07B9A"])
        fig.add_hline(y=50, line_dash="dash", line_color="gray", annotation_text="50% parity")
        fig.update_layout(transition={"duration": 500}, yaxis_title="% Female", xaxis_title="Role type")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # prominence by gender
        prom_gender = filtered.groupby("actor_gender")["prominence_score"].mean().reset_index()
        prom_gender.columns = ["gender", "avg_prominence"]
        fig = px.bar(prom_gender, x="gender", y="avg_prominence",
                     title="Average prominence score by gender",
                     color="gender",
                     color_discrete_map={"female": "#E07B9A", "male": "#5B8DB8", "unspecified": "#B0B0B0"})
        fig.update_layout(transition={"duration": 500}, yaxis_title="Avg prominence score")
        st.plotly_chart(fig, use_container_width=True)

    # gender over time
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

    # gender by media type
    gender_media = filtered.groupby(["media_type", "role_type"]).apply(
        lambda x: (x["actor_gender"] == "female").mean() * 100
    ).reset_index()
    gender_media.columns = ["media_type", "role_type", "pct_female"]
    gender_media = gender_media[gender_media["role_type"].isin(["lead", "supporting", "minor"])]

    fig = px.bar(gender_media, x="role_type", y="pct_female", color="media_type",
                 barmode="group", title="% Female by role type and media type",
                 category_orders={"role_type": ["lead", "supporting", "minor"]},
                 color_discrete_map={"movie": "#5B8DB8", "tv": "#E07B9A"})
    fig.add_hline(y=50, line_dash="dash", line_color="gray", annotation_text="50% parity")
    fig.update_layout(transition={"duration": 500}, yaxis_title="% Female")
    st.plotly_chart(fig, use_container_width=True)


# ethnicity tab
with tab3:
    st.subheader("Ethnicity representation")

    col1, col2 = st.columns(2)

    with col1:
        eth_role = filtered.groupby("role_type").apply(
            lambda x: (x["actor_ethnicity"] != "White").mean() * 100
        ).reset_index()
        eth_role.columns = ["role_type", "pct_nonwhite"]
        eth_role = eth_role[eth_role["role_type"].isin(["lead", "supporting", "minor"])]
        fig = px.bar(eth_role, x="role_type", y="pct_nonwhite",
                     title="% Non-white by role type",
                     category_orders={"role_type": ["lead", "supporting", "minor"]},
                     color_discrete_sequence=["#E8A838"])
        fig.update_layout(transition={"duration": 500}, yaxis_title="% Non-white", xaxis_title="Role type")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        prom_eth = filtered.groupby("ethnicity_simple")["prominence_score"].mean().reset_index()
        prom_eth.columns = ["ethnicity", "avg_prominence"]
        fig = px.bar(prom_eth, x="ethnicity", y="avg_prominence",
                     title="Average prominence score by ethnicity",
                     color="ethnicity",
                     color_discrete_map={"White": "#5B8DB8", "Non-white": "#E8A838", "Unknown": "#B0B0B0"})
        fig.update_layout(transition={"duration": 500}, yaxis_title="Avg prominence score")
        st.plotly_chart(fig, use_container_width=True)

    # ethnicity over time
    eth_decade = filtered.groupby("decade").apply(lambda x: pd.Series({
        "White": (x["actor_ethnicity"] == "White").mean() * 100,
        "Non-white": (x["actor_ethnicity"] != "White").mean() * 100,
    })).reset_index()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=eth_decade["decade"], y=eth_decade["White"],
                             mode="lines+markers", name="White", line=dict(color="#5B8DB8")))
    fig.add_trace(go.Scatter(x=eth_decade["decade"], y=eth_decade["Non-white"],
                             mode="lines+markers", name="Non-white", line=dict(color="#E8A838")))
    fig.update_layout(title="Ethnicity distribution over time",
                      xaxis_title="Decade", yaxis_title="%",
                      transition={"duration": 500})
    st.plotly_chart(fig, use_container_width=True)

    # ethnicity by genre
    genre_eth = filtered.groupby("genre_primary").apply(
        lambda x: (x["actor_ethnicity"] != "White").mean() * 100 if len(x) >= 10 else None
    ).dropna().reset_index()
    genre_eth.columns = ["genre", "pct_nonwhite"]
    genre_eth = genre_eth.sort_values("pct_nonwhite")

    fig = px.bar(genre_eth, x="pct_nonwhite", y="genre", orientation="h",
                 title="% Non-white by genre",
                 color_discrete_sequence=["#E8A838"])
    fig.update_layout(transition={"duration": 500}, xaxis_title="% Non-white", yaxis_title="Genre",
                      height=500)
    st.plotly_chart(fig, use_container_width=True)


# intersectionality tab
with tab4:
    st.subheader("Gender × Ethnicity")

    leads_only = filtered[filtered["role_type"] == "lead"]

    # lead counts by gender x ethnicity
    intersect = leads_only.groupby(["actor_gender", "actor_ethnicity"]).size().reset_index(name="count")
    intersect = intersect[intersect["actor_gender"].isin(["female", "male"])]
    fig = px.bar(intersect, x="actor_ethnicity", y="count", color="actor_gender",
                 barmode="group", title="Lead role counts: gender × ethnicity",
                 color_discrete_map={"female": "#E07B9A", "male": "#5B8DB8"})
    fig.update_layout(transition={"duration": 500}, xaxis_title="Ethnicity", yaxis_title="Count")
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        # all roles gender x ethnicity simplified %
        intersect_all = filtered.groupby(["actor_gender", "ethnicity_simple"]).size().reset_index(name="count")
        intersect_all = intersect_all[intersect_all["actor_gender"].isin(["female", "male"])]
        total = intersect_all["count"].sum()
        intersect_all["pct"] = intersect_all["count"] / total * 100
        fig = px.bar(intersect_all, x="actor_gender", y="pct", color="ethnicity_simple",
                     barmode="stack", title="All roles: gender × ethnicity (%)",
                     color_discrete_map={"White": "#5B8DB8", "Non-white": "#E8A838", "Unknown": "#B0B0B0"})
        fig.update_layout(transition={"duration": 500}, yaxis_title="%", xaxis_title="Gender")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # prominence by gender x ethnicity
        prom_int = filtered[filtered["actor_gender"].isin(["female", "male"])].groupby(
            ["actor_gender", "ethnicity_simple"]
        )["prominence_score"].mean().reset_index()
        prom_int.columns = ["gender", "ethnicity", "avg_prominence"]
        fig = px.bar(prom_int, x="gender", y="avg_prominence", color="ethnicity",
                     barmode="group", title="Avg prominence: gender × ethnicity",
                     color_discrete_map={"White": "#5B8DB8", "Non-white": "#E8A838", "Unknown": "#B0B0B0"})
        fig.update_layout(transition={"duration": 500}, yaxis_title="Avg prominence score")
        st.plotly_chart(fig, use_container_width=True)


# arc and sympathy tab
with tab5:
    st.subheader("Character arc & sympathy coding")

    arc_cols = ["sympathy_coding", "arc_presence", "arc_direction"]
    available = [c for c in arc_cols if c in filtered.columns and filtered[c].notna().sum() > 0]

    if not available:
        st.info("Arc and sympathy data not yet available in this dataset.")
    else:
        col1, col2 = st.columns(2)

        with col1:
            if "sympathy_coding" in available:
                symp = filtered["sympathy_coding"].value_counts().reset_index()
                symp.columns = ["category", "count"]
                fig = px.bar(symp, x="category", y="count",
                             title="Sympathy coding distribution",
                             color_discrete_sequence=["#9B59B6"])
                fig.update_layout(transition={"duration": 500}, xaxis_title="Category", yaxis_title="Count")
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            if "arc_presence" in available:
                arc = filtered["arc_presence"].value_counts().reset_index()
                arc.columns = ["arc", "count"]
                fig = px.bar(arc, x="arc", y="count",
                             title="Arc presence distribution",
                             color_discrete_sequence=["#1ABC9C"])
                fig.update_layout(transition={"duration": 500}, xaxis_title="Arc type", yaxis_title="Count")
                st.plotly_chart(fig, use_container_width=True)

        # sympathy by gender
        if "sympathy_coding" in available:
            symp_gender = filtered[filtered["actor_gender"].isin(["female", "male"])].groupby(
                ["actor_gender", "sympathy_coding"]
            ).size().reset_index(name="count")
            fig = px.bar(symp_gender, x="sympathy_coding", y="count", color="actor_gender",
                         barmode="group", title="Sympathy coding by gender",
                         color_discrete_map={"female": "#E07B9A", "male": "#5B8DB8"})
            fig.update_layout(transition={"duration": 500}, xaxis_title="Sympathy coding", yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True)

        # sympathy by ethnicity
        if "sympathy_coding" in available:
            symp_eth = filtered[filtered["ethnicity_simple"].isin(["White", "Non-white"])].groupby(
                ["ethnicity_simple", "sympathy_coding"]
            ).size().reset_index(name="count")
            fig = px.bar(symp_eth, x="sympathy_coding", y="count", color="ethnicity_simple",
                         barmode="group", title="Sympathy coding by ethnicity",
                         color_discrete_map={"White": "#5B8DB8", "Non-white": "#E8A838"})
            fig.update_layout(transition={"duration": 500}, xaxis_title="Sympathy coding", yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True)

        # arc by gender
        if "arc_presence" in available:
            arc_gender = filtered[filtered["actor_gender"].isin(["female", "male"])].groupby(
                ["actor_gender", "arc_presence"]
            ).size().reset_index(name="count")
            fig = px.bar(arc_gender, x="arc_presence", y="count", color="actor_gender",
                         barmode="group", title="Arc presence by gender",
                         color_discrete_map={"female": "#E07B9A", "male": "#5B8DB8"})
            fig.update_layout(transition={"duration": 500}, xaxis_title="Arc presence", yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True)


# statistics tab
with tab6:
    st.subheader("Statistical tests")
    st.markdown("""
    All tests use independent samples t-tests (or one-way ANOVA for genre comparisons),
    corrected with **Benjamini-Hochberg** at FDR = 0.05.
    Cohen's d: small ≈ 0.2, medium ≈ 0.5, large ≈ 0.8.
    """)

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

    tests = []
    f = filtered  # shorthand

    add_test("Female: leads vs non-leads",
        (f[f["role_type"] == "lead"]["actor_gender"] == "female").astype(float),
        (f[f["role_type"] != "lead"]["actor_gender"] == "female").astype(float), tests)

    add_test("Non-white: leads vs non-leads",
        (f[f["role_type"] == "lead"]["actor_ethnicity"] != "White").astype(float),
        (f[f["role_type"] != "lead"]["actor_ethnicity"] != "White").astype(float), tests)

    add_test("Prominence: male vs female",
        f[f["actor_gender"] == "male"]["prominence_score"].dropna(),
        f[f["actor_gender"] == "female"]["prominence_score"].dropna(), tests)

    add_test("Prominence: White vs non-white",
        f[f["actor_ethnicity"] == "White"]["prominence_score"].dropna(),
        f[f["actor_ethnicity"] != "White"]["prominence_score"].dropna(), tests)

    tv_f  = (f[f["media_type"] == "tv"]["actor_gender"] == "female").astype(float)
    mov_f = (f[f["media_type"] == "movie"]["actor_gender"] == "female").astype(float)
    if len(tv_f) > 0 and len(mov_f) > 0:
        add_test("Female: TV vs film", tv_f, mov_f, tests)

    tv_nw  = (f[f["media_type"] == "tv"]["actor_ethnicity"] != "White").astype(float)
    mov_nw = (f[f["media_type"] == "movie"]["actor_ethnicity"] != "White").astype(float)
    if len(tv_nw) > 0 and len(mov_nw) > 0:
        add_test("Non-white: TV vs film", tv_nw, mov_nw, tests)

    w_f  = f[(f["actor_gender"] == "female") & (f["actor_ethnicity"] == "White")]["prominence_score"].dropna()
    nw_f = f[(f["actor_gender"] == "female") & (f["actor_ethnicity"] != "White")]["prominence_score"].dropna()
    if len(w_f) > 0 and len(nw_f) > 0:
        add_test("Prominence: white female vs non-white female", w_f, nw_f, tests)

    w_m  = f[(f["actor_gender"] == "male") & (f["actor_ethnicity"] == "White")]["prominence_score"].dropna()
    nw_m = f[(f["actor_gender"] == "male") & (f["actor_ethnicity"] != "White")]["prominence_score"].dropna()
    if len(w_m) > 0 and len(nw_m) > 0:
        add_test("Prominence: white male vs non-white male", w_m, nw_m, tests)

    genre_g = [(f[f["genre_primary"] == g]["actor_gender"] == "female").astype(float)
               for g in f["genre_primary"].dropna().unique() if len(f[f["genre_primary"] == g]) >= 10]
    if len(genre_g) >= 2:
        add_test("Gender differs across genres (ANOVA)", genre_g, None, tests, anova=True)

    genre_e = [(f[f["genre_primary"] == g]["actor_ethnicity"] != "White").astype(float)
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

        # visual summary
        p_display = [-np.log10(max(p, 1e-300)) for p in p_corr]
        colors = ["#2ecc71" if r else "#e74c3c" for r in reject]
        fig = go.Figure(go.Bar(
            x=p_display,
            y=list(names),
            orientation="h",
            marker_color=colors
        ))
        fig.add_vline(x=-np.log10(0.05), line_dash="dash", line_color="black",
                      annotation_text="p = 0.05")
        fig.update_layout(
            title="-log10(corrected p-value) — green = significant, red = not significant",
            xaxis_title="-log10(p)",
            height=400,
            transition={"duration": 500}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough data with current filters to run statistical tests.")
