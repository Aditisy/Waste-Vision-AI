import streamlit as st
from PIL import Image, ImageOps
from config import MODEL_PROVIDER, MODEL_PATH
from core.detector import detect
from core.recommender import RULES
from core.db import record_scan
from core.ui import render_table

def demo_detections(image):
    w,h=image.size
    # Synthetic boxes demonstrate the workflow; these are never model output.
    boxes=[("plastic",.92,(.10,.18,.42,.62)),("paper",.84,(.52,.30,.88,.72)),("organic",.77,(.30,.67,.58,.92))]
    from PIL import ImageDraw
    out=image.convert("RGB"); d=ImageDraw.Draw(out); rows=[]
    for cat,conf,(x1,y1,x2,y2) in boxes:
        box=(int(w*x1),int(h*y1),int(w*x2),int(h*y2)); d.rectangle(box,outline="#18a558",width=4); d.text((box[0]+3,max(0,box[1]-18)),f"DEMO {cat} {conf:.0%}",fill="white",stroke_width=2,stroke_fill="#174b32")
        rows.append({"label":f"demo {cat}","category":cat,"confidence":conf,"box":box})
    return out,rows

def render(demo_mode=False, threshold=.20):
    st.markdown("<div class='section-kicker'>PHOTO IN · SORTING ACTION OUT</div>",unsafe_allow_html=True)
    st.title("📷 AI Waste Scanner")
    st.write("Upload a waste photo to identify likely categories, review confidence, and get a practical next step.")
    if not demo_mode and MODEL_PROVIDER == "ultralytics" and "-world" in MODEL_PATH.lower():
        st.info("Open-vocabulary mode is active with waste-focused text prompts. It can recognize more item descriptions than the default COCO model, but it is still a general detector—not a validated waste-sorting system. The first scan may download weights.")
    if not demo_mode and MODEL_PROVIDER == "ultralytics" and MODEL_PATH.lower().endswith("yolov8n.pt"):
        st.warning("The configured yolov8n.pt weights are a general COCO object detector, not a waste-trained model. They can find familiar objects such as bottles and food, but won't reliably recognize wrappers, scattered litter, or dumped piles. Use waste-trained weights via WASTEVISION_MODEL_PATH for those classes.")
    if not demo_mode:
        st.caption("Waste-only filtering is enabled: background classes such as people and vehicles are ignored. Add your custom model's waste labels in config.py → CLASS_MAPPING.")
    upload=st.file_uploader("Choose an image",type=["jpg","jpeg","png"],key="scan_upload")
    if not upload: return
    image=ImageOps.exif_transpose(Image.open(upload)).convert("RGB")
    upload_id=getattr(upload,"file_id",upload.name)
    c1,c2=st.columns([1,1]); c1.image(image,caption="Your uploaded image",use_container_width=True)
    detections=[]; annotated=image
    if demo_mode:
        annotated,detections=demo_detections(image)
        scan_key=f"demo_scan_{upload_id}"
        if scan_key not in st.session_state: record_scan(True); st.session_state[scan_key]=True
        st.warning("DEMO DATA - not model output. Sample boxes illustrate the workflow.")
    elif st.button("Run waste detection",type="primary"):
        try:
            with st.spinner("Loading detector and analyzing image…"):
                annotated,detections=detect(image,threshold)
            record_scan(False)
            st.session_state["last_scan"]=(upload_id,annotated,detections)
        except Exception as e: st.error(f"The detector could not run: {e}. Try Demo mode from the sidebar.")
    if not demo_mode and "last_scan" in st.session_state and not detections and st.session_state["last_scan"][0]==upload_id:
        _,annotated,detections=st.session_state["last_scan"]
    c2.image(annotated,caption="DEMO ANNOTATION · NOT MODEL OUTPUT" if demo_mode else "Model result",use_container_width=True)
    if not detections:
        if not demo_mode and ("last_scan" not in st.session_state or st.session_state["last_scan"][0]!=upload_id): st.info("Run detection to see results. No model result is shown yet.")
        else: st.info("No supported waste objects were found above the confidence threshold. Try lowering the confidence slider, using a closer/brighter photo, or configure waste-trained model weights. General object classes are intentionally ignored.")
        return
    st.subheader("Detection results")
    render_table([{"Label":x["label"],"Category":x["category"].title(),"Confidence":f'{x["confidence"]:.0%}'} for x in detections])
    cats=sorted(set(x["category"] for x in detections)); cleanup=len(detections)>=5 or "general" in cats
    st.markdown("#### Scan summary")
    a,b,c=st.columns(3); a.metric("Waste types detected",len(cats)); b.metric("Guidance generated",len(cats)); c.metric("Cleanup needed","Yes" if cleanup else "No")
    st.write("**Suggested next action:** " + ("Report this location for cleanup." if cleanup else "Sort each item using the guidance below."))
    for cat in cats:
        rule=RULES[cat]; st.markdown(f'<div class="card" style="border-left:6px solid {rule["color"]};margin:.5rem 0"><b>{cat.title()} · {rule["bin"]}</b><br>{rule["how"]}</div>',unsafe_allow_html=True)
