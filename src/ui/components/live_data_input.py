"""
LOCUS Live Data Input & Automated Security Analysis Center
Module: src.ui.components.live_data_input

Provides an integrated, robust ingestion console supporting:
1. File Upload (CSV, JSON, NMEA text/logs)
2. Pasted Raw GNSS Telemetry or NMEA sentences
3. Live Serial Hardware Stream (Verified ports, Start/Stop controls)
4. Historical Forensic Replay selection

Executes the automated end-to-end security pipeline upon clicking 'PROCESS GNSS DATA'
and renders a live stage-by-stage progression timeline:
PENDING -> VALIDATING -> PREPROCESSING -> FEATURE ENGINEERING -> DETECTION -> AGENT ANALYSIS -> RAG -> EVIDENCE SAVED -> COMPLETE
"""

import time
import json
import streamlit as st
import pandas as pd


def render_live_data_input_panel(data_service=None, on_event_processed_callback=None, service=None, on_pipeline_complete=None):
    """
    Renders the Live Data Input & Automated Analysis Center near the top of the dashboard.
    """
    data_service = data_service or service
    on_event_processed_callback = on_event_processed_callback or on_pipeline_complete
    st.markdown(
        """
        <div class="soc-panel" style="border-left: 4px solid #00f2fe; padding: 14px 18px; margin-bottom: 14px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-weight: 800; font-size: 15px; letter-spacing: 0.05em; color: #00f2fe;">
                    LIVE DATA INPUT &amp; AUTOMATED ANALYSIS CENTER
                </span>
                <span class="badge badge-info" style="font-size: 10px;">AUTONOMOUS PIPELINE DISPATCH</span>
            </div>
            <div style="font-size: 12px; color: #94a3b8; line-height: 1.4;">
                Ingest real GNSS sentences or structured telemetry via file upload, raw pasted records, or verified hardware serial streams.
                Click <strong>PROCESS GNSS DATA</strong> to execute the full end-to-end detection, multi-agent deliberation, and RAG grounding pipeline.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Ingestion Modes Tabs
    tab_upload, tab_paste, tab_serial, tab_replay = st.tabs([
        "FILE UPLOAD (CSV / JSON / NMEA)",
        "PASTE RAW RECORDS",
        "SERIAL HARDWARE STREAM",
        "FORENSIC REPLAY SELECTION"
    ])

    active_payload = None
    input_format = "auto"
    source_name = "interactive_input"
    source_type = "UPLOADED FILE"

    with tab_upload:
        st.caption("Upload raw GNSS data in CSV, JSON, or NMEA log formats (.csv, .json, .nmea, .txt, .log).")
        uploaded_file = st.file_uploader(
            "Select GNSS Data File:",
            type=["csv", "json", "nmea", "txt", "log"],
            key="soc_file_uploader",
            label_visibility="collapsed"
        )
        if uploaded_file is not None:
            source_name = uploaded_file.name
            source_type = f"FILE UPLOAD: {uploaded_file.name}"
            active_payload = uploaded_file.getvalue()
            # Infer format from extension
            ext = uploaded_file.name.lower().split(".")[-1]
            if ext in ["nmea", "log"]:
                input_format = "nmea"
            elif ext == "csv":
                input_format = "csv"
            elif ext == "json":
                input_format = "json"

            st.markdown(
                f"""
                <div style='background: #0f172a; border: 1px solid #1e293b; padding: 8px 12px; border-radius: 6px; font-size: 12px; margin-top: 6px;'>
                    Active File: <strong style='color: #38bdf8;'>{uploaded_file.name}</strong> 
                    ({uploaded_file.size:,} bytes) &bull; Format: <code>{input_format.upper()}</code>
                </div>
                """,
                unsafe_allow_html=True
            )

    with tab_paste:
        st.caption("Paste raw NMEA 0183 sentence strings ($GPGGA, $GPRMC...), JSON arrays, or comma-separated CSV records.")
        sample_paste_placeholder = (
            "$GPGGA,092750.000,2306.2400,N,07235.5200,E,1,10,1.03,61.7,M,55.2,M,,*76\n"
            "$GPRMC,092750.000,A,2306.2400,N,07235.5200,E,0.02,31.66,280511,,,A*43\n"
            "$GPGGA,092751.000,2306.2401,N,07235.5201,E,1,10,1.03,61.7,M,55.2,M,,*77\n"
            "$GPRMC,092751.000,A,2306.2401,N,07235.5201,E,0.02,31.66,280511,,,A*42"
        )
        pasted_text = st.text_area(
            "Paste Raw GNSS Sentences or Records:",
            height=120,
            placeholder=sample_paste_placeholder,
            key="soc_paste_text_area",
            label_visibility="collapsed"
        )
        if pasted_text and pasted_text.strip():
            active_payload = pasted_text.strip()
            source_name = "pasted_gnss_stream"
            source_type = "PASTED DATA"
            st.markdown(
                f"""
                <div style='background: #0f172a; border: 1px solid #1e293b; padding: 6px 12px; border-radius: 6px; font-size: 12px; margin-top: 6px;'>
                    Pasted Buffer: <strong style='color: #38bdf8;'>{len(pasted_text.splitlines())} lines</strong> ready for ingestion.
                </div>
                """,
                unsafe_allow_html=True
            )

    with tab_serial:
        st.caption("Live Hardware Serial Interfacing (Arduino / 7Semi L89HA Multi-GNSS module). Zero fabrication.")
        ports = data_service.get_available_serial_ports()
        col_p1, col_p2, col_p3 = st.columns([3, 2, 2])

        with col_p1:
            port_options = [p["device"] for p in ports] if ports else ["No Ports Detected"]
            selected_port = st.selectbox("Serial Device Port:", port_options, key="serial_port_select")
        with col_p2:
            baud_rate = st.selectbox("Baud Rate:", [115200, 9600, 38400, 57600], index=0, key="serial_baud_select")
        with col_p3:
            st.markdown("<div style='height: 27px;'></div>", unsafe_allow_html=True)
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                serial_started = st.button("Start Live", key="btn_serial_start", type="secondary")
            with col_b2:
                serial_stopped = st.button("Stop", key="btn_serial_stop")

        if ports:
            st.success(f"Hardware Detected: {len(ports)} connected serial device(s). Target: `{selected_port}` at {baud_rate} baud.")
            if serial_started:
                st.session_state["serial_stream_active"] = True
            if serial_stopped:
                st.session_state["serial_stream_active"] = False

            if st.session_state.get("serial_stream_active", False):
                st.info(f"Live hardware capture active on `{selected_port}`. Listening for NMEA frames...")
                source_name = f"serial_{selected_port}"
                source_type = f"SERIAL HARDWARE: {selected_port}"
        else:
            st.markdown(
                """
                <div style='background: #1e293b; border: 1px solid #334155; padding: 10px 14px; border-radius: 6px; font-size: 12px; color: #94a3b8;'>
                    <strong style='color: #f87171;'>NO SERIAL GNSS RECEIVER CONNECTED:</strong> 
                    No active USB/UART COM ports found on local system. Please connect hardware or use File Upload / Replay mode.
                </div>
                """,
                unsafe_allow_html=True
            )

    with tab_replay:
        st.caption("Select a baseline session from the verified 27,687-row recorded dataset.")
        existing_events = data_service.get_events()
        evt_ids = [e["event_id"] for e in existing_events] if existing_events else ["evt_4_220"]
        chosen_replay = st.selectbox("Select Historical Event to Re-Analyze:", evt_ids, key="sel_replay_event")
        if st.button("Load Replay Records for Processing", key="btn_load_replay"):
            b = data_service.load_event(chosen_replay)
            if b:
                b_dict = b.to_dict()
                active_payload = [b_dict.get("location", {}) | b_dict.get("security_features", {}) | {
                    "timestamp_utc": b_dict.get("timestamp_utc"),
                    "session_id": b_dict.get("session_id", 1),
                    "epoch_id": b_dict.get("epoch_id", 1),
                    "fix_quality": b_dict.get("data_quality", {}).get("fix_quality", 1)
                }]
                source_name = f"replay_{chosen_replay}"
                source_type = f"HISTORICAL REPLAY: {chosen_replay}"
                st.success(f"Loaded event records for `{chosen_replay}`.")

    # Status & Trigger Bar
    st.markdown("<hr style='border-color: #1e293b; margin: 12px 0;'>", unsafe_allow_html=True)
    col_status, col_btn = st.columns([5, 2])

    with col_status:
        st.markdown(
            f"""
            <div style='font-size: 12px; color: #94a3b8; display: flex; align-items: center; gap: 10px;'>
                <span>ACTIVE SOURCE: <strong style='color: #00f2fe;'>{source_type}</strong></span>
                <span>&bull;</span>
                <span>IDENTIFIER: <code>{source_name}</code></span>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_btn:
        process_clicked = st.button(
            "PROCESS GNSS DATA",
            key="btn_process_gnss_data",
            type="primary",
            use_container_width=True,
            disabled=(active_payload is None)
        )

    # Automated Processing Execution
    if process_clicked and active_payload is not None:
        st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)

        with st.status("Executing Automated GNSS Security Pipeline...", expanded=True) as status_box:
            st.write("Initializing validation and NMEA sentence extraction...")
            res_dict = data_service.process_gnss_data(
                raw_data=active_payload,
                input_format=input_format,
                source_name=source_name,
                source_type=source_type
            )

            # Check execution outcomes
            stages = res_dict.get("stages", [])
            for stg in stages:
                sid = stg.get("stage_id")
                s_stat = stg.get("status")
                s_desc = stg.get("details", "")
                s_dur = stg.get("duration_ms", 0.0)

                icon = "DONE" if s_stat == "DONE" else ("FAILED" if s_stat == "FAILED" else s_stat)
                st.write(f"**[{icon}] {stg.get('name')}:** {s_desc} *({s_dur:.1f}ms)*")

            if res_dict.get("success", False):
                status_box.update(
                    label=f"Pipeline Complete: Event '{res_dict.get('event_id')}' Generated & Verified ({res_dict.get('processing_time_ms', 0):.1f}ms)",
                    state="complete",
                    expanded=True
                )
            else:
                status_box.update(
                    label=f"Pipeline Completed with Warnings/Failures ({len(res_dict.get('errors', []))} error(s))",
                    state="error",
                    expanded=True
                )

        # Store latest processing run in session state
        st.session_state["latest_pipeline_result"] = res_dict
        new_event_id = res_dict.get("event_id")

        if new_event_id:
            # Update global active event
            from src.ui.utils.state import set_selected_event
            set_selected_event(new_event_id)
            st.session_state["selected_event_id"] = new_event_id
            st.session_state["global_header_event_select"] = new_event_id
            st.session_state["workspace_event_select"] = new_event_id
            if on_event_processed_callback:
                on_event_processed_callback(new_event_id)

    # Render results summary if available
    latest_res = st.session_state.get("latest_pipeline_result")
    if latest_res:
        _render_processing_results_summary(latest_res)


def _render_processing_results_summary(res: dict):
    """
    Renders clean summary metrics, detection quad findings, agent consensus, and RAG grounding
    for newly processed records.
    """
    st.markdown("---")
    st.markdown(
        f"""
        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;'>
            <span style='font-size: 16px; font-weight: 700; color: #ffffff;'>
                AUTOMATED PIPELINE OUTCOME &bull; EVENT <code>{res.get('event_id')}</code>
            </span>
            <span class='badge badge-ready'>PROCESSED IN {res.get('processing_time_ms', 0):.1f} MS</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    ca = res.get("canonical_assessment", {})
    val = res.get("validation_summary", {})
    det = res.get("detector_results", {})
    rag = res.get("rag_grounding", {})
    feats = res.get("feature_metrics", {})

    # Top KPI Metrics Row
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("TOTAL RECORDS", f"{res.get('total_records', 0):,}")
    with m2:
        st.metric("VALID EPOCHS", f"{res.get('valid_records', 0):,}")
    with m3:
        st.metric("SECURITY STATUS", ca.get("current_status", "NOMINAL"))
    with m4:
        st.metric("THREAT RATING", ca.get("defcon_display", "DEFCON 5"))
    with m5:
        st.metric("CONSENSUS CONF", f"{ca.get('confidence', 1.0)*100:.1f}%")

    # Quad Detections & Agents Summary Grid
    col_det, col_agents = st.columns(2)

    with col_det:
        st.markdown("<div class='soc-panel-title'>DETECTION QUAD FINDINGS</div>", unsafe_allow_html=True)
        pr = det.get("physical_rules", {})
        ifo = det.get("isolation_forest", {})
        xgb = det.get("xgboost", {})
        lstm = det.get("temporal_model", {})

        pr_cls = "badge-critical" if pr.get("actual_result") != "NOMINAL" else "badge-normal"
        ifo_cls = "badge-critical" if ifo.get("is_anomaly") else "badge-normal"
        xgb_cls = "badge-warning" if "UNAVAILABLE" in str(xgb.get("actual_result")) else "badge-normal"
        lstm_cls = "badge-warning" if "BUFFERING" in str(lstm.get("actual_result")) else ("badge-critical" if lstm.get("is_anomaly") else "badge-normal")

        st.markdown(
            f"""
            <div style='background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 10px 14px; font-size: 12px;'>
                <div style='margin-bottom: 6px;'><b>1. Physical Invariants:</b> <span class='{pr_cls}'>{pr.get('actual_result')}</span> &bull; {pr.get('triggered_count', 0)} violation(s)</div>
                <div style='margin-bottom: 6px;'><b>2. Spatial Isolation Forest:</b> <span class='{ifo_cls}'>{ifo.get('actual_result')}</span> &bull; Score: <code>{ifo.get('score')}</code> (Thresh: 0.50)</div>
                <div style='margin-bottom: 6px;'><b>3. Supervised XGBoost:</b> <span class='{xgb_cls}'>{xgb.get('actual_result')}</span></div>
                <div><b>4. Temporal Autoencoder:</b> <span class='{lstm_cls}'>{lstm.get('actual_result')}</span> &bull; Error: <code>{lstm.get('score')}</code></div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_agents:
        st.markdown("<div class='soc-panel-title'>3-AGENT SOC CONSENSUS &amp; RAG</div>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div style='background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 10px 14px; font-size: 12px;'>
                <div style='margin-bottom: 6px;'><b>Master SOC Summary:</b> {ca.get('summary', 'Nominal')}</div>
                <div style='margin-bottom: 6px;'><b>Directives:</b> <code>{', '.join(ca.get('recommended_next_action', ['MAINTAIN_STANDARD_FIX']))}</code></div>
                <div><b>Regulatory Grounding:</b> {len(rag.get('citations', []))} citation(s) from {', '.join(rag.get('regulatory_standards', [])) or 'Approved Technical Standards'}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 10-D Features Preview Table
    if feats:
        with st.expander("Inspect Generated 10-D Security Feature Vector Values", expanded=False):
            feat_df = pd.DataFrame([feats])
            st.dataframe(feat_df, use_container_width=True, hide_index=True)
