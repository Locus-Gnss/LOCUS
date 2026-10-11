import React, { useState, useEffect } from 'react';
import { Sliders, CheckCircle, AlertTriangle, Play, RefreshCw, Cpu, Database, Award } from 'lucide-react';
import { locusApi } from '../../api/locusApi';

export default function TrainingView() {
  const [modelStatuses, setModelStatuses] = useState(null);
  const [contamination, setContamination] = useState(0.02);
  const [nEstimators, setNEstimators] = useState(200);
  const [confirmReplace, setConfirmReplace] = useState(false);
  const [isTraining, setIsTraining] = useState(false);
  const [trainingResult, setTrainingResult] = useState(null);
  const [error, setError] = useState(null);

  const fetchStatus = async () => {
    try {
      const data = await locusApi.getModelsStatus();
      setModelStatuses(data.detectors || {});
    } catch (err) {
      console.warn('Failed to fetch models status', err);
    }
  };

  const [xgbInfo, setXgbInfo] = useState(null);
  const [xgbScenarioPath, setXgbScenarioPath] = useState('data/features/locus_security_features.csv');
  const [isXgbTraining, setIsXgbTraining] = useState(false);

  const fetchXgbInfo = async () => {
    try {
      const data = await locusApi.getXGBoostInfo();
      setXgbInfo(data);
    } catch (err) {
      console.warn('Could not fetch XGBoost info:', err);
    }
  };

  useEffect(() => {
    fetchStatus();
    fetchXgbInfo();
  }, []);

  const handleTrain = async () => {
    setIsTraining(true);
    setError(null);
    setTrainingResult(null);
    try {
      const res = await locusApi.trainModel({
        model_type: 'isolation_forest',
        contamination: parseFloat(contamination),
        n_estimators: parseInt(nEstimators, 10),
        confirm_replace: confirmReplace,
      });
      setTrainingResult(res);
      await fetchStatus();
    } catch (err) {
      setError(err.message || 'Model training failed.');
    } finally {
      setIsTraining(false);
    }
  };

  const handleTrainXgb = async () => {
    setIsXgbTraining(true);
    setError(null);
    setTrainingResult(null);
    try {
      const res = await locusApi.trainModel({
        model_type: 'xgboost',
        dataset_path: xgbScenarioPath.trim() || undefined,
      });
      setTrainingResult({
        message: res.status === 'OPERATIONAL'
          ? 'XGBoost successfully trained and validated on scenario partition.'
          : 'XGBoost audit completed: supervised labels unavailable in provided dataset.',
        model_type: 'xgboost',
        metrics: res.metrics || res.audit_details || res,
      });
      await fetchXgbInfo();
      await fetchStatus();
    } catch (err) {
      setError(err.message || 'XGBoost training pipeline error.');
    } finally {
      setIsXgbTraining(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Top Banner */}
      <div className="cyber-card" style={{ borderLeft: '4px solid var(--purple-agent)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ fontFamily: 'var(--font-hud)', fontSize: '1.15rem', color: '#fff' }}>
              SECTION 10: MODEL TRAINING &amp; CONTROLLED EVALUATION
            </h2>
            <p style={{ color: 'var(--text-dim)', fontSize: '0.82rem', marginTop: '0.2rem' }}>
              Leakage-free dataset splitting (70% Train, 15% Val, 15% Test) across &gt;27,687 records. Unbiased threshold validation.
            </p>
          </div>
          <span className="badge-normal" style={{ fontSize: '0.72rem', padding: '0.25rem 0.6rem', borderRadius: '4px' }}>
            ZERO-LEAKAGE AUDITED
          </span>
        </div>
      </div>

      {/* Dataset Partitions Card */}
      <div className="cyber-card">
        <h3 style={{ fontFamily: 'var(--font-hud)', fontSize: '0.95rem', color: '#cbd5e1', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <Database size={16} color="var(--cyan-primary)" />
          <span>DATASET PARTITION INTEGRITY</span>
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
          <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.75rem', borderRadius: '4px', borderLeft: '3px solid var(--cyan-primary)' }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>TRAIN PARTITION (70%)</span>
            <div style={{ fontSize: '1.15rem', fontWeight: 800, color: '#fff', fontFamily: 'var(--font-mono)' }}>~19,380 Rows</div>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>Scalers fit exclusively here</span>
          </div>
          <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.75rem', borderRadius: '4px', borderLeft: '3px solid var(--amber-warning)' }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>VALIDATION PARTITION (15%)</span>
            <div style={{ fontSize: '1.15rem', fontWeight: 800, color: '#fff', fontFamily: 'var(--font-mono)' }}>~4,153 Rows</div>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>Threshold &amp; hyperparameter tuning</span>
          </div>
          <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.75rem', borderRadius: '4px', borderLeft: '3px solid var(--green-nominal)' }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>TEST PARTITION (15%)</span>
            <div style={{ fontSize: '1.15rem', fontWeight: 800, color: '#fff', fontFamily: 'var(--font-mono)' }}>~4,154 Rows</div>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>Held-out final evaluation only</span>
          </div>
        </div>
      </div>

      {/* Model Readiness Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem' }}>
        {/* Isolation Forest Tuning */}
        <div className="cyber-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--cyan-primary)', fontFamily: 'var(--font-mono)' }}>DETECTOR 2 // ML TUNING</span>
            <span className="badge-normal" style={{ fontSize: '0.7rem' }}>FIT READY</span>
          </div>
          <h3 style={{ fontFamily: 'var(--font-hud)', fontSize: '1rem', color: '#fff', marginBottom: '0.4rem' }}>
            Isolation Forest Hyperparameters
          </h3>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '1rem' }}>
            Unsupervised tree ensemble detecting spatial deviations across the canonical 10-D feature manifold.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', marginBottom: '0.2rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>Contamination Rate:</span>
                <strong style={{ fontFamily: 'var(--font-mono)', color: 'var(--cyan-primary)' }}>{contamination}</strong>
              </div>
              <input
                type="range"
                min="0.005"
                max="0.08"
                step="0.005"
                value={contamination}
                onChange={(e) => setContamination(e.target.value)}
                style={{ width: '100%' }}
              />
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', marginBottom: '0.2rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>Number of Estimators:</span>
                <strong style={{ fontFamily: 'var(--font-mono)', color: 'var(--cyan-primary)' }}>{nEstimators}</strong>
              </div>
              <input
                type="range"
                min="50"
                max="400"
                step="50"
                value={nEstimators}
                onChange={(e) => setNEstimators(e.target.value)}
                style={{ width: '100%' }}
              />
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.4rem' }}>
              <input
                type="checkbox"
                id="chkConfirm"
                checked={confirmReplace}
                onChange={(e) => setConfirmReplace(e.target.checked)}
              />
              <label htmlFor="chkConfirm" style={{ fontSize: '0.75rem', color: '#cbd5e1' }}>
                Deploy to Production (/models/isolation_forest)
              </label>
            </div>

            <button
              className="cyber-btn"
              disabled={isTraining}
              onClick={handleTrain}
              style={{
                marginTop: '0.5rem',
                background: 'linear-gradient(135deg, rgba(0, 240, 255, 0.2), rgba(168, 85, 247, 0.25))',
                border: '1px solid var(--cyan-primary)',
                color: '#fff',
                fontWeight: 700,
                fontSize: '0.82rem',
                padding: '0.55rem',
                borderRadius: '6px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.4rem'
              }}
            >
              <Play size={14} color="var(--cyan-primary)" />
              <span>{isTraining ? 'RETRAINING ON PARTITION...' : 'START CONTROLLED TRAINING'}</span>
            </button>
          </div>
        </div>

        {/* XGBoost Status (Truthful Zero-Fabrication) */}
        <div className="cyber-card" style={{
          borderLeft: xgbInfo?.is_fitted ? '4px solid var(--green-nominal)' : '4px solid var(--amber-warning)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--cyan-primary)', fontFamily: 'var(--font-mono)' }}>
              DETECTOR 3 // SUPERVISED CLASSIFIER
            </span>
            <span className={xgbInfo?.is_fitted ? 'badge-normal' : 'badge-warning'} style={{ fontSize: '0.7rem' }}>
              {xgbInfo?.is_fitted ? 'OPERATIONAL' : 'AWAITING ATTACK LABELS'}
            </span>
          </div>
          <h3 style={{ fontFamily: 'var(--font-hud)', fontSize: '1rem', color: '#fff', marginBottom: '0.4rem' }}>
            XGBoost Supervised Scenario Pipeline
          </h3>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '0.75rem' }}>
            Supervised learning on canonical 10-D GNSS vectors. Unlabelled baseline records are never fabricated into synthetic attacks. Verified scenario datasets can be supplied below.
          </p>

          <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.75rem', borderRadius: '4px', fontSize: '0.78rem', display: 'flex', flexDirection: 'column', gap: '0.4rem', marginBottom: '0.75rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Status:</span>
              <strong style={{ color: xgbInfo?.is_fitted ? 'var(--green-nominal)' : 'var(--amber-warning)' }}>
                {xgbInfo?.status || 'UNAVAILABLE — MODEL NOT TRAINED'}
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Model Version:</span>
              <strong style={{ fontFamily: 'var(--font-mono)' }}>{xgbInfo?.model_version || 'xgb-unfitted-v1.0'}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Leakage Guard:</span>
              <strong style={{ color: 'var(--green-nominal)' }}>GROUPED SPLITTING ENFORCED</strong>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <div>
              <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.2rem' }}>
                Scenario Dataset Path (CSV):
              </label>
              <input
                type="text"
                value={xgbScenarioPath}
                onChange={(e) => setXgbScenarioPath(e.target.value)}
                placeholder="e.g. data/scenarios/labelled_gnss_attack.csv"
                style={{
                  width: '100%',
                  background: 'rgba(0,0,0,0.4)',
                  border: '1px solid var(--border-glow)',
                  color: '#fff',
                  padding: '0.4rem 0.6rem',
                  borderRadius: '4px',
                  fontSize: '0.75rem',
                  fontFamily: 'var(--font-mono)'
                }}
              />
            </div>

            <button
              className="cyber-btn"
              disabled={isXgbTraining}
              onClick={handleTrainXgb}
              style={{
                background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.2), rgba(0, 240, 255, 0.2))',
                border: '1px solid var(--amber-warning)',
                color: '#fff',
                fontWeight: 700,
                fontSize: '0.82rem',
                padding: '0.55rem',
                borderRadius: '6px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.4rem'
              }}
            >
              <Play size={14} color="var(--amber-warning)" />
              <span>{isXgbTraining ? 'VALIDATING & TRAINING...' : 'AUDIT / TRAIN XGBOOST'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Training Results Banner */}
      {trainingResult && (
        <div className="cyber-card" style={{ borderLeft: '4px solid var(--green-nominal)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <Award size={18} color="var(--green-nominal)" />
            <h4 style={{ fontFamily: 'var(--font-hud)', fontSize: '0.95rem', color: '#fff' }}>
              TRAINING &amp; INDEPENDENT VALIDATION EVALUATION RESULTS
            </h4>
          </div>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-dim)', marginBottom: '0.75rem' }}>
            {trainingResult.message}
          </p>
          <pre style={{
            background: 'rgba(0,0,0,0.4)',
            padding: '0.75rem',
            borderRadius: '4px',
            fontSize: '0.72rem',
            color: 'var(--cyan-primary)',
            overflowX: 'auto',
            fontFamily: 'var(--font-mono)'
          }}>
            {JSON.stringify(trainingResult.metrics || trainingResult, null, 2)}
          </pre>
        </div>
      )}

      {error && (
        <div className="cyber-card" style={{ borderLeft: '4px solid var(--red-critical)', color: '#f87171', fontSize: '0.8rem' }}>
          Training error: {error}
        </div>
      )}
    </div>
  );
}
