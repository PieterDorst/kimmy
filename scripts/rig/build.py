# Turns Pieter's Tripo Kimmy GLB (Kimmy1, Kimmy2 or Kimmy3) into a TalkingHead-ready avatar:
# Mixamo/RPM skeleton (local axes copied from brunette-t.glb), skin weights,
# a lip cut + mouth interior, and procedural ARKit + Oculus viseme blendshapes.
import json, struct, sys, numpy as np
from glbio import load, acc

import os
SRC = sys.argv[1] if len(sys.argv) > 1 else '/mnt/project-files/kimmy/models/Kimmy3.glb'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'kimmy.glb'
PROFILE = sys.argv[3] if len(sys.argv) > 3 else 'kimmy3'
REF = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'brunette-t.glb')

# ---------------------------------------------------------------- mesh in
j, b = load(SRC)
prim = j['meshes'][0]['primitives'][0]
P = acc(j, b, prim['attributes']['POSITION']).astype(np.float64)
N = acc(j, b, prim['attributes']['NORMAL']).astype(np.float64)
UV = acc(j, b, prim['attributes']['TEXCOORD_0']).astype(np.float64)
T = acc(j, b, prim['indices']).reshape(-1, 3).astype(np.int64)
if PROFILE == 'kimmy3': P /= 100   # exported in centimetres

# Tripo splits vertices at every UV seam, which gives faceted shading. Recompute normals
# smoothed across seams (area-weighted, welded by position) so she reads as a smooth surface.
def smooth_normals(P, T):
  fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
  _, weld = np.unique(np.round(P / 1e-5).astype(np.int64), axis=0, return_inverse=True)
  weld = weld.ravel()
  acc_n = np.zeros((weld.max() + 1, 3))
  for k in range(3): np.add.at(acc_n, weld[T[:, k]], fn)
  n = acc_n[weld]
  return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
N = smooth_normals(P, T)

# ---------------------------------------------------------------- landmarks (source units, glTF axes, +x = her left)
# Each Tripo export has its own proportions, so joints and face features are measured per model.
if PROFILE == 'kimmy1':   # A-pose, measured from renders
  L = {
    'Hips': (0, .52, 0), 'Spine': (0, .575, 0), 'Spine1': (0, .625, -.005), 'Spine2': (0, .675, -.01),
    'Neck': (0, .765, -.015), 'Head': (0, .805, -.012), 'HeadTop_End': (0, .978, -.01),
    'LeftEye': (.028, .875, .055),
    'LeftShoulder': (.025, .745, -.02), 'LeftArm': (.10, .73, -.022), 'LeftForeArm': (.19, .716, -.024),
    'LeftHand': (.285, .706, -.021),
    'LeftHandThumb1': (.298, .700, -.006), 'LeftHandThumb2': (.310, .697, .002), 'LeftHandThumb3': (.320, .695, .009), 'LeftHandThumb4': (.328, .694, .015),
    'LeftUpLeg': (.055, .50, 0), 'LeftLeg': (.08, .27, 0), 'LeftFoot': (.10, .065, -.02), 'LeftToeBase': (.105, .02, .06), 'LeftToe_End': (.105, .02, .115),
  }
  for f, base, tip in [('Index', (.328, .707, -.010), (.3566, .700, -.010)), ('Middle', (.329, .707, -.021), (.3606, .699, -.021)),
                       ('Ring', (.328, .707, -.033), (.3566, .700, -.033)), ('Pinky', (.324, .706, -.044), (.344, .701, -.044))]:
    base, tip = np.array(base), np.array(tip)
    for k, t in zip((1, 2, 3, 4), (0, .42, .72, 1)):
      L[f'LeftHand{f}{k}'] = tuple(base + (tip - base) * t)
  F = dict(MY=.8319, CURVE=.0011, CX=-.0008, XL=-.0205, XR=.019, LIPZ=.066, CHIN=.81, PIT=.045,
           EX=.028, EXO=0, EY=.875, ERX=.0125, ERY=.0115, BROW=.903)
elif PROFILE == 'kimmy3':   # T-pose, quad remesh (~90k tris) with a normal map; measured from slices and grid renders
  L = {
    'Hips': (0, .53, 0), 'Spine': (0, .585, 0), 'Spine1': (0, .635, -.004), 'Spine2': (0, .685, -.008),
    'Neck': (0, .78, -.015), 'Head': (0, .812, -.012), 'HeadTop_End': (0, .977, -.01),
    'LeftEye': (.0253, .8776, .048),
    'LeftShoulder': (.03, .741, -.018), 'LeftArm': (.09, .738, -.022), 'LeftForeArm': (.245, .735, -.024),
    'LeftHand': (.40, .741, -.024),
    'LeftUpLeg': (.058, .505, .004), 'LeftLeg': (.078, .29, 0), 'LeftFoot': (.105, .075, -.03), 'LeftToeBase': (.105, .02, .05), 'LeftToe_End': (.105, .02, .11),
  }
  for f, pts in [('Thumb', [(.405, .737, -.004), (.417, .735, .004), (.426, .733, .010)]),
                 ('Index', [(.447, .741, -.0077), (.4614, .741, -.0077), (.4722, .740, -.0077)]),
                 ('Middle', [(.448, .741, -.021), (.4644, .741, -.021), (.4767, .740, -.021)]),
                 ('Ring', [(.447, .741, -.033), (.4614, .741, -.033), (.4722, .740, -.033)]),
                 ('Pinky', [(.444, .740, -.0435), (.4544, .740, -.0435), (.4622, .739, -.0435)])]:
    pts = [np.array(p) for p in pts]
    pts.append(pts[2] + (pts[2] - pts[1]) * .9)   # fingertip
    for k, p in enumerate(pts): L[f'LeftHand{f}{k + 1}'] = tuple(p)
  F = dict(MY=.8367, CURVE=.0011, CX=-.003, XL=-.021, XR=.015, LIPZ=.069, CHIN=.812, PIT=.045,
           EX=.0275, EXO=-.0021, EY=.8776, ERX=.0135, ERY=.0095, BROW=.900)
else:   # kimmy2: T-pose; body joints from Tripo's own auto-rig, face measured from renders
  L = {
    'Hips': (0, .541, .004), 'Spine': (0, .595, .002), 'Spine1': (0, .645, -.002), 'Spine2': (0, .695, -.006),
    'Neck': (0, .785, -.015), 'Head': (0, .82, -.012), 'HeadTop_End': (0, .977, -.01),
    'LeftEye': (.027, .881, .055),
    'LeftShoulder': (.033, .768, -.013), 'LeftArm': (.087, .768, -.013), 'LeftForeArm': (.233, .756, -.021),
    'LeftHand': (.374, .748, -.032),
    'LeftUpLeg': (.056, .518, .006), 'LeftLeg': (.083, .306, .01), 'LeftFoot': (.106, .071, -.021), 'LeftToeBase': (.11, .017, .048), 'LeftToe_End': (.11, .017, .10),
  }
  for f, pts in [('Thumb', [(.40, .743, -.019), (.421, .740, -.008), (.437, .733, 0)]),
                 ('Index', [(.447, .747, -.017), (.463, .743, -.015), (.477, .741, -.013)]),
                 ('Middle', [(.448, .747, -.028), (.465, .744, -.028), (.48, .741, -.028)]),
                 ('Ring', [(.447, .745, -.041), (.462, .743, -.041), (.476, .741, -.042)]),
                 ('Pinky', [(.441, .744, -.048), (.454, .740, -.051), (.464, .738, -.054)])]:
    pts = [np.array(p) for p in pts]
    pts.append(pts[2] + (pts[2] - pts[1]) * .9)   # fingertip
    for k, p in enumerate(pts): L[f'LeftHand{f}{k + 1}'] = tuple(p)
  F = dict(MY=.8402, CURVE=.0013, CX=-.0019, XL=-.020, XR=.0163, LIPZ=.0646, CHIN=.815, PIT=.062,
           EX=.0273, EXO=-.0006, EY=.8812, ERX=.0118, ERY=.0088, BROW=.901)
for k in list(L):
  if k.startswith('Left'):
    x, y, z = L[k]; L['Right' + k[4:]] = (-x, y, z)
L = {k: np.array(v, float) for k, v in L.items()}

HIPS_Y = L['Hips'][1]
S = 1.037 / HIPS_Y   # scale so her hips sit at the reference rig's hip height

# ---------------------------------------------------------------- face subdivision (denser face for lips and blinks)
def in_face(p):
  return (np.abs(p[..., 0]) < .068) & (p[..., 1] > F['CHIN'] - .025) & (p[..., 1] < F['BROW'] + .032) & (p[..., 2] > .015)

def subdivide(P, N, UV, T, sel, phong=0.0):
  # Splits each selected triangle in four. With phong > 0 the new edge points are pushed onto the
  # curved surface implied by the vertex normals (Phong tessellation), which rounds off the facets.
  # Edge points depend only on the edge's two vertices, so UV-seam copies stay welded.
  key = {}
  newP, newN, newUV = [P], [N], [UV]
  cnt = [len(P)]
  def mid(a, b):
    k = (a, b) if a < b else (b, a)
    if k not in key:
      key[k] = cnt[0]; cnt[0] += 1
      m = (P[a] + P[b]) / 2
      if phong:
        qa = m - np.dot(m - P[a], N[a]) * N[a]; qb = m - np.dot(m - P[b], N[b]) * N[b]
        m = (1 - phong) * m + phong * (qa + qb) / 2
      newP.append(m[None]); n = N[a] + N[b]; newN.append((n / (np.linalg.norm(n) + 1e-12))[None])
      newUV.append(((UV[a] + UV[b]) / 2)[None])
    return key[k]
  out = []
  for t, s in zip(T, sel):
    if not s: out.append(t); continue
    a, b_, c = t; ab, bc, ca = mid(a, b_), mid(b_, c), mid(c, a)
    out += [(a, ab, ca), (ab, b_, bc), (ca, bc, c), (ab, bc, ca)]
  return np.concatenate(newP), np.concatenate(newN), np.concatenate(newUV), np.array(out, np.int64)

# whole body: one rounded level (about 4x the triangles), then fresh smooth normals.
# Kimmy3 is already dense enough (and has a normal map), so only the face gets extra triangles.
if PROFILE != 'kimmy3':
  P, N, UV, T = subdivide(P, N, UV, T, np.ones(len(T), bool), phong=.75)
  N = smooth_normals(P, T)
# face: one more flat level, enough density for lips and blinks
sel = in_face(P[T]).all(1)
P, N, UV, T = subdivide(P, N, UV, T, sel)

# ---------------------------------------------------------------- lip cut
CX, XL, XR, MY = F['CX'], F['XL'], F['XR'], F['MY']
def lipline(x):
  return MY + F['CURVE'] * ((x - CX) / ((XR - XL) / 2)) ** 2

side = np.where(P[:, 1] >= lipline(P[:, 0]), 1, -1)
def cuttable(tri):
  p = P[tri]
  return (p[:, 0] > XL + .001).all() and (p[:, 0] < XR - .001).all() and (p[:, 2] > F['LIPZ'] - .021).all() and \
         (np.abs(p[:, 1] - MY) < .01).all() and len(set(side[tri])) == 2

cutpts = {}
addP, addN, addUV, addSide = [], [], [], []
def cutpoint(a, b_, s):
  k = (min(a, b_), max(a, b_), s)
  if k not in cutpts:
    # solve for the crossing along the edge by bisection on y - lipline(x)
    lo, hi = 0.0, 1.0
    fa = P[a, 1] - lipline(P[a, 0])
    for _ in range(30):
      m = (lo + hi) / 2; q = P[a] + (P[b_] - P[a]) * m
      if (q[1] - lipline(q[0]) >= 0) == (fa >= 0): lo = m
      else: hi = m
    t = (lo + hi) / 2
    cutpts[k] = len(P) + len(addP)
    addP.append(P[a] + (P[b_] - P[a]) * t); n = N[a] + (N[b_] - N[a]) * t; addN.append(n / np.linalg.norm(n))
    addUV.append(UV[a] + (UV[b_] - UV[a]) * t); addSide.append(s)
  return cutpts[k]

newT = []
ncut = 0
for t in T:
  if not cuttable(t): newT.append(tuple(t)); continue
  ncut += 1
  s = side[t]
  # rotate so the lone vertex is first, keeping winding
  lone = [i for i in range(3) if (s == s[i]).sum() == 1][0]
  a, b_, c = t[lone], t[(lone + 1) % 3], t[(lone + 2) % 3]
  sa, sb = side[a], side[b_]
  ab_a, ca_a = cutpoint(a, b_, sa), cutpoint(c, a, sa)
  ab_b, ca_b = cutpoint(a, b_, sb), cutpoint(c, a, sb)
  newT += [(a, ab_a, ca_a), (ab_b, b_, c), (ab_b, c, ca_b)]
P = np.concatenate([P, np.array(addP)]); N = np.concatenate([N, np.array(addN)]); UV = np.concatenate([UV, np.array(addUV)])
side = np.concatenate([side, np.array(addSide)])
T = np.array(newT, np.int64)
print('cut triangles', ncut, 'verts', len(P), 'tris', len(T))

# ---------------------------------------------------------------- mouth interior (dark, with a strip of upper teeth)
face = in_face(P) & (P[:, 2] > .04)
FP = P[face]
gx = np.linspace(XL - .003, XR + .003, 17); gy = np.linspace(MY - .019, MY + .009, 29)
MP, MC = [], []
for y in gy:
  for x in gx:
    near = FP[(np.abs(FP[:, 0] - x) < .004) & (np.abs(FP[:, 1] - y) < .004)]
    z = (near[:, 2].min() if len(near) else .05) - .006
    MP.append((x, y, z))
    ly = lipline(x)
    tw = .012 * np.sqrt(max(0, 1 - ((y - ly) / .004) ** 2))
    teeth = (y > ly - .0025) and abs(x - CX) < tw
    MC.append((.72, .68, .64, 1) if teeth else (.07, .02, .03, 1))
MP = np.array(MP); MC = np.array(MC, np.float32)
MT = []
for r in range(len(gy) - 1):
  for c in range(len(gx) - 1):
    i = r * len(gx) + c
    MT += [(i, i + 1, i + len(gx)), (i + 1, i + 1 + len(gx), i + len(gx))]  # faces +z
MT = np.array(MT)
MN = np.tile([0, 0, 1.0], (len(MP), 1))

# ---------------------------------------------------------------- skeleton from the reference rig
rj, rb = load(REF)
RN = rj['nodes']
name2i = {n.get('name'): i for i, n in enumerate(RN)}
parent = {c: i for i, n in enumerate(RN) for c in n.get('children', [])}
bones = [n['name'] for n in RN if 'mesh' not in n and n.get('name') != 'Armature']

def q2m(q):
  x, y, z, w = q
  return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                   [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                   [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
def m2q(m):
  t = np.trace(m)
  if t > 0:
    s = np.sqrt(t + 1) * 2; return np.array([(m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s, s / 4])
  i = np.argmax(np.diag(m))
  if i == 0:
    s = np.sqrt(1 + m[0, 0] - m[1, 1] - m[2, 2]) * 2; return np.array([s / 4, (m[0, 1] + m[1, 0]) / s, (m[0, 2] + m[2, 0]) / s, (m[2, 1] - m[1, 2]) / s])
  if i == 1:
    s = np.sqrt(1 + m[1, 1] - m[0, 0] - m[2, 2]) * 2; return np.array([(m[0, 1] + m[1, 0]) / s, s / 4, (m[1, 2] + m[2, 1]) / s, (m[0, 2] - m[2, 0]) / s])
  s = np.sqrt(1 + m[2, 2] - m[0, 0] - m[1, 1]) * 2; return np.array([(m[0, 2] + m[2, 0]) / s, (m[1, 2] + m[2, 1]) / s, s / 4, (m[1, 0] - m[0, 1]) / s])
def minrot(u, v):
  u = u / np.linalg.norm(u); v = v / np.linalg.norm(v)
  c = np.cross(u, v); d = np.dot(u, v)
  if d < -.9999: raise ValueError('opposite')
  K = np.array([[0, -c[2], c[1]], [c[2], 0, -c[0]], [-c[1], c[0], 0]])
  return np.eye(3) + K + K @ K / (1 + d)

def rparent(nm):
  pi = parent.get(name2i[nm]); pn = RN[pi].get('name') if pi is not None else None
  return None if pn == 'Armature' else pn

Rb = {}
for nm in bones:  # reference world rotations (parents come later in node order, so resolve recursively)
  pass
def refworld(nm):
  if nm in Rb: return Rb[nm]
  r = q2m(RN[name2i[nm]].get('rotation', [0, 0, 0, 1]))
  pn = rparent(nm)
  Rb[nm] = r if pn is None else refworld(pn) @ r
  return Rb[nm]
for nm in bones: refworld(nm)

PRIMARY = {'Hips': 'Spine', 'Spine': 'Spine1', 'Spine1': 'Spine2', 'Spine2': 'Neck', 'Neck': 'Head', 'Head': 'HeadTop_End'}
for s_ in ('Left', 'Right'):
  PRIMARY.update({f'{s_}Shoulder': f'{s_}Arm', f'{s_}Arm': f'{s_}ForeArm', f'{s_}ForeArm': f'{s_}Hand', f'{s_}Hand': f'{s_}HandMiddle1',
                  f'{s_}UpLeg': f'{s_}Leg', f'{s_}Leg': f'{s_}Foot', f'{s_}Foot': f'{s_}ToeBase', f'{s_}ToeBase': f'{s_}Toe_End'})
  for f in ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky'):
    for k in (1, 2, 3): PRIMARY[f'{s_}Hand{f}{k}'] = f'{s_}Hand{f}{k + 1}'

Rk = {}
def kimworld(nm):
  if nm in Rk: return Rk[nm]
  if nm in PRIMARY:
    q = minrot(Rb[nm] @ [0, 1, 0], L[PRIMARY[nm]] - L[nm])
  else:
    pn = rparent(nm); kimworld(pn); q = Rk[pn] @ Rb[pn].T  # leaf: same correction as parent
  Rk[nm] = q @ Rb[nm]
  return Rk[nm]
for nm in bones: kimworld(nm)

local = {}
for nm in bones:
  pn = rparent(nm)
  if pn is None: R, t = Rk[nm], L[nm] * S
  else: R, t = Rk[pn].T @ Rk[nm], Rk[pn].T @ ((L[nm] - L[pn]) * S)
  local[nm] = (m2q(R), t)

# ---------------------------------------------------------------- hair by colour (Kimmy3)
# Kimmy3's hair is fused with the jacket at the shoulders, so depth alone can't tell them apart. Hair
# texels are mid-saturated tan/brown; the cream jacket is pale and the skin more saturated. Hair found
# this way may only follow the head, neck and spine, never the shoulders or arms.
HAIRC = None
if PROFILE == 'kimmy3':
  import io
  from PIL import Image
  t0 = j['textures'][j['materials'][0]['pbrMetallicRoughness']['baseColorTexture']['index']]['source']
  bv = j['bufferViews'][j['images'][t0]['bufferView']]
  tex = np.asarray(Image.open(io.BytesIO(b[bv.get('byteOffset', 0): bv.get('byteOffset', 0) + bv['byteLength']]))
                   .convert('RGB').resize((1024, 1024))) / 255.
  col = tex[np.clip((UV[:, 1] % 1) * 1023, 0, 1023).astype(int), np.clip((UV[:, 0] % 1) * 1023, 0, 1023).astype(int)]
  mx, mn = col.max(1), col.min(1); sat = (mx - mn) / np.maximum(mx, 1e-6)
  ax_, y_, z_ = np.abs(P[:, 0]), P[:, 1], P[:, 2]
  turtle = (ax_ < .075) & (z_ > -.03) & (y_ < .80) & (y_ > .6) & (mx < .56)
  arm_ = L['LeftArm']   # inside the sleeve's own tube it is jacket, whatever the colour
  sleeve = (ax_ > .1) & (z_ > arm_[2] - .055) & (z_ < arm_[2] + .045) & (np.abs(y_ - arm_[1]) < .05)
  h = ((sat > .22) & (sat < .56) & (mx < .88) & (y_ > .5) & (ax_ < .16) & ~turtle & ~sleeve).astype(float)
  # single texels (jacket folds, shadows) get caught too: smooth the guess over the welded mesh so only
  # coherent patches of hair remain
  _, wld = np.unique(np.round(P / 1e-5).astype(np.int64), axis=0, return_inverse=True); wld = wld.ravel()
  E = np.concatenate([wld[T[:, [0, 1]]], wld[T[:, [1, 2]]], wld[T[:, [2, 0]]]])
  hw = np.zeros(wld.max() + 1); np.maximum.at(hw, wld, h)
  deg = np.bincount(E.ravel(), minlength=len(hw)).astype(float)
  for _ in range(8):
    acc_h = hw.copy(); np.add.at(acc_h, E[:, 0], hw[E[:, 1]]); np.add.at(acc_h, E[:, 1], hw[E[:, 0]])
    hw = acc_h / (1 + deg)
  # 0..1 hair amount: weights blend from body to hair-only across the boundary, so the fused
  # hair/jacket surface stretches gently instead of tearing
  HAIRC = np.clip((hw[wld] - .3) / .4, 0, 1)
  print('hair vertices', int((HAIRC > .5).sum()))
  if os.environ.get('HAIRDUMP'): np.save(os.environ['HAIRDUMP'], np.c_[P, HAIRC, col])

# ---------------------------------------------------------------- skin weights
DEFORM = [nm for nm in bones if nm in PRIMARY]
seg_a = np.array([L[nm] for nm in DEFORM]); seg_b = np.array([L[PRIMARY[nm]] for nm in DEFORM])

def allowed(nm, p, hairy=False):
  # Which vertices a bone may influence, relative to the joints (keeps hair off the arms, legs apart, etc.)
  x, y, z = p[:, 0], p[:, 1], p[:, 2]; ax = np.abs(x)
  Y = lambda b_: L[b_][1]
  arm, hand = L['LeftArm'], L['LeftHand']
  # long hair hanging in front of or behind the shoulders: outside the sleeve's depth range
  hair = (ax < arm[0] + .06) & ((z > arm[2] + .045) | (z < arm[2] - .055))
  if hairy: hair = np.ones(len(p), bool)
  sideok = (x > .004) if nm.startswith('Left') else (x < -.004) if nm.startswith('Right') else np.ones(len(p), bool)
  if 'Hand' in nm and nm[-1] in '123':
    base = (ax > hand[0] + .005) & (z > -.012) if 'Thumb' in nm else (ax > hand[0] + .025)
    return sideok & base & (y > hand[1] - .046)
  if nm.endswith(('Arm', 'ForeArm', 'Hand')):
    cap = (ax > arm[0] - .02) & (y > arm[1] + .005)   # top of the shoulder rides along with the arm
    return sideok & ~hair & ((ax > .098) | cap) & (y > arm[1] - .11) & (y < arm[1] + .06) & ~((y < arm[1] - F['PIT']) & (ax < arm[0] + .04))
  if nm.endswith('Shoulder'): return sideok & ~hair & (ax > .03) & (y > arm[1] - .05) & (y < arm[1] + .07)
  if nm.endswith(('UpLeg', 'Leg')): return sideok & (y < Y('Hips') + .06)
  if nm.endswith('Foot'): return sideok & (y < .15)
  if nm.endswith('ToeBase'): return sideok & (y < .06)
  return {'Head': y > Y('Head') - .03, 'Neck': (y > Y('Neck') - .045) & (y < Y('Neck') + .095),
          'Spine2': y > Y('Spine2') - .075, 'Spine1': (y > Y('Spine1') - .075) & (y < Y('Spine1') + .125),
          'Spine': (y > Y('Spine') - .095) & (y < Y('Spine') + .105), 'Hips': y < Y('Hips') + .10}[nm]

def dense_weights(p, hairy=False):
  ab = seg_b - seg_a
  d = np.empty((len(p), len(DEFORM)))
  for i in range(len(DEFORM)):
    t = np.clip(((p - seg_a[i]) @ ab[i]) / (ab[i] @ ab[i]), 0, 1)
    d[:, i] = np.linalg.norm(p - (seg_a[i] + t[:, None] * ab[i]), axis=1)
    d[~allowed(DEFORM[i], p, hairy), i] = np.inf
  # rigid face: lips, eyes and brows must move only by blendshapes
  hard = (p[:, 1] > F['CHIN'] - .01) & (np.abs(p[:, 0]) < .075) & (p[:, 2] > .02)
  d[hard] = np.inf; d[hard, DEFORM.index('Head')] = .01
  d = np.maximum(d, .004)
  w = (d.min(1, keepdims=True) / d) ** 7
  return w / w.sum(1, keepdims=True)

def weights(p):
  w = dense_weights(p)
  if HAIRC is not None:
    a = HAIRC[:, None]; w = (1 - a) * w + a * dense_weights(p, hairy=True)
  idx = np.argsort(-w, 1)[:, :4]
  ww = np.take_along_axis(w, idx, 1); ww /= ww.sum(1, keepdims=True)
  ww[ww < .01] = 0; ww /= ww.sum(1, keepdims=True)
  return idx, ww

Jn, Wn = weights(P)
Jn = np.array([bones.index(DEFORM[k]) for k in range(len(DEFORM))])[Jn]
if os.environ.get('WDUMP'): np.savez(os.environ['WDUMP'], P=P, J=Jn, W=Wn, bones=np.array(bones), H=HAIRC if HAIRC is not None else 0)
Jm = np.zeros((len(MP), 4), int); Jm[:, 0] = bones.index('Head'); Wm = np.zeros((len(MP), 4)); Wm[:, 0] = 1

# ---------------------------------------------------------------- blendshapes (computed in source units)
x, y, z = P[:, 0], P[:, 1], P[:, 2]
front = np.clip((z - .03) / .015, 0, 1)
def bump(cx, cy, rx, ry):
  r2 = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
  return np.where(r2 < 1, (1 - r2) ** 2, 0) * front
def sstep(a, b_, v):
  t = np.clip((v - a) / (b_ - a), 0, 1); return t * t * (3 - 2 * t)
ly = lipline(x)
hw = (XR - XL) / 2
up, lo = side > 0, side < 0
lipprof = np.sqrt(np.clip(1 - ((x - CX) / hw) ** 2, 0, 1))
broad = np.clip(1 - ((x - CX) / .036) ** 2, 0, 1) ** 1.5
below = np.clip((ly - y) / .012, 0, 1)
jawprof = (lipprof * (1 - below) + broad * below) * sstep(F['CHIN'] - .02, F['CHIN'] + .002, y) * front * (np.abs(x - CX) < .045)
lipnear_up = (1 - sstep(0, .008, y - ly)) * lipprof * front
lipnear_lo = (1 - sstep(0, .008, ly - y)) * lipprof * front
mouthw = bump(CX, MY - .001, .032, .02)

def V(dx=0, dy=0, dz=0):
  d = np.zeros_like(P); d[:, 0] += dx; d[:, 1] += dy; d[:, 2] += dz; return d
SH = {}
J = .0095
SH['jawOpen'] = V(dy=np.where(lo, -J * jawprof, 0) + np.where(up, .0012 * lipnear_up, 0),
                  dz=np.where(lo, -.35 * J * jawprof, 0))
SH['jawForward'] = V(dz=np.where(lo, .002 * jawprof, 0))
SH['jawLeft'] = V(dx=np.where(lo, .002 * jawprof, 0)); SH['jawRight'] = V(dx=np.where(lo, -.002 * jawprof, 0))
SH['mouthClose'] = V(dz=.0005 * mouthw)
for nm, sx in (('Left', 1), ('Right', -1)):
  cx = XR if sx > 0 else XL
  c = bump(cx, MY + .0006, .013, .011)
  SH[f'mouthSmile{nm}'] = V(dx=sx * .0025 * c, dy=.0035 * c, dz=-.0015 * c)
  SH[f'mouthFrown{nm}'] = V(dx=sx * .001 * c, dy=-.003 * c)
  SH[f'mouthStretch{nm}'] = V(dx=sx * .0035 * c, dy=-.0008 * c)
  SH[f'mouthDimple{nm}'] = V(dx=sx * .001 * c, dz=-.002 * c)
  half = mouthw * sstep(-.004, .004, sx * (x - CX))
  SH[f'mouthPress{nm}'] = V(dy=-.3 * (y - ly) * half, dz=-.001 * half)
  SH[f'mouthUpperUp{nm}'] = V(dy=np.where(up, .0022 * lipnear_up * sstep(-.006, .006, sx * (x - CX)), 0))
  SH[f'mouthLowerDown{nm}'] = V(dy=np.where(lo, -.0028 * lipnear_lo * sstep(-.006, .006, sx * (x - CX)), 0))
  SH[f'mouth{nm}'] = V(dx=sx * .003 * mouthw)
  ch = bump(sx * .036, MY + .01, .018, .016)
  SH[f'cheekSquint{nm}'] = V(dy=.0018 * ch)
  ns = bump(sx * .008, MY + .019, .007, .006)
  SH[f'noseSneer{nm}'] = V(dy=.0015 * ns, dz=-.0005 * ns)
  # eyes: painted, so blink squashes the eye region onto the lower lid line
  ex, ey, rx, ry = sx * F['EX'] + F['EXO'], F['EY'], F['ERX'], F['ERY']
  r = np.sqrt(((x - ex) / rx) ** 2 + ((y - ey) / ry) ** 2)
  ew = (1 - sstep(1.0, 1.45, r)) * front
  lid = ey - .55 * ry
  SH[f'eyeBlink{nm}'] = V(dy=np.where(y > lid, .96, .45) * (lid - y) * ew)
  SH[f'eyeSquint{nm}'] = V(dy=np.where(y < ey, .3 * (ey - y), -.08 * (y - ey)) * ew)
  SH[f'eyeWide{nm}'] = V(dy=np.where(y > ey, .16 * (y - ey), 0) * ew)
  bw = bump(sx * F['EX'] + F['EXO'], F['BROW'], .026, .012)
  inner = bump(sx * .011 + F['EXO'], F['BROW'] - .001, .013, .011)
  outer = bump(sx * .042 + F['EXO'], F['BROW'], .015, .012)
  SH[f'browDown{nm}'] = V(dy=-.0022 * bw - .001 * inner, dx=-sx * .001 * inner)
  SH[f'browOuterUp{nm}'] = V(dy=.003 * outer)
  for k in ('LookUp', 'LookDown', 'LookIn', 'LookOut'): SH[f'eye{k}{nm}'] = V()
ib = bump(-.011 + F['EXO'], F['BROW'] - .001, .013, .011) + bump(.011 + F['EXO'], F['BROW'] - .001, .013, .011)
SH['browInnerUp'] = V(dy=.0032 * ib)
SH['cheekPuff'] = (bump(.036, MY + .006, .02, .02) + bump(-.036, MY + .006, .02, .02))[:, None] * N * .003
SH['mouthPucker'] = V(dx=-.3 * (x - CX) * mouthw, dz=.003 * mouthw)
SH['mouthFunnel'] = V(dx=-.2 * (x - CX) * mouthw, dz=.0025 * mouthw,
                      dy=np.where(up, .0015 * lipnear_up, -.0022 * lipnear_lo))
SH['mouthRollLower'] = V(dy=np.where(lo, -.4 * (y - ly) * mouthw, 0), dz=np.where(lo, -.0015 * mouthw, 0))
SH['mouthRollUpper'] = V(dy=np.where(up, -.4 * (y - ly) * mouthw, 0), dz=np.where(up, -.0015 * mouthw, 0))
SH['mouthShrugLower'] = V(dy=np.where(lo, .0012 * lipnear_lo, 0), dz=np.where(lo, .001 * mouthw, 0))
SH['mouthShrugUpper'] = V(dy=np.where(up, .001 * lipnear_up, 0))
SH['tongueOut'] = V()

ARKIT = ['eyeBlinkLeft', 'eyeLookDownLeft', 'eyeLookInLeft', 'eyeLookOutLeft', 'eyeLookUpLeft', 'eyeSquintLeft', 'eyeWideLeft',
         'eyeBlinkRight', 'eyeLookDownRight', 'eyeLookInRight', 'eyeLookOutRight', 'eyeLookUpRight', 'eyeSquintRight', 'eyeWideRight',
         'jawForward', 'jawLeft', 'jawRight', 'jawOpen', 'mouthClose', 'mouthFunnel', 'mouthPucker', 'mouthLeft', 'mouthRight',
         'mouthSmileLeft', 'mouthSmileRight', 'mouthFrownLeft', 'mouthFrownRight', 'mouthDimpleLeft', 'mouthDimpleRight',
         'mouthStretchLeft', 'mouthStretchRight', 'mouthRollLower', 'mouthRollUpper', 'mouthShrugLower', 'mouthShrugUpper',
         'mouthPressLeft', 'mouthPressRight', 'mouthLowerDownLeft', 'mouthLowerDownRight', 'mouthUpperUpLeft', 'mouthUpperUpRight',
         'browDownLeft', 'browDownRight', 'browInnerUp', 'browOuterUpLeft', 'browOuterUpRight', 'cheekPuff', 'cheekSquintLeft',
         'cheekSquintRight', 'noseSneerLeft', 'noseSneerRight', 'tongueOut']
assert set(ARKIT) == set(SH), set(ARKIT) ^ set(SH)
def mix(**kw):
  return sum(SH[k] * v for k, v in kw.items())
both = lambda base, v: {base + 'Left': v, base + 'Right': v}
VIS = {
  'viseme_sil': V(),
  'viseme_PP': mix(**both('mouthPress', .6), mouthRollLower=.2),
  'viseme_FF': mix(jawOpen=.12, mouthRollLower=.6, **both('mouthUpperUp', .4)),
  'viseme_TH': mix(jawOpen=.25, **both('mouthUpperUp', .2)),
  'viseme_DD': mix(jawOpen=.3, **both('mouthStretch', .25)),
  'viseme_kk': mix(jawOpen=.35, **both('mouthStretch', .3)),
  'viseme_CH': mix(jawOpen=.2, mouthFunnel=.6, **both('mouthUpperUp', .3)),
  'viseme_SS': mix(jawOpen=.12, **both('mouthStretch', .45), **{'mouthUpperUpLeft': .3, 'mouthUpperUpRight': .3}),
  'viseme_nn': mix(jawOpen=.22, **both('mouthStretch', .15)),
  'viseme_RR': mix(jawOpen=.2, mouthFunnel=.45),
  'viseme_aa': mix(jawOpen=.75, **both('mouthUpperUp', .2)),
  'viseme_E': mix(jawOpen=.4, **both('mouthStretch', .45)),
  'viseme_I': mix(jawOpen=.25, **both('mouthStretch', .6), **{'mouthSmileLeft': .2, 'mouthSmileRight': .2}),
  'viseme_O': mix(jawOpen=.45, mouthFunnel=.7),
  'viseme_U': mix(jawOpen=.15, mouthPucker=.9),
}
TARGETS = ARKIT + list(VIS)
DELTAS = [SH[k] for k in ARKIT] + [VIS[k] for k in VIS]
print('nonzero per target', [int((np.abs(d).max(1) > 1e-6).sum()) for d in DELTAS][:20])

# ---------------------------------------------------------------- glTF out
buf = bytearray()
views, accs = [], []
def view(data, target=None):
  while len(buf) % 4: buf.append(0)
  v = {'buffer': 0, 'byteOffset': len(buf), 'byteLength': len(data)}
  if target: v['target'] = target
  buf.extend(data); views.append(v); return len(views) - 1
def accessor(arr, ctype, typ, target=None, minmax=False):
  arr = np.ascontiguousarray(arr)
  a = {'bufferView': view(arr.tobytes(), target), 'componentType': ctype, 'count': len(arr), 'type': typ}
  if minmax: a['min'] = arr.min(0).tolist(); a['max'] = arr.max(0).tolist()
  accs.append(a); return len(accs) - 1
def sparse_target(d):
  d = (d * S).astype(np.float32)
  nz = np.nonzero(np.abs(d).max(1) > 1e-7)[0]
  a = {'componentType': 5126, 'count': len(d), 'type': 'VEC3', 'min': d.min(0).tolist(), 'max': d.max(0).tolist()}
  if len(nz):
    a['sparse'] = {'count': int(len(nz)),
                   'indices': {'bufferView': view(nz.astype(np.uint32).tobytes()), 'componentType': 5125},
                   'values': {'bufferView': view(d[nz].tobytes())}}
  accs.append(a); return len(accs) - 1

ARRAY, ELEM = 34962, 34963
attrs = {
  'POSITION': accessor((P * S).astype(np.float32), 5126, 'VEC3', ARRAY, True),
  'NORMAL': accessor(N.astype(np.float32), 5126, 'VEC3', ARRAY),
  'TEXCOORD_0': accessor(UV.astype(np.float32), 5126, 'VEC2', ARRAY),
  'JOINTS_0': accessor(Jn.astype(np.uint16), 5123, 'VEC4', ARRAY),
  'WEIGHTS_0': accessor(Wn.astype(np.float32), 5126, 'VEC4', ARRAY),
}
idx = accessor(T.astype(np.uint32).ravel(), 5125, 'SCALAR', ELEM)
targets = [{'POSITION': sparse_target(d)} for d in DELTAS]
mattrs = {
  'POSITION': accessor((MP * S).astype(np.float32), 5126, 'VEC3', ARRAY, True),
  'NORMAL': accessor(MN.astype(np.float32), 5126, 'VEC3', ARRAY),
  'COLOR_0': accessor(MC, 5126, 'VEC4', ARRAY),
  'JOINTS_0': accessor(Jm.astype(np.uint16), 5123, 'VEC4', ARRAY),
  'WEIGHTS_0': accessor(Wm.astype(np.float32), 5126, 'VEC4', ARRAY),
}
midx = accessor(MT.astype(np.uint32).ravel(), 5125, 'SCALAR', ELEM)
accs.append({'componentType': 5126, 'count': len(MP), 'type': 'VEC3', 'min': [0, 0, 0], 'max': [0, 0, 0]})
zero = len(accs) - 1

# textures from the source file. Big 4K PNGs (Kimmy3's normal and roughness maps) are re-encoded as JPEG
# so the download stays small enough for phones; the roughness/metal map has no fine detail, so it goes to 2K.
mat = dict(j['materials'][0]); mat['name'] = 'Kimmy'; mat.pop('extensions', None)
rm_tex = mat.get('pbrMetallicRoughness', {}).get('metallicRoughnessTexture')
rm_img = j['textures'][rm_tex['index']]['source'] if rm_tex else None
images = []
for ii, im in enumerate(j['images']):
  bv = j['bufferViews'][im['bufferView']]
  data = b[bv.get('byteOffset', 0): bv.get('byteOffset', 0) + bv['byteLength']]
  mime = im['mimeType']
  if mime == 'image/png' and len(data) > 2_000_000:
    import io
    from PIL import Image
    img = Image.open(io.BytesIO(data)).convert('RGB')
    if ii == rm_img: img = img.resize((img.width // 2, img.height // 2), Image.LANCZOS)
    o = io.BytesIO(); img.save(o, 'JPEG', quality=90); data, mime = o.getvalue(), 'image/jpeg'
  images.append({'bufferView': view(data), 'mimeType': mime})
if PROFILE == 'kimmy3': mat['pbrMetallicRoughness']['metallicFactor'] = 0   # skin and cloth: no metal
mouth_mat = {'name': 'KimmyMouth', 'pbrMetallicRoughness': {'baseColorFactor': [1, 1, 1, 1], 'metallicFactor': 0, 'roughnessFactor': .7}}

# nodes: 0 Armature, 1 mesh, then bones
nodes = [{'name': 'Armature', 'children': []}, {'name': 'Kimmy', 'mesh': 0, 'skin': 0}]
bi = {nm: 2 + k for k, nm in enumerate(bones)}
for nm in bones:
  q, t = local[nm]
  nd = {'name': nm, 'rotation': [float(v) for v in q / np.linalg.norm(q)], 'translation': [float(v) for v in t]}
  kids = [bi[c] for c in bones if rparent(c) == nm]
  if kids: nd['children'] = kids
  nodes.append(nd)
nodes[0]['children'] = [bi['Hips'], 1]
# inverse bind matrices from the bind (rest) pose
ibm = []
for nm in bones:
  M = np.eye(4); M[:3, :3] = Rk[nm]; M[:3, 3] = L[nm] * S
  ibm.append(np.linalg.inv(M).T.ravel())  # column-major
ibm_acc = accessor(np.array(ibm, np.float32), 5126, 'MAT4')

gl = {
  'asset': {'version': '2.0', 'generator': 'kimmy rig builder'},
  'scene': 0, 'scenes': [{'name': 'Scene', 'nodes': [0]}], 'nodes': nodes,
  'meshes': [{'name': 'Kimmy', 'primitives': [
      {'attributes': attrs, 'indices': idx, 'material': 0, 'targets': targets},
      {'attributes': mattrs, 'indices': midx, 'material': 1, 'targets': [{'POSITION': zero} for _ in TARGETS]}],
    'weights': [0] * len(TARGETS), 'extras': {'targetNames': TARGETS}}],
  'skins': [{'name': 'Armature', 'joints': [bi[nm] for nm in bones], 'inverseBindMatrices': ibm_acc}],
  'materials': [mat, mouth_mat], 'textures': j['textures'], 'samplers': j.get('samplers', [{}]), 'images': images,
  'accessors': accs, 'bufferViews': views, 'buffers': [{'byteLength': 0}],
}
while len(buf) % 4: buf.append(0)
gl['buffers'][0]['byteLength'] = len(buf)
js = json.dumps(gl, separators=(',', ':')).encode()
js += b' ' * (-len(js) % 4)
out = struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(buf)) + struct.pack('<II', len(js), 0x4E4F534A) + js + struct.pack('<II', len(buf), 0x004E4942) + bytes(buf)
open(OUT, 'wb').write(out)
print('wrote', OUT, len(out) // 1024, 'KB', 'height', round(P[:, 1].max() * S, 3))
