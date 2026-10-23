"""Small HTML table renderer that avoids Streamlit's Arrow serialization path."""
from html import escape
import math
import streamlit as st

def render_table(data, columns=None, labels=None):
    if hasattr(data,"to_dict"):
        rows=data.to_dict(orient="records")
    else:
        rows=list(data)
    if not rows:
        st.caption("No rows to display.")
        return
    keys=list(columns or rows[0].keys())
    labels=labels or {}
    head="".join(f"<th>{escape(str(labels.get(key,key)))}</th>" for key in keys)
    body=[]
    for row in rows:
        cells=[]
        for key in keys:
            value=row.get(key,"")
            if value is None or (isinstance(value,float) and math.isnan(value)): value="—"
            shown=escape(str(value))
            badge=""
            if key.lower() in {"priority","status"}:
                clean=str(value).replace("● ","").lower().replace(" ","-")
                badge=f"<span class='wv-badge {escape(clean)}'>{shown}</span>"
            cells.append(f"<td>{badge or shown}</td>")
        body.append("<tr>"+"".join(cells)+"</tr>")
    table=("<div class='wv-table-wrap'><table class='wv-table'><thead><tr>"+head+"</tr></thead><tbody>"+"".join(body)+"</tbody></table></div>")
    st.markdown(table,unsafe_allow_html=True)