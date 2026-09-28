"""
epoch_aggregator.py - Multi-Constellation Epoch Aggregation for LOCUS GNSS Security Framework.

Aggregates individual NMEA sentences (GGA, GSA, GSV, RMC) into coherent 1Hz epoch observations.
Correctly sums satellites across multi-GNSS talkers and retains satellite PRN identities.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set
import numpy as np

from .nmea_parser import ParsedSentence


@dataclass
class GNSSEpochObservation:
    """
    Standardized, clean GNSS observation for a single 1Hz physical epoch.
    Represents raw physical measurements, NOT machine learning features.
    """
    timestamp_pc: str
    timestamp_gnss: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude_m: Optional[float] = None
    speed_kmh: float = 0.0
    heading_deg: float = 0.0
    fix_quality: int = 0
    satellites_used: int = 0
    satellites_in_view: int = 0
    satellite_prns: str = ""  # Semicolon-separated PRN list: "GP01;GP03;GL07;GA05"
    hdop: Optional[float] = None
    vdop: Optional[float] = None
    pdop: Optional[float] = None
    avg_cno: float = 0.0
    max_cno: float = 0.0
    min_cno: float = 0.0

    def to_dict(self) -> dict:
        return {
            "timestamp_pc": self.timestamp_pc,
            "timestamp_gnss": self.timestamp_gnss or "",
            "latitude": self.latitude if self.latitude is not None else np.nan,
            "longitude": self.longitude if self.longitude is not None else np.nan,
            "altitude_m": self.altitude_m if self.altitude_m is not None else np.nan,
            "speed_kmh": round(self.speed_kmh, 2),
            "heading_deg": round(self.heading_deg, 2),
            "fix_quality": self.fix_quality,
            "satellites_used": self.satellites_used,
            "satellites_in_view": self.satellites_in_view,
            "satellite_prns": self.satellite_prns,
            "hdop": self.hdop if self.hdop is not None else np.nan,
            "vdop": self.vdop if self.vdop is not None else np.nan,
            "pdop": self.pdop if self.pdop is not None else np.nan,
            "avg_cno": round(self.avg_cno, 2),
            "max_cno": round(self.max_cno, 2),
            "min_cno": round(self.min_cno, 2),
        }


class EpochAggregator:
    """
    Aggregates multi-sentence NMEA streams into unified 1Hz GNSS epoch observations.
    """

    def __init__(self):
        self.reset_all()

    def reset_all(self):
        """Complete reset of all state."""
        self.current_lat: Optional[float] = None
        self.current_lon: Optional[float] = None
        self.current_alt: Optional[float] = None
        self.fix_quality: int = 0
        self.satellites_used: int = 0
        self.speed_kmh: float = 0.0
        self.heading_deg: float = 0.0
        self.hdop: Optional[float] = None
        self.vdop: Optional[float] = None
        self.pdop: Optional[float] = None

        # Multi-constellation GSV tracking
        self.sats_in_view_by_talker: Dict[str, int] = {}
        self.epoch_prns: Set[str] = set()
        self.cno_list: List[float] = []

    def reset_epoch_buffers(self):
        """Reset intra-epoch buffers after an observation is exported."""
        self.cno_list.clear()
        self.epoch_prns.clear()

    def process_sentence(
        self, parsed: ParsedSentence, pc_timestamp: Optional[str] = None
    ) -> Optional[GNSSEpochObservation]:
        """
        Process a parsed NMEA sentence. Returns GNSSEpochObservation when an epoch completes (on RMC).

        Parameters
        ----------
        parsed : ParsedSentence
            Parsed sentence from NMEAParser.
        pc_timestamp : Optional[str]
            ISO wall-clock timestamp of sentence arrival.

        Returns
        -------
        Optional[GNSSEpochObservation]
            Emitted epoch observation on RMC, or None if accumulating.
        """
        if not parsed or not parsed.is_valid:
            return None

        stype = parsed.sentence_type
        now_iso = pc_timestamp or datetime.now().isoformat()

        # 1. GGA updates
        if stype == "GGA":
            self.fix_quality = parsed.fix_quality or 0
            self.satellites_used = parsed.satellites_used or 0
            if parsed.hdop is not None:
                self.hdop = parsed.hdop
            if parsed.altitude_m is not None:
                self.current_alt = parsed.altitude_m
            if parsed.latitude is not None and parsed.longitude is not None:
                self.current_lat = parsed.latitude
                self.current_lon = parsed.longitude

        # 2. GSA updates
        elif stype == "GSA":
            if parsed.pdop is not None:
                self.pdop = parsed.pdop
            if parsed.hdop is not None:
                self.hdop = parsed.hdop
            if parsed.vdop is not None:
                self.vdop = parsed.vdop
            for prn in parsed.active_prns:
                self.epoch_prns.add(prn)

        # 3. GSV updates: Multi-constellation accumulation
        elif stype == "GSV":
            if parsed.satellites_in_view_talker is not None:
                self.sats_in_view_by_talker[parsed.talker] = parsed.satellites_in_view_talker

            for sat in parsed.satellites_info:
                if sat.prn:
                    self.epoch_prns.add(sat.prn)
                if sat.snr_dbhz is not None and sat.snr_dbhz > 0:
                    self.cno_list.append(sat.snr_dbhz)

        # 4. RMC: Epoch Delimiter
        elif stype == "RMC":
            self.speed_kmh = parsed.speed_kmh or 0.0
            self.heading_deg = parsed.heading_deg or 0.0

            # Construct GNSS UTC ISO timestamp
            gnss_iso: Optional[str] = None
            if parsed.utc_datetime:
                gnss_iso = parsed.utc_datetime.replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            elif parsed.utc_time:
                gnss_iso = str(parsed.utc_time)

            # Sum total satellites in view across all active constellations
            total_in_view = sum(self.sats_in_view_by_talker.values())
            # Ensure physical invariant: in_view >= used
            total_in_view = max(total_in_view, self.satellites_used)

            # C/N0 statistics
            avg_cno = float(np.mean(self.cno_list)) if self.cno_list else 0.0
            max_cno = float(np.max(self.cno_list)) if self.cno_list else 0.0
            min_cno = float(np.min(self.cno_list)) if self.cno_list else 0.0

            # Format active PRNs string
            sorted_prns = sorted(list(self.epoch_prns))
            prn_str = ";".join(sorted_prns)

            observation = GNSSEpochObservation(
                timestamp_pc=now_iso,
                timestamp_gnss=gnss_iso,
                latitude=self.current_lat if self.fix_quality > 0 else None,
                longitude=self.current_lon if self.fix_quality > 0 else None,
                altitude_m=self.current_alt if self.fix_quality > 0 else None,
                speed_kmh=self.speed_kmh,
                heading_deg=self.heading_deg,
                fix_quality=self.fix_quality,
                satellites_used=self.satellites_used,
                satellites_in_view=total_in_view,
                satellite_prns=prn_str,
                hdop=self.hdop,
                vdop=self.vdop,
                pdop=self.pdop,
                avg_cno=avg_cno,
                max_cno=max_cno,
                min_cno=min_cno,
            )

            # Reset intra-epoch buffers for the next cycle
            self.reset_epoch_buffers()
            return observation

        return None
