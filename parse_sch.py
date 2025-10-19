import json
from pathlib import Path
import sexpdata

def safe_val(x):
    """Return string for both Symbol or plain string."""
    if hasattr(x, "value"):
        return x.value()
    return str(x)


def find_all(keyword, tree):
    """Recursively find all lists that start with a given keyword."""
    results = []
    if isinstance(tree, list) and len(tree) > 0:
        head = safe_val(tree[0])
        if head == keyword:
            results.append(tree)
        for item in tree[1:]:
            results.extend(find_all(keyword, item))
    return results


def value_for(tree, key):
    """Get a property value for a key within a symbol definition."""
    for p in find_all("property", tree):
        if len(p) >= 3:
            k = safe_val(p[1])
            v = safe_val(p[2])
            if k == key:
                return v
    return None


def get_symbol_lib(tree):
    """Extract the library ID if present."""
    for p in tree:
        if isinstance(p, list) and len(p) >= 2 and safe_val(p[0]) == "lib_id":
            return safe_val(p[1])
    return ""


def parse_kicad_sch(path: Path):
    """Parse a KiCad schematic (.kicad_sch) and extract components, nets, and footprints."""
    text = path.read_text(encoding="utf-8")
    data = sexpdata.loads(text)

    components = []
    nets = []
    footprint_suggestions = {}

    # --- COMPONENTS ---
    for symbol in find_all("symbol", data):
        ref = value_for(symbol, "Reference") or ""
        val = value_for(symbol, "Value") or ""
        fp = value_for(symbol, "Footprint") or ""
        lib = get_symbol_lib(symbol)

        # if not ref:
        #     continue
        import re
        if not ref or not re.search(r"\d", ref):
            continue  # skip generic symbols like "U", "R", "C"


        components.append({
            "ref": ref,
            "value": val,
            "footprint": fp,
            "lib_id": lib,
        })

        # Footprint suggestions
        if ref.startswith("R"):
            footprint_suggestions[ref] = "Resistor_SMD:R_0603"
        elif ref.startswith("C"):
            footprint_suggestions[ref] = "Capacitor_SMD:C_0603"
        elif ref.startswith("U"):
            footprint_suggestions[ref] = "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"
        elif ref.startswith("J"):
            footprint_suggestions[ref] = "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"
        elif ref.startswith("TP"):
            footprint_suggestions[ref] = "TestPoint:TestPoint_Pad_D1.0mm"
        else:
            footprint_suggestions[ref] = "Resistor_SMD:R_0603"

    # --- NET LABELS ---
    for label in find_all("label", data):
        if len(label) > 1:
            name = safe_val(label[1])
            nets.append({
                "name": name,
                "code": len(nets) + 1,
                "nodes": []
            })

    # --- PIN CONNECTIONS ---
    for symbol in find_all("symbol", data):
        # Safe property extraction
        props = {}
        for p in find_all("property", symbol):
            if len(p) >= 3:
                props[safe_val(p[1])] = safe_val(p[2])

        ref = props.get("Reference", "")
        if not ref:
            continue

        for pin in find_all("pin", symbol):
            pin_num = ""
            for part in pin:
                if isinstance(part, list) and len(part) >= 2:
                    if safe_val(part[0]) == "number":
                        pin_num = safe_val(part[1])
            if pin_num:
                nets.append({
                    "name": f"NET_{ref}_{pin_num}",
                    "code": len(nets) + 1,
                    "nodes": [{"ref": ref, "pin": pin_num}]
                })

    return {
        "components": components,
        "nets": nets,
        "footprint_suggestions": footprint_suggestions,
    }


# ---------- MAIN EXECUTION ----------
if __name__ == "__main__":
    input_path = Path("outputs/Lab4.kicad_sch")  # your schematic file
    result = parse_kicad_sch(input_path)

    output_path = Path("outputs/Lab4_parsed.json")
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2))

    print(f"✅ Parsed schematic saved to: {output_path}")
    print(f"📦 Components: {len(result['components'])}, Nets: {len(result['nets'])}")
