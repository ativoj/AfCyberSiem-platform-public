#!/usr/bin/env python3
"""
SIEM Platform REST API Integration Module

This module provides REST API endpoints for external tool integration
including ServiceNow, Slack, PagerDuty, and other SOAR platforms.
"""

from flask import Flask, request, jsonify, abort
from flask_restx import Api, Resource, fields, Namespace
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import jwt
import hashlib
import hmac
import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio
import aiohttp
from dataclasses import dataclass, asdict
import redis
import elasticsearch
from functools import wraps
import os
from werkzeug.security import check_password_hash, generate_password_hash

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-change-this')

# Initialize extensions
CORS(app)
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Initialize API
api = Api(
    app,
    version='1.0',
    title='SIEM Platform API',
    description='REST API for SIEM Platform external integrations',
    doc='/docs/'
)

# Redis client for caching and rate limiting
redis_client = redis.Redis(
    host=os.environ.get('REDIS_HOST', 'localhost'),
    port=int(os.environ.get('REDIS_PORT', 6379)),
    db=int(os.environ.get('REDIS_DB', 0))
)

# Elasticsearch client
es_client = elasticsearch.Elasticsearch(
    [{'host': os.environ.get('ES_HOST', 'localhost'), 
      'port': int(os.environ.get('ES_PORT', 9200))}],
    http_auth=(os.environ.get('ES_USER', 'admin'), 
               os.environ.get('ES_PASS', 'admin')),
    verify_certs=False
)

@dataclass
class Alert:
    """Alert data structure"""
    id: str
    timestamp: datetime
    severity: str
    title: str
    description: str
    source: str
    affected_assets: List[str]
    indicators: Dict[str, Any]
    status: str = "open"
    assigned_to: Optional[str] = None
    tags: List[str] = None

@dataclass
class Incident:
    """Incident data structure"""
    id: str
    title: str
    description: str
    severity: str
    status: str
    created_at: datetime
    updated_at: datetime
    assigned_to: Optional[str]
    alerts: List[str]
    timeline: List[Dict[str, Any]]

# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            current_user = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

# API Models
alert_model = api.model('Alert', {
    'id': fields.String(required=True, description='Alert ID'),
    'timestamp': fields.DateTime(required=True, description='Alert timestamp'),
    'severity': fields.String(required=True, description='Alert severity', enum=['low', 'medium', 'high', 'critical']),
    'title': fields.String(required=True, description='Alert title'),
    'description': fields.String(required=True, description='Alert description'),
    'source': fields.String(required=True, description='Alert source'),
    'affected_assets': fields.List(fields.String, description='Affected assets'),
    'indicators': fields.Raw(description='Threat indicators'),
    'status': fields.String(description='Alert status', enum=['open', 'investigating', 'resolved', 'false_positive']),
    'assigned_to': fields.String(description='Assigned analyst'),
    'tags': fields.List(fields.String, description='Alert tags')
})

incident_model = api.model('Incident', {
    'id': fields.String(required=True, description='Incident ID'),
    'title': fields.String(required=True, description='Incident title'),
    'description': fields.String(required=True, description='Incident description'),
    'severity': fields.String(required=True, description='Incident severity'),
    'status': fields.String(required=True, description='Incident status'),
    'created_at': fields.DateTime(description='Creation timestamp'),
    'updated_at': fields.DateTime(description='Last update timestamp'),
    'assigned_to': fields.String(description='Assigned analyst'),
    'alerts': fields.List(fields.String, description='Associated alert IDs'),
    'timeline': fields.List(fields.Raw, description='Incident timeline')
})

# Namespaces
auth_ns = Namespace('auth', description='Authentication operations')
alerts_ns = Namespace('alerts', description='Alert management operations')
incidents_ns = Namespace('incidents', description='Incident management operations')
integrations_ns = Namespace('integrations', description='External integrations')
threat_intel_ns = Namespace('threat-intel', description='Threat intelligence operations')

api.add_namespace(auth_ns, path='/api/v1/auth')
api.add_namespace(alerts_ns, path='/api/v1/alerts')
api.add_namespace(incidents_ns, path='/api/v1/incidents')
api.add_namespace(integrations_ns, path='/api/v1/integrations')
api.add_namespace(threat_intel_ns, path='/api/v1/threat-intel')

# Authentication endpoints
@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.expect(api.model('LoginCredentials', {
        'username': fields.String(required=True),
        'password': fields.String(required=True)
    }))
    def post(self):
        """Authenticate user and return JWT token"""
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        # Validate credentials (implement your authentication logic)
        if self.validate_credentials(username, password):
            token = jwt.encode({
                'user_id': username,
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, app.config['JWT_SECRET_KEY'], algorithm='HS256')
            
            return {'token': token, 'expires_in': 86400}
        
        return {'message': 'Invalid credentials'}, 401
    
    def validate_credentials(self, username: str, password: str) -> bool:
        """Validate user credentials"""
        # Implement your authentication logic here
        # This could integrate with LDAP, database, etc.
        return username == 'admin' and password == 'admin'  # Demo only

# Alert management endpoints
@alerts_ns.route('/')
class AlertList(Resource):
    @token_required
    @alerts_ns.marshal_list_with(alert_model)
    @limiter.limit("100 per minute")
    def get(self, current_user):
        """Get list of alerts"""
        try:
            # Query parameters
            severity = request.args.get('severity')
            status = request.args.get('status')
            limit = int(request.args.get('limit', 100))
            offset = int(request.args.get('offset', 0))
            
            # Build Elasticsearch query
            query = {
                "query": {"bool": {"must": []}},
                "sort": [{"@timestamp": {"order": "desc"}}],
                "from": offset,
                "size": limit
            }
            
            if severity:
                query["query"]["bool"]["must"].append({"term": {"severity": severity}})
            if status:
                query["query"]["bool"]["must"].append({"term": {"status": status}})
            
            # Execute query
            response = es_client.search(index="siem-alerts-*", body=query)
            
            alerts = []
            for hit in response['hits']['hits']:
                source = hit['_source']
                alert = Alert(
                    id=hit['_id'],
                    timestamp=datetime.fromisoformat(source['@timestamp'].replace('Z', '+00:00')),
                    severity=source.get('severity', 'medium'),
                    title=source.get('title', ''),
                    description=source.get('description', ''),
                    source=source.get('source', ''),
                    affected_assets=source.get('affected_assets', []),
                    indicators=source.get('indicators', {}),
                    status=source.get('status', 'open'),
                    assigned_to=source.get('assigned_to'),
                    tags=source.get('tags', [])
                )
                alerts.append(asdict(alert))
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error fetching alerts: {e}")
            return {'message': 'Internal server error'}, 500
    
    @token_required
    @alerts_ns.expect(alert_model)
    @alerts_ns.marshal_with(alert_model)
    def post(self, current_user):
        """Create new alert"""
        try:
            data = request.get_json()
            
            # Create alert document
            alert_doc = {
                '@timestamp': datetime.utcnow().isoformat(),
                'severity': data.get('severity', 'medium'),
                'title': data['title'],
                'description': data['description'],
                'source': data['source'],
                'affected_assets': data.get('affected_assets', []),
                'indicators': data.get('indicators', {}),
                'status': 'open',
                'assigned_to': data.get('assigned_to'),
                'tags': data.get('tags', []),
                'created_by': current_user
            }
            
            # Index in Elasticsearch
            response = es_client.index(index="siem-alerts", body=alert_doc)
            alert_id = response['_id']
            
            # Send notifications
            self.send_alert_notifications(alert_doc, alert_id)
            
            alert_doc['id'] = alert_id
            return alert_doc, 201
            
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            return {'message': 'Internal server error'}, 500
    
    def send_alert_notifications(self, alert: Dict[str, Any], alert_id: str):
        """Send alert notifications to external systems"""
        try:
            # Send to Slack
            if alert['severity'] in ['high', 'critical']:
                self.send_slack_notification(alert, alert_id)
            
            # Send to PagerDuty for critical alerts
            if alert['severity'] == 'critical':
                self.send_pagerduty_alert(alert, alert_id)
            
        except Exception as e:
            logger.error(f"Error sending notifications: {e}")
    
    def send_slack_notification(self, alert: Dict[str, Any], alert_id: str):
        """Send alert to Slack"""
        webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
        if not webhook_url:
            return
        
        color = {
            'low': '#36a64f',
            'medium': '#ff9500',
            'high': '#ff0000',
            'critical': '#8b0000'
        }.get(alert['severity'], '#36a64f')
        
        payload = {
            "attachments": [{
                "color": color,
                "title": f"🚨 {alert['severity'].upper()} Alert: {alert['title']}",
                "text": alert['description'],
                "fields": [
                    {"title": "Source", "value": alert['source'], "short": True},
                    {"title": "Severity", "value": alert['severity'], "short": True},
                    {"title": "Alert ID", "value": alert_id, "short": True},
                    {"title": "Timestamp", "value": alert['@timestamp'], "short": True}
                ],
                "footer": "SIEM Platform",
                "ts": int(datetime.utcnow().timestamp())
            }]
        }
        
        requests.post(webhook_url, json=payload)
    
    def send_pagerduty_alert(self, alert: Dict[str, Any], alert_id: str):
        """Send alert to PagerDuty"""
        integration_key = os.environ.get('PAGERDUTY_INTEGRATION_KEY')
        if not integration_key:
            return
        
        payload = {
            "routing_key": integration_key,
            "event_action": "trigger",
            "dedup_key": alert_id,
            "payload": {
                "summary": f"{alert['severity'].upper()}: {alert['title']}",
                "source": alert['source'],
                "severity": alert['severity'],
                "custom_details": {
                    "description": alert['description'],
                    "affected_assets": alert['affected_assets'],
                    "indicators": alert['indicators']
                }
            }
        }
        
        requests.post("https://events.pagerduty.com/v2/enqueue", json=payload)

@alerts_ns.route('/<string:alert_id>')
class AlertDetail(Resource):
    @token_required
    @alerts_ns.marshal_with(alert_model)
    def get(self, current_user, alert_id):
        """Get specific alert"""
        try:
            response = es_client.get(index="siem-alerts", id=alert_id)
            source = response['_source']
            
            alert = Alert(
                id=alert_id,
                timestamp=datetime.fromisoformat(source['@timestamp'].replace('Z', '+00:00')),
                severity=source.get('severity', 'medium'),
                title=source.get('title', ''),
                description=source.get('description', ''),
                source=source.get('source', ''),
                affected_assets=source.get('affected_assets', []),
                indicators=source.get('indicators', {}),
                status=source.get('status', 'open'),
                assigned_to=source.get('assigned_to'),
                tags=source.get('tags', [])
            )
            
            return asdict(alert)
            
        except elasticsearch.NotFoundError:
            return {'message': 'Alert not found'}, 404
        except Exception as e:
            logger.error(f"Error fetching alert: {e}")
            return {'message': 'Internal server error'}, 500
    
    @token_required
    @alerts_ns.expect(api.model('AlertUpdate', {
        'status': fields.String(enum=['open', 'investigating', 'resolved', 'false_positive']),
        'assigned_to': fields.String(),
        'tags': fields.List(fields.String())
    }))
    def put(self, current_user, alert_id):
        """Update alert"""
        try:
            data = request.get_json()
            
            # Update document
            update_doc = {
                'doc': {
                    'updated_at': datetime.utcnow().isoformat(),
                    'updated_by': current_user
                }
            }
            
            if 'status' in data:
                update_doc['doc']['status'] = data['status']
            if 'assigned_to' in data:
                update_doc['doc']['assigned_to'] = data['assigned_to']
            if 'tags' in data:
                update_doc['doc']['tags'] = data['tags']
            
            es_client.update(index="siem-alerts", id=alert_id, body=update_doc)
            
            return {'message': 'Alert updated successfully'}
            
        except elasticsearch.NotFoundError:
            return {'message': 'Alert not found'}, 404
        except Exception as e:
            logger.error(f"Error updating alert: {e}")
            return {'message': 'Internal server error'}, 500

# ServiceNow integration
@integrations_ns.route('/servicenow/incidents')
class ServiceNowIntegration(Resource):
    @token_required
    def post(self, current_user):
        """Create ServiceNow incident from SIEM alert"""
        try:
            data = request.get_json()
            alert_id = data.get('alert_id')
            
            if not alert_id:
                return {'message': 'Alert ID is required'}, 400
            
            # Get alert details
            alert_response = es_client.get(index="siem-alerts", id=alert_id)
            alert = alert_response['_source']
            
            # Create ServiceNow incident
            incident_data = {
                'short_description': f"Security Alert: {alert['title']}",
                'description': alert['description'],
                'urgency': self.map_severity_to_urgency(alert['severity']),
                'impact': self.map_severity_to_impact(alert['severity']),
                'category': 'Security',
                'subcategory': 'Security Incident',
                'u_alert_id': alert_id,
                'u_alert_source': alert['source']
            }
            
            # Send to ServiceNow
            snow_response = self.create_servicenow_incident(incident_data)
            
            if snow_response:
                # Update alert with ServiceNow incident number
                es_client.update(
                    index="siem-alerts",
                    id=alert_id,
                    body={
                        'doc': {
                            'servicenow_incident': snow_response['number'],
                            'updated_at': datetime.utcnow().isoformat()
                        }
                    }
                )
                
                return {
                    'message': 'ServiceNow incident created successfully',
                    'incident_number': snow_response['number'],
                    'incident_sys_id': snow_response['sys_id']
                }
            else:
                return {'message': 'Failed to create ServiceNow incident'}, 500
                
        except Exception as e:
            logger.error(f"Error creating ServiceNow incident: {e}")
            return {'message': 'Internal server error'}, 500
    
    def map_severity_to_urgency(self, severity: str) -> str:
        """Map SIEM severity to ServiceNow urgency"""
        mapping = {
            'low': '3',
            'medium': '2',
            'high': '1',
            'critical': '1'
        }
        return mapping.get(severity, '3')
    
    def map_severity_to_impact(self, severity: str) -> str:
        """Map SIEM severity to ServiceNow impact"""
        mapping = {
            'low': '3',
            'medium': '2',
            'high': '1',
            'critical': '1'
        }
        return mapping.get(severity, '3')
    
    def create_servicenow_incident(self, incident_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create incident in ServiceNow"""
        try:
            snow_url = os.environ.get('SERVICENOW_URL')
            snow_user = os.environ.get('SERVICENOW_USER')
            snow_pass = os.environ.get('SERVICENOW_PASS')
            
            if not all([snow_url, snow_user, snow_pass]):
                logger.error("ServiceNow credentials not configured")
                return None
            
            url = f"{snow_url}/api/now/table/incident"
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            response = requests.post(
                url,
                json=incident_data,
                headers=headers,
                auth=(snow_user, snow_pass)
            )
            
            if response.status_code == 201:
                return response.json()['result']
            else:
                logger.error(f"ServiceNow API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error calling ServiceNow API: {e}")
            return None

# Threat intelligence endpoints
@threat_intel_ns.route('/iocs')
class ThreatIntelIOCs(Resource):
    @token_required
    def get(self, current_user):
        """Get threat intelligence indicators"""
        try:
            ioc_type = request.args.get('type')  # ip, domain, hash, etc.
            limit = int(request.args.get('limit', 100))
            
            # Query threat intel database
            query = {
                "query": {"bool": {"must": []}},
                "sort": [{"timestamp": {"order": "desc"}}],
                "size": limit
            }
            
            if ioc_type:
                query["query"]["bool"]["must"].append({"term": {"type": ioc_type}})
            
            response = es_client.search(index="threat-intel-*", body=query)
            
            iocs = []
            for hit in response['hits']['hits']:
                source = hit['_source']
                iocs.append({
                    'id': hit['_id'],
                    'type': source.get('type'),
                    'value': source.get('value'),
                    'confidence': source.get('confidence'),
                    'source': source.get('source'),
                    'tags': source.get('tags', []),
                    'timestamp': source.get('timestamp')
                })
            
            return {'iocs': iocs, 'total': len(iocs)}
            
        except Exception as e:
            logger.error(f"Error fetching IOCs: {e}")
            return {'message': 'Internal server error'}, 500
    
    @token_required
    def post(self, current_user):
        """Add new threat intelligence indicator"""
        try:
            data = request.get_json()
            
            ioc_doc = {
                'type': data['type'],
                'value': data['value'],
                'confidence': data.get('confidence', 'medium'),
                'source': data.get('source', 'manual'),
                'tags': data.get('tags', []),
                'timestamp': datetime.utcnow().isoformat(),
                'created_by': current_user
            }
            
            response = es_client.index(index="threat-intel", body=ioc_doc)
            
            return {
                'message': 'IOC added successfully',
                'id': response['_id']
            }, 201
            
        except Exception as e:
            logger.error(f"Error adding IOC: {e}")
            return {'message': 'Internal server error'}, 500

# Health check endpoint
@api.route('/health')
class HealthCheck(Resource):
    def get(self):
        """Health check endpoint"""
        try:
            # Check Elasticsearch
            es_health = es_client.cluster.health()
            
            # Check Redis
            redis_client.ping()
            
            return {
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'services': {
                    'elasticsearch': es_health['status'],
                    'redis': 'healthy'
                }
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }, 500

if __name__ == '__main__':
    # Development server
    app.run(host='0.0.0.0', port=5000, debug=True)

