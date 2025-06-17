#!/usr/bin/env python3
"""
SIEM Platform Machine Learning Anomaly Detection Module

This module implements advanced ML-based anomaly detection for the SIEM platform,
including time series analysis, NLP-based log analysis, and behavioral analytics.
"""

import numpy as np
import pandas as pd
import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import DBSCAN
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModel
import elasticsearch
from kafka import KafkaConsumer, KafkaProducer
import redis
import pickle
import joblib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AnomalyResult:
    """Data class for anomaly detection results"""
    timestamp: datetime
    source: str
    anomaly_score: float
    is_anomaly: bool
    confidence: float
    features: Dict[str, Any]
    explanation: str
    severity: str

class TimeSeriesAnomalyDetector:
    """
    Time series anomaly detection using LSTM neural networks
    """
    
    def __init__(self, sequence_length: int = 60, threshold: float = 0.95):
        self.sequence_length = sequence_length
        self.threshold = threshold
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def build_model(self, n_features: int) -> Sequential:
        """Build LSTM model for time series anomaly detection"""
        model = Sequential([
            LSTM(50, return_sequences=True, input_shape=(self.sequence_length, n_features)),
            Dropout(0.2),
            LSTM(50, return_sequences=False),
            Dropout(0.2),
            Dense(25),
            Dense(n_features)
        ])
        
        model.compile(optimizer='adam', loss='mse')
        return model
    
    def prepare_sequences(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare sequences for LSTM training"""
        X, y = [], []
        for i in range(self.sequence_length, len(data)):
            X.append(data[i-self.sequence_length:i])
            y.append(data[i])
        return np.array(X), np.array(y)
    
    def train(self, training_data: pd.DataFrame, epochs: int = 100):
        """Train the LSTM model on normal data"""
        logger.info("Training time series anomaly detector...")
        
        # Normalize data
        scaled_data = self.scaler.fit_transform(training_data.values)
        
        # Prepare sequences
        X_train, y_train = self.prepare_sequences(scaled_data)
        
        # Build and train model
        self.model = self.build_model(training_data.shape[1])
        
        history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=32,
            validation_split=0.2,
            verbose=1
        )
        
        self.is_trained = True
        logger.info("Time series model training completed")
        
        return history
    
    def detect_anomalies(self, data: pd.DataFrame) -> List[AnomalyResult]:
        """Detect anomalies in time series data"""
        if not self.is_trained:
            raise ValueError("Model must be trained before detection")
        
        # Normalize data
        scaled_data = self.scaler.transform(data.values)
        
        # Prepare sequences
        X_test, y_test = self.prepare_sequences(scaled_data)
        
        # Predict
        predictions = self.model.predict(X_test)
        
        # Calculate reconstruction errors
        mse = np.mean(np.power(y_test - predictions, 2), axis=1)
        
        # Determine threshold
        threshold = np.percentile(mse, self.threshold * 100)
        
        # Generate results
        results = []
        for i, error in enumerate(mse):
            timestamp = data.index[i + self.sequence_length]
            is_anomaly = error > threshold
            
            result = AnomalyResult(
                timestamp=timestamp,
                source="time_series",
                anomaly_score=float(error),
                is_anomaly=is_anomaly,
                confidence=min(error / threshold, 2.0) if is_anomaly else 1.0 - (error / threshold),
                features=data.iloc[i + self.sequence_length].to_dict(),
                explanation=f"Reconstruction error: {error:.4f}, Threshold: {threshold:.4f}",
                severity="high" if error > threshold * 2 else "medium" if is_anomaly else "low"
            )
            results.append(result)
        
        return results

class LogAnomalyDetector:
    """
    NLP-based log anomaly detection using transformer models
    """
    
    def __init__(self, model_name: str = "distilbert-base-uncased"):
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        self.is_trained = False
        
    def extract_features(self, logs: List[str]) -> np.ndarray:
        """Extract features from log messages using transformer model"""
        features = []
        
        for log in logs:
            # Tokenize and encode
            inputs = self.tokenizer(log, return_tensors="pt", truncation=True, padding=True, max_length=512)
            
            # Get embeddings
            with torch.no_grad():
                outputs = self.model(**inputs)
                # Use CLS token embedding
                embedding = outputs.last_hidden_state[:, 0, :].numpy().flatten()
                features.append(embedding)
        
        return np.array(features)
    
    def train(self, normal_logs: List[str]):
        """Train the log anomaly detector on normal logs"""
        logger.info("Training log anomaly detector...")
        
        # Extract features
        features = self.extract_features(normal_logs)
        
        # Train isolation forest
        self.isolation_forest.fit(features)
        self.is_trained = True
        
        logger.info("Log anomaly detector training completed")
    
    def detect_anomalies(self, logs: List[str], timestamps: List[datetime]) -> List[AnomalyResult]:
        """Detect anomalies in log messages"""
        if not self.is_trained:
            raise ValueError("Model must be trained before detection")
        
        # Extract features
        features = self.extract_features(logs)
        
        # Predict anomalies
        predictions = self.isolation_forest.predict(features)
        scores = self.isolation_forest.decision_function(features)
        
        # Generate results
        results = []
        for i, (log, timestamp, pred, score) in enumerate(zip(logs, timestamps, predictions, scores)):
            is_anomaly = pred == -1
            
            result = AnomalyResult(
                timestamp=timestamp,
                source="log_analysis",
                anomaly_score=float(-score),  # Convert to positive score
                is_anomaly=is_anomaly,
                confidence=abs(score),
                features={"log_message": log, "log_length": len(log)},
                explanation=f"Log pattern anomaly detected. Score: {score:.4f}",
                severity="high" if score < -0.5 else "medium" if is_anomaly else "low"
            )
            results.append(result)
        
        return results

class BehavioralAnomalyDetector:
    """
    User and entity behavioral anomaly detection
    """
    
    def __init__(self, contamination: float = 0.1):
        self.contamination = contamination
        self.models = {}
        self.scalers = {}
        self.is_trained = False
        
    def extract_behavioral_features(self, events: pd.DataFrame) -> pd.DataFrame:
        """Extract behavioral features from security events"""
        features = pd.DataFrame()
        
        # Time-based features
        features['hour_of_day'] = events['timestamp'].dt.hour
        features['day_of_week'] = events['timestamp'].dt.dayofweek
        features['is_weekend'] = features['day_of_week'].isin([5, 6]).astype(int)
        
        # Activity features
        features['events_per_hour'] = events.groupby([events['user_id'], events['timestamp'].dt.floor('H')]).size().reset_index(drop=True)
        features['unique_ips'] = events.groupby('user_id')['source_ip'].nunique().reset_index(drop=True)
        features['unique_destinations'] = events.groupby('user_id')['destination_ip'].nunique().reset_index(drop=True)
        
        # Risk features
        features['failed_logins'] = events[events['event_type'] == 'failed_login'].groupby('user_id').size().reset_index(drop=True)
        features['privilege_escalations'] = events[events['event_type'] == 'privilege_escalation'].groupby('user_id').size().reset_index(drop=True)
        features['data_transfers'] = events[events['event_type'] == 'data_transfer']['bytes_transferred'].groupby(events['user_id']).sum().reset_index(drop=True)
        
        # Fill NaN values
        features = features.fillna(0)
        
        return features
    
    def train(self, training_events: pd.DataFrame):
        """Train behavioral anomaly detectors for each user"""
        logger.info("Training behavioral anomaly detector...")
        
        # Group by user
        for user_id in training_events['user_id'].unique():
            user_events = training_events[training_events['user_id'] == user_id]
            
            if len(user_events) < 10:  # Skip users with insufficient data
                continue
            
            # Extract features
            features = self.extract_behavioral_features(user_events)
            
            # Scale features
            scaler = StandardScaler()
            scaled_features = scaler.fit_transform(features)
            
            # Train isolation forest
            model = IsolationForest(contamination=self.contamination, random_state=42)
            model.fit(scaled_features)
            
            # Store model and scaler
            self.models[user_id] = model
            self.scalers[user_id] = scaler
        
        self.is_trained = True
        logger.info("Behavioral anomaly detector training completed")
    
    def detect_anomalies(self, events: pd.DataFrame) -> List[AnomalyResult]:
        """Detect behavioral anomalies"""
        if not self.is_trained:
            raise ValueError("Model must be trained before detection")
        
        results = []
        
        # Group by user
        for user_id in events['user_id'].unique():
            if user_id not in self.models:
                continue  # Skip users not in training data
            
            user_events = events[events['user_id'] == user_id]
            features = self.extract_behavioral_features(user_events)
            
            # Scale features
            scaled_features = self.scalers[user_id].transform(features)
            
            # Predict anomalies
            predictions = self.models[user_id].predict(scaled_features)
            scores = self.models[user_id].decision_function(scaled_features)
            
            # Generate results
            for i, (_, event) in enumerate(user_events.iterrows()):
                is_anomaly = predictions[i] == -1
                score = scores[i]
                
                result = AnomalyResult(
                    timestamp=event['timestamp'],
                    source="behavioral_analysis",
                    anomaly_score=float(-score),
                    is_anomaly=is_anomaly,
                    confidence=abs(score),
                    features={
                        "user_id": user_id,
                        "event_type": event['event_type'],
                        "source_ip": event['source_ip']
                    },
                    explanation=f"Behavioral anomaly for user {user_id}. Score: {score:.4f}",
                    severity="high" if score < -0.5 else "medium" if is_anomaly else "low"
                )
                results.append(result)
        
        return results

class AnomalyDetectionEngine:
    """
    Main anomaly detection engine that coordinates multiple detectors
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.detectors = {}
        self.redis_client = redis.Redis(
            host=config.get('redis_host', 'localhost'),
            port=config.get('redis_port', 6379),
            db=config.get('redis_db', 0)
        )
        
        # Initialize detectors
        if config.get('enable_time_series', True):
            self.detectors['time_series'] = TimeSeriesAnomalyDetector()
        
        if config.get('enable_log_analysis', True):
            self.detectors['log_analysis'] = LogAnomalyDetector()
        
        if config.get('enable_behavioral', True):
            self.detectors['behavioral'] = BehavioralAnomalyDetector()
    
    async def process_events(self, events: List[Dict[str, Any]]) -> List[AnomalyResult]:
        """Process events through all enabled detectors"""
        all_results = []
        
        # Convert to DataFrame
        df = pd.DataFrame(events)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Time series detection
        if 'time_series' in self.detectors and 'metric_value' in df.columns:
            ts_data = df.set_index('timestamp')[['metric_value']]
            ts_results = self.detectors['time_series'].detect_anomalies(ts_data)
            all_results.extend(ts_results)
        
        # Log analysis
        if 'log_analysis' in self.detectors and 'log_message' in df.columns:
            logs = df['log_message'].tolist()
            timestamps = df['timestamp'].tolist()
            log_results = self.detectors['log_analysis'].detect_anomalies(logs, timestamps)
            all_results.extend(log_results)
        
        # Behavioral analysis
        if 'behavioral' in self.detectors and 'user_id' in df.columns:
            behavioral_results = self.detectors['behavioral'].detect_anomalies(df)
            all_results.extend(behavioral_results)
        
        # Store results in Redis
        await self.store_results(all_results)
        
        return all_results
    
    async def store_results(self, results: List[AnomalyResult]):
        """Store anomaly results in Redis"""
        for result in results:
            if result.is_anomaly:
                key = f"anomaly:{result.timestamp.isoformat()}:{result.source}"
                value = {
                    'timestamp': result.timestamp.isoformat(),
                    'source': result.source,
                    'anomaly_score': result.anomaly_score,
                    'confidence': result.confidence,
                    'features': result.features,
                    'explanation': result.explanation,
                    'severity': result.severity
                }
                
                # Store with TTL
                self.redis_client.setex(key, 86400, json.dumps(value))  # 24 hours TTL
    
    def train_all_detectors(self, training_data: Dict[str, Any]):
        """Train all enabled detectors"""
        logger.info("Training all anomaly detectors...")
        
        # Train time series detector
        if 'time_series' in self.detectors and 'time_series_data' in training_data:
            self.detectors['time_series'].train(training_data['time_series_data'])
        
        # Train log detector
        if 'log_analysis' in self.detectors and 'normal_logs' in training_data:
            self.detectors['log_analysis'].train(training_data['normal_logs'])
        
        # Train behavioral detector
        if 'behavioral' in self.detectors and 'user_events' in training_data:
            self.detectors['behavioral'].train(training_data['user_events'])
        
        logger.info("All detectors trained successfully")
    
    def save_models(self, model_path: str):
        """Save trained models to disk"""
        models_data = {}
        
        for name, detector in self.detectors.items():
            if hasattr(detector, 'is_trained') and detector.is_trained:
                if name == 'time_series':
                    detector.model.save(f"{model_path}/{name}_model.h5")
                    joblib.dump(detector.scaler, f"{model_path}/{name}_scaler.pkl")
                elif name == 'log_analysis':
                    joblib.dump(detector.isolation_forest, f"{model_path}/{name}_model.pkl")
                elif name == 'behavioral':
                    joblib.dump(detector.models, f"{model_path}/{name}_models.pkl")
                    joblib.dump(detector.scalers, f"{model_path}/{name}_scalers.pkl")
        
        logger.info(f"Models saved to {model_path}")
    
    def load_models(self, model_path: str):
        """Load trained models from disk"""
        for name, detector in self.detectors.items():
            try:
                if name == 'time_series':
                    detector.model = tf.keras.models.load_model(f"{model_path}/{name}_model.h5")
                    detector.scaler = joblib.load(f"{model_path}/{name}_scaler.pkl")
                    detector.is_trained = True
                elif name == 'log_analysis':
                    detector.isolation_forest = joblib.load(f"{model_path}/{name}_model.pkl")
                    detector.is_trained = True
                elif name == 'behavioral':
                    detector.models = joblib.load(f"{model_path}/{name}_models.pkl")
                    detector.scalers = joblib.load(f"{model_path}/{name}_scalers.pkl")
                    detector.is_trained = True
                
                logger.info(f"Loaded {name} model successfully")
            except FileNotFoundError:
                logger.warning(f"Model file not found for {name} detector")

# Example usage and configuration
if __name__ == "__main__":
    # Configuration
    config = {
        'enable_time_series': True,
        'enable_log_analysis': True,
        'enable_behavioral': True,
        'redis_host': 'localhost',
        'redis_port': 6379,
        'redis_db': 0
    }
    
    # Initialize engine
    engine = AnomalyDetectionEngine(config)
    
    # Example training data
    training_data = {
        'time_series_data': pd.DataFrame({
            'metric_value': np.random.normal(100, 10, 1000)
        }, index=pd.date_range('2023-01-01', periods=1000, freq='H')),
        'normal_logs': [
            "User login successful",
            "File access granted",
            "Network connection established",
            "Database query executed"
        ] * 100,
        'user_events': pd.DataFrame({
            'user_id': ['user1', 'user2'] * 500,
            'timestamp': pd.date_range('2023-01-01', periods=1000, freq='H'),
            'event_type': ['login', 'file_access', 'network'] * 333 + ['login'],
            'source_ip': ['192.168.1.100', '192.168.1.101'] * 500,
            'destination_ip': ['10.0.0.1', '10.0.0.2'] * 500,
            'bytes_transferred': np.random.randint(1000, 10000, 1000)
        })
    }
    
    # Train detectors
    engine.train_all_detectors(training_data)
    
    # Save models
    engine.save_models("./models")
    
    print("Anomaly detection engine initialized and trained successfully!")

