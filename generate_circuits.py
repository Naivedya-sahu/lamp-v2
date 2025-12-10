#!/usr/bin/env python3
"""
generate_circuits.py

MVP generator:
- Loads Library.svg (symbol source).
- Places symbols to create simple circuits (R, RC, LC, RLC, R-series, R-parallel).
- Draws simple orthogonal wires between symbol pins.
- Emits schematic SVG and netlist JSON.

Usage:
    python3 generate_circuits.py --out-dir ./out --variant rc

Variants supported: r, rc, lc, rlc_series, r_series, r_parallel

Note: update SYMBOL_IDS and PIN_MAP to match your Library.svg symbol ids and desired pin coordinates.
"""

import argparse
import copy
import json
import math
import os
import xml.etree.ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)

# === CONFIG ===
LIBRARY_SVG = "examples/Library.svg"   # path to uploaded library
OUTPUT_DIR = "out"

# Map logical symbol names to element ids in Library.svg
SYMBOL_IDS = {
    "R": "resistor",    # change if your library uses different ids
    "C": "capacitor",
    "L": "inductor",
    "GND": "gnd",
    "V": "vplus",
    # If library has pin helper or anchor, optionally use it
}

# Pin coordinate map (relative to symbol origin). Units are SVG units (assume px).
# Use approx positions for common symbols; refine later by inspecting Library.svg
PIN_MAP = {
    "R": [(0, 12), (100, 12)],       # left pin, right pin
    "C": [(0, 12), (100, 12)],
    "L": [(0, 12), (100, 12)],
    "GND": [(10, 10)],
    "V": [(10, 10)]
}

GRID_SPACING = 160   # spacing between symbol centers
SYMBOL_SCALE = 1.0

# Output filenames template
SVG_TEMPLATE = "schematic_{variant}.svg"
NETLIST_TEMPLATE = "netlist_{variant}.json"

# === Helpers ===

def ns(tag):
    return f"{{{SVG_NS}}}{tag}"

def load_svg_tree(path):
    return ET.parse(path)

def find_symbol_element(lib_tree, symbol_id):
    root = lib_tree.getroot()
    # search for element with matching id (any tag)
    for elem in root.iter():
        if 'id' in elem.attrib and elem.attrib['id'] == symbol_id:
            return elem
    return None

def clone_element(elem):
    # deep copy
    return copy.deepcopy(elem)

def create_root_svg(width=1200, height=800):
    root = ET.Element(ns("svg"), {
        "width": str(width),
        "height": str(height),
        "viewBox": f"0 0 {width} {height}",
        "version":"1.1",
        "xmlns": SVG_NS
    })
    return ET.ElementTree(root)

def add_symbol_to_svg(root, symbol_elem, x, y, scale=1.0, id_suffix=None):
    # Wrap in <g transform="translate(x,y) scale(s)">
    g = ET.Element(ns("g"))
    transform = f"translate({x},{y}) scale({scale})"
    if id_suffix:
        g.set("id", f"{symbol_elem.get('id')}_{id_suffix}")
    else:
        if 'id' in symbol_elem.attrib:
            g.set("id", symbol_elem.attrib['id'])
    g.set("transform", transform)
    # copy all children of symbol_elem into this group
    # if symbol_elem itself is a group copy children; if it's a shape copy itself.
    if len(symbol_elem):
        for c in symbol_elem:
            g.append(copy.deepcopy(c))
    else:
        g.append(copy.deepcopy(symbol_elem))
    root.append(g)
    return g

def svg_line(x1,y1,x2,y2, stroke="black", stroke_width=2):
    return ET.Element(ns("line"), {
        "x1": str(x1),
        "y1": str(y1),
        "x2": str(x2),
        "y2": str(y2),
        "stroke": stroke,
        "stroke-width": str(stroke_width),
        "stroke-linecap": "round",
        "fill": "none"
    })

def orthogonal_route(p1, p2, mid_offset=0):
    # Simple L-shaped Manhattan connector: from p1 horizontally then vertically (or vice versa)
    x1,y1 = p1
    x2,y2 = p2
    # choose an intermediate point to avoid overlap: use horizontal-first
    mx, my = x2, y1
    return [(x1,y1),(mx,my),(x2,y2)]

def save_tree(tree, path):
    tree.write(path, encoding="utf-8", xml_declaration=True)

# === Circuit builders ===

class SchematicBuilder:
    def __init__(self, lib_svg_path):
        self.lib_tree = load_svg_tree(lib_svg_path)
        self.lib_root = self.lib_tree.getroot()
        self.out_tree = create_root_svg()
        self.out_root = self.out_tree.getroot()
        self.components = []  # list of placed components
        self.nets = {}        # netname -> list of (ref, pin_index, abs_x, abs_y)
        self.ref_counter = {"R":1, "C":1, "L":1, "V":1}

    def place(self, symbol_key, x, y, rotation=0, ref=None):
        if symbol_key not in SYMBOL_IDS:
            raise ValueError(f"Unknown symbol key {symbol_key}. Update SYMBOL_IDS mapping.")
        symbol_id = SYMBOL_IDS[symbol_key]
        symbol_elem = find_symbol_element(self.lib_tree, symbol_id)
        if symbol_elem is None:
            raise ValueError(f"Symbol id '{symbol_id}' not found inside {LIBRARY_SVG}.")
        # clone and place
        ref_name = ref if ref else f"{symbol_key}{self.ref_counter.setdefault(symbol_key,1)}"
        self.ref_counter[symbol_key] = self.ref_counter.get(symbol_key,1) + 1
        g = add_symbol_to_svg(self.out_root, symbol_elem, x, y, SYMBOL_SCALE, id_suffix=ref_name)
        # compute absolute pin coords from PIN_MAP
        pin_points = []
        if symbol_key in PIN_MAP:
            for (px,py) in PIN_MAP[symbol_key]:
                absx = x + px*SYMBOL_SCALE
                absy = y + py*SYMBOL_SCALE
                pin_points.append((absx,absy))
        else:
            pin_points = []
        comp = {"ref": ref_name, "type": symbol_key, "x": x, "y": y, "pins": pin_points}
        self.components.append(comp)
        return comp

    def wire(self, comp_pin_a, comp_pin_b, netname=None):
        # comp_pin: (ref, pin_index)
        ref_a, pin_a = comp_pin_a
        ref_b, pin_b = comp_pin_b
        ca = next(c for c in self.components if c['ref']==ref_a)
        cb = next(c for c in self.components if c['ref']==ref_b)
        pA = ca['pins'][pin_a]
        pB = cb['pins'][pin_b]
        route = orthogonal_route(pA,pB)
        # add lines to svg
        for i in range(len(route)-1):
            l = svg_line(route[i][0], route[i][1], route[i+1][0], route[i+1][1])
            self.out_root.append(l)
        # add to nets
        net = netname if netname else f"net{len(self.nets)+1}"
        self.nets.setdefault(net, []).append((ref_a, pin_a, pA[0], pA[1]))
        self.nets.setdefault(net, []).append((ref_b, pin_b, pB[0], pB[1]))
        return net

    def connect_series(self, sequence, net_base="N"):
        # sequence: list of (ref, pin_out_index, pin_in_index) or simpler: place components and connect sequentially
        # Not used in example directly; left for extension
        pass

    def export(self, svg_path, netlist_path):
        # simplify nets: combine duplicates
        normalized = {}
        for net, entries in self.nets.items():
            key = net
            # de-dup by (ref,pin)
            seen = set()
            newlist = []
            for (r,p,x,y) in entries:
                k = (r,p)
                if k in seen: continue
                seen.add(k)
                newlist.append({"ref":r,"pin":p,"x":x,"y":y})
            normalized[key] = newlist
        # build netlist array: components + nets
        netlist = {
            "components": self.components,
            "nets": normalized
        }
        save_tree(self.out_tree, svg_path)
        with open(netlist_path, "w") as f:
            json.dump(netlist, f, indent=2)
        print(f"Wrote {svg_path} and {netlist_path}")

# === High-level scenario generators ===

def build_rc_variant(out_dir):
    s = SchematicBuilder(LIBRARY_SVG)
    # place voltage source left, resistor center, capacitor right, ground below capacitor
    v = s.place("V", 80, 160, ref="V1")
    r = s.place("R", 240, 160, ref="R1")
    c = s.place("C", 400, 160, ref="C1")
    gnd = s.place("GND", 400, 260, ref="GND1")
    # wire V1 pin0 to R1 pin0
    s.wire(("V1",0),("R1",0), netname="vin")
    # R1 pin1 to C1 pin0
    s.wire(("R1",1),("C1",0), netname="node1")
    # C1 pin1 to ground
    s.wire(("C1",1),("GND1",0), netname="gnd")
    # optionally wire V1 other pin to ground to complete circuit (depends on library V pins)
    # wire V1 pin1 to ground if exists
    if len(v['pins'])>1:
        s.wire(("V1",1),("GND1",0), netname="gnd")
    svg_path = os.path.join(out_dir, SVG_TEMPLATE.format(variant="rc"))
    netlist_path = os.path.join(out_dir, NETLIST_TEMPLATE.format(variant="rc"))
    s.export(svg_path, netlist_path)
    return svg_path, netlist_path

def build_lc_variant(out_dir):
    s = SchematicBuilder(LIBRARY_SVG)
    v = s.place("V", 80, 160, ref="V1")
    l = s.place("L", 240, 160, ref="L1")
    c = s.place("C", 400, 160, ref="C1")
    gnd = s.place("GND", 400, 260, ref="GND1")
    s.wire(("V1",0),("L1",0), netname="vin")
    s.wire(("L1",1),("C1",0), netname="node1")
    s.wire(("C1",1),("GND1",0), netname="gnd")
    if len(v['pins'])>1:
        s.wire(("V1",1),("GND1",0), netname="gnd")
    svg_path = os.path.join(out_dir, SVG_TEMPLATE.format(variant="lc"))
    netlist_path = os.path.join(out_dir, NETLIST_TEMPLATE.format(variant="lc"))
    s.export(svg_path, netlist_path)
    return svg_path, netlist_path

def build_rlc_series_variant(out_dir):
    s = SchematicBuilder(LIBRARY_SVG)
    v = s.place("V", 80, 160, ref="V1")
    r = s.place("R", 240, 160, ref="R1")
    l = s.place("L", 360, 160, ref="L1")
    c = s.place("C", 480, 160, ref="C1")
    gnd = s.place("GND", 480, 260, ref="GND1")
    s.wire(("V1",0),("R1",0), netname="vin")
    s.wire(("R1",1),("L1",0), netname="node1")
    s.wire(("L1",1),("C1",0), netname="node2")
    s.wire(("C1",1),("GND1",0), netname="gnd")
    if len(v['pins'])>1:
        s.wire(("V1",1),("GND1",0), netname="gnd")
    svg_path = os.path.join(out_dir, SVG_TEMPLATE.format(variant="rlc_series"))
    netlist_path = os.path.join(out_dir, NETLIST_TEMPLATE.format(variant="rlc_series"))
    s.export(svg_path, netlist_path)
    return svg_path, netlist_path

def build_r_series(out_dir):
    s = SchematicBuilder(LIBRARY_SVG)
    v = s.place("V", 80, 160, ref="V1")
    r1 = s.place("R", 240, 120, ref="R1")
    r2 = s.place("R", 240, 200, ref="R2")
    gnd = s.place("GND", 360, 200, ref="GND1")
    s.wire(("V1",0),("R1",0), netname="vin")
    s.wire(("R1",1),("R2",0), netname="node1")
    s.wire(("R2",1),("GND1",0), netname="gnd")
    if len(v['pins'])>1:
        s.wire(("V1",1),("GND1",0), netname="gnd")
    svg_path = os.path.join(out_dir, SVG_TEMPLATE.format(variant="r_series"))
    netlist_path = os.path.join(out_dir, NETLIST_TEMPLATE.format(variant="r_series"))
    s.export(svg_path, netlist_path)
    return svg_path, netlist_path

def build_r_parallel(out_dir):
    s = SchematicBuilder(LIBRARY_SVG)
    v = s.place("V", 80, 160, ref="V1")
    r1 = s.place("R", 240, 120, ref="R1")
    r2 = s.place("R", 240, 200, ref="R2")
    gnd = s.place("GND", 360, 200, ref="GND1")
    # connect both R1 and R2 between same nodes
    s.wire(("V1",0),("R1",0), netname="vin")
    s.wire(("V1",0),("R2",0), netname="vin")
    s.wire(("R1",1),("GND1",0), netname="gnd")
    s.wire(("R2",1),("GND1",0), netname="gnd")
    if len(v['pins'])>1:
        s.wire(("V1",1),("GND1",0), netname="gnd")
    svg_path = os.path.join(out_dir, SVG_TEMPLATE.format(variant="r_parallel"))
    netlist_path = os.path.join(out_dir, NETLIST_TEMPLATE.format(variant="r_parallel"))
    s.export(svg_path, netlist_path)
    return svg_path, netlist_path

# === CLI ===

def ensure_outdir(outdir):
    if not os.path.exists(outdir):
        os.makedirs(outdir)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out-dir", default=OUTPUT_DIR)
    p.add_argument("--variant", choices=["r","rc","lc","rlc_series","r_series","r_parallel"], default="rc")
    p.add_argument("--to-lamp", action="store_true", help="If set, run svg_to_lamp_improved.py on generated SVG (must exist locally)")
    args = p.parse_args()

    ensure_outdir(args.out_dir)

    if args.variant == "rc":
        svg, net = build_rc_variant(args.out_dir)
    elif args.variant == "lc":
        svg, net = build_lc_variant(args.out_dir)
    elif args.variant == "rlc_series":
        svg, net = build_rlc_series_variant(args.out_dir)
    elif args.variant == "r":
        svg, net = build_r_series(args.out_dir)
    elif args.variant == "r_series":
        svg, net = build_r_series(args.out_dir)
    elif args.variant == "r_parallel":
        svg, net = build_r_parallel(args.out_dir)
    else:
        raise ValueError("unknown variant")

    print("Generated:", svg, net)

    if args.to_lamp:
        # attempt to call your converter (assumes it's in the same directory or PATH)
        import subprocess, shlex
        cmd = f"python3 svg_to_lamp_improved.py --input \"{svg}\" --output \"{svg}.cmds\""
        print("Running:", cmd)
        subprocess.run(shlex.split(cmd), check=False)
        print("If svg_to_lamp_improved.py is present, it will produce pen commands file <svg>.cmds")

if __name__ == "__main__":
    main()
