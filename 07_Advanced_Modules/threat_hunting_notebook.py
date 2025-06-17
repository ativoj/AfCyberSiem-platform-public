#!/usr/bin/env python3
"""
SIEM Platform Threat Hunting Jupyter Notebook Integration

This module provides threat hunting capabilities through Jupyter notebooks
with pre-built hunting queries, visualizations, and interactive analysis tools.
"""

import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ipywidgets as widgets
from IPython.display import display, HTML, Markdown
import elasticsearch
from elasticsearch_dsl import Search, Q
import requests
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class ThreatHuntingNotebook:
    """
    Main class for threat hunting notebook functionality
    """
    
    def __init__(self, config_file: str = "hunting_config.json"):
        """Initialize threat hunting environment"""
        self.config = self.load_config(config_file)
        self.es_client = self.connect_elasticsearch()
        self.wazuh_api = self.connect_wazuh_api()
        self.graylog_api = self.connect_graylog_api()
        
        # Set up plotting style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        print("🔍 Threat Hunting Environment Initialized")
        print(f"📊 Connected to Elasticsearch: {self.config['elasticsearch']['host']}")
        print(f"🛡️  Connected to Wazuh: {self.config['wazuh']['host']}")
        print(f"📝 Connected to Graylog: {self.config['graylog']['host']}")
    
    def load_config(self, config_file: str) -> dict:
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Default configuration
            return {
                "elasticsearch": {
                    "host": "localhost",
                    "port": 9200,
                    "username": "admin",
                    "password": "admin"
                },
                "wazuh": {
                    "host": "localhost",
                    "port": 55000,
                    "username": "admin",
                    "password": "admin"
                },
                "graylog": {
                    "host": "localhost",
                    "port": 9000,
                    "username": "admin",
                    "password": "admin"
                }
            }
    
    def connect_elasticsearch(self):
        """Connect to Elasticsearch"""
        try:
            es = elasticsearch.Elasticsearch(
                [{'host': self.config['elasticsearch']['host'], 
                  'port': self.config['elasticsearch']['port']}],
                http_auth=(self.config['elasticsearch']['username'], 
                          self.config['elasticsearch']['password']),
                verify_certs=False
            )
            return es
        except Exception as e:
            print(f"❌ Failed to connect to Elasticsearch: {e}")
            return None
    
    def connect_wazuh_api(self):
        """Connect to Wazuh API"""
        try:
            base_url = f"https://{self.config['wazuh']['host']}:{self.config['wazuh']['port']}"
            auth = (self.config['wazuh']['username'], self.config['wazuh']['password'])
            return {"base_url": base_url, "auth": auth}
        except Exception as e:
            print(f"❌ Failed to connect to Wazuh API: {e}")
            return None
    
    def connect_graylog_api(self):
        """Connect to Graylog API"""
        try:
            base_url = f"http://{self.config['graylog']['host']}:{self.config['graylog']['port']}/api"
            auth = (self.config['graylog']['username'], self.config['graylog']['password'])
            return {"base_url": base_url, "auth": auth}
        except Exception as e:
            print(f"❌ Failed to connect to Graylog API: {e}")
            return None

class HuntingQueries:
    """
    Pre-built threat hunting queries and techniques
    """
    
    def __init__(self, notebook: ThreatHuntingNotebook):
        self.notebook = notebook
        self.es = notebook.es_client
    
    def suspicious_login_patterns(self, time_range: str = "24h") -> pd.DataFrame:
        """Hunt for suspicious login patterns"""
        print("🔍 Hunting for suspicious login patterns...")
        
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"match": {"event.category": "authentication"}},
                        {"range": {"@timestamp": {"gte": f"now-{time_range}"}}}
                    ]
                }
            },
            "aggs": {
                "users": {
                    "terms": {"field": "user.name.keyword", "size": 100},
                    "aggs": {
                        "failed_logins": {
                            "filter": {"term": {"event.outcome": "failure"}}
                        },
                        "success_logins": {
                            "filter": {"term": {"event.outcome": "success"}}
                        },
                        "unique_ips": {
                            "cardinality": {"field": "source.ip"}
                        }
                    }
                }
            }
        }
        
        try:
            response = self.es.search(index="wazuh-alerts-*", body=query)
            
            data = []
            for bucket in response['aggregations']['users']['buckets']:
                user = bucket['key']
                total_attempts = bucket['doc_count']
                failed = bucket['failed_logins']['doc_count']
                success = bucket['success_logins']['doc_count']
                unique_ips = bucket['unique_ips']['value']
                
                # Calculate risk score
                risk_score = (failed / total_attempts * 50) + (unique_ips * 10)
                
                data.append({
                    'user': user,
                    'total_attempts': total_attempts,
                    'failed_logins': failed,
                    'successful_logins': success,
                    'unique_ips': unique_ips,
                    'failure_rate': failed / total_attempts if total_attempts > 0 else 0,
                    'risk_score': risk_score
                })
            
            df = pd.DataFrame(data)
            df = df.sort_values('risk_score', ascending=False)
            
            # Highlight high-risk users
            high_risk = df[df['risk_score'] > 30]
            if not high_risk.empty:
                print(f"⚠️  Found {len(high_risk)} high-risk users:")
                for _, user in high_risk.iterrows():
                    print(f"   👤 {user['user']}: {user['failed_logins']} failed logins from {user['unique_ips']} IPs")
            
            return df
            
        except Exception as e:
            print(f"❌ Error executing query: {e}")
            return pd.DataFrame()
    
    def lateral_movement_detection(self, time_range: str = "24h") -> pd.DataFrame:
        """Hunt for lateral movement indicators"""
        print("🔍 Hunting for lateral movement patterns...")
        
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"terms": {"event.category": ["network", "process"]}},
                        {"range": {"@timestamp": {"gte": f"now-{time_range}"}}}
                    ]
                }
            },
            "aggs": {
                "source_ips": {
                    "terms": {"field": "source.ip", "size": 100},
                    "aggs": {
                        "unique_destinations": {
                            "cardinality": {"field": "destination.ip"}
                        },
                        "unique_ports": {
                            "cardinality": {"field": "destination.port"}
                        },
                        "protocols": {
                            "terms": {"field": "network.protocol.keyword"}
                        }
                    }
                }
            }
        }
        
        try:
            response = self.es.search(index="wazuh-alerts-*", body=query)
            
            data = []
            for bucket in response['aggregations']['source_ips']['buckets']:
                source_ip = bucket['key']
                connections = bucket['doc_count']
                unique_destinations = bucket['unique_destinations']['value']
                unique_ports = bucket['unique_ports']['value']
                
                # Calculate lateral movement score
                lateral_score = (unique_destinations * 5) + (unique_ports * 2) + (connections * 0.1)
                
                data.append({
                    'source_ip': source_ip,
                    'total_connections': connections,
                    'unique_destinations': unique_destinations,
                    'unique_ports': unique_ports,
                    'lateral_movement_score': lateral_score
                })
            
            df = pd.DataFrame(data)
            df = df.sort_values('lateral_movement_score', ascending=False)
            
            # Highlight suspicious activity
            suspicious = df[df['lateral_movement_score'] > 50]
            if not suspicious.empty:
                print(f"⚠️  Found {len(suspicious)} IPs with suspicious lateral movement:")
                for _, row in suspicious.iterrows():
                    print(f"   🌐 {row['source_ip']}: {row['unique_destinations']} destinations, {row['unique_ports']} ports")
            
            return df
            
        except Exception as e:
            print(f"❌ Error executing query: {e}")
            return pd.DataFrame()
    
    def data_exfiltration_hunt(self, time_range: str = "24h", threshold_mb: int = 100) -> pd.DataFrame:
        """Hunt for potential data exfiltration"""
        print("🔍 Hunting for data exfiltration patterns...")
        
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"exists": {"field": "network.bytes"}},
                        {"range": {"@timestamp": {"gte": f"now-{time_range}"}}},
                        {"range": {"network.bytes": {"gte": threshold_mb * 1024 * 1024}}}
                    ]
                }
            },
            "aggs": {
                "users": {
                    "terms": {"field": "user.name.keyword", "size": 50},
                    "aggs": {
                        "total_bytes": {
                            "sum": {"field": "network.bytes"}
                        },
                        "destinations": {
                            "terms": {"field": "destination.ip", "size": 10}
                        }
                    }
                }
            }
        }
        
        try:
            response = self.es.search(index="wazuh-alerts-*", body=query)
            
            data = []
            for bucket in response['aggregations']['users']['buckets']:
                user = bucket['key']
                total_bytes = bucket['total_bytes']['value']
                total_mb = total_bytes / (1024 * 1024)
                
                destinations = [dest['key'] for dest in bucket['destinations']['buckets']]
                
                data.append({
                    'user': user,
                    'total_bytes': total_bytes,
                    'total_mb': total_mb,
                    'destinations': destinations,
                    'destination_count': len(destinations)
                })
            
            df = pd.DataFrame(data)
            df = df.sort_values('total_mb', ascending=False)
            
            if not df.empty:
                print(f"⚠️  Found {len(df)} users with high data transfer:")
                for _, row in df.head(5).iterrows():
                    print(f"   👤 {row['user']}: {row['total_mb']:.2f} MB to {row['destination_count']} destinations")
            
            return df
            
        except Exception as e:
            print(f"❌ Error executing query: {e}")
            return pd.DataFrame()
    
    def privilege_escalation_hunt(self, time_range: str = "24h") -> pd.DataFrame:
        """Hunt for privilege escalation attempts"""
        print("🔍 Hunting for privilege escalation patterns...")
        
        escalation_keywords = [
            "sudo", "su", "runas", "privilege", "escalation", 
            "admin", "administrator", "root", "system"
        ]
        
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"range": {"@timestamp": {"gte": f"now-{time_range}"}}},
                        {"bool": {
                            "should": [
                                {"terms": {"event.category": ["process", "authentication"]}},
                                {"multi_match": {
                                    "query": " ".join(escalation_keywords),
                                    "fields": ["message", "process.command_line", "event.action"]
                                }}
                            ]
                        }}
                    ]
                }
            },
            "aggs": {
                "users": {
                    "terms": {"field": "user.name.keyword", "size": 50},
                    "aggs": {
                        "processes": {
                            "terms": {"field": "process.name.keyword", "size": 10}
                        },
                        "hosts": {
                            "terms": {"field": "host.name.keyword", "size": 10}
                        }
                    }
                }
            }
        }
        
        try:
            response = self.es.search(index="wazuh-alerts-*", body=query)
            
            data = []
            for bucket in response['aggregations']['users']['buckets']:
                user = bucket['key']
                attempts = bucket['doc_count']
                
                processes = [proc['key'] for proc in bucket['processes']['buckets']]
                hosts = [host['key'] for host in bucket['hosts']['buckets']]
                
                data.append({
                    'user': user,
                    'escalation_attempts': attempts,
                    'processes': processes,
                    'affected_hosts': hosts,
                    'process_count': len(processes),
                    'host_count': len(hosts)
                })
            
            df = pd.DataFrame(data)
            df = df.sort_values('escalation_attempts', ascending=False)
            
            if not df.empty:
                print(f"⚠️  Found {len(df)} users with privilege escalation attempts:")
                for _, row in df.head(5).iterrows():
                    print(f"   👤 {row['user']}: {row['escalation_attempts']} attempts on {row['host_count']} hosts")
            
            return df
            
        except Exception as e:
            print(f"❌ Error executing query: {e}")
            return pd.DataFrame()

class HuntingVisualizations:
    """
    Visualization tools for threat hunting
    """
    
    def __init__(self, notebook: ThreatHuntingNotebook):
        self.notebook = notebook
    
    def create_timeline_chart(self, df: pd.DataFrame, time_col: str, value_col: str, title: str):
        """Create interactive timeline chart"""
        fig = px.line(df, x=time_col, y=value_col, title=title)
        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Count",
            hovermode='x unified'
        )
        return fig
    
    def create_network_graph(self, connections_df: pd.DataFrame):
        """Create network graph for connection analysis"""
        import networkx as nx
        
        G = nx.from_pandas_edgelist(
            connections_df, 
            source='source_ip', 
            target='destination_ip',
            edge_attr='connection_count'
        )
        
        pos = nx.spring_layout(G)
        
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines'
        )
        
        node_x = []
        node_y = []
        node_text = []
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=node_text,
            textposition="middle center",
            marker=dict(
                showscale=True,
                colorscale='YlOrRd',
                reversescale=True,
                color=[],
                size=10,
                colorbar=dict(
                    thickness=15,
                    len=0.5,
                    x=1.1,
                    title="Node Connections"
                ),
                line=dict(width=2)
            )
        )
        
        # Color nodes by number of connections
        node_adjacencies = []
        for node in G.nodes():
            node_adjacencies.append(len(list(G.neighbors(node))))
        
        node_trace.marker.color = node_adjacencies
        
        fig = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(
                           title='Network Connection Graph',
                           titlefont_size=16,
                           showlegend=False,
                           hovermode='closest',
                           margin=dict(b=20,l=5,r=5,t=40),
                           annotations=[ dict(
                               text="Network connections between IPs",
                               showarrow=False,
                               xref="paper", yref="paper",
                               x=0.005, y=-0.002,
                               xanchor='left', yanchor='bottom',
                               font=dict(color="#888", size=12)
                           )],
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                       ))
        
        return fig
    
    def create_risk_heatmap(self, df: pd.DataFrame, x_col: str, y_col: str, value_col: str):
        """Create risk heatmap"""
        pivot_df = df.pivot_table(values=value_col, index=y_col, columns=x_col, aggfunc='mean')
        
        fig = px.imshow(
            pivot_df,
            title=f"Risk Heatmap: {value_col} by {x_col} and {y_col}",
            color_continuous_scale='Reds'
        )
        
        return fig
    
    def create_anomaly_dashboard(self, anomaly_data: dict):
        """Create comprehensive anomaly dashboard"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Login Anomalies', 'Network Anomalies', 
                          'Process Anomalies', 'Data Transfer Anomalies'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Login anomalies
        if 'login_anomalies' in anomaly_data:
            fig.add_trace(
                go.Scatter(
                    x=anomaly_data['login_anomalies']['timestamp'],
                    y=anomaly_data['login_anomalies']['score'],
                    mode='markers',
                    name='Login Anomalies',
                    marker=dict(color='red', size=8)
                ),
                row=1, col=1
            )
        
        # Network anomalies
        if 'network_anomalies' in anomaly_data:
            fig.add_trace(
                go.Scatter(
                    x=anomaly_data['network_anomalies']['timestamp'],
                    y=anomaly_data['network_anomalies']['score'],
                    mode='markers',
                    name='Network Anomalies',
                    marker=dict(color='orange', size=8)
                ),
                row=1, col=2
            )
        
        fig.update_layout(
            title_text="Security Anomaly Dashboard",
            showlegend=True,
            height=600
        )
        
        return fig

class InteractiveHunting:
    """
    Interactive widgets for threat hunting
    """
    
    def __init__(self, hunting_queries: HuntingQueries, visualizations: HuntingVisualizations):
        self.queries = hunting_queries
        self.viz = visualizations
    
    def create_time_range_selector(self):
        """Create time range selector widget"""
        return widgets.Dropdown(
            options=['1h', '6h', '12h', '24h', '7d', '30d'],
            value='24h',
            description='Time Range:',
            style={'description_width': 'initial'}
        )
    
    def create_hunt_selector(self):
        """Create hunt type selector widget"""
        return widgets.Dropdown(
            options=[
                ('Suspicious Logins', 'login'),
                ('Lateral Movement', 'lateral'),
                ('Data Exfiltration', 'exfiltration'),
                ('Privilege Escalation', 'privilege')
            ],
            value='login',
            description='Hunt Type:',
            style={'description_width': 'initial'}
        )
    
    def create_interactive_dashboard(self):
        """Create interactive hunting dashboard"""
        time_selector = self.create_time_range_selector()
        hunt_selector = self.create_hunt_selector()
        run_button = widgets.Button(description="Run Hunt", button_style='primary')
        output = widgets.Output()
        
        def run_hunt(b):
            with output:
                output.clear_output()
                
                time_range = time_selector.value
                hunt_type = hunt_selector.value
                
                print(f"🔍 Running {hunt_type} hunt for {time_range}...")
                
                if hunt_type == 'login':
                    df = self.queries.suspicious_login_patterns(time_range)
                    if not df.empty:
                        fig = px.bar(df.head(10), x='user', y='risk_score', 
                                   title='Top 10 Risky Users')
                        fig.show()
                        display(df.head(10))
                
                elif hunt_type == 'lateral':
                    df = self.queries.lateral_movement_detection(time_range)
                    if not df.empty:
                        fig = px.scatter(df, x='unique_destinations', y='unique_ports',
                                       size='total_connections', hover_data=['source_ip'],
                                       title='Lateral Movement Analysis')
                        fig.show()
                        display(df.head(10))
                
                elif hunt_type == 'exfiltration':
                    df = self.queries.data_exfiltration_hunt(time_range)
                    if not df.empty:
                        fig = px.bar(df.head(10), x='user', y='total_mb',
                                   title='Data Transfer by User (MB)')
                        fig.show()
                        display(df.head(10))
                
                elif hunt_type == 'privilege':
                    df = self.queries.privilege_escalation_hunt(time_range)
                    if not df.empty:
                        fig = px.bar(df.head(10), x='user', y='escalation_attempts',
                                   title='Privilege Escalation Attempts')
                        fig.show()
                        display(df.head(10))
        
        run_button.on_click(run_hunt)
        
        dashboard = widgets.VBox([
            widgets.HTML("<h2>🔍 Interactive Threat Hunting Dashboard</h2>"),
            widgets.HBox([time_selector, hunt_selector, run_button]),
            output
        ])
        
        return dashboard

# Notebook initialization function
def initialize_threat_hunting():
    """Initialize threat hunting environment in Jupyter notebook"""
    
    # Display welcome message
    display(HTML("""
    <div style="background-color: #f0f8ff; padding: 20px; border-radius: 10px; border-left: 5px solid #4CAF50;">
        <h1>🔍 SIEM Platform Threat Hunting Notebook</h1>
        <p><strong>Welcome to the interactive threat hunting environment!</strong></p>
        <p>This notebook provides advanced threat hunting capabilities including:</p>
        <ul>
            <li>🔍 Pre-built hunting queries for common attack patterns</li>
            <li>📊 Interactive visualizations and dashboards</li>
            <li>🤖 Machine learning-based anomaly detection</li>
            <li>🌐 Network analysis and graph visualizations</li>
            <li>📈 Time series analysis and trend detection</li>
        </ul>
        <p><em>Get started by running the cells below to initialize your hunting environment.</em></p>
    </div>
    """))
    
    # Initialize components
    notebook = ThreatHuntingNotebook()
    queries = HuntingQueries(notebook)
    visualizations = HuntingVisualizations(notebook)
    interactive = InteractiveHunting(queries, visualizations)
    
    # Create interactive dashboard
    dashboard = interactive.create_interactive_dashboard()
    
    return {
        'notebook': notebook,
        'queries': queries,
        'visualizations': visualizations,
        'interactive': interactive,
        'dashboard': dashboard
    }

# Example hunting notebook cells
def create_example_notebook():
    """Create example notebook with hunting scenarios"""
    
    notebook_content = """
# SIEM Platform Threat Hunting Notebook

## Setup and Initialization

```python
# Initialize threat hunting environment
hunting_env = initialize_threat_hunting()
notebook = hunting_env['notebook']
queries = hunting_env['queries']
viz = hunting_env['visualizations']
dashboard = hunting_env['dashboard']

# Display interactive dashboard
display(dashboard)
```

## Hunt 1: Suspicious Login Patterns

```python
# Hunt for suspicious login patterns
login_df = queries.suspicious_login_patterns(time_range="24h")

# Visualize results
if not login_df.empty:
    fig = px.bar(login_df.head(10), x='user', y='risk_score', 
                title='Top 10 Users by Risk Score')
    fig.show()
    
    # Display detailed results
    display(login_df.head(10))
```

## Hunt 2: Lateral Movement Detection

```python
# Hunt for lateral movement indicators
lateral_df = queries.lateral_movement_detection(time_range="24h")

# Create network visualization
if not lateral_df.empty:
    # Prepare connection data
    connections = []
    for _, row in lateral_df.iterrows():
        connections.append({
            'source_ip': row['source_ip'],
            'destination_ip': f"dest_{row['unique_destinations']}",
            'connection_count': row['total_connections']
        })
    
    conn_df = pd.DataFrame(connections)
    network_fig = viz.create_network_graph(conn_df)
    network_fig.show()
```

## Hunt 3: Data Exfiltration Analysis

```python
# Hunt for potential data exfiltration
exfil_df = queries.data_exfiltration_hunt(time_range="24h", threshold_mb=50)

# Visualize data transfers
if not exfil_df.empty:
    fig = px.treemap(exfil_df, path=['user'], values='total_mb',
                    title='Data Transfer Volume by User')
    fig.show()
    
    # Time series analysis
    # (Additional code for time series analysis would go here)
```

## Hunt 4: Privilege Escalation Detection

```python
# Hunt for privilege escalation attempts
priv_df = queries.privilege_escalation_hunt(time_range="24h")

# Create risk heatmap
if not priv_df.empty:
    # Prepare data for heatmap
    heatmap_data = priv_df.copy()
    heatmap_data['hour'] = pd.to_datetime(heatmap_data.get('timestamp', pd.Timestamp.now())).dt.hour
    
    fig = viz.create_risk_heatmap(heatmap_data, 'hour', 'user', 'escalation_attempts')
    fig.show()
```

## Custom Hunt: Build Your Own Query

```python
# Custom Elasticsearch query
custom_query = {
    "query": {
        "bool": {
            "must": [
                {"range": {"@timestamp": {"gte": "now-1h"}}},
                # Add your custom query conditions here
            ]
        }
    }
}

# Execute custom query
try:
    response = notebook.es_client.search(index="wazuh-alerts-*", body=custom_query)
    print(f"Found {response['hits']['total']['value']} results")
    
    # Process and visualize results
    # (Add your custom analysis code here)
    
except Exception as e:
    print(f"Error executing custom query: {e}")
```

## Threat Intelligence Integration

```python
# Integrate with threat intelligence feeds
def check_iocs(ip_list):
    \"\"\"Check IPs against threat intelligence\"\"\"
    # This would integrate with your threat intel feeds
    # For example: MISP, OpenCTI, etc.
    pass

# Example usage
suspicious_ips = lateral_df['source_ip'].unique()
ioc_results = check_iocs(suspicious_ips)
```

## Export Results

```python
# Export hunting results
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Save to CSV
login_df.to_csv(f"hunt_results_login_{timestamp}.csv", index=False)
lateral_df.to_csv(f"hunt_results_lateral_{timestamp}.csv", index=False)

# Generate report
report = f\"\"\"
# Threat Hunting Report - {timestamp}

## Summary
- Suspicious logins: {len(login_df)} users analyzed
- Lateral movement: {len(lateral_df)} source IPs analyzed
- High-risk findings: {len(login_df[login_df['risk_score'] > 30])} users

## Recommendations
1. Investigate high-risk users immediately
2. Implement additional monitoring for lateral movement
3. Review and update security policies

Generated by SIEM Platform Threat Hunting Notebook
\"\"\"

with open(f"threat_hunt_report_{timestamp}.md", "w") as f:
    f.write(report)

print(f"Results exported with timestamp: {timestamp}")
```
"""
    
    return notebook_content

if __name__ == "__main__":
    # Create example configuration file
    config = {
        "elasticsearch": {
            "host": "localhost",
            "port": 9200,
            "username": "admin",
            "password": "admin"
        },
        "wazuh": {
            "host": "localhost",
            "port": 55000,
            "username": "admin",
            "password": "admin"
        },
        "graylog": {
            "host": "localhost",
            "port": 9000,
            "username": "admin",
            "password": "admin"
        }
    }
    
    with open("hunting_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print("Threat hunting notebook module created successfully!")
    print("Configuration file 'hunting_config.json' created.")
    print("Use 'initialize_threat_hunting()' in your Jupyter notebook to get started.")

