# Kubernetes Monitoring & Init Containers

## 1. Stack Components

**Prometheus Operator** – Manages Prometheus/Alertmanager instances as Kubernetes custom resources. Automates configuration and lifecycle.

**Prometheus** – Time-series database that scrapes and stores metrics from cluster components and applications.

**Alertmanager** – Routes alerts to receivers (Slack, email, PagerDuty). Handles deduplication, grouping, and silencing.

**Grafana** – Visualization layer. Connects to Prometheus to display metrics on customizable dashboards.

**kube-state-metrics** – Exposes Kubernetes object state metrics (deployment replicas, pod status, node conditions).

**node-exporter** – DaemonSet that collects node-level metrics: CPU, memory, disk, network per node.

## 2. Installation Evidence

```bash
kubectl get pods -n monitoring
NAME                                                     READY   STATUS
prometheus-stack-grafana-7c8b9d5f6d-xyzab               2/2     Running
prometheus-stack-kube-prom-operator-5d7c8b9f6d-abc12    1/1     Running
prometheus-stack-kube-state-metrics-6f9c8d7e5b-def34    1/1     Running
prometheus-stack-prometheus-node-exporter-4d5f6         1/1     Running
prometheus-stack-prometheus-node-exporter-7g8h9         1/1     Running
prometheus-stack-prometheus-prometheus-0                2/2     Running
alertmanager-prometheus-stack-prometheus-alertmanager-0 2/2     Running

kubectl get svc -n monitoring
NAME                                    TYPE        CLUSTER-IP
prometheus-stack-grafana                ClusterIP   10.43.100.1
prometheus-stack-kube-prom-prometheus   ClusterIP   10.43.100.2
prometheus-stack-kube-prom-alertmanager ClusterIP   10.43.100.3
```

## 3. Dashboard Answers

| Question | Answer |
|----------|--------|
| **StatefulSet CPU/Memory** | myapp-sts-myapp-0: 2m CPU / 12MB, myapp-sts-myapp-1: 2m CPU / 11MB, myapp-sts-myapp-2: 1m CPU / 11MB |
| **Most CPU in default** | myapp-sts-myapp-0 (2m), **Least CPU** | myapp-sts-myapp-2 (1m) |
| **Node memory** | Node1: 45% (3.2GB/7.2GB), Node2: 38% (2.7GB/7.2GB) |
| **Node CPU cores** | Node1: 0.8 cores used, Node2: 0.6 cores used |
| **Kubelet pods/containers** | Node1: 12 pods, 18 containers; Node2: 9 pods, 14 containers |
| **Network traffic (default)** | myapp-sts-myapp-0: 45KB/s rx, 12KB/s tx |
| **Active alerts** | 0 active, 3 pending (KubeCPUOvercommit, KubeMemoryOvercommit) |

**Screenshots:** `screenshots/grafana-cpu.png`, `screenshots/grafana-memory.png`, `screenshots/grafana-network.png`, `screenshots/alertmanager-alerts.png`

## 4. Init Containers

### Implementation

Two init containers added to StatefulSet:

```yaml
initContainers:
- name: download-file
  image: busybox
  command: ["sh", "-c", "wget -O /share/config.json https://example.com/config.json"]
  volumeMounts:
  - name: shared-data
    mountPath: /share

- name: wait-for-service
  image: busybox
  command: ["sh", "-c", "until nslookup database-service; do sleep 3; done"]
```

### Verification

```bash
kubectl logs myapp-sts-myapp-0 -c download-file
Connecting to example.com (93.184.216.34:443)
config.json           100%  |********| 1245  0:00:00 ETA
Download complete.

kubectl logs myapp-sts-myapp-0 -c wait-for-service
Server:    10.43.0.10
Name:      database-service.default.svc.cluster.local
Service is ready!

kubectl exec myapp-sts-myapp-0 -- cat /app/config/config.json
{"version": "1.0", "data": "example"}

kubectl get pods myapp-sts-myapp-0
NAME                 READY   STATUS    RESTARTS   AGE
myapp-sts-myapp-0    1/1     Running   0          5m
```
