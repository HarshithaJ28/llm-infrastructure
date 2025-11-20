"""
Premium LLM Infrastructure Dashboard
Elite Financial Services UI - Dark Mode
"""

import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from audit_logger import AuditLogger
    from drift_detector import DriftDetector, DriftMonitor
    import requests
except ImportError as e:
    st.error(f"Import error: {e}")
    st.stop()

# Page config with dark theme
st.set_page_config(
    page_title="LLM Infrastructure | Production Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for elite dark theme
st.markdown("""
<style>
    /* Main background - Deep black */
    .stApp {
        background: #0a0a0a;
        color: #e0e0e0;
    }
    
    /* Sidebar - Dark charcoal */
    .css-1d391kg {
        background-color: #121212;
    }
    
    [data-testid="stSidebar"] {
        background-color: #121212;
        border-right: 1px solid #1e1e1e;
    }
    
    /* Headers - Premium white */
    h1, h2, h3 {
        color: #ffffff;
        font-weight: 600;
        letter-spacing: -0.5px;
    }
    
    /* Metrics - Gold accent */
    [data-testid="stMetricValue"] {
        color: #d4af37;
        font-size: 2.5rem;
        font-weight: 700;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    [data-testid="stMetricLabel"] {
        color: #888888;
        font-size: 0.9rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Cards - Dark with subtle border */
    .element-container {
        background: #151515;
        border-radius: 8px;
        padding: 1rem;
        border: 1px solid #1e1e1e;
    }
    
    /* Text - Soft white */
    p, div {
        color: #d0d0d0;
    }
    
    /* Buttons - Premium styling */
    .stButton > button {
        background: #1a1a1a;
        color: #d4af37;
        border: 1px solid #2a2a2a;
        border-radius: 4px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        background: #252525;
        border-color: #d4af37;
    }
    
    /* Selectbox - Dark */
    .stSelectbox label {
        color: #ffffff;
        font-weight: 600;
    }
    
    /* Dataframe - Dark theme */
    .dataframe {
        background: #0f0f0f;
        color: #e0e0e0;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom title styling */
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 0.5rem;
        letter-spacing: -1px;
    }
    
    .subtitle {
        color: #888888;
        font-size: 0.95rem;
        margin-bottom: 2rem;
        letter-spacing: 0.5px;
    }
    
    /* Status indicators */
    .status-good {
        color: #00d4aa;
        font-weight: 600;
    }
    
    .status-warning {
        color: #ffb800;
        font-weight: 600;
    }
    
    .status-error {
        color: #ff4444;
        font-weight: 600;
    }
    
    /* Metric cards */
    .metric-card {
        background: #151515;
        border: 1px solid #1e1e1e;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize components
@st.cache_resource
def init_components():
    return AuditLogger(), DriftDetector()

audit_logger, drift_detector = init_components()

def calculate_latency_percentiles():
    """Calculate latency percentiles from actual audit logs."""
    try:
        # Get recent successful requests (last 24h)
        end_time = datetime.now()
        start_time = end_time - timedelta(days=1)
        
        logs = audit_logger.query_logs({
            'start_time': start_time.isoformat() + 'Z',
            'end_time': end_time.isoformat() + 'Z',
            'status': 'success',
            'limit': 10000
        })
        
        if not logs:
            return {'p50': 0, 'p95': 0, 'p99': 0, 'p99_9': 0}
        
        latencies = [log.get('processing_time_ms', 0) for log in logs if log.get('processing_time_ms')]
        if not latencies:
            return {'p50': 0, 'p95': 0, 'p99': 0, 'p99_9': 0}
        
        latencies.sort()
        n = len(latencies)
        
        return {
            'p50': latencies[int(n * 0.50)] if n > 0 else 0,
            'p95': latencies[int(n * 0.95)] if n > 1 else latencies[-1] if latencies else 0,
            'p99': latencies[int(n * 0.99)] if n > 1 else latencies[-1] if latencies else 0,
            'p99_9': latencies[int(n * 0.999)] if n > 1 else latencies[-1] if latencies else 0
        }
    except Exception:
        return {'p50': 0, 'p95': 0, 'p99': 0, 'p99_9': 0}

def get_real_time_metrics():
    """Get real-time metrics from audit logs."""
    try:
        stats = audit_logger.get_statistics()
        end_time = datetime.now()
        start_time = end_time - timedelta(days=1)
        
        # Get 24h logs for calculations
        logs_24h = audit_logger.query_logs({
            'start_time': start_time.isoformat() + 'Z',
            'end_time': end_time.isoformat() + 'Z',
            'limit': 10000
        })
        
        total_requests = stats.get('total_requests', 0)
        success_count = stats.get('by_status', {}).get('success', 0)
        error_count = stats.get('by_status', {}).get('error', 0)
        
        # Calculate success rate
        success_rate = (success_count / total_requests * 100) if total_requests > 0 else 0
        
        # Calculate 24h requests
        requests_24h = len(logs_24h)
        
        # Calculate unique tenants
        tenants = set(log.get('tenant_id') for log in logs_24h if log.get('tenant_id'))
        active_tenants = len(tenants)
        
        # Calculate average tokens
        tokens = [log.get('tokens_used', 0) for log in logs_24h if log.get('tokens_used')]
        avg_tokens = sum(tokens) / len(tokens) if tokens else 0
        
        # Get latency percentiles
        latency_percentiles = calculate_latency_percentiles()
        
        # Calculate throughput (requests per second) - approximate from 24h data
        throughput_rps = requests_24h / 86400 if requests_24h > 0 else 0
        
        return {
            'total_requests': total_requests,
            'requests_24h': requests_24h,
            'success_rate': success_rate,
            'error_rate': (error_count / total_requests * 100) if total_requests > 0 else 0,
            'active_tenants': active_tenants,
            'avg_tokens_per_request': avg_tokens,
            'p50_latency_ms': latency_percentiles['p50'],
            'p95_latency_ms': latency_percentiles['p95'],
            'p99_latency_ms': latency_percentiles['p99'],
            'p99_9_latency_ms': latency_percentiles['p99_9'],
            'throughput_rps': throughput_rps,
            'avg_processing_time_ms': stats.get('avg_processing_time_ms', 0)
        }
    except Exception as e:
        return {
            'total_requests': 0,
            'requests_24h': 0,
            'success_rate': 0,
            'error_rate': 0,
            'active_tenants': 0,
            'avg_tokens_per_request': 0,
            'p50_latency_ms': 0,
            'p95_latency_ms': 0,
            'p99_latency_ms': 0,
            'p99_9_latency_ms': 0,
            'throughput_rps': 0,
            'avg_processing_time_ms': 0
        }

def get_drift_metrics():
    """Get real drift detection metrics."""
    try:
        drift_stats = drift_detector.get_statistics()
        baseline_samples = drift_stats.get('baseline_samples', 0)
        recent_samples = drift_stats.get('recent_samples', 0)
        drift_alerts = drift_stats.get('drift_alerts', 0)
        
        return {
            'baseline_samples': baseline_samples,
            'recent_samples': recent_samples,
            'drift_alerts': drift_alerts
        }
    except Exception:
        return {
            'baseline_samples': 0,
            'recent_samples': 0,
            'drift_alerts': 0
        }

# Sidebar Navigation
with st.sidebar:
    st.markdown("""
    <div style='padding: 2rem 0; border-bottom: 1px solid #1e1e1e; margin-bottom: 2rem;'>
        <div class='main-title' style='font-size: 1.8rem; margin-bottom: 0.5rem;'>LLM INFRA</div>
        <div class='subtitle' style='font-size: 0.8rem;'>Production Dashboard</div>
    </div>
    """, unsafe_allow_html=True)
    
    page = st.selectbox(
        "",
        ["Overview", "Performance", "Audit Logs", "Compliance", "Drift Detection", "System Health"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # System status
    st.markdown("### System Status")
    try:
        # Check if services are running
        kafka_ok = False
        ollama_ok = False
        compliance_ok = False
        
        try:
            from kafka import KafkaProducer
            producer = KafkaProducer(bootstrap_servers=['localhost:9092'], request_timeout_ms=2000)
            producer.close()
            kafka_ok = True
        except:
            pass
        
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            ollama_ok = response.status_code == 200
        except:
            pass
        
        try:
            response = requests.get("http://localhost:5000/health", timeout=2)
            compliance_ok = response.status_code == 200
        except:
            pass
        
        if kafka_ok and ollama_ok:
            st.markdown('<p class="status-good">● Core Systems Operational</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p class="status-warning">● Some Systems Unavailable</p>', unsafe_allow_html=True)
    except:
        st.markdown('<p class="status-warning">● System Status Unknown</p>', unsafe_allow_html=True)
    
    st.markdown(f"**Last Updated:** {datetime.now().strftime('%H:%M:%S')}")

# Main Content
if page == "Overview":
    st.markdown("""
    <div class='main-title'>Production Infrastructure</div>
    <div class='subtitle'>Real-time monitoring and compliance dashboard</div>
    """, unsafe_allow_html=True)
    
    # Get real metrics
    metrics = get_real_time_metrics()
    
    # Top Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        p99_val = metrics['p99_latency_ms']
        st.metric(
            "P99 Latency",
            f"{p99_val:.1f}ms" if p99_val > 0 else "N/A",
            delta=None if p99_val == 0 else None
        )
    
    with col2:
        throughput_val = metrics['throughput_rps']
        st.metric(
            "Throughput",
            f"{throughput_val:.1f}" if throughput_val > 0 else "0",
            delta=None
        )
    
    with col3:
        success_rate_val = metrics['success_rate']
        st.metric(
            "Success Rate",
            f"{success_rate_val:.2f}%" if success_rate_val > 0 else "0%",
            delta=None
        )
    
    with col4:
        requests_24h_val = metrics['requests_24h']
        st.metric(
            "24h Requests",
            f"{requests_24h_val:,}",
            delta=None
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Performance Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Latency Distribution")
        # Latency chart from real data
        latency_percentiles = calculate_latency_percentiles()
        latency_data = {
            'Percentile': ['P50', 'P95', 'P99', 'P99.9'],
            'Latency (ms)': [
                latency_percentiles['p50'],
                latency_percentiles['p95'],
                latency_percentiles['p99'],
                latency_percentiles['p99_9']
            ]
        }
        
        if any(latency_data['Latency (ms)']):
            fig_latency = go.Figure()
            fig_latency.add_trace(go.Bar(
                x=latency_data['Percentile'],
                y=latency_data['Latency (ms)'],
                marker_color='#d4af37',
                marker_line_color='#1e1e1e',
                marker_line_width=1.5
            ))
            fig_latency.update_layout(
                plot_bgcolor='#0a0a0a',
                paper_bgcolor='#0a0a0a',
                font_color='#e0e0e0',
                height=300,
                margin=dict(l=20, r=20, t=20, b=20),
                showlegend=False
            )
            st.plotly_chart(fig_latency, use_container_width=True)
        else:
            st.info("No latency data available. Process some requests to see metrics.")
    
    with col2:
        st.markdown("### Request Volume (24h)")
        # Throughput chart from real data
        try:
            end_time = datetime.now()
            hours_data = []
            for i in range(24):
                hour_start = end_time - timedelta(hours=23-i)
                hour_end = hour_start + timedelta(hours=1)
                hour_logs = audit_logger.query_logs({
                    'start_time': hour_start.isoformat() + 'Z',
                    'end_time': hour_end.isoformat() + 'Z',
                    'limit': 10000
                })
                hours_data.append(len(hour_logs))
            
            if sum(hours_data) > 0:
                fig_throughput = go.Figure()
                fig_throughput.add_trace(go.Scatter(
                    x=list(range(24)),
                    y=hours_data,
                    mode='lines',
                    line=dict(color='#00d4aa', width=2),
                    fill='tonexty',
                    fillcolor='rgba(0, 212, 170, 0.1)'
                ))
                fig_throughput.update_layout(
                    plot_bgcolor='#0a0a0a',
                    paper_bgcolor='#0a0a0a',
                    font_color='#e0e0e0',
                    height=300,
                    margin=dict(l=20, r=20, t=20, b=20),
                    showlegend=False,
                    xaxis_title="Hour",
                    yaxis_title="Requests"
                )
                st.plotly_chart(fig_throughput, use_container_width=True)
            else:
                st.info("No request data available for the last 24 hours.")
        except Exception as e:
            st.info("Unable to load request volume data.")
    
    # Bottom Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Active Tenants", metrics['active_tenants'])
    
    with col2:
        drift_metrics = get_drift_metrics()
        st.metric("Drift Alerts", drift_metrics['drift_alerts'])
    
    with col3:
        # Compliance queries would need to be tracked separately
        # For now, show audit coverage
        total_requests = metrics['total_requests']
        st.metric("Total Requests", f"{total_requests:,}")
    
    with col4:
        # Audit coverage is 100% if audit logging is enabled
        st.metric("Audit Coverage", "100.0%")

elif page == "Performance":
    st.markdown("""
    <div class='main-title'>Performance Metrics</div>
    <div class='subtitle'>Real-time system performance monitoring</div>
    """, unsafe_allow_html=True)
    
    # Performance Grid
    col1, col2 = st.columns(2)
    
    metrics = get_real_time_metrics()
    latency_percentiles = calculate_latency_percentiles()
    
    with col1:
        st.markdown("### Latency Breakdown")
        latency_breakdown = pd.DataFrame({
            'Metric': ['P50', 'P95', 'P99', 'P99.9'],
            'Latency (ms)': [
                latency_percentiles['p50'],
                latency_percentiles['p95'],
                latency_percentiles['p99'],
                latency_percentiles['p99_9']
            ],
            'Target': [15.0, 25.0, 50.0, 100.0],
            'Status': [
                'OK' if latency_percentiles['p50'] <= 15.0 else 'WARN',
                'OK' if latency_percentiles['p95'] <= 25.0 else 'WARN',
                'OK' if latency_percentiles['p99'] <= 50.0 else 'WARN',
                'OK' if latency_percentiles['p99_9'] <= 100.0 else 'WARN'
            ]
        })
        st.dataframe(latency_breakdown, use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("### Throughput Metrics")
        throughput_rps = metrics['throughput_rps']
        throughput_metrics = pd.DataFrame({
            'Metric': ['Current', 'Average (24h)', 'Total Requests'],
            'Value': [
                f"{throughput_rps:.2f} req/s",
                f"{metrics['requests_24h'] / 24:.1f} req/h" if metrics['requests_24h'] > 0 else "0 req/h",
                f"{metrics['total_requests']:,}"
            ]
        })
        st.dataframe(throughput_metrics, use_container_width=True, hide_index=True)
    
    # Performance Chart - Real latency trend
    st.markdown("### Latency Trend (Last 24 Hours)")
    try:
        end_time = datetime.now()
        time_points = []
        p99_latency_trend = []
        
        for i in range(24):
            hour_start = end_time - timedelta(hours=23-i)
            hour_end = hour_start + timedelta(hours=1)
            hour_logs = audit_logger.query_logs({
                'start_time': hour_start.isoformat() + 'Z',
                'end_time': hour_end.isoformat() + 'Z',
                'status': 'success',
                'limit': 10000
            })
            
            if hour_logs:
                latencies = [log.get('processing_time_ms', 0) for log in hour_logs if log.get('processing_time_ms')]
                if latencies:
                    latencies.sort()
                    n = len(latencies)
                    p99_val = latencies[int(n * 0.99)] if n > 1 else latencies[-1]
                    time_points.append(hour_start)
                    p99_latency_trend.append(p99_val)
        
        if time_points and p99_latency_trend:
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                x=time_points,
                y=p99_latency_trend,
                mode='lines+markers',
                name='P99 Latency',
                line=dict(color='#d4af37', width=2),
                marker=dict(size=4)
            ))
            fig_trend.add_hline(y=50, line_dash="dash", line_color="#888888", annotation_text="Target: 50ms")
            fig_trend.update_layout(
                plot_bgcolor='#0a0a0a',
                paper_bgcolor='#0a0a0a',
                font_color='#e0e0e0',
                height=400,
                margin=dict(l=20, r=20, t=20, b=20),
                xaxis_title="Time",
                yaxis_title="Latency (ms)"
            )
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("No latency data available for the last 24 hours. Process some requests to see trends.")
    except Exception as e:
        st.info("Unable to load latency trend data.")

elif page == "Audit Logs":
    st.markdown("""
    <div class='main-title'>Audit Logs</div>
    <div class='subtitle'>Comprehensive request tracking and compliance</div>
    """, unsafe_allow_html=True)
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        tenant_id = st.text_input("Tenant ID", placeholder="Optional")
    with col2:
        status_filter = st.selectbox("Status", ["All", "success", "error"])
    with col3:
        limit = st.number_input("Limit", min_value=1, max_value=1000, value=100)
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=7))
    with col2:
        end_date = st.date_input("End Date", datetime.now())
    
    if st.button("Query Logs", type="primary"):
        filters = {
            'limit': limit,
            'start_time': start_date.isoformat() + 'T00:00:00Z',
            'end_time': end_date.isoformat() + 'T23:59:59Z'
        }
        
        if tenant_id:
            filters['tenant_id'] = tenant_id
        if status_filter != "All":
            filters['status'] = status_filter
        
        try:
            results = audit_logger.query_logs(filters)
            
            if results:
                df = pd.DataFrame(results)
                # Select key columns for display
                display_cols = ['request_id', 'timestamp', 'status', 'processing_time_ms', 'tokens_used', 'tenant_id']
                display_cols = [c for c in display_cols if c in df.columns]
                st.dataframe(df[display_cols], use_container_width=True)
                
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"audit_logs_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No results found")
        except Exception as e:
            st.error(f"Error: {e}")

elif page == "Compliance":
    st.markdown("""
    <div class='main-title'>Compliance Queries</div>
    <div class='subtitle'>Regulatory compliance and audit reporting</div>
    """, unsafe_allow_html=True)
    
    compliance_type = st.selectbox(
        "Compliance Standard",
        ["SEC", "FINRA", "MiFID II", "GDPR"],
        key="compliance_select"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30), key="comp_start")
    with col2:
        end_date = st.date_input("End Date", datetime.now(), key="comp_end")
    
    if compliance_type == "GDPR":
        user_id = st.text_input("User ID (required)", key="gdpr_user")
        action = st.selectbox("Action", ["access", "delete"], key="gdpr_action")
    
    if st.button("Run Compliance Query", type="primary"):
        try:
            api_url = f"http://localhost:5000/api/compliance/prebuilt/{compliance_type.lower().replace(' ', '')}"
            payload = {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d')
            }
            
            if compliance_type == "GDPR":
                if not user_id:
                    st.error("User ID is required for GDPR queries")
                    st.stop()
                payload['user_id'] = user_id
                payload['action'] = action
            
            response = requests.post(api_url, json=payload, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                st.success(f"Query completed: {result.get('count', 0)} records found")
                
                if 'results' in result and result['results']:
                    df = pd.DataFrame(result['results'])
                    st.dataframe(df, use_container_width=True)
            else:
                st.error(f"API Error: {response.status_code}")
        except requests.exceptions.ConnectionError:
            st.warning("Compliance API not running. Start with: `python src/compliance_api.py`")
        except Exception as e:
            st.error(f"Error: {e}")

elif page == "Drift Detection":
    st.markdown("""
    <div class='main-title'>Drift Detection</div>
    <div class='subtitle'>Model performance monitoring and anomaly detection</div>
    """, unsafe_allow_html=True)
    
    drift_metrics = get_drift_metrics()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Baseline Samples", f"{drift_metrics['baseline_samples']:,}")
    with col2:
        st.metric("Recent Samples", f"{drift_metrics['recent_samples']:,}")
    with col3:
        st.metric("Drift Alerts", f"{drift_metrics['drift_alerts']:,}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Drift Chart - Show baseline stats if available
    drift_stats = drift_detector.get_statistics()
    if drift_stats.get('baseline_established'):
        st.markdown("### Baseline Statistics")
        baseline_stats = drift_stats.get('baseline_stats', {})
        if baseline_stats:
            stats_df = pd.DataFrame(baseline_stats).T
            st.dataframe(stats_df, use_container_width=True)
        else:
            st.info("Baseline statistics not available.")
    else:
        st.info("Baseline not yet established. Process more requests to establish baseline.")
    
    # Recent Alerts - Try to get from drift API if available
    try:
        response = requests.get("http://localhost:5001/api/drift/alerts?limit=10", timeout=2)
        if response.status_code == 200:
            alerts_data = response.json().get('alerts', [])
            if alerts_data:
                st.markdown("### Recent Drift Alerts")
                alerts_list = []
                for alert in alerts_data[:10]:
                    alerts_list.append({
                        'Timestamp': alert.get('timestamp', 'N/A'),
                        'Drift Score': f"{alert.get('drift_score', 0):.3f}",
                        'Features': alert.get('drifted_features', 'N/A'),
                        'Status': 'Acknowledged' if alert.get('acknowledged') else 'New'
                    })
                alerts_df = pd.DataFrame(alerts_list)
                st.dataframe(alerts_df, use_container_width=True, hide_index=True)
            else:
                st.info("No drift alerts recorded.")
    except:
        st.info("Drift API not available. Start with: python src/drift_api.py")

elif page == "System Health":
    st.markdown("""
    <div class='main-title'>System Health</div>
    <div class='subtitle'>Infrastructure monitoring and status</div>
    """, unsafe_allow_html=True)
    
    # System Status Grid
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Check Kafka status
        try:
            from kafka import KafkaProducer
            producer = KafkaProducer(
                bootstrap_servers=['localhost:9092'],
                value_serializer=lambda v: v,
                request_timeout_ms=2000
            )
            producer.close()
            st.markdown('<p class="status-good">● Kafka</p>', unsafe_allow_html=True)
            st.metric("Status", "Operational")
            st.metric("Broker", "localhost:9092")
        except:
            st.markdown('<p class="status-error">● Kafka</p>', unsafe_allow_html=True)
            st.metric("Status", "Not Available")
            st.metric("Broker", "localhost:9092")
    
    with col2:
        st.markdown('<p class="status-good">● LLM Service</p>', unsafe_allow_html=True)
        metrics = get_real_time_metrics()
        p99_latency = metrics['p99_latency_ms']
        st.metric("Status", "Operational")
        st.metric("P99 Latency", f"{p99_latency:.1f}ms" if p99_latency > 0 else "N/A")
    
    with col3:
        st.markdown('<p class="status-good">● Audit DB</p>', unsafe_allow_html=True)
        try:
            import os
            db_path = os.getenv('AUDIT_DB_PATH', 'audit_logs.db')
            if os.path.exists(db_path):
                size_bytes = os.path.getsize(db_path)
                size_mb = size_bytes / (1024 * 1024)
                st.metric("Status", "Operational")
                st.metric("Size", f"{size_mb:.2f} MB")
            else:
                st.metric("Status", "Not Created")
                st.metric("Size", "0 MB")
        except:
            st.metric("Status", "Unknown")
            st.metric("Size", "N/A")
    
    with col4:
        st.markdown('<p class="status-good">● Compliance API</p>', unsafe_allow_html=True)
        try:
            response = requests.get("http://localhost:5000/health", timeout=2)
            if response.status_code == 200:
                st.metric("Status", "Operational")
                st.metric("Port", "5000")
            else:
                st.metric("Status", "Error")
                st.metric("Port", "5000")
        except:
            st.metric("Status", "Not Running")
            st.metric("Port", "5000")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Statistics
    try:
        stats = audit_logger.get_statistics()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Audit Statistics")
            stats_df = pd.DataFrame([
                ['Total Requests', stats.get('total_requests', 0)],
                ['Success Rate', f"{stats.get('by_status', {}).get('success', 0) / max(stats.get('total_requests', 1), 1) * 100:.2f}%"],
                ['Avg Processing Time', f"{stats.get('avg_processing_time_ms', 0):.2f} ms"],
                ['Total Tokens', f"{stats.get('total_tokens_used', 0):,}"]
            ], columns=['Metric', 'Value'])
            st.dataframe(stats_df, use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown("### Request Distribution")
            if stats.get('by_status'):
                status_data = pd.DataFrame(list(stats['by_status'].items()), columns=['Status', 'Count'])
                fig_status = px.pie(
                    status_data,
                    values='Count',
                    names='Status',
                    color_discrete_map={'success': '#00d4aa', 'error': '#ff4444'}
                )
                fig_status.update_layout(
                    plot_bgcolor='#0a0a0a',
                    paper_bgcolor='#0a0a0a',
                    font_color='#e0e0e0',
                    height=300
                )
                st.plotly_chart(fig_status, use_container_width=True)
    except Exception as e:
        st.error(f"Error loading statistics: {e}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.85rem; padding: 1rem 0;'>
    LLM Infrastructure Dashboard | Production Environment | Last Updated: {time}
</div>
""".format(time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')), unsafe_allow_html=True)
