"""Action-oriented dashboard for cleanup operations and waste patterns."""
import json
import pandas as pd
import plotly.express as px
import streamlit as st

from core.db import list_reports, scan_count
from core.ui import render_table

PRIORITY_COLORS = {"High":"#d74d3f", "Medium":"#e4a62d", "Low":"#32966a"}
STATUS_COLORS = {"Reported":"#d74d3f", "In Progress":"#e4a62d", "Resolved":"#32966a"}


def _style(fig):
    fig.update_layout(template="plotly_white",paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        font={"family":"DM Sans, sans-serif","color":"#254b36"},margin={"l":10,"r":10,"t":45,"b":10},legend_title_text="")
    fig.update_xaxes(showgrid=False,zeroline=False)
    fig.update_yaxes(gridcolor="#e9f0ea",zeroline=False)
    return fig


def render():
    st.markdown("<div class='section-kicker'>FIELD INTELLIGENCE · LIVE OVERVIEW</div>",unsafe_allow_html=True)
    st.title("Cleanup impact")
    st.write("See where attention is needed and which cleanup reports should move first.")

    all_reports = list_reports()
    filter_col, note_col = st.columns([1,2.2])
    source = filter_col.selectbox("Data view",["All reports","Real reports only","Demo reports only"])
    if source == "Real reports only":
        reports = [row for row in all_reports if not row["is_demo"]]
        scans = scan_count(is_demo=False)
        note_col.success("Showing only reports submitted outside Demo mode.")
    elif source == "Demo reports only":
        reports = [row for row in all_reports if row["is_demo"]]
        scans = scan_count(is_demo=True)
        note_col.info("Demo rows are illustrative examples, not verified field observations.")
    else:
        reports = all_reports
        scans = scan_count()
        note_col.info("Demo data is included in this view and is not verified field activity.")

    if not reports:
        st.info("No reports match this view yet. Submit a hotspot report or select the demo view.")
        return

    open_rows = [row for row in reports if row["status"] != "Resolved"]
    high_open = [row for row in open_rows if row["priority"] == "High"]
    resolved = sum(row["status"] == "Resolved" for row in reports)
    metrics = st.columns(5)
    metrics[0].metric("Scans",scans)
    metrics[1].metric("Hotspots",len(reports))
    metrics[2].metric("Need action",len(open_rows))
    metrics[3].metric("High priority open",len(high_open))
    metrics[4].metric("Resolution rate",f"{resolved/len(reports):.0%}")

    st.markdown("### 🚦 Cleanup response queue")
    queue = sorted(open_rows,key=lambda row:(int(row.get("priority_score",0)),0 if row["priority"]=="High" else 1 if row["priority"]=="Medium" else 2),reverse=True)[:6]
    if queue:
        qdf = pd.DataFrame(queue)
        qdf["Priority"] = qdf["priority"].map(lambda value:f"● {value}")
        qdf["Estimate"] = qdf["priority_score"].map(lambda value:f"{value}/26" if value else "—")
        qdf["Overflow"] = qdf["overflowing"].map(lambda value:"Yes" if value else "No")
        qdf["Sensitive site"] = qdf["sensitive_site"].map(lambda value:"Yes" if value else "No")
        qdf["Categories"] = qdf["categories"].map(lambda value:", ".join(json.loads(value)).title() if value else "—")
        qdf["Reported"] = pd.to_datetime(qdf["timestamp"]).dt.strftime("%b %d, %H:%M")
        qdf["Source"] = qdf["is_demo"].map(lambda value:"Demo sample" if value else "Field report")
        render_table(qdf,columns=["Priority","Estimate","severity","Overflow","Sensitive site","location","item_count","Categories","status","Reported","Source"],
            labels={"severity":"Severity","location":"Location","item_count":"Items","status":"Status"})
    else:
        st.success("Nothing is waiting in the cleanup queue.")
    st.caption("Priority estimates combine detected item count and category variety with the reporter's visible-severity, overflow, and sensitive-site inputs. They are not official hazard assessments.")

    categories = []
    for value in pd.DataFrame(reports)["categories"]:
        try: categories.extend(json.loads(value))
        except (ValueError,TypeError): continue
    frame = pd.DataFrame(reports)
    by_status = frame["status"].value_counts().rename_axis("Status").reset_index(name="Reports")
    by_priority = frame["priority"].value_counts().reindex(["High","Medium","Low"],fill_value=0).rename_axis("Priority").reset_index(name="Reports")
    st.markdown("### 📡 Waste and response signals")
    left,right = st.columns(2)
    with left:
        st.markdown("<div class='section-kicker'>MATERIAL MIX</div>",unsafe_allow_html=True)
        if categories:
            count = pd.Series(categories).value_counts().rename_axis("Category").reset_index(name="Detections")
            fig = px.pie(count,names="Category",values="Detections",hole=.62,color_discrete_sequence=["#23824e","#4f9f73","#d9a52a","#3e83a2","#9a6946","#87988c"])
            fig.update_traces(textposition="inside",textinfo="percent+label")
            st.plotly_chart(_style(fig),use_container_width=True)
        else: st.caption("No categories recorded yet.")
    with right:
        st.markdown("<div class='section-kicker'>CLEANUP URGENCY</div>",unsafe_allow_html=True)
        fig = px.bar(by_priority,x="Reports",y="Priority",orientation="h",color="Priority",color_discrete_map=PRIORITY_COLORS,text="Reports",category_orders={"Priority":["High","Medium","Low"]})
        fig.update_traces(textposition="outside",cliponaxis=False)
        st.plotly_chart(_style(fig),use_container_width=True)

    lower_left,lower_right = st.columns(2)
    with lower_left:
        st.markdown("<div class='section-kicker'>RESPONSE STATUS</div>",unsafe_allow_html=True)
        fig=px.pie(by_status,names="Status",values="Reports",hole=.55,color="Status",color_discrete_map=STATUS_COLORS)
        fig.update_traces(textposition="inside",textinfo="label+value")
        st.plotly_chart(_style(fig),use_container_width=True)
    with lower_right:
        st.markdown("<div class='section-kicker'>REPORT RHYTHM</div>",unsafe_allow_html=True)
        frame["Day"] = pd.to_datetime(frame["timestamp"]).dt.date
        trend=frame.groupby("Day",as_index=False).size().rename(columns={"size":"Reports"})
        fig=px.area(trend,x="Day",y="Reports",markers=True,color_discrete_sequence=["#23824e"])
        fig.update_traces(line={"width":3},fillcolor="rgba(35,130,78,.12)")
        st.plotly_chart(_style(fig),use_container_width=True)

    st.markdown("### 🗺️ Hotspot field map")
    points = frame.copy()
    points["lat"] = pd.to_numeric(points["lat"],errors="coerce")
    points["lon"] = pd.to_numeric(points["lon"],errors="coerce")
    points = points[points["lat"].notna() & points["lon"].notna() & ((points["lat"]!=0)|(points["lon"]!=0))]
    if not points.empty:
        fig=px.scatter_mapbox(points,lat="lat",lon="lon",color="priority",size="item_count",size_max=18,
            hover_name="location",hover_data={"status":True,"item_count":True,"priority_score":True,"is_demo":True,"lat":False,"lon":False},
            zoom=10,height=440,color_discrete_map=PRIORITY_COLORS,mapbox_style="open-street-map")
        fig.update_layout(margin={"l":0,"r":0,"t":0,"b":0},legend_title_text="Cleanup priority")
        st.plotly_chart(fig,use_container_width=True)
        st.caption("Marker color is estimated priority; marker size reflects detected count. Demo coordinates are illustrative.")
    else:
        st.info("Add latitude and longitude to a report to place it on the map.")
