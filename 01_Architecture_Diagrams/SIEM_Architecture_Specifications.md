# The AfCyber SIEM Platform Architecture Specifications

## The AfCyber Single-Node Deployment Architecture

### Overview
The single-node deployment provides a complete AfCyber SIEM platform implementation on a single Proxmox virtual machine, designed for small to medium organizations, development environments, or proof-of-concept implementations.

### The AfCyber SIEM Architecture Components

#### The AfCyber Web Interface Layer (Top Tier)
- **Grafana Dashboard** (Port 3000)
  - Executive dashboards and KPI visualization
  - SOC operations monitoring
  - Threat hunting analytics interface
  - Custom dashboard creation and management

- **Graylog Web UI** (Port 9000)
  - Log search and analysis interface
  - Stream management and configuration
  - Alert rule configuration
  - User and permission management

- **TheHive Case Management** (Port 9001)
  - Incident response workflow management
  - Case creation and tracking
  - Evidence collection and analysis
  - Collaboration and reporting tools

- **Wazuh Dashboard** (Port 443)
  - Agent management and monitoring
  - Rule and decoder configuration
  - Compliance reporting
  - File integrity monitoring

#### The AfCyber Core Services Layer (Middle Tier)
- **Wazuh Manager + Agents**
  - Real-time log collection and analysis
  - File integrity monitoring (FIM)
  - Rootkit and malware detection
  - Security configuration assessment
  - Custom rule engine for threat detection

- **Graylog Server + Pipelines**
  - Centralized log management and processing
  - Message parsing and enrichment
  - Stream processing and routing
  - Alert generation and notification
  - Search and analytics engine

- **TheHive + Cortex**
  - Structured incident response workflows
  - Case management and tracking
  - Observable analysis and enrichment
  - Automated response actions
  - Integration with external tools

- **OpenCTI + MISP**
  - Threat intelligence management
  - Indicator of Compromise (IoC) processing
  - Threat actor and campaign tracking
  - Intelligence sharing and collaboration
  - Custom intelligence feed integration

#### The AfCyber Data Storage Layer (Bottom Tier)
- **Elasticsearch Cluster**
  - Primary search and analytics engine
  - Log data indexing and storage
  - Real-time search capabilities
  - Aggregation and analytics processing

- **Redis Cache**
  - Session management and caching
  - Real-time data processing
  - Message queuing and pub/sub
  - Performance optimization

- **Cassandra Database**
  - TheHive case and observable storage
  - High-availability data persistence
  - Scalable NoSQL data management
  - Backup and recovery support

### External Connections
- **Customer Endpoints**: Wazuh agents and syslog forwarding
- **Network Devices**: Syslog and SNMP data collection
- **Cloud Services**: API-based log collection and threat intelligence feeds

### The AfCyber Resource Specifications
- **CPU**: 32 vCPU (minimum 16 vCPU)
- **Memory**: 64 GB RAM (minimum 32 GB)
- **Storage**: 1 TB SSD (minimum 500 GB)
- **Network**: 1 Gbps connection
- **Performance**: 10,000 events/second, 1,000 endpoints

---

## The AfCyber SIEM Multi-Tenant SaaS Deployment Architecture

### Overview of the AfCyber SIEM Platform
The AfCyber SIEM multi-tenant deployment offers enterprise-grade capabilities, suitable for managed security service providers, large enterprises, or organizations that require strict data isolation with shared infrastructure efficiency.

### The AfCyber SIEM Architecture Components

#### Load Balancer & API Gateway (Entry Point)
- **Load Balancer with Tenant Routing**
  - Intelligent traffic distribution
  - SSL termination and certificate management
  - Health checking and failover
  - Rate limiting and DDoS protection
  - Tenant-based routing and isolation

#### Control Plane (Management Layer)
- **Management Console**
  - Centralized platform administration
  - Tenant lifecycle management
  - Resource allocation and monitoring
  - Configuration management
  - User and access control

- **Tenant Provisioning System**
  - Automated tenant onboarding
  - Resource allocation and configuration
  - Network isolation setup
  - Service deployment automation
  - Template-based provisioning

- **Billing System**
  - Usage metering and tracking
  - Automated billing and invoicing
  - Resource consumption monitoring
  - Cost allocation and reporting
  - Payment processing integration

- **Monitoring & Analytics**
  - Platform health monitoring
  - Performance metrics collection
  - Capacity planning and optimization
  - SLA monitoring and reporting
  - Alerting and notification

#### Isolated Tenant Environments
Each tenant receives dedicated, isolated resources:

- **Tenant-Specific Services**
  - Dedicated Wazuh manager and agents
  - Isolated Graylog instance with custom pipelines
  - Private TheHive case management
  - Tenant-specific threat intelligence feeds

- **Network Isolation**
  - VLAN-based network separation (VLAN 100, 200, 300, etc.)
  - Dedicated IP address ranges
  - Firewall rules and access controls
  - Encrypted inter-tenant communication

- **Data Isolation**
  - Separate databases per tenant
  - Encrypted data storage
  - Isolated backup and recovery
  - Compliance-specific data handling

#### Shared Infrastructure Layer
- **Proxmox Cluster (3+ Nodes)**
  - High-availability virtualization platform
  - Live migration and failover
  - Distributed resource management
  - Centralized cluster management

- **Ceph Distributed Storage**
  - Scalable, fault-tolerant storage
  - Automatic data replication
  - Performance optimization
  - Backup and disaster recovery

- **SDN Networking & VLANs**
  - Software-defined networking
  - Dynamic VLAN allocation
  - Network policy enforcement
  - Traffic monitoring and analysis

#### Shared Services
- **Threat Intelligence Feeds**
  - Centralized threat intelligence processing
  - Multi-source intelligence aggregation
  - Custom intelligence feed management
  - Real-time indicator updates

- **ML Analytics Engine**
  - Shared machine learning capabilities
  - Anomaly detection algorithms
  - Behavioral analysis models
  - Predictive analytics processing

- **Backup Systems**
  - Centralized backup management
  - Automated backup scheduling
  - Disaster recovery capabilities
  - Compliance-specific retention

### Resource Specifications
- **CPU**: 128+ vCPU across cluster (scalable)
- **Memory**: 256+ GB RAM across cluster (scalable)
- **Storage**: 10+ TB distributed storage (scalable)
- **Network**: 10 Gbps with redundancy
- **Performance**: 100,000+ events/second per tenant, unlimited tenants

### Tenant Isolation Features
- **Network Isolation**: Complete VLAN separation with firewall rules
- **Data Isolation**: Encrypted, tenant-specific databases and storage
- **Compute Isolation**: Dedicated CPU and memory allocation
- **Access Isolation**: Role-based access control with tenant boundaries

### Scalability Features
- **Horizontal Scaling**: Add nodes to cluster for increased capacity
- **Vertical Scaling**: Increase resources per tenant as needed
- **Auto-Scaling**: Automatic resource allocation based on demand
- **Load Distribution**: Intelligent workload distribution across cluster

### High Availability Features
- **Redundancy**: Multiple nodes with failover capabilities
- **Live Migration**: Zero-downtime maintenance and updates
- **Backup and Recovery**: Automated backup with point-in-time recovery
- **Monitoring**: Comprehensive health monitoring with alerting

---

## AfCyber SIEM Deployment Comparison

| Feature | Single-Node | Multi-Tenant |
|---------|-------------|--------------|
| **Target Use Case** | SME, Labs, PoC | Enterprise, MSP, SaaS |
| **Tenant Support** | Single organization | Unlimited tenants |
| **Resource Requirements** | 32 vCPU, 64GB RAM | 128+ vCPU, 256+ GB RAM |
| **Scalability** | Vertical only | Horizontal + Vertical |
| **High Availability** | Single point of failure | Cluster redundancy |
| **Data Isolation** | Application-level | Infrastructure-level |
| **Management Complexity** | Low | Medium to High |
| **Cost** | Low | Medium (shared infrastructure) |
| **Performance** | 10K events/sec | 100K+ events/sec per tenant |

Both architectures provide comprehensive SIEM capabilities while addressing different organizational needs and scale requirements. The AfCyber SIEM single-node deployment offers simplicity and cost-effectiveness, while the AfCyber SIEM multi-tenant deployment provides enterprise-grade scalability and isolation.

---Dr.J.
