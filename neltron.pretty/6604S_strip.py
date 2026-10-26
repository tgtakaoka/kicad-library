# Round-pin single-row IC socket strip (Neltron 6604S style, Akizuki 101591),
# from the Akizuki dimension guide: B = 2.54 wide, C = 4.2 stack height,
# D = 3.23 lead length, 2.54 pitch; details after the user's photos: V notches
# on both sides between cells, tin sleeve and tail, gold inner contact, tin
# collar under the housing.  Pin 1 at the origin, strip along +X, board top
# surface at Z = 0.
import sys
import cadquery as cq

n = int(sys.argv[1]) if len(sys.argv) > 1 else 32
out = sys.argv[2] if len(sys.argv) > 2 else f'6604S-{n}.step'
P, B, C, D = 2.54, 2.54, 4.2, 3.23
COLLAR_H, COLLAR_D = 0.6, 1.1
SLEEVE_OD, OPEN_D, TAIL_D = 1.6, 0.8, 0.5
NOTCH_W, NOTCH_D = 0.7, 0.35
L = n * P
x0 = -P / 2

housing = (cq.Workplane('XY').workplane(offset=COLLAR_H)
           .center(x0 + L / 2, 0).box(L, B, C - COLLAR_H, centered=(True, True, False)))
# V notches on both long sides between cells, full height
for k in range(1, n):
    x = x0 + k * P
    for s in (1, -1):
        tri = (cq.Workplane('XY').workplane(offset=COLLAR_H - 0.1)
               .polyline([(x - NOTCH_W / 2, s * B / 2), (x, s * (B / 2 - NOTCH_D)),
                          (x + NOTCH_W / 2, s * B / 2), (x + NOTCH_W / 2, s * (B / 2 + 0.2)),
                          (x - NOTCH_W / 2, s * (B / 2 + 0.2))]).close()
               .extrude(C))
        housing = housing.cut(tri)
pts = [(k * P, 0) for k in range(n)]
housing = housing.cut(cq.Workplane('XY').pushPoints(pts).circle(SLEEVE_OD / 2).extrude(C + 1))

tin = gold = None
for x, y in pts:
    sleeve = (cq.Workplane('XY').workplane(offset=COLLAR_H).center(x, y)
              .circle(SLEEVE_OD / 2).extrude(C - COLLAR_H)
              .cut(cq.Workplane('XY').workplane(offset=COLLAR_H + 0.3).center(x, y)
                   .circle(SLEEVE_OD / 2 - 0.2).extrude(C)))
    collar = cq.Workplane('XY').center(x, y).circle(COLLAR_D / 2).extrude(COLLAR_H)
    tail = cq.Workplane('XY').workplane(offset=-D).center(x, y).circle(TAIL_D / 2).extrude(D)
    t = sleeve.union(collar).union(tail)
    tin = t if tin is None else tin.union(t)
    # gold inner contact seen through the opening, its top just below the rim
    insert = (cq.Workplane('XY').workplane(offset=COLLAR_H + 0.3).center(x, y)
              .circle(SLEEVE_OD / 2 - 0.2).extrude(C - COLLAR_H - 0.45)
              .cut(cq.Workplane('XY').workplane(offset=COLLAR_H + 1.0).center(x, y)
                   .circle(OPEN_D / 2).extrude(C)))
    gold = insert if gold is None else gold.union(insert)

asm = cq.Assembly(name=f'6604S-{n}')
asm.add(housing, name='housing', color=cq.Color(0.06, 0.06, 0.06))
asm.add(tin, name='tin', color=cq.Color(0.78, 0.78, 0.76))
asm.add(gold, name='gold', color=cq.Color(0.86, 0.68, 0.28))
asm.save(out, 'STEP')
print('wrote', out)
