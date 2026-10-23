from html import escape
import streamlit as st
from config import CATEGORIES
from core.recommender import RULES, classify_item


def render():
    st.markdown("<div class='section-kicker'>SORTING FIELD GUIDE</div>", unsafe_allow_html=True)
    st.title("🧭 Smart Segregation Assistant")
    st.write("Type an item or describe it in your own words. The result comes from transparent local sorting rules.")

    mode = st.radio("Find guidance by", ["Type an item", "Choose a category"], horizontal=True)
    if mode == "Type an item":
        query = st.text_input("What are you throwing away?", placeholder="Try: greasy pizza box, soda bottle, or vegetable scraps")
        st.caption("Examples: snack wrapper · cardboard box · glass jar · eggshells · broken glass")
        if not query.strip():
            st.info("Enter an item above to get a disposal route.")
            return
        category, match = classify_item(query)
        if match == "fallback":
            st.warning("I couldn't match that description exactly. Showing the cautious residual-waste route; check your local authority before disposal.")
        elif match.startswith("contains:"):
            st.caption(f"Matched the item phrase “{match.split(':',1)[1]}” in your description.")
    else:
        category = st.selectbox("Waste category", CATEGORIES)
        match = "category"
        query = category

    rule = RULES[category]
    safe_query = escape(query.title())
    st.markdown(
        f'<div class="panel" style="border-left:8px solid {rule["color"]};padding:1.6rem">'
        f'<div class="section-kicker">RECOMMENDED ROUTE</div><h2>{safe_query} → {rule["bin"]}</h2>'
        f'<p><b>{rule["stream"]}</b></p><p>{rule["how"]}</p></div>',
        unsafe_allow_html=True,
    )
    st.caption("Sorting rules vary by municipality. For hazardous items or uncertain materials, check your local waste authority.")
