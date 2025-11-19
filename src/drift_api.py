"""
Drift Detection API for monitoring LLM performance.

Provides REST API for querying drift alerts and statistics.
"""

import logging
import os
from flask import Flask, request, jsonify
from typing import Dict

try:
    from drift_detector import DriftMonitor, DriftDetector
    DRIFT_DETECTION_AVAILABLE = True
except ImportError:
    DRIFT_DETECTION_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize drift monitor (read-only for API)
drift_monitor = None
if DRIFT_DETECTION_AVAILABLE:
    try:
        detector = DriftDetector()
        db_path = os.getenv('DRIFT_DB_PATH', 'drift_alerts.db')
        drift_monitor = DriftMonitor(detector=detector, db_path=db_path)
    except Exception as e:
        logger.warning(f"Failed to initialize drift monitor: {e}")


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "drift-detection-api",
        "drift_detection_available": DRIFT_DETECTION_AVAILABLE
    }), 200


@app.route('/api/drift/alerts', methods=['GET'])
def get_alerts():
    """
    Get drift alerts.
    
    Query parameters:
        limit: Maximum number of alerts (default: 10)
        acknowledged: Filter by acknowledged status (true/false)
    """
    if not drift_monitor:
        return jsonify({"error": "Drift detection not available"}), 503
    
    try:
        limit = int(request.args.get('limit', 10))
        acknowledged = request.args.get('acknowledged')
        
        alerts = drift_monitor.get_recent_alerts(limit=limit)
        
        # Filter by acknowledged if specified
        if acknowledged is not None:
            acknowledged_bool = acknowledged.lower() == 'true'
            alerts = [a for a in alerts if a.get('acknowledged', 0) == (1 if acknowledged_bool else 0)]
        
        return jsonify({
            "count": len(alerts),
            "alerts": alerts
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting alerts: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/drift/statistics', methods=['GET'])
def get_statistics():
    """Get drift detection statistics."""
    if not drift_monitor:
        return jsonify({"error": "Drift detection not available"}), 503
    
    try:
        stats = drift_monitor.detector.get_statistics()
        alerts = drift_monitor.get_recent_alerts(limit=100)
        
        # Calculate additional statistics
        unacknowledged_count = sum(1 for a in alerts if not a.get('acknowledged', 0))
        
        stats['total_alerts'] = len(alerts)
        stats['unacknowledged_alerts'] = unacknowledged_count
        stats['acknowledged_alerts'] = len(alerts) - unacknowledged_count
        
        if alerts:
            avg_drift_score = sum(a.get('drift_score', 0) for a in alerts) / len(alerts)
            stats['avg_drift_score'] = round(avg_drift_score, 3)
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/drift/alert/<int:alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id: int):
    """Acknowledge a drift alert."""
    if not drift_monitor:
        return jsonify({"error": "Drift detection not available"}), 503
    
    try:
        drift_monitor.acknowledge_alert(alert_id)
        return jsonify({"message": "Alert acknowledged", "alert_id": alert_id}), 200
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/drift/reset-baseline', methods=['POST'])
def reset_baseline():
    """
    Reset baseline distribution with recent outputs.
    
    This should be called after model updates or when you want to recalibrate.
    """
    if not drift_monitor:
        return jsonify({"error": "Drift detection not available"}), 503
    
    try:
        drift_monitor.detector.reset_baseline()
        return jsonify({"message": "Baseline reset successfully"}), 200
    except Exception as e:
        logger.error(f"Error resetting baseline: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.getenv('DRIFT_API_PORT', 5001))
    host = os.getenv('DRIFT_API_HOST', '0.0.0.0')
    
    logger.info(f"Starting Drift Detection API on {host}:{port}")
    logger.info("Endpoints:")
    logger.info("  GET  /api/drift/alerts - Get drift alerts")
    logger.info("  GET  /api/drift/statistics - Get statistics")
    logger.info("  POST /api/drift/alert/<id>/acknowledge - Acknowledge alert")
    logger.info("  POST /api/drift/reset-baseline - Reset baseline")
    
    app.run(host=host, port=port, debug=False)

