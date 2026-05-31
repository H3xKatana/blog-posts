#!/usr/bin/env python3
"""Generate K8s cluster architecture diagram with Excalidraw K8s icons."""
import json, sys, copy

with open('/tmp/k8s-icons-nik.excalidrawlib') as f:
    lib_data = json.load(f)
items = lib_data.get('libraryItems', [])

ICON_MAP = {
    'api': 63, 'sched': 65, 'c-m': 64,
    'kubelet': 62, 'k-proxy': 66, 'etcd': 73,
    'master': 69, 'node': 71, 'user': 49,
    'pod': 3, 'deploy': 7, 'svc': 19,
}

def get_icon(name):
    return copy.deepcopy(items[ICON_MAP[name]]['elements'])

def place_icon(name, tx, ty, scale=0.5):
    elems = get_icon(name)
    mx = min(el.get('x', 0) for el in elems)
    my = min(el.get('y', 0) for el in elems)
    for el in elems:
        el['x'] = tx + (el.get('x', 0) - mx) * scale
        el['y'] = ty + (el.get('y', 0) - my) * scale
        if el.get('width'):  el['width']  *= scale
        if el.get('height'): el['height'] *= scale
        if el.get('points'):
            el['points'] = [[p[0]*scale, p[1]*scale] for p in el['points']]
        if el.get('strokeWidth'): el['strokeWidth'] = max(1, el['strokeWidth'])
        el['id'] = f"i_{name}_{el['id']}"
        el['groupIds'] = []
        el['boundElements'] = []
    return elems

# ---- helpers ----
_uid = [0]
def uid():
    _uid[0] += 1; return f"e{_uid[0]:04d}"

def rect(x, y, w, h, fill="#fff", stroke="#333", sw=2, roughness=1,
         roundness={"type":3}, dash=False, opacity=100, label=None):
    eid = uid()
    el = {"type":"rectangle","id":eid,"x":x,"y":y,"width":w,"height":h,
          "strokeColor":stroke,"backgroundColor":fill,"fillStyle":"solid",
          "strokeWidth":sw,"roughness":roughness,"opacity":opacity,
          "roundness":roundness,"boundElements":[],"groupIds":[],"locked":False}
    if dash: el["strokeStyle"]="dashed"
    out = [el]
    if label:
        tid = uid(); fs = 14
        el["boundElements"].append({"id":tid,"type":"text"})
        out.append({"type":"text","id":tid,"x":x+8,"y":y+h/2-10,"width":w-16,"height":20,
                    "text":label,"fontSize":fs,"fontFamily":1,"strokeColor":"#1e1e1e",
                    "textAlign":"center","verticalAlign":"middle","containerId":eid,
                    "originalText":label,"autoResize":True,"groupIds":[],"locked":False})
    return out

def label(x, y, text, size=14, color="#1e1e1e", center=True):
    tid = uid()
    return {"type":"text","id":tid,"x":x,"y":y,"width":len(text)*size*0.55,"height":size+4,
            "text":text,"fontSize":size,"fontFamily":1,"strokeColor":color,
            "textAlign":"center" if center else "left",
            "originalText":text,"autoResize":True,"groupIds":[],"locked":False}

def arrow(x1,y1,x2,y2,color="#666",sw=2,dash=False,tag=None):
    aid=uid(); dx=x2-x1; dy=y2-y1
    el={"type":"arrow","id":aid,"x":x1,"y":y1,"width":dx,"height":dy,
        "strokeColor":color,"strokeWidth":sw,"roughness":1,"opacity":100,
        "points":[[0,0],[dx,dy]],"endArrowhead":"arrow",
        "startBinding":None,"endBinding":None,
        "boundElements":[],"groupIds":[],"locked":False}
    if dash: el["strokeStyle"]="dashed"
    out=[el]
    if tag:
        out.append(label(x1+dx/2-len(tag)*6, y1+dy/2-10, tag, 11, color))
    return out

# ============ LAYOUT ============
CX = 580  # canvas center

COLORS = {
    'cp_bg': '#e3f2fd', 'cp_stroke': '#1565c0',
    'etcd_bg': '#fff3bf', 'etcd_stroke': '#f59e0b',
    'worker_bg': '#c8e6c9', 'worker_stroke': '#2e7d32',
    'storage_bg': '#f3e5f5', 'storage_stroke': '#7b1fa2',
    'zone_bg': '#f8f9fa', 'zone_stroke': '#adb5bd',
    'neutral': '#868e96',
}

C = COLORS
elements = []

# ============ OUTER ZONE ============
zx, zy, zw, zh = 70, 50, 1020, 760
elements += rect(zx, zy, zw, zh, fill=C['zone_bg'], stroke=C['zone_stroke'], sw=1, dash=True)
elements.append(label(CX, zy-28, "Kubernetes Cluster Architecture", 22, "#343a40"))

# ============ 1. USER / CLIENT ============
uy = zy + 12
elements += rect(CX-75, uy, 150, 36, fill="#fff", stroke=C['neutral'], roughness=0, label="kubectl")
elements += place_icon('user', CX+90, uy+2, 0.38)

# ============ 2. LOAD BALANCER ============
ly = uy + 65
elements += rect(CX-85, ly, 170, 36, fill="#fff", stroke=C['neutral'], roughness=0, label="Load Balancer :6443")
elements += arrow(CX, uy+36, CX, ly, C['neutral'], sw=1)

# ============ 3. CONTROL PLANE ============
cpsy = ly + 70
cpzh = 270
elements += rect(zx+40, cpsy, zw-80, cpzh, fill="#e7f5ff", stroke=C['cp_stroke'], sw=1, dash=True, opacity=30)
elements.append(label(CX, cpsy+6, "Control Plane — 3 Master Nodes", 17, C['cp_stroke']))

elements += arrow(CX, ly+36, CX, cpsy+2, C['cp_stroke'], sw=1, tag="kube-apiserver proxy")

# 3 CP nodes
cpw, cph = 270, 222
cpgap = 28
cpsx = CX - (3*cpw + 2*cpgap)//2

for i in range(3):
    nx = cpsx + i*(cpw + cpgap)
    ny = cpsy + 38
    elements += rect(nx, ny, cpw, cph, fill=C['cp_bg'], stroke=C['cp_stroke'], label=f"cp-0{i+1}")

    # Components: icon left, text right
    comps = [('api', 'kube-apiserver'), ('sched', 'kube-scheduler'), ('c-m', 'kube-controller-mgr')]
    for j, (iname, l) in enumerate(comps):
        cy = ny + 45 + j*55
        elements += rect(nx+10, cy, cpw-20, 40, fill="#fff", stroke=C['cp_stroke'], sw=1, roughness=0)
        elements += place_icon(iname, nx+16, cy+3, 0.25)
        elements.append(label(nx+55, cy+11, l, 11, "#1e1e1e", False))

    # Raft arrows between CP nodes
    if i < 2:
        elements += arrow(nx+cpw, ny+28, nx+cpw+cpgap, ny+28, C['cp_stroke'], sw=1)

# ============ 4. ETCD ============
etcdy = cpsy + cpzh + 10
etcdzh = 130
elements += rect(zx+70, etcdy, zw-140, etcdzh, fill="#fff9db", stroke=C['etcd_stroke'], sw=1, dash=True, opacity=40)
elements.append(label(CX, etcdy+6, "etcd — Distributed Key-Value Store (Raft Consensus)", 15, C['etcd_stroke']))

ew, eh = 195, 65
egap = 38
esx = CX - (3*ew + 2*egap)//2

for i in range(3):
    ex = esx + i*(ew + egap)
    ey = etcdy + 42
    role = "LEADER" if i == 0 else "FOLLOWER"
    elements += rect(ex, ey, ew, eh, fill=C['etcd_bg'], stroke=C['etcd_stroke'], label=f"etcd-{i} ({role})")
    elements += place_icon('etcd', ex+10, ey+6, 0.35)

    if i < 2:
        elements += arrow(ex+ew, ey+eh//2, ex+ew+egap, ey+eh//2, C['etcd_stroke'], sw=1)

elements += arrow(CX, cpsy+cpzh, CX, etcdy+2, C['etcd_stroke'], sw=1, tag="gRPC (watch/list/put)")

# ============ 5. WORKER NODES ============
wky = etcdy + etcdzh + 10
wkzh = 168
elements += rect(zx+110, wky, zw-220, wkzh, fill="#ebfbee", stroke=C['worker_stroke'], sw=1, dash=True, opacity=30)
elements.append(label(CX, wky+6, "Worker Nodes", 17, C['worker_stroke']))

ww, wh = 285, 118
wgap = 48
wsx = CX - (2*ww + wgap)//2

for i in range(2):
    wx = wsx + i*(ww + wgap)
    wy = wky + 38
    elements += rect(wx, wy, ww, wh, fill=C['worker_bg'], stroke=C['worker_stroke'], label=f"worker-0{i+1}")

    comps = [('kubelet', 'kubelet'), ('k-proxy', 'kube-proxy'), ('pod', 'Pod')]
    for j, (iname, l) in enumerate(comps):
        cy = wy + 44 + j*24
        elements += rect(wx+10, cy, 160, 20, fill="#fff", stroke=C['worker_stroke'], sw=1, roughness=0)
        ic_scale = 0.18 if iname == 'pod' else 0.22
        elements += place_icon(iname, wx+14, cy, ic_scale)
        elements.append(label(wx+44, cy+1, l, 10, "#1e1e1e", False))

elements += arrow(CX, etcdy+etcdzh, CX, wky+2, C['worker_stroke'], sw=1, tag="kubelet watches API Server")

# ============ 6. STORAGE LAYER ============
sty = wky + wkzh + 10
elements += rect(270, sty, 620, 44, fill=C['storage_bg'], stroke=C['storage_stroke'], label="Storage: SSD / NVMe (dedicated disk per node)")
elements.append(label(CX, sty+56, "Disk fsync latency → Commit latency → Raft latency → API latency", 12, C['storage_stroke']))
elements += arrow(CX, wky+wkzh, CX, sty+2, C['storage_stroke'], sw=1, tag="fsync / write")

# ============ LEGEND ============
lgx, lgy = 150, zy+zh+16
elements.append(label(lgx, lgy, "Legend:", 13, "#495057", False))
for i,(bg,st,l) in enumerate([(C['cp_bg'],C['cp_stroke'],"Control Plane"),
                                (C['etcd_bg'],C['etcd_stroke'],"etcd / Store"),
                                (C['worker_bg'],C['worker_stroke'],"Worker Nodes"),
                                (C['storage_bg'],C['storage_stroke'],"Storage")]):
    ly2 = lgy+20+i*20
    elements += rect(lgx, ly2, 42, 14, fill=bg, stroke=st, sw=1, roughness=0)
    elements.append(label(lgx+48, ly2-2, l, 11, "#495057", False))

# ============ SAVE ============
output = {"type":"excalidraw","version":2,
          "source":"hermes-agent (boemska-nik/kubernetes-icons)",
          "elements":elements,"appState":{"viewBackgroundColor":"#ffffff"}}

path = sys.argv[1] if len(sys.argv) > 1 else "/opt/data/blog-posts/etcd-production-management/cluster-architecture-icons.excalidraw"
with open(path,'w') as f:
    json.dump(output, f, indent=2)
print(f"Saved: {path}")
print(f"Elements: {len(elements)}")
