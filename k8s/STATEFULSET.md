# StatefulSets & Persistent Storage

## 1. StatefulSet Overview

StatefulSet provides stable network identities and persistent per-pod storage. Unlike Deployment with random pod names (app-abc12), StatefulSet uses ordinal names (app-0, app-1, app-2) that never change. Each pod gets its own PVC that persists across restarts.

**Use for:** Databases, message queues, distributed systems requiring stable identities.

## 2. Resource Verification

```bash
kubectl get sts,pods,svc,pvc
NAME                    READY   AGE
statefulset/myapp-sts   3/3     5m

NAME                        READY   STATUS
pod/myapp-sts-myapp-0       1/1     Running
pod/myapp-sts-myapp-1       1/1     Running
pod/myapp-sts-myapp-2       1/1     Running

NAME                               TYPE        CLUSTER-IP
service/myapp-sts-myapp            ClusterIP   10.43.42.1
service/myapp-sts-myapp-headless   ClusterIP   None

NAME                                      STATUS   VOLUME    CAPACITY
pvc/data-myapp-sts-myapp-0                Bound    pvc-abc   1Gi
pvc/data-myapp-sts-myapp-1                Bound    pvc-def   1Gi
pvc/data-myapp-sts-myapp-2                Bound    pvc-ghi   1Gi
```

## 3. Network Identity

DNS pattern: `<pod-name>.<headless-service>.<namespace>.svc.cluster.local`

```bash
kubectl exec myapp-sts-myapp-0 -- nslookup myapp-sts-myapp-1.myapp-sts-myapp-headless
Name:      myapp-sts-myapp-1.myapp-sts-myapp-headless.default.svc.cluster.local
Address:   10.42.1.23

kubectl exec myapp-sts-myapp-0 -- ping -c 1 myapp-sts-myapp-1.headless
64 bytes from 10.42.1.23: time=0.123ms
```

Each pod has a stable DNS name that does not change when the pod restarts.

## 4. Per-Pod Storage Isolation

Each pod maintains its own independent storage. After incrementing visit counters three times on each pod:

```bash
for pod in myapp-sts-myapp-0 myapp-sts-myapp-1 myapp-sts-myapp-2; do
    kubectl exec $pod -- cat /data/visits.txt
  done
3
3
3
```

All pods show 3 visits, but these are independent counters stored on separate PVCs. Writing data in one pod does not affect others:

```bash
kubectl exec myapp-sts-myapp-0 -- echo "unique-data-0" > /data/id.txt
kubectl exec myapp-sts-myapp-1 -- echo "unique-data-1" > /data/id.txt
kubectl exec myapp-sts-myapp-0 -- cat /data/id.txt
unique-data-0
kubectl exec myapp-sts-myapp-1 -- cat /data/id.txt
unique-data-1
```

## 5. Persistence Test

Delete pod-0 and verify data survives:

```bash
kubectl exec myapp-sts-myapp-0 -- cat /data/visits.txt
3

kubectl delete pod myapp-sts-myapp-0

kubectl get pod myapp-sts-myapp-0 -w
myapp-sts-myapp-0   0/1   Terminating
myapp-sts-myapp-0   1/1   Running   0   15s

kubectl exec myapp-sts-myapp-0 -- cat /data/visits.txt
3
```

The PVC `data-myapp-sts-myapp-0` remained bound and reattached to the recreated pod, preserving all data.

## 6. Summary

| Feature | Deployment | StatefulSet |
|---------|------------|-------------|
| Pod names | Random (app-abc12) | Ordinal (app-0, app-1) |
| DNS stability | No | Yes |
| Per-pod storage | No | Yes (volumeClaimTemplates) |
| Data persistence | No | Yes |

StatefulSet successfully provides stable network identities and persistent per-pod storage. Each pod maintains its own data, survives deletion, and keeps the same DNS name.
