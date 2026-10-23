"""Create cleanup reports and update their response status."""
import json
import os
import uuid

import pandas as pd
import streamlit as st
from PIL import Image, ImageOps

from core.db import create_report, list_reports, update_status
from core.detector import detect
from core.priority import calculate_priority
from core.ui import render_table
from modules.scanner import demo_detections


def render(demo_mode=False, threshold=.20):
    st.markdown("<div class='section-kicker'>FIELD REPORT · CLEANUP ROUTING</div>", unsafe_allow_html=True)
    st.title("📍 Report a Garbage Hotspot")
    st.write("Capture the location, record what you see, and route the issue into a tracked cleanup queue.")

    with st.form("report_form"):
        image_upload = st.file_uploader("Street or public-area image", type=["jpg", "jpeg", "png"], key="report_upload")
        location = st.text_input("Location name", placeholder="e.g. Community park entrance")
        col_lat, col_lon = st.columns(2)
        latitude = col_lat.number_input("Latitude (optional)", min_value=-90.0, max_value=90.0, value=0.0, format="%.6f")
        longitude = col_lon.number_input("Longitude (optional)", min_value=-180.0, max_value=180.0, value=0.0, format="%.6f")
        notes = st.text_area("Notes (optional)", placeholder="Describe the visible issue")
        severity = st.select_slider("Visible waste severity", options=["Light", "Moderate", "Severe"], value="Moderate", help="Your assessment of the visible pile size and spread.")
        overflowing = st.checkbox("Overflowing bin or dumped waste is visible")
        sensitive_site = st.checkbox("Near a sensitive place (school, clinic, waterbody, or busy transit area)")
        submitted = st.form_submit_button("Analyze and submit report", type="primary")

    if submitted:
        if image_upload is None or not location.strip():
            st.error("Please add an image and location name.")
        else:
            try:
                image = ImageOps.exif_transpose(Image.open(image_upload)).convert("RGB")
                with st.spinner("Analyzing hotspot image…"):
                    if demo_mode:
                        _, detections = demo_detections(image)
                    else:
                        _, detections = detect(image, threshold)
                if not detections:
                    st.warning("No waste items were found above the confidence threshold. Try another image or adjust the threshold.")
                else:
                    os.makedirs("uploads", exist_ok=True)
                    image_path = os.path.join("uploads", f"{uuid.uuid4().hex}.jpg")
                    image.save(image_path)
                    categories = sorted({item["category"] for item in detections})
                    estimate = calculate_priority(len(detections), categories, overflowing, severity, sensitive_site)
                    priority = estimate["level"]
                    report_id = create_report(
                        location.strip(), latitude or None, longitude or None, categories,
                        len(detections), priority, image_path, notes, is_demo=demo_mode,
                        priority_score=estimate["score"], severity=severity,
                        overflowing=overflowing, sensitive_site=sensitive_site,
                    )
                    if demo_mode:
                        st.warning("Report uses DEMO DATA - not model output.")
                    st.success(f"Report #{report_id} saved · {priority} estimated priority · score {estimate['score']}/26 · {len(detections)} items detected.")
                    st.caption("This is a triage estimate to help compare reports. It is not an official hazard assessment.")
                    with st.expander("How this estimate was calculated"):
                        for factor, explanation in estimate["factors"].items():
                            st.write(f"- **{factor}:** {explanation}")
            except Exception as error:
                st.error(f"Could not analyze or save the report: {error}. Try Demo mode if the model is unavailable.")

    st.markdown("### Recent reports")
    reports = list_reports()
    if not reports:
        st.info("No reports yet. Submit a hotspot above to start the cleanup queue.")
        return

    table = pd.DataFrame(reports)
    table["source"] = table["is_demo"].map(lambda value: "Demo sample" if value else "Field report")
    table["Overflow"] = table["overflowing"].map(lambda value: "Yes" if value else "No")
    table["Sensitive site"] = table["sensitive_site"].map(lambda value: "Yes" if value else "No")
    table["timestamp"] = pd.to_datetime(table["timestamp"]).dt.strftime("%b %d, %Y %H:%M")
    table["categories"] = table["categories"].map(lambda value: ", ".join(json.loads(value)).title())
    render_table(
        table,
        columns=["id", "timestamp", "location", "categories", "item_count", "severity", "Overflow", "Sensitive site", "priority", "priority_score", "status", "source"],
        labels={"id": "ID", "timestamp": "Reported", "location": "Location", "categories": "Categories", "item_count": "Items", "priority": "Priority", "priority_score": "Score / 26", "severity": "Severity", "status": "Status", "source": "Source"},
    )

    open_reports = [item for item in reports if item["status"] != "Resolved"]
    if open_reports:
        report_options = {f"#{item['id']} · {item['location']} · {item['status']}": item["id"] for item in open_reports}
        selected = st.selectbox("Update report status", list(report_options))
        new_status = st.selectbox("New status", ["Reported", "In Progress", "Resolved"])
        if st.button("Save status", type="primary"):
            update_status(report_options[selected], new_status)
            st.success("Report status updated.")
            st.rerun()
    else:
        st.success("All reports in the queue are resolved.")
