import json
import google.generativeai as genai

# --- Configure Gemini ---
genai.configure(api_key="AIzaSyCG35kPUUGS6mV_huGWZt5FYoFN0wxMtN0")

def infer_nets_with_gemini(parsed_data):
    """
    Uses Gemini 2.5 Flash to infer probable electrical nets.
    If Gemini fails, falls back to parsed nets.
    """
    components = parsed_data.get("components", [])
    labels = [n["name"] for n in parsed_data.get("nets", []) if n.get("name")]

    prompt = f"""
You are an expert electrical engineer. 
Given schematic components and signal labels, infer the electrical connections between components.

Rules:
- Each net should represent a unique electrical signal (VDD, GND, SIG_IN, Vout, etc.)
- Each net must include a list of component:pin mappings.
- TLV2372 pins 4 and 8 are GND and VDD.
- Use reasonable circuit logic (resistors connect between signals, testpoints connect to signals).
- Output only valid JSON, no explanations.

Example:
[
  {{
    "name": "VDD",
    "nodes": [
      {{"ref": "U1", "pin": "8"}},
      {{"ref": "VDD_TP1", "pin": "1"}}
    ]
  }},
  {{
    "name": "GND",
    "nodes": [
      {{"ref": "U1", "pin": "4"}},
      {{"ref": "GND_TP1", "pin": "1"}}
    ]
  }}
]

Components:
{json.dumps(components, indent=2)}

Labels:
{json.dumps(labels, indent=2)}
"""

    try:
        model_name = "models/gemini-2.5-flash"
        model = genai.GenerativeModel(model_name)
        print(f"🧠 Using Gemini model: {model_name}")

        response = model.generate_content(prompt, request_options={"timeout": 60})
        text = response.text.strip()

        # Clean possible markdown fencing
        if text.startswith("```"):
            text = text.split("```")[1]
        text = text.replace("json", "").strip()

        inferred_nets = json.loads(text)
        print("✅ Gemini inferred nets successfully.")
        return inferred_nets

    except json.JSONDecodeError:
        print("⚠️ Gemini returned invalid JSON — using fallback nets.")
    except Exception as e:
        print(f"⚠️ Gemini inference failed: {e}")

    return parsed_data.get("nets", [])
