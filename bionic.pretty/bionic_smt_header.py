# Bionic SMD connector model: KiCad's PinHeader_1x24_P2.54mm_Vertical_SMD_Pin1Right
# with the metal of the unpopulated positions removed (the body keeps its holes)
# and straight through-hole pins at both ends, where the footprint has THT pads.
# usage: bionic_smt_header.py <in.step> <out.step> <missing y,...> <straight y,...>
# (model y = -footprint y)
import sys, collections
import cadquery as cq
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorType
from OCP.TDF import TDF_LabelSequence
from OCP.Quantity import Quantity_Color
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib

src, out = sys.argv[1], sys.argv[2]
missing = [float(v) for v in sys.argv[3].split(',')]
straight = [float(v) for v in sys.argv[4].split(',')]
POST, TOP, TAIL, CHAMFER = 0.64, 9.3, 3.0, 0.12
doc = TDocStd_Document(TCollection_ExtendedString('d'))
r = STEPCAFControl_Reader(); r.SetColorMode(True); r.ReadFile(src); r.Transfer(doc)
st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main()); ct = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
labs = TDF_LabelSequence(); st.GetFreeShapes(labs); shape = st.GetShape_s(labs.Value(1))

groups, dropped = collections.defaultdict(list), 0
ex = TopExp_Explorer(shape, TopAbs_FACE)
while ex.More():
    f = ex.Current(); c = Quantity_Color()
    ct.GetColor(f, XCAFDoc_ColorType.XCAFDoc_ColorSurf, c) or ct.GetColor(f, XCAFDoc_ColorType.XCAFDoc_ColorGen, c)
    rgb = (c.Red(), c.Green(), c.Blue())
    b = Bnd_Box(); BRepBndLib.Add_s(f, b); x0, y0, z0, x1, y1, z1 = b.Get()
    metal = rgb[0] > 0.3
    if metal and any(abs((y0 + y1) / 2 - m) < 1.0 and y1 - y0 < 2.0 for m in missing + straight):
        dropped += 1
    else:
        groups[rgb].append(cq.Face(f))
    ex.Next()

gold = max(groups, key=lambda rgb: rgb[0])
pins = None
for y in straight:
    pin = (cq.Workplane('XY').workplane(offset=-TAIL).center(0, y)
           .rect(POST, POST).extrude(TOP + TAIL)
           .faces('>Z').edges().chamfer(CHAMFER).faces('<Z').edges().chamfer(CHAMFER))
    pins = pin if pins is None else pins.union(pin)

asm = cq.Assembly(name='Bionic_SMT_1x24')
asm.add(pins, name='straight_pins', color=cq.Color(*gold))
for i, (rgb, faces) in enumerate(groups.items()):
    asm.add(cq.Compound.makeCompound(faces), name=f'part{i}', color=cq.Color(*rgb))
asm.save(out, 'STEP')
print('dropped', dropped, 'faces; kept', {k: len(v) for k, v in groups.items()})
