"""
LOCUS SOC State Management
Module: src.ui.utils.state
Focus: Coherent session state management across pages (Event Selection -> Evidence -> SOC Deliberation).
"""

from typing import List, Optional
import streamlit as st


def init_session_state(available_events: List[str]):
    """
    Initialize persistent session state keys if not already defined.
    Safely validates that selected_event_id is present in available_events.
    """
    if "selected_event_id" not in st.session_state:
        if available_events and available_events != ["NO DATA AVAILABLE"]:
            if "evt_4_220" in available_events:
                st.session_state["selected_event_id"] = "evt_4_220"
            else:
                st.session_state["selected_event_id"] = available_events[0]
        else:
            st.session_state["selected_event_id"] = "NO DATA AVAILABLE"
    else:
        # Validate that the currently selected event still exists in the event list
        current = st.session_state.get("selected_event_id")
        if available_events and available_events != ["NO DATA AVAILABLE"]:
            if current not in available_events:
                st.session_state["selected_event_id"] = available_events[0]

    if "rag_query_history" not in st.session_state:
        st.session_state["rag_query_history"] = []


def get_selected_event() -> str:
    """
    Get current globally selected event ID safely.
    """
    return st.session_state.get("selected_event_id", "NO DATA AVAILABLE")


def set_selected_event(event_id: str):
    """
    Set current globally selected event ID and keep all selector widget states in sync.
    """
    if not event_id or event_id == "NO DATA AVAILABLE":
        return
    st.session_state["selected_event_id"] = event_id

    # Sync selector widget keys if already defined
    for k in [
        "global_event_selector",
        "ev_deep_select",
        "ev_bundle_selector",
        "delib_event_select",
        "workspace_event_select",
    ]:
        if k in st.session_state and st.session_state[k] != event_id:
            try:
                st.session_state[k] = event_id
            except Exception:
                pass
