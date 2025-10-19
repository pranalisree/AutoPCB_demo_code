import json
import os
from pathlib import Path
from ai_net import infer_nets_with_gemini

# --- KiCad Environment Setup ---
os.environ["KICAD9_FOOTPRINT_DIR"] = r"C:\Program Files\KiCad\9.0\share\kicad\footprints"
os.environ["KICAD_SYMBOL_DIR"] = r"C:\Program Files\KiCad\9.0\share\kicad\symbols"

# --- Try KiCad API ---
try:
    import pcbnew
    import wx
    KICAD_AVAILABLE = True
    print("✅ KiCad API loaded successfully.")

    kicad_share = Path(r"C:\Program Files\KiCad\9.0\share\kicad")
    fp_lib_table_path = kicad_share / "template" / "fp-lib-table"

    if fp_lib_table_path.exists():
        print(f"✅ Loaded KiCad footprint libraries from {fp_lib_table_path}")
    else:
        print("⚠️ Could not find KiCad fp-lib-table — footprints may not load.")

except ImportError:
    KICAD_AVAILABLE = False
    pcbnew = None
    print("⚠️ KiCad Python API not found. Using text-only fallback.")


# --- PCB Generator Class ---
class PCBGenerator:
    def __init__(self):
        self.output_dir = Path("outputs")
        self.output_dir.mkdir(exist_ok=True)

    def generate(self, parsed_json_path: str):
        with open(parsed_json_path, "r") as f:
            data = json.load(f)

        components = data.get("components", [])
        nets = data.get("nets", [])
        footprints = data.get("footprint_suggestions", {})

        print(f"📦 Components loaded: {len(components)} | Nets detected: {len(nets)}")
        print("🤖 Sending schematic to Gemini for net inference...")

        ai_nets = infer_nets_with_gemini(data)
        print(f"✅ Gemini returned {len(ai_nets)} inferred nets.")

        if not KICAD_AVAILABLE:
            result = self._generate_text_board(components, ai_nets, footprints)
        else:
            result = self._generate_kicad_board(components, ai_nets, footprints)

        print(f"✅ Board generated successfully → {result}")
        return result

    # --- Text fallback (if KiCad not found) ---
    def _generate_text_board(self, components, nets, footprints):
        output = self.output_dir / "ai_generated_board.txt"
        with open(output, "w", encoding="utf-8") as f:
            f.write("📘 AI-Generated PCB Summary\n")
            f.write("=" * 50 + "\n\n")

            f.write("Components:\n")
            for c in components:
                f.write(f"  {c['ref']} - {c['value']} ({c.get('lib_id', '')})\n")

            f.write("\nNets:\n")
            for n in nets:
                f.write(f"  {n['name']}: {n.get('nodes', [])}\n")

            f.write("\nFootprints:\n")
            for ref, fp in footprints.items():
                f.write(f"  {ref} -> {fp}\n")

        return str(output)

    # --- Real KiCad PCB generation ---
    def _generate_kicad_board(self, components, nets, footprints):
        board = pcbnew.BOARD()

        # Add title block info
        title_block = board.GetTitleBlock()
        title_block.SetTitle("AI_Generated_PCB")
        title_block.SetComment(0, "Auto-generated via Gemini AI")

        # Add visible board outline (100mm x 80mm)
        self._add_board_outline(board)

        # Add components + nets + dummy autorouting
        self._add_components(board, components, footprints)
        self._add_nets(board, nets)
        self._autoroute(board, nets)

        out_file = self.output_dir / "ai_generated_board.kicad_pcb"
        pcbnew.SaveBoard(str(out_file), board)
        return str(out_file)

    def _add_board_outline(self, board):
        """Create a visible 100mm x 80mm board rectangle on Edge.Cuts"""
        width = pcbnew.FromMM(100)
        height = pcbnew.FromMM(80)

        rect = pcbnew.PCB_SHAPE(board)
        rect.SetShape(pcbnew.SHAPE_T_RECT)
        rect.SetLayer(pcbnew.Edge_Cuts)
        rect.SetStart(pcbnew.VECTOR2I(0, 0))
        rect.SetEnd(pcbnew.VECTOR2I(width, height))
        rect.SetWidth(pcbnew.FromMM(0.15))
        board.Add(rect)

    def _add_components(self, board, components, footprints):
        """Prompt user for each component footprint in the terminal."""
        grid_x, grid_y = 0, 0
        step = 20  # mm spacing between parts

        print("\n🧱 Adding components to the board...")
        print("Enter a valid KiCad footprint (example: Resistor_SMD:R_0603)")
        print("Press ENTER to use the suggested footprint if available.\n")

        for c in components:
            ref = c["ref"]
            val = c.get("value", "") or "N/A"
            default_fp = footprints.get(ref, "Resistor_SMD:R_0603")

            # Ask user for input
            print(f"\nWhat footprint do you want for {ref} ({val})?")
            fp_name = input(f"→ [{default_fp}]: ").strip() or default_fp

            try:
                # Split into library:name format if needed
                if ":" in fp_name:
                    lib, name = fp_name.split(":", 1)
                else:
                    lib, name = "", fp_name

                fp_dir = Path(os.environ["KICAD9_FOOTPRINT_DIR"]) / f"{lib}.pretty"
                footprint = pcbnew.FootprintLoad(str(fp_dir), name)

                if not footprint:
                    print(f"⚠️ Could not load {fp_name} — skipping {ref}")
                    continue

                footprint.SetReference(ref)
                footprint.SetValue(val)
                footprint.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(10 + grid_x),
                                                     pcbnew.FromMM(10 + grid_y)))
                board.Add(footprint)

                print(f"✅ Added {ref} ({fp_name}) successfully.")

                grid_x += step
                if grid_x > 80:
                    grid_x = 0
                    grid_y += step

            except Exception as e:
                print(f"⚠️ Failed to add {ref} ({fp_name}): {e}")

    def _add_nets(self, board, nets):
        """Create net entries for connectivity."""
        for n in nets:
            try:
                net = pcbnew.NETINFO_ITEM(board, n["name"])
                board.Add(net)
            except Exception as e:
                print(f"⚠️ Failed to create net {n['name']}: {e}")

    def _autoroute(self, board, nets):
        """Draw simple visible demo tracks."""
        for i, n in enumerate(nets):
            if len(n.get("nodes", [])) < 2:
                continue
            try:
                x = pcbnew.FromMM(20 + i)
                y = pcbnew.FromMM(20 + i)
                track = pcbnew.TRACK(board)
                track.SetStart(pcbnew.VECTOR2I(x, y))
                track.SetEnd(pcbnew.VECTOR2I(x + pcbnew.FromMM(10), y + pcbnew.FromMM(10)))
                track.SetWidth(pcbnew.FromMM(0.25))
                board.Add(track)
            except Exception as e:
                print(f"⚠️ Autoroute failed for {n['name']}: {e}")


# --- Run Script ---
if __name__ == "__main__":
    gen = PCBGenerator()
    gen.generate("outputs/Lab4_parsed.json")