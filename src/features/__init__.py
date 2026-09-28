"""
LOCUS Security Feature Engineering Package.

Defines the official 10-dimensional cybersecurity feature vector for GNSS threat detection:
1. disp_haversine
2. vel_kinematic
3. acc_kinematic
4. jerk_kinematic
5. bearing_rate
6. HDOP
7. VDOP
8. fix_integrity
9. sat_count_tot
10. sat_churn
"""

from .security_features import SecurityFeatureExtractor

__all__ = ["SecurityFeatureExtractor"]
