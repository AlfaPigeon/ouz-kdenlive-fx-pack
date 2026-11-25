#!/usr/bin/env python3
"""Static validation of the pack against a Kdenlive data directory.

Checks: XML well-formed; effect-template root/ids; every effect id used inside a
group exists in Kdenlive's effect definitions; every property is a declared
parameter of that effect; >1 effect per group (Kdenlive treats single-effect
groups differently); composition tags exist; luma files referenced exist.

usage: validate.py <kdenlive-data-dir> [<kdenlive-data-dir> ...]
       e.g. /usr/share/kdenlive  or  a kdenlive git checkout's data/
"""
import glob
import os
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def load_defs(datadir):
    defs = {}
    for path in glob.glob(os.path.join(datadir, "effects", "**", "*.xml"), recursive=True):
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        nodes = [root] if root.tag.endswith("effect") else root.iter()
        for e in nodes:
            if not str(e.tag).endswith("effect"):
                continue
            eid = e.get("id") or e.get("tag")
            if not eid:
                continue
            params = set()
            for p in e:
                if str(p.tag).endswith("parameter"):
                    for n in (p.get("name") or "").split("\n"):
                        params.add(n)
            defs.setdefault(eid, set()).update(params)
    return defs


def main(dirs):
    errors = 0
    files = glob.glob(os.path.join(ROOT, "pack", "**", "*.xml"), recursive=True)
    for f in files:
        try:
            ET.parse(f)
        except ET.ParseError as e:
            print("XML ERROR", f, e)
            errors += 1
    print(f"well-formed: {len(files)} XML files")
    for d in dirs:
        defs = load_defs(d)
        print(f"\n== against {d} ({len(defs)} effect ids)")
        n = 0
        for f in sorted(glob.glob(os.path.join(ROOT, "pack", "*", "effect-templates", "*.xml"))):
            root = ET.parse(f).getroot()
            assert root.tag == "effectgroup", f
            effs = root.findall("effect")
            warned = globals().setdefault("warned", set())
            if len(effs) < 2:
                print("ERROR <2 effects", f); errors += 1
            for e in effs:
                eid = e.get("id")
                if eid not in defs:
                    print("ERROR unknown effect", eid, os.path.basename(f)); errors += 1; continue
                for p in e.findall("property"):
                    if p.get("name") not in defs[eid] and (eid, p.get("name")) not in warned:
                        # newer-Kdenlive parameter: older versions just pass it to MLT, which ignores it
                        warned.add((eid, p.get("name")))
                        print("WARN param not in this Kdenlive version (ignored there):", eid, p.get("name"))
            n += 1
        print(f"effect templates checked: {n}")
        tdefs = set()
        for path in glob.glob(os.path.join(d, "transitions", "**", "*.xml"), recursive=True):
            try:
                r = ET.parse(path).getroot()
                tdefs.add(r.get("tag"))
            except ET.ParseError:
                pass
        for f in glob.glob(os.path.join(ROOT, "pack", "*", "transitions", "*.xml")):
            r = ET.parse(f).getroot()
            if r.get("tag") not in tdefs:
                print("ERROR unknown transition tag", r.get("tag"), f); errors += 1
            for p in r.findall("parameter"):
                v = p.get("value") or ""
                if "@LUMADIR@" in v:
                    luma = v.replace("@LUMADIR@", os.path.join(ROOT, "pack", "lumas"))
                    if not os.path.exists(luma):
                        print("ERROR missing luma", luma); errors += 1
    print("\nRESULT:", "OK" if errors == 0 else f"{errors} errors")
    return errors


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1:] or ["/usr/share/kdenlive"]) else 0)
