import React, { useState, useEffect } from 'react';
import { Layers, ShieldCheck, ShieldAlert, Cpu, Activity, Clock, AlertTriangle } from 'lucide-react';
import { locusApi } from '../../api/locusApi';

export default function DetectorsView({ bundle }) {
  const pr = bundle?.physical_rules || {};
  const ifo = bundle?.isolation_forest || {};
  const xgb = bundle?.xgboost || {};
  const lstm = bundle?.temporal_model || {};

  const [xgbInfo, setXgbInfo] = useState(null);
  const [loadingXgb, setLoadingXgb] = useState(false);

  useEffect(() => {
    let isMounted = true;
    setLoadingXgb(true);
    locusApi.getXGBoostInfo()
      .then((data) => {
        if (isMounted) setXgbInfo(data);
      })
      .catch((err) => {
        console.warn('Could not fetch XGBoost info:', err);
      })
      .finally(() => {
        if (isMounted) setLoadingXgb(false);
      });
    return () => { isMounted = false; };
  }, []);

  const isXgbFitted = Boolean(xgbInfo?.is_fitted || (xgb.status && xgb.status === 'OPERATIONAL'));
  const xgbStatusText = isXgbFitted ? 'OPERATIONAL' : 'UNAVAILABLE — MODEL NOT TRAINED';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Top Banner */}
      <div className="cyber-card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <Layers size={18} color="var(--cyan-primary)" />
          <div>
            <h2 style={{ fontFamily: 'var(--font-hud)', fontSize: '1.1rem' }}>
              MULTI-DETECTOR CONSENSUS QUAD
            </h2>
            <p style={{ color: 'var(--text-dim)', fontSize: '0.82rem', marginTop: '0.2rem' }}>
              Decoupled multi-tiered defense: Physical Invariants, Unsupervised Spatial Outliers, Supervised Classification, and Deep Temporal Reconstruction.
            </p>
          </div>
        </div>
      </div>

      {/* 4 Detectors Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem' }}>
        {/* Detector 1: Physical Rules Engine */}
        <div className={`cyber-card ${pr.is_anomalous ? 'cyber-card-danger' : ''}`} style={{
          borderLeft: pr.is_anomalous ? '4px solid var(--red-critical)' : '4px solid var(--green-nominal)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--cyan-primary)', fontFamily: 'var(--font-mono)' }}>
              Detector 1 // Deterministic
            </span>
            <span style={{
              fontSize: '0.72rem',
              padding: '0.2rem 0.5rem',
              borderRadius: '3px',
              background: pr.is_anomalous ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.2)',
              color: pr.is_anomalous ? 'var(--red-critical)' : 'var(--green-nominal)',
              border: `1px solid ${pr.is_anomalous ? 'var(--red-critical)' : 'var(--green-nominal)'}`,
              fontFamily: 'var(--font-hud)'
            }}>
              {pr.is_anomalous ? 'TRIGGERED' : 'PASSED'}
            </span>
          </div>

          <h3 style={{ fontFamily: 'var(--font-hud)', fontSize: '1rem', color: '#fff', marginBottom: '0.5rem' }}>
            Physical Rules Engine
          </h3>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '0.75rem' }}>
            Evaluates hard Newtonian acceleration, jerk, velocity, and GDOP bounds.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.8rem', background: 'rgba(0,0,0,0.3)', padding: '0.65rem', borderRadius: '4px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Engine Version:</span>
              <strong style={{ fontFamily: 'var(--font-mono)' }}>prules-v1.1</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Rules Triggered:</span>
              <strong style={{ color: pr.triggered_count > 0 ? 'var(--red-critical)' : 'var(--green-nominal)' }}>
                {pr.triggered_count || 0} violations
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Max Severity:</span>
              <strong style={{ color: pr.max_severity === 'CRITICAL' ? 'var(--red-critical)' : 'var(--green-nominal)' }}>
                {pr.max_severity || 'INFO'}
              </strong>
            </div>
          </div>
        </div>

        {/* Detector 2: Isolation Forest */}
        <div className={`cyber-card ${ifo.is_anomaly ? 'cyber-card-danger' : ''}`} style={{
          borderLeft: ifo.is_anomaly ? '4px solid var(--red-critical)' : '4px solid var(--green-nominal)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--cyan-primary)', fontFamily: 'var(--font-mono)' }}>
              Detector 2 // Spatial ML
            </span>
            <span style={{
              fontSize: '0.72rem',
              padding: '0.2rem 0.5rem',
              borderRadius: '3px',
              background: ifo.is_anomaly ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.2)',
              color: ifo.is_anomaly ? 'var(--red-critical)' : 'var(--green-nominal)',
              border: `1px solid ${ifo.is_anomaly ? 'var(--red-critical)' : 'var(--green-nominal)'}`,
              fontFamily: 'var(--font-hud)'
            }}>
              {ifo.is_anomaly ? 'ANOMALY' : 'IN-BOUNDS'}
            </span>
          </div>

          <h3 style={{ fontFamily: 'var(--font-hud)', fontSize: '1rem', color: '#fff', marginBottom: '0.5rem' }}>
            Spatial Isolation Forest
          </h3>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '0.75rem' }}>
            10-D unsupervised partition forest (n=150, contam=0.01) tuned on clean baselines.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.8rem', background: 'rgba(0,0,0,0.3)', padding: '0.65rem', borderRadius: '4px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Model Version:</span>
              <strong style={{ fontFamily: 'var(--font-mono)' }}>{ifo.model_version || 'iforest-tuned-v1.1'}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Anomaly Score:</span>
              <strong style={{ fontFamily: 'var(--font-mono)', color: ifo.anomaly_score > 0.5 ? 'var(--red-critical)' : 'var(--cyan-primary)' }}>
                {ifo.anomaly_score !== undefined ? Number(ifo.anomaly_score).toFixed(4) : 'N/A'}
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Threshold Score:</span>
              <strong style={{ fontFamily: 'var(--font-mono)' }}>0.5000</strong>
            </div>
          </div>
        </div>

        {/* Detector 3: XGBoost Supervised Classifier */}
        <div className="cyber-card" style={{
          borderLeft: isXgbFitted ? '4px solid var(--green-nominal)' : '4px solid var(--amber-warning)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--cyan-primary)', fontFamily: 'var(--font-mono)' }}>
              Detector 3 // Supervised Tier
            </span>
            <span style={{
              fontSize: '0.68rem',
              padding: '0.2rem 0.5rem',
              borderRadius: '3px',
              background: isXgbFitted ? 'rgba(16, 185, 129, 0.2)' : 'rgba(245, 158, 11, 0.2)',
              color: isXgbFitted ? 'var(--green-nominal)' : 'var(--amber-warning)',
              border: `1px solid ${isXgbFitted ? 'var(--green-nominal)' : 'var(--amber-warning)'}`,
              fontFamily: 'var(--font-hud)'
            }}>
              {isXgbFitted ? 'OPERATIONAL' : 'UNAVAILABLE'}
            </span>
          </div>

          <h3 style={{ fontFamily: 'var(--font-hud)', fontSize: '1rem', color: '#fff', marginBottom: '0.5rem' }}>
            XGBoost Classifier
          </h3>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '0.75rem' }}>
            Supervised gradient boosted decision tree classifier on canonical 10-D GNSS vectors.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.78rem', background: 'rgba(0,0,0,0.3)', padding: '0.65rem', borderRadius: '4px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Model Status:</span>
              <strong style={{ color: isXgbFitted ? 'var(--green-nominal)' : 'var(--amber-warning)' }}>
                {xgbStatusText}
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Model Version:</span>
              <strong style={{ fontFamily: 'var(--font-mono)' }}>
                {xgbInfo?.model_version || xgb.model_version || 'xgb-unfitted-v1.0'}
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Dataset Provenance:</span>
              <span style={{ color: 'var(--text-dim)', textAlign: 'right', fontSize: '0.72rem' }}>
                {xgbInfo?.dataset_provenance || 'L89HA Baseline (27,686 records — Unlabelled)'}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Last Trained:</span>
              <strong style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-dim)', fontSize: '0.72rem' }}>
                {xgbInfo?.last_trained ? new Date(xgbInfo.last_trained).toLocaleString() : 'Never (Pending labelled data)'}
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Selected Event Prediction:</span>
              <strong style={{ color: isXgbFitted ? 'var(--cyan-primary)' : 'var(--amber-warning)', fontFamily: 'var(--font-mono)' }}>
                {xgb.predicted_label !== undefined && xgb.predicted_label !== null && !String(xgb.predicted_label).includes('UNAVAILABLE')
                  ? String(xgb.predicted_label)
                  : 'UNAVAILABLE — MODEL NOT TRAINED'}
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Attack Probability:</span>
              <strong style={{ fontFamily: 'var(--font-mono)', color: 'var(--cyan-primary)' }}>
                {xgb.attack_probability !== undefined && xgb.attack_probability !== null
                  ? `${(Number(xgb.attack_probability) * 100).toFixed(1)}%`
                  : 'UNAVAILABLE'}
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Evaluation F1 / Acc:</span>
              <strong style={{ fontFamily: 'var(--font-mono)', color: isXgbFitted ? 'var(--green-nominal)' : 'var(--text-muted)' }}>
                {xgbInfo?.metrics?.f1_score !== undefined
                  ? `${(xgbInfo.metrics.f1_score * 100).toFixed(1)}%`
                  : 'N/A (Awaiting Labelled Scenarios)'}
              </strong>
            </div>
          </div>

          {!isXgbFitted && (
            <div style={{
              marginTop: '0.65rem',
              padding: '0.5rem',
              background: 'rgba(245, 158, 11, 0.08)',
              border: '1px solid rgba(245, 158, 11, 0.25)',
              borderRadius: '4px',
              fontSize: '0.72rem',
              color: 'var(--amber-warning)',
              lineHeight: '1.4'
            }}>
              <strong>Honest Data Limitation:</strong> The 27,687-record baseline dataset contains benign terrestrial navigation telemetry only. In accordance with strict non-fabrication constraints, attack labels are never fabricated. Supervised training requires verified scenario data.
            </div>
          )}
        </div>

        {/* Detector 4: LSTM Temporal Autoencoder */}
        <div className={`cyber-card ${lstm.is_anomaly ? 'cyber-card-danger' : ''}`} style={{
          borderLeft: lstm.is_anomaly ? '4px solid var(--red-critical)' : '4px solid var(--green-nominal)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--cyan-primary)', fontFamily: 'var(--font-mono)' }}>
              Detector 4 // Deep Learning
            </span>
            <span style={{
              fontSize: '0.72rem',
              padding: '0.2rem 0.5rem',
              borderRadius: '3px',
              background: lstm.is_anomaly ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.2)',
              color: lstm.is_anomaly ? 'var(--red-critical)' : 'var(--green-nominal)',
              border: `1px solid ${lstm.is_anomaly ? 'var(--red-critical)' : 'var(--green-nominal)'}`,
              fontFamily: 'var(--font-hud)'
            }}>
              {lstm.status === 'BUFFERING' ? 'BUFFERING' : (lstm.is_anomaly ? 'ANOMALOUS DRIFT' : 'NOMINAL')}
            </span>
          </div>

          <h3 style={{ fontFamily: 'var(--font-hud)', fontSize: '1rem', color: '#fff', marginBottom: '0.5rem' }}>
            LSTM Autoencoder
          </h3>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '0.75rem' }}>
            Temporal sequence model (W=10, H=64) detecting cognitive drag-off & progressive drift.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.8rem', background: 'rgba(0,0,0,0.3)', padding: '0.65rem', borderRadius: '4px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Model Architecture:</span>
              <strong style={{ fontFamily: 'var(--font-mono)' }}>LSTM-AE-v1.1 (H=64)</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Reconstruction MSE:</span>
              <strong style={{ fontFamily: 'var(--font-mono)', color: lstm.is_anomaly ? 'var(--red-critical)' : 'var(--green-nominal)' }}>
                {lstm.reconstruction_error !== undefined && lstm.reconstruction_error !== null
                  ? Number(lstm.reconstruction_error).toFixed(5)
                  : (lstm.status === 'BUFFERING' ? 'BUFFERING (W < 10)' : 'N/A')}
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Buffer Window:</span>
              <strong style={{ fontFamily: 'var(--font-mono)' }}>10 Epochs</strong>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
