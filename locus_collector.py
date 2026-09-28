import csv
from datetime import datetime
import os
import sys
import pynmea2
import serial

# Prevent Windows console encoding crashes
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ==========================================
# CONFIGURATION
# ==========================================
PORT = "COM5"  # Change to your Arduino COM port
BAUD_RATE = 115200
OUTPUT_FILE = "locus_telemetry_features.csv"

CSV_HEADERS = [
    "timestamp_pc",
    "timestamp_utc",
    "fix_quality",
    "latitude",
    "longitude",
    "altitude_m",
    "speed_kmh",
    "heading_deg",
    "satellites_used",
    "satellites_in_view",
    "hdop",
    "pdop",
    "vdop",
    "avg_cno",
    "max_cno",
    "min_cno",
]


class EpochAggregator:
    def __init__(self):
        self.reset()

    def reset(self):
        self.utc_time = None
        self.fix_quality = 0
        self.lat = None
        self.lon = None
        self.alt = None
        self.speed_kmh = 0.0
        self.heading = 0.0
        self.sats_used = 0
        self.sats_in_view = 0
        self.hdop = None
        self.pdop = None
        self.vdop = None
        self.cno_list = []

    def export_row(self, pc_time):
        avg_cno = sum(self.cno_list) / len(self.cno_list) if self.cno_list else 0.0
        max_cno = max(self.cno_list) if self.cno_list else 0.0
        min_cno = min(self.cno_list) if self.cno_list else 0.0
        return [
            pc_time,
            str(self.utc_time) if self.utc_time else "",
            self.fix_quality,
            f"{self.lat:.7f}" if self.lat is not None else "",
            f"{self.lon:.7f}" if self.lon is not None else "",
            f"{self.alt:.2f}" if self.alt is not None else "",
            f"{self.speed_kmh:.2f}",
            f"{self.heading:.2f}",
            self.sats_used,
            self.sats_in_view,
            f"{self.hdop:.2f}" if self.hdop is not None else "",
            f"{self.pdop:.2f}" if self.pdop is not None else "",
            f"{self.vdop:.2f}" if self.vdop is not None else "",
            f"{avg_cno:.2f}",
            f"{max_cno:.2f}",
            f"{min_cno:.2f}",
        ]


def main():
    try:
        ser = serial.Serial(port=PORT, baudrate=BAUD_RATE, timeout=1.5)
    except serial.SerialException as e:
        sys.exit(f"[ERROR] Could not open port {PORT}: {e}")

    print(f"[*] Serial port {PORT} open at {BAUD_RATE} baud.")
    print(f"[*] Logging structured data to: {OUTPUT_FILE}")
    print("[*] Listening for incoming NMEA frames... (Press Ctrl+C to terminate)\n")

    aggregator = EpochAggregator()
    file_exists = os.path.exists(OUTPUT_FILE)

    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        if not file_exists or os.path.getsize(OUTPUT_FILE) == 0:
            writer.writerow(CSV_HEADERS)
            csv_file.flush()

        try:
            while True:
                raw_bytes = ser.readline()
                try:
                    line = raw_bytes.decode("ascii", errors="ignore").strip()
                except Exception:
                    continue

                if not line.startswith("$"):
                    continue

                try:
                    msg = pynmea2.parse(line)
                except Exception:
                    continue

                # Safely extract sentence type (e.g., GGA, RMC, GSA, GSV)
                stype = getattr(msg, "sentence_type", None)
                if not stype:
                    continue

                # 1. GGA: Position, Fix Status, Satellites, HDOP, Altitude
                if stype == "GGA":
                    aggregator.fix_quality = int(getattr(msg, "gps_qual", 0) or 0)
                    aggregator.sats_used = int(getattr(msg, "num_sats", 0) or 0)
                    hdop_val = getattr(msg, "horizontal_dil", None)
                    aggregator.hdop = float(hdop_val) if hdop_val else None
                    alt_val = getattr(msg, "altitude", None)
                    aggregator.alt = float(alt_val) if alt_val is not None else None
                    if hasattr(msg, "latitude") and hasattr(msg, "longitude"):
                        if msg.latitude and msg.longitude:
                            aggregator.lat = float(msg.latitude)
                            aggregator.lon = float(msg.longitude)

                # 2. GSA: Dilution of Precision metrics
                elif stype == "GSA":
                    pdop_val = getattr(msg, "pdop", None)
                    aggregator.pdop = float(pdop_val) if pdop_val else None
                    hdop_val = getattr(msg, "hdop", None)
                    aggregator.hdop = float(hdop_val) if hdop_val else aggregator.hdop
                    vdop_val = getattr(msg, "vdop", None)
                    aggregator.vdop = float(vdop_val) if vdop_val else None

                # 3. GSV: Signal strengths (C/N0 in dB-Hz)
                elif stype == "GSV":
                    siv = getattr(msg, "num_sv_in_view", None)
                    if siv and str(siv).isdigit():
                        aggregator.sats_in_view = int(siv)

                    for sat_idx in ("1", "2", "3", "4"):
                        cno = getattr(msg, f"snr_{sat_idx}", None)
                        if cno and str(cno).isdigit() and int(cno) > 0:
                            aggregator.cno_list.append(int(cno))

                # 4. RMC: Speed, Course, Timestamp, and Epoch Boundary
                elif stype == "RMC":
                    aggregator.utc_time = getattr(msg, "timestamp", None)
                    spd = getattr(msg, "spd_over_grnd", None)
                    aggregator.speed_kmh = float(spd) * 1.852 if spd else 0.0
                    heading = getattr(msg, "true_course", None)
                    aggregator.heading = float(heading) if heading else 0.0

                    pc_time = datetime.now().isoformat()
                    row = aggregator.export_row(pc_time)
                    writer.writerow(row)
                    csv_file.flush()

                    status = "LOCKED" if aggregator.fix_quality > 0 else "SEARCHING"
                    print(
                        f"[{pc_time}] Fix: {status} ({aggregator.fix_quality}) | "
                        f"Sats: {aggregator.sats_used:02d} | "
                        f"Lat: {str(aggregator.lat):<10} | Lon: {str(aggregator.lon):<10} | "
                        f"Avg C/N0: {row[13]} dB-Hz"
                    )
                    aggregator.cno_list.clear()

        except KeyboardInterrupt:
            print("\n[*] Stopping logger safely...")
        finally:
            ser.close()
            print("[*] Serial port closed.")


if __name__ == "__main__":
    main()