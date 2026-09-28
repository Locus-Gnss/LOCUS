"""
nmea_parser.py - Safe, Robust NMEA 0183 Sentence Parsing Engine for LOCUS.

Handles sentence validation, error isolation, multi-constellation talker extraction,
and satellite PRN/SNR retention across GGA, GSA, GSV, and RMC sentences.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import Dict, List, Optional, Tuple
import pynmea2


@dataclass
class SatelliteSignal:
    talker: str
    prn: str
    elevation_deg: Optional[float] = None
    azimuth_deg: Optional[float] = None
    snr_dbhz: Optional[float] = None


@dataclass
class ParsedSentence:
    sentence_type: str
    talker: str
    is_valid: bool
    error_message: Optional[str] = None
    raw_sentence: str = ""

    # GGA Fields
    fix_quality: Optional[int] = None
    satellites_used: Optional[int] = None
    hdop: Optional[float] = None
    altitude_m: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # GSA Fields
    fix_mode: Optional[str] = None
    fix_type: Optional[int] = None
    pdop: Optional[float] = None
    vdop: Optional[float] = None
    active_prns: List[str] = field(default_factory=list)

    # GSV Fields
    total_messages: Optional[int] = None
    message_num: Optional[int] = None
    satellites_in_view_talker: Optional[int] = None
    satellites_info: List[SatelliteSignal] = field(default_factory=list)

    # RMC Fields
    utc_time: Optional[time] = None
    utc_date: Optional[date] = None
    utc_datetime: Optional[datetime] = None
    status: Optional[str] = None
    speed_kmh: Optional[float] = None
    heading_deg: Optional[float] = None


class NMEAParser:
    """
    Decoupled, fail-safe NMEA sentence parser.
    Never crashes on malformed data; returns typed ParsedSentence objects with validation state.
    """

    SUPPORTED_SENTENCES = {"GGA", "RMC", "GSA", "GSV"}

    @staticmethod
    def parse_line(line: str, check_checksum: bool = False) -> Optional[ParsedSentence]:
        """
        Parse a single NMEA sentence string safely.

        Parameters
        ----------
        line : str
            Raw NMEA string (e.g., "$GPGGA,...*79").
        check_checksum : bool
            Whether to enforce strict NMEA XOR checksum verification (default: False).

        Returns
        -------
        Optional[ParsedSentence]
            Parsed sentence structure, or None if the line is empty/unrelated.
        """
        if not line or not isinstance(line, str):
            return None

        clean_line = line.strip()
        if not clean_line.startswith("$") and not clean_line.startswith("!"):
            return None

        try:
            msg = pynmea2.parse(clean_line)
        except pynmea2.ChecksumError as c_err:
            if not check_checksum:
                try:
                    msg = pynmea2.parse(clean_line.split("*")[0])
                except Exception as inner_e:
                    return ParsedSentence(
                        sentence_type="UNKNOWN",
                        talker="UNKNOWN",
                        is_valid=False,
                        error_message=f"ParseError: {inner_e}",
                        raw_sentence=clean_line,
                    )
            else:
                return ParsedSentence(
                    sentence_type="UNKNOWN",
                    talker="UNKNOWN",
                    is_valid=False,
                    error_message=f"ChecksumError: {c_err}",
                    raw_sentence=clean_line,
                )
        except Exception as e:
            return ParsedSentence(
                sentence_type="UNKNOWN",
                talker="UNKNOWN",
                is_valid=False,
                error_message=f"ParseError: {e}",
                raw_sentence=clean_line,
            )

        stype = getattr(msg, "sentence_type", None)
        talker = getattr(msg, "talker", "GN")

        if stype not in NMEAParser.SUPPORTED_SENTENCES:
            return ParsedSentence(
                sentence_type=stype or "UNSUPPORTED",
                talker=talker,
                is_valid=True,
                raw_sentence=clean_line,
            )

        record = ParsedSentence(
            sentence_type=stype,
            talker=talker,
            is_valid=True,
            raw_sentence=clean_line,
        )

        try:
            # 1. GGA: Position, Fix status, Satellites, HDOP, Altitude
            if stype == "GGA":
                record.fix_quality = int(getattr(msg, "gps_qual", 0) or 0)
                record.satellites_used = int(getattr(msg, "num_sats", 0) or 0)
                hdop_val = getattr(msg, "horizontal_dil", None)
                record.hdop = float(hdop_val) if hdop_val else None
                alt_val = getattr(msg, "altitude", None)
                record.altitude_m = float(alt_val) if alt_val is not None else None

                if hasattr(msg, "latitude") and hasattr(msg, "longitude"):
                    if msg.latitude and msg.longitude:
                        record.latitude = float(msg.latitude)
                        record.longitude = float(msg.longitude)

            # 2. GSA: Dilution of precision and active satellite PRNs
            elif stype == "GSA":
                record.fix_mode = getattr(msg, "mode", None)
                ftype = getattr(msg, "mode_fix_type", None)
                record.fix_type = int(ftype) if ftype and str(ftype).isdigit() else None
                pdop_val = getattr(msg, "pdop", None)
                record.pdop = float(pdop_val) if pdop_val else None
                hdop_val = getattr(msg, "hdop", None)
                record.hdop = float(hdop_val) if hdop_val else None
                vdop_val = getattr(msg, "vdop", None)
                record.vdop = float(vdop_val) if vdop_val else None

                # Extract active satellite IDs used in solution (channels 1-12)
                active_list = []
                for ch in range(1, 13):
                    sv_id = getattr(msg, f"sv_id{ch:02d}", None)
                    if sv_id and str(sv_id).strip():
                        # Standardize with talker prefix
                        prn_str = str(sv_id).strip().zfill(2)
                        active_list.append(f"{talker}{prn_str}")
                record.active_prns = active_list

            # 3. GSV: Satellites in view and individual satellite PRN / SNR telemetry
            elif stype == "GSV":
                tmsg = getattr(msg, "num_messages", None)
                record.total_messages = int(tmsg) if tmsg and str(tmsg).isdigit() else None
                mnum = getattr(msg, "msg_num", None)
                record.message_num = int(mnum) if mnum and str(mnum).isdigit() else None
                siv = getattr(msg, "num_sv_in_view", None)
                record.satellites_in_view_talker = int(siv) if siv and str(siv).isdigit() else 0

                sats_info: List[SatelliteSignal] = []
                for sat_idx in ("1", "2", "3", "4"):
                    prn = getattr(msg, f"sv_prn_num_{sat_idx}", None)
                    if prn and str(prn).strip():
                        prn_clean = f"{talker}{str(prn).strip().zfill(2)}"
                        elev = getattr(msg, f"elevation_deg_{sat_idx}", None)
                        elev_val = float(elev) if elev and str(elev).replace("-", "").isdigit() else None
                        azim = getattr(msg, f"azimuth_{sat_idx}", None)
                        azim_val = float(azim) if azim and str(azim).isdigit() else None
                        snr = getattr(msg, f"snr_{sat_idx}", None)
                        snr_val = float(snr) if snr and str(snr).isdigit() and int(snr) > 0 else None

                        sats_info.append(
                            SatelliteSignal(
                                talker=talker,
                                prn=prn_clean,
                                elevation_deg=elev_val,
                                azimuth_deg=azim_val,
                                snr_dbhz=snr_val,
                            )
                        )
                record.satellites_info = sats_info

            # 4. RMC: Navigation time, date, status, velocity, heading
            elif stype == "RMC":
                record.utc_time = getattr(msg, "timestamp", None)
                record.utc_date = getattr(msg, "datestamp", None)
                record.status = getattr(msg, "status", None)

                # Construct combined UTC datetime if both date and time exist
                if record.utc_time and record.utc_date:
                    try:
                        record.utc_datetime = datetime.combine(record.utc_date, record.utc_time)
                    except Exception:
                        record.utc_datetime = None

                spd = getattr(msg, "spd_over_grnd", None)
                record.speed_kmh = float(spd) * 1.852 if spd is not None and str(spd).replace(".", "").isdigit() else 0.0
                course = getattr(msg, "true_course", None)
                record.heading_deg = float(course) if course is not None and str(course).replace(".", "").isdigit() else 0.0

        except Exception as field_err:
            record.is_valid = False
            record.error_message = f"FieldExtractionError: {field_err}"

        return record
