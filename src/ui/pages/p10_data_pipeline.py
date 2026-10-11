"""
Page 10: Data Pipeline
Module: src.ui.pages.p10_data_pipeline
Comprehensive GNSS Data Processing, Validation, and Machine Learning Pipeline Interface.
Supports uploading or selecting new GNSS data, inspecting data quality audits,
and dynamic pipeline execution without fake animated bars.
Strictly no emojis.
"""

import os
from typing import Dict, Any, List
import pandas as pd
import streamlit as st


def render_data_pipeline_page(data_service):
    """
    Render Data Pipeline Page.
    """
    st.markdown("<div class='section-header'>END-TO-END GNSS DEFENSE PIPELINE</div>", unsafe_allow_html=True)
    st.markdown(
        """
    <div class="soc-callout">
        <strong>DATA PIPELINE LIFECYCLE:</strong>
        Connects raw NMEA/CSV GNSS data ingestion to multi-detector fusion and agentic deliberation.
        All stages reflect real implemented components in the backend. Unimplemented stages are explicitly marked
        <code>PENDING IMPLEMENTATION</code>.
    </div>
    """,
        unsafe_allow_html=True,
    )

    # 1. Pipeline Stage Implementation Architecture Matrix
    st.markdown("<div class='soc-panel-title'>PIPELINE STAGE IMPLEMENTATION AUDIT</div>", unsafe_allow_html=True)

    stages = [
        {"Stage": "1. Data Ingestion", "Component": "NMEA Ingestion / CSV Reader", "Status": "IMPLEMENTED", "Details": "Supports GGA, GSA, RMC, GSV sentence streams & telemetry CSVs"},
        {"Stage": "2. Validation", "Component": "Fix Validity & Bounds Check", "Status": "IMPLEMENTED", "Details": "Validates lat [-90, 90], lon [-180, 180], atomic UTC time continuity"},
        {"Stage": "3. Parsing", "Component": "src.parsing.nmea_parser", "Status": "IMPLEMENTED", "Details": "Tokenizes NMEA talkers, PRN constellation IDs, and signal-to-noise"},
        {"Stage": "4. Cleaning", "Component": "src.locus_quality", "Status": "IMPLEMENTED", "Details": "Demarcates sessions on dt > 5.0s, reconstructs atomic UTC timestamps"},
        {"Stage": "5. Data Quality", "Component": "src.ui.data_service (Audit)", "Status": "IMPLEMENTED", "Details": "Calculates record counts, fix distribution, DOP stats, and null values"},
        {"Stage": "6. Feature Engineering", "Component": "src.features.security_features", "Status": "IMPLEMENTED", "Details": "Extracts canonical 10-D kinematic, nav quality & sat churn metrics"},
        {"Stage": "7. 10-D Features", "Component": "Canonical Feature Matrix", "Status": "IMPLEMENTED", "Details": "Stored in data/features/locus_security_features.csv"},
        {"Stage": "8. Detection Quad", "Component": "Rules + IF + XGB + Temporal", "Status": "IMPLEMENTED", "Details": "4-detector complementary spatial, physical, and temporal models"},
        {"Stage": "9. Event Generation", "Component": "src.evidence.evidence_bundle", "Status": "IMPLEMENTED", "Details": "Fuses detector outputs into forensic event bundles"},
        {"Stage": "10. Evidence Bundles", "Component": "data/evidence/*.json", "Status": "IMPLEMENTED", "Details": "Cryptographically hashed JSON forensic records"},
        {"Stage": "11. RAG Intelligence", "Component": "src.rag.rag_engine", "Status": "IMPLEMENTED", "Details": "Vector retrieval across ICAO Annex 10, RTCA DO-229E, and MITRE"},
        {"Stage": "12. Multi-Agent Analysis", "Component": "src.agents (Integrity + Threat)", "Status": "IMPLEMENTED", "Details": "3-agent deliberation hierarchy with consensus ratings"},
        {"Stage": "13. SOC Deliberation", "Component": "src.query.query_processor", "Status": "IMPLEMENTED", "Details": "Master SOC arbitration and DEFCON rating declarations"},
        {"Stage": "14. Model Retraining", "Component": "src.detection.pipeline", "Status": "IMPLEMENTED (OFFLINE)", "Details": "Full batch training script available via src/detection/pipeline.py"},
        {"Stage": "15. Interactive Fine-Tuning", "Component": "Online Web Fine-Tuning", "Status": "PENDING IMPLEMENTATION", "Details": "Interactive parameter fine-tuning from GUI is scheduled for future release"}
    ]

    df_stages = pd.DataFrame(stages)
    st.dataframe(df_stages, use_container_width=True, hide_index=True)

    st.markdown("<hr style='border-color: #1e293b; margin: 18px 0;'>", unsafe_allow_html=True)

    # 2. Section: Ingest & Process New GNSS Data
    st.markdown("<div class='section-header'>INGEST / SELECT NEW GNSS DATASET</div>", unsafe_allow_html=True)

    # Select between local dataset or upload new
    src_choice = st.radio(
        "Data Source Selection:",
        options=["Use Existing Recorded Dataset (data/processed/locus_telemetry_clean.csv)", "Upload New GNSS File (CSV / NMEA Log)"],
        horizontal=True,
        key="pipeline_src_choice"
    )

    working_df = None
    data_label = ""

    if "Upload New" in src_choice:
        uploaded_file = st.file_uploader(
            "Select New GNSS Data File to Ingest:",
            type=["csv", "nmea", "txt", "log"],
            key="file_uploader_new_gnss"
        )
        if uploaded_file is not None:
            data_label = uploaded_file.name
            try:
                if uploaded_file.name.endswith(".csv"):
                    working_df = pd.read_csv(uploaded_file)
                    st.success(f"Successfully loaded {len(working_df)} records from {uploaded_file.name}.")
                else:
                    st.info("NMEA raw file uploaded. Parsing through NMEA Sentence Parser...")
                    from src.parsing.nmea_parser import NMEAParser
                    parser = NMEAParser()
                    lines = uploaded_file.getvalue().decode("utf-8", errors="ignore").splitlines()
                    parsed_records = []
                    for line in lines:
                        rec = parser.parse_sentence(line)
                        if rec:
                            parsed_records.append(rec)
                    if parsed_records:
                        working_df = pd.DataFrame(parsed_records)
                        st.success(f"Successfully parsed {len(working_df)} NMEA sentences.")
                    else:
                        st.warning("No valid NMEA sentences could be parsed from this file.")
            except Exception as e:
                st.error(f"Error parsing uploaded file: {str(e)}")
    else:
        working_df = data_service.load_telemetry_dataset()
        data_label = "locus_telemetry_clean.csv (Canonical Dataset)"

    if working_df is None or working_df.empty:
        st.info("NO DATA LOADED. Please select or upload a dataset to run the pipeline.")
        return

    # 3. Data Quality Audit Section
    st.markdown("<div class='section-header'>DATA QUALITY AUDIT & SENSOR VALIDATION</div>", unsafe_allow_html=True)
    st.write(f"Target Dataset: **{data_label}**")

    dq = data_service.compute_data_quality_metrics(working_df)
    if dq.get("has_data", False):
        dq1, dq2, dq3, dq4, dq5 = st.columns(5)
        with dq1:
            st.metric("TOTAL RECORDS", f"{dq['total_records']:,}")
        with dq2:
            st.metric("VALID RECORDS", f"{dq['valid_records']:,}")
        with dq3:
            st.metric("INVALID RECORDS", f"{dq['invalid_records']:,}")
        with dq4:
            st.metric("MISSING VALUES", f"{dq['missing_values']:,}")
        with dq5:
            st.metric("DUPLICATES", f"{dq['duplicates']:,}")

        dq6, dq7, dq8, dq9 = st.columns(4)
        with dq6:
            coords_status = "VALID WGS-84" if dq["coordinates_valid"] else "OUT OF BOUNDS"
            st.metric("COORDINATE BOUNDS", coords_status)
        with dq7:
            sat_s = dq.get("satellite_stats", {})
            sat_str = f"Min {sat_s.get('min', 0)} / Avg {sat_s.get('mean', 0)} / Max {sat_s.get('max', 0)}" if sat_s else "N/A"
            st.metric("SATELLITE AVAILABILITY", sat_str)
        with dq8:
            h_s = dq.get("hdop_stats", {})
            h_str = f"Avg {h_s.get('mean', 0)} / Med {h_s.get('median', 0)}" if h_s else "N/A"
            st.metric("HDOP METRICS", h_str)
        with dq9:
            v_s = dq.get("vdop_stats", {})
            v_str = f"Avg {v_s.get('mean', 0)} / Med {v_s.get('median', 0)}" if v_s else "N/A"
            st.metric("VDOP METRICS", v_str)

        # Fix Distribution
        fix_dist = dq.get("fix_distribution", {})
        if fix_dist:
            st.markdown("<div style='font-size: 11px; font-weight: 700; color: #94a3b8; margin-top: 8px;'>GNSS FIX QUALITY BREAKDOWN:</div>", unsafe_allow_html=True)
            dist_cols = st.columns(len(fix_dist))
            for i, (k, v) in enumerate(fix_dist.items()):
                with dist_cols[i]:
                    label = "Invalid Fix (0)" if k == "0" else ("SPS 3D Fix (1)" if k == "1" else f"Differential Fix ({k})")
                    st.metric(label, f"{v:,}")
    else:
        st.info("NO DATA AVAILABLE FOR DATA QUALITY METRICS")

    st.markdown("<hr style='border-color: #1e293b; margin: 18px 0;'>", unsafe_allow_html=True)

    # 4. Pipeline Execution & Feature Extraction Trigger
    st.markdown("<div class='section-header'>PIPELINE EXECUTION DISPATCH</div>", unsafe_allow_html=True)

    col_act1, col_act2 = st.columns(2)

    with col_act1:
        st.markdown("<div class='soc-panel-title'>FEATURE EXTRACTION DISPATCH</div>", unsafe_allow_html=True)
        st.write("Extract the canonical 10-D security features across all epochs in the active dataset.")
        if st.button("Run 10-D Feature Extraction", key="btn_run_fe"):
            with st.spinner("Extracting canonical 10-D security features..."):
                try:
                    from src.features.security_features import SecurityFeatureExtractor
                    extractor = SecurityFeatureExtractor()
                    feat_df = extractor.extract_features(working_df)
                    st.success(f"Extracted {len(feat_df)} 10-D feature vectors successfully.")
                    st.dataframe(feat_df.head(10), use_container_width=True, hide_index=True)
                except Exception as e:
                    st.error(f"Feature extraction encountered an issue: {str(e)}")

    with col_act2:
        st.markdown("<div class='soc-panel-title'>MODEL TRAINING / FINE-TUNING</div>", unsafe_allow_html=True)
        st.markdown(
            """
        <div class="soc-callout">
            <strong>TRAINING ENGINE STATUS:</strong><br>
            Batch model training (Isolation Forest, XGBoost audit, Temporal LSTM) is supported via the
            detection pipeline script: <code>python -m src.detection.pipeline</code>.<br><br>
            <strong>ONLINE GUI FINE-TUNING:</strong><br>
            <span class="badge badge-warning">MODEL TRAINING / FINE-TUNING PENDING IMPLEMENTATION</span><br>
            <em>Interactive fine-tuning controls are reserved for the next system phase.</em>
        </div>
        """,
            unsafe_allow_html=True,
        )
