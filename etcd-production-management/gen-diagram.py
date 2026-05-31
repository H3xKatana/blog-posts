#!/usr/bin/env python3
"""Generate K8s cluster architecture diagram as .excalidraw"""
import json, uuid, sys

NEXT_ID = 0
def uid():
    global NEXT_ID
    NEXT_ID += 1
    return f"el{NEXT_ID:04d}"

def rect(x, y, w, h, fill="#ffffff", stroke="#1e1e1e", sw=2, roughness=1,
         roundness={"type": 3}, dash=False, opacity=100, label=None):
    eid = uid()
    el = {
        "type": "rectangle", "id": eid,
        "x": x, "y": y, "width": w, "height": h,
        "strokeColor": stroke, "backgroundColor": fill,
        "fillStyle": "solid", "strokeWidth": sw,
        "roughness": roughness, "opacity": opacity,
        "roundness": roundness,
        "boundElements": [],
        "groupIds": [], "locked": False,
    }
    if dash: el["strokeStyle"] = "dashed"
    if label:
        tid = uid()
        fx = 16
        tw = len(label) * fx * 0.55
        if tw > w - 20: tw = w - 20
        el["boundElements"].append({"id": tid, "type": "text"})
        txt = {
            "type": "text", "id": tid,
            "x": x + 10, "y": y + h/2 - 12,
            "width": tw, "height": 24,
            "text": label, "fontSize": fx, "fontFamily": 1,
            "strokeColor": "#1e1e1e", "textAlign": "center",
            "verticalAlign": "middle", "containerId": eid,
            "originalText": label, "autoResize": True,
            "groupIds": [], "locked": False,
        }
        return [el, txt]
    return [el]

def text(x, y, content, size=16, color="#1e1e1e", bold=False, center=True):
    tid = uid()
    tw = len(content) * size * 0.55
    return {
        "type": "text", "id": tid,
        "x": x, "y": y, "width": tw, "height": size + 4,
        "text": content, "fontSize": size, "fontFamily": 1,
        "strokeColor": color,
        "textAlign": "center" if center else "left",
        "originalText": content, "autoResize": True,
        "groupIds": [], "locked": False,
    }

def arrow(x1, y1, x2, y2, color="#1e1e1e", sw=2, dash=False, label=None):
    aid = uid()
    dx, dy = x2 - x1, y2 - y1
    el = {
        "type": "arrow", "id": aid,
        "x": x1, "y": y1, "width": dx, "height": dy,
        "strokeColor": color, "strokeWidth": sw,
        "roughness": 1, "opacity": 100,
        "points": [[0, 0], [dx, dy]],
        "endArrowhead": "arrow",
        "startBinding": None, "endBinding": None,
        "boundElements": [],
        "groupIds": [], "locked": False,
    }
    if dash: el["strokeStyle"] = "dashed"
    els = [el]
    if label:
        tid = uid()
        lx = x1 + dx/2 - len(label)*5
        ly = y1 + dy/2 - 12
        els.append({
            "type": "text", "id": tid,
            "x": lx, "y": ly, "width": len(label)*10, "height": 20,
            "text": label, "fontSize": 12, "fontFamily": 1,
            "strokeColor": color, "textAlign": "center",
            "originalText": label, "autoResize": True,
            "groupIds": [], "locked": False,
        })
    return els

# ============================================================
# LAYOUT CONSTANTS
# ============================================================
CX = 550  # canvas center x

# Colors
CP_BG = "#e3f2fd"     # light blue
CP_STROKE = "#1565c0" # blue
WORKER_BG = "#c8e6c9"  # light green
WORKER_STROKE = "#2e7d32"  # green
ETCD_BG = "#fff3bf"    # light yellow
ETCD_STROKE = "#f59e0b"  # amber
DISK_BG = "#f3e5f5"    # light purple
DISK_STROKE = "#7b1fa2"  # purple
ZONE_BG = "#f8f9fa"
ZONE_STROKE = "#adb5bd"

elements = []

# ============================================================
# ZONE: CLUSTER
# ============================================================
# Cluster bounding box
cluster_x, cluster_y = 100, 80
cluster_w, cluster_h = 900, 680
elements += rect(cluster_x, cluster_y, cluster_w, cluster_h,
                 fill=ZONE_BG, stroke=ZONE_STROKE, sw=1, dash=True)
# Cluster label
elements.append(text(CX, cluster_y - 30, "Kubernetes Cluster", 22, "#495057"))

# ============================================================
# SECTION: User / kubectl
# ============================================================
user_x = CX - 80
user_y = cluster_y + 20
elements += rect(user_x, user_y, 160, 50, fill="#fff", stroke="#868e96",
                 roughness=0, label="kubectl / CLI")

# ============================================================
# SECTION: Load Balancer
# ============================================================
lb_x = CX - 90
lb_y = user_y + 90
elements += rect(lb_x, lb_y, 180, 45, fill="#fff", stroke="#868e96",
                 roughness=0, label="Load Balancer :6443")

# Arrows: user -> LB
elements += arrow(CX, user_y + 50, CX, lb_y, "#868e96", sw=1)

# ============================================================
# SECTION: Control Plane
# ============================================================
cp_section_y = lb_y + 80
# Zone background for control plane
cp_zone_x, cp_zone_w = 130, 840
cp_zone_h = 280
elements += rect(cp_zone_x, cp_section_y, cp_zone_w, cp_zone_h,
                 fill="#e7f5ff", stroke="#1565c0", sw=1, dash=True, opacity=30)
elements.append(text(CX, cp_section_y + 10, "Control Plane Nodes", 18, "#1565c0"))

# Arrow: LB -> CP
elements += arrow(CX, lb_y + 45, CX, cp_section_y + 5, "#1565c0", sw=1, label="kube-apiserver proxy")

# 3 CP nodes side by side
cp_node_w, cp_node_h = 250, 200
cp_gap = 30
cp_start_x = CX - (3 * cp_node_w + 2 * cp_gap) // 2

cp_labels = ["cp-01", "cp-02", "cp-03"]
cp_components = [
    ["kube-apiserver", "kube-scheduler", "kube-controller-mgr"],
    ["kube-apiserver", "kube-scheduler", "kube-controller-mgr"],
    ["kube-apiserver", "kube-scheduler", "kube-controller-mgr"],
]

for i in range(3):
    nx = cp_start_x + i * (cp_node_w + cp_gap)
    ny = cp_section_y + 40
    
    # Node box
    elements += rect(nx, ny, cp_node_w, cp_node_h, fill=CP_BG, stroke=CP_STROKE,
                     label=cp_labels[i])
    
    # Component boxes inside each node
    comp_y = ny + 35
    for j, comp in enumerate(cp_components[i]):
        cy = comp_y + j * 45
        elements += rect(nx + 10, cy, cp_node_w - 20, 35,
                         fill="#fff", stroke=CP_STROKE, sw=1, roughness=0,
                         label=comp)

    # Arrows between CP nodes (Raft)
    if i < 2:
        ax1 = nx + cp_node_w
        ax2 = nx + cp_node_w + cp_gap
        raft_y = ny + 60
        elements += arrow(ax1, raft_y, ax2, raft_y, CP_STROKE, sw=1)

# ============================================================
# SECTION: etcd Cluster
# ============================================================
etcd_section_y = cp_section_y + cp_zone_h + 10
etcd_zone_x, etcd_zone_w = 150, 800
etcd_zone_h = 130
elements += rect(etcd_zone_x, etcd_section_y, etcd_zone_w, etcd_zone_h,
                 fill="#fff9db", stroke=ETCD_STROKE, sw=1, dash=True, opacity=40)
elements.append(text(CX, etcd_section_y + 8, "etcd — Raft Consensus", 16, ETCD_STROKE))

# 3 etcd members
etcd_w, etcd_h = 180, 65
etcd_gap = 40
etcd_start_x = CX - (3 * etcd_w + 2 * etcd_gap) // 2

for i in range(3):
    ex = etcd_start_x + i * (etcd_w + etcd_gap)
    ey = etcd_section_y + 35
    role = "LEADER" if i == 0 else "FOLLOWER"
    elements += rect(ex, ey, etcd_w, etcd_h, fill=ETCD_BG, stroke=ETCD_STROKE,
                     label=f"etcd-{i} ({role})")
    
    # Raft arrows between members
    if i < 2:
        rx1 = ex + etcd_w
        rx2 = ex + etcd_w + etcd_gap
        ry = ey + etcd_h // 2
        elements += arrow(rx1, ry, rx2, ry, ETCD_STROKE, sw=1)

# Arrow from CP to etcd
elements += arrow(CX, cp_section_y + cp_zone_h, CX, etcd_section_y + 5,
                  ETCD_STROKE, sw=1, label="gRPC watch/list/put")

# ============================================================
# SECTION: Worker Nodes
# ============================================================
worker_section_y = etcd_section_y + etcd_zone_h + 15
worker_zone_x, worker_zone_w = 160, 780
worker_zone_h = 165
elements += rect(worker_zone_x, worker_section_y, worker_zone_w, worker_zone_h,
                 fill="#ebfbee", stroke=WORKER_STROKE, sw=1, dash=True, opacity=30)
elements.append(text(CX, worker_section_y + 8, "Worker Nodes", 18, WORKER_STROKE))

worker_w, worker_h = 260, 115
worker_gap = 60
worker_start_x = CX - (2 * worker_w + worker_gap) // 2

for i in range(2):
    wx = worker_start_x + i * (worker_w + worker_gap)
    wy = worker_section_y + 40
    
    # Node box
    elements += rect(wx, wy, worker_w, worker_h, fill=WORKER_BG, stroke=WORKER_STROKE,
                     label=f"worker-0{i+1}")
    
    # Components
    components = ["kubelet", "kube-proxy", "Pod"]
    cy = wy + 35
    for j, comp in enumerate(components):
        cy2 = cy + j * 25
        elements += rect(wx + 10, cy2, worker_w - 100, 20,
                         fill="#fff", stroke=WORKER_STROKE, sw=1, roughness=0,
                         label=comp)

# Arrow: etcd -> workers (kubelet watches API)
elements += arrow(CX, etcd_section_y + etcd_zone_h, CX, worker_section_y + 5,
                  WORKER_STROKE, sw=1, label="kubelet watches API Server")

# ============================================================
# SECTION: Storage Layer
# ============================================================
storage_y = worker_section_y + worker_zone_h + 15
elements += rect(220, storage_y, 660, 55, fill=DISK_BG, stroke=DISK_STROKE,
                 label="Storage: SSD / NVMe (dedicated disk per node)")
elements.append(text(CX, storage_y + 75,
                     "Disk latency → Commit latency → Raft latency → API latency",
                     13, DISK_STROKE, center=True))

# Arrow: workers -> storage
elements += arrow(CX, worker_section_y + worker_zone_h, CX, storage_y + 3,
                  DISK_STROKE, sw=1, label="fsync / write")

# ============================================================
# LEGEND (bottom right)
# ============================================================
legend_x, legend_y = 720, cluster_y + cluster_h + 15
elements.append(text(legend_x, legend_y, "Legend:", 14, "#495057", center=False))
items = [
    (CP_BG, CP_STROKE, "Control Plane"),
    (ETCD_BG, ETCD_STROKE, "etcd / Data Store"),
    (WORKER_BG, WORKER_STROKE, "Worker Nodes"),
    (DISK_BG, DISK_STROKE, "Storage"),
]
for i, (bg, st, lbl) in enumerate(items):
    ly = legend_y + 22 + i * 22
    elements += rect(legend_x, ly, 50, 16, fill=bg, stroke=st, sw=1, roughness=0)
    elements.append(text(legend_x + 56, ly - 2, lbl, 12, "#495057", center=False))

# ============================================================
# WRAP & SAVE
# ============================================================
output = {
    "type": "excalidraw",
    "version": 2,
    "source": "hermes-agent",
    "elements": elements,
    "appState": {
        "viewBackgroundColor": "#ffffff",
        "gridSize": None,
    }
}

path = sys.argv[1] if len(sys.argv) > 1 else "/opt/data/blog-posts/etcd-production-management/cluster-architecture.excalidraw"
with open(path, 'w') as f:
    json.dump(output, f, indent=2)

print(f"Saved: {path}")
print(f"Elements: {len(elements)}")
