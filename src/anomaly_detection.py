from backend.app.services.anomaly_service import anomaly_service

def detect_anomalies():
    """Wrapper calling backend anomaly detection service."""
    return anomaly_service.detect_anomalies()
