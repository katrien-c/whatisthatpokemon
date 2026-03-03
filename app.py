import streamlit as st
import random
import requests

st.set_page_config(
    page_title="Pokemon Dance Party!",
    page_icon="🕺",
    layout="wide",
)

# ---------- constants ----------

TYPE_COLORS = {
    "fire": "#FF6B35", "water": "#4ECDC4", "grass": "#7EC8A0",
    "electric": "#FFE66D", "psychic": "#FF6B8A", "ice": "#A8E6CF",
    "dragon": "#7B68EE", "dark": "#6B5B95", "fairy": "#FFB3DE",
    "normal": "#B5B5B5", "fighting": "#E84855", "flying": "#87CEEB",
    "poison": "#9B59B6", "ground": "#D4A853", "rock": "#95A5A6",
    "bug": "#82C341", "ghost": "#7F6EC7", "steel": "#BFC9CA",
}

DANCE_KEYFRAMES = {
    "bounce": """
        @keyframes bounce {
            0%, 100% { transform: translateY(0px) scaleX(1); }
            50% { transform: translateY(-35px) scaleX(1.05); }
        }""",
    "wiggle": """
        @keyframes wiggle {
            0%, 100% { transform: rotate(-15deg); }
            50% { transform: rotate(15deg); }
        }""",
    "pulse": """
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.35); }
        }""",
    "slide": """
        @keyframes slide {
            0%, 100% { transform: translateX(-20px) rotate(-8deg); }
            50% { transform: translateX(20px) rotate(8deg); }
        }""",
    "headbang": """
        @keyframes headbang {
            0%, 100% { transform: translateY(0) rotate(0deg); }
            25% { transform: translateY(-20px) rotate(-10deg); }
            75% { transform: translateY(-20px) rotate(10deg); }
        }""",
    "spin": """
        @keyframes spin {
            0% { transform: rotate(0deg) scale(1); }
            50% { transform: rotate(180deg) scale(1.2); }
            100% { transform: rotate(360deg) scale(1); }
        }""",
}

DANCE_SPEEDS = {
    "bounce": "0.55s",
    "wiggle": "0.45s",
    "pulse": "0.5s",
    "slide": "0.6s",
    "headbang": "0.4s",
    "spin": "0.8s",
}

# ---------- helpers ----------

def get_type_color(types: list[str]) -> str:
    return TYPE_COLORS.get(types[0] if types else "", "#FF6B6B")


def fetch_pokemon(pid: int) -> dict | None:
    try:
        r = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pid}", timeout=6)
        r.raise_for_status()
        data = r.json()
        animated = (
            f"https://raw.githubusercontent.com/PokeAPI/sprites/master/"
            f"sprites/pokemon/versions/generation-v/black-white/animated/{pid}.gif"
        )
        fallback = data["sprites"]["front_default"] or ""
        types = [t["type"]["name"] for t in data["types"]]
        return {
            "id": pid,
            "name": data["name"].capitalize(),
            "animated": animated,
            "fallback": fallback,
            "types": types,
        }
    except Exception:
        return None


def get_random_pokemon(count: int = 5):
    ids = random.sample(range(1, 899), count * 2)  # extra in case of failures
    results = []
    bar = st.progress(0, text="Pokemon vangen...")
    for pid in ids:
        if len(results) >= count:
            break
        p = fetch_pokemon(pid)
        if p:
            results.append(p)
        bar.progress(len(results) / count, text=f"Pokemon vangen... {len(results)}/{count}")
    bar.empty()
    return results[:count]


# ---------- HTML builder ----------

MUSIC_JS = """
<script>
(function() {
  let ctx = null;
  let intervalId = null;
  let nextBeat = 0;
  let playing = false;

  const SCALES = [
    [261.63, 293.66, 329.63, 392.00, 440.00, 523.25],  // C maj
    [293.66, 329.63, 369.99, 440.00, 493.88, 587.33],  // D maj
    [349.23, 392.00, 440.00, 523.25, 587.33, 659.25],  // F maj
    [392.00, 440.00, 493.88, 587.33, 659.25, 783.99],  // G maj
  ];

  function rnd(arr) { return arr[Math.floor(Math.random() * arr.length)]; }

  function note(freq, t, dur, type, vol) {
    const o = ctx.createOscillator();
    const g = ctx.createGain();
    o.connect(g); g.connect(ctx.destination);
    o.type = type;
    o.frequency.setValueAtTime(freq, t);
    g.gain.setValueAtTime(vol, t);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.start(t); o.stop(t + dur);
  }

  function beat(t, scale) {
    const step = 0.18;
    for (let i = 0; i < 8; i++) {
      note(rnd(scale), t + i * step, step * 0.85, 'square', 0.12);
    }
    // bass on every 4 beats
    note(rnd(scale) / 2, t, step * 4, 'triangle', 0.18);
    note(rnd(scale) / 2, t + step * 4, step * 4, 'triangle', 0.18);
    // snare-ish noise
    for (let i = 1; i < 8; i += 2) {
      note(150 + Math.random() * 50, t + i * step, 0.05, 'sawtooth', 0.06);
    }
    return t + 8 * step;
  }

  let currentScale = null;

  function schedule() {
    if (!playing) return;
    while (nextBeat < ctx.currentTime + 1.0) {
      nextBeat = beat(nextBeat, currentScale);
    }
  }

  window.toggleMusic = function() {
    const btn = document.getElementById('musicBtn');
    if (playing) {
      clearInterval(intervalId);
      ctx.close();
      ctx = null; playing = false;
      btn.textContent = '🎵 Start Muziek';
      btn.className = 'music-btn off';
    } else {
      ctx = new (window.AudioContext || window.webkitAudioContext)();
      currentScale = SCALES[Math.floor(Math.random() * SCALES.length)];
      nextBeat = ctx.currentTime;
      playing = true;
      schedule();
      intervalId = setInterval(schedule, 400);
      btn.textContent = '🔇 Stop Muziek';
      btn.className = 'music-btn on';
    }
  };

  window.newMusic = function() {
    if (playing && ctx) {
      currentScale = SCALES[Math.floor(Math.random() * SCALES.length)];
    }
  };
})();
</script>
"""


def build_html(pokemon_list: list[dict]) -> str:
    dance_names = list(DANCE_KEYFRAMES.keys())
    assigned = [random.choice(dance_names) for _ in pokemon_list]

    all_keyframes = "\n".join(DANCE_KEYFRAMES[name] for name in set(assigned))

    sprite_css = ""
    for i, name in enumerate(assigned):
        delay = round(random.uniform(0, 0.4), 2)
        speed = DANCE_SPEEDS[name]
        sprite_css += f"""
        .poke-{i} img {{
            animation: {name} {speed} ease-in-out {delay}s infinite;
            image-rendering: pixelated;
        }}"""

    cards_html = ""
    for i, p in enumerate(pokemon_list):
        color = get_type_color(p["types"])
        type_badges = "".join(
            f'<span class="badge" style="background:{color}88;">{t}</span>'
            for t in p["types"]
        )
        cards_html += f"""
        <div class="card poke-{i}" style="
            background: linear-gradient(160deg, {color}22, {color}55);
            border: 2px solid {color};
            border-radius: 18px;
            box-shadow: 0 4px 20px {color}66;
        ">
            <img src="{p['animated']}"
                 onerror="this.onerror=null;this.src='{p['fallback']}'"
                 width="120" height="120" />
            <div class="name" style="text-shadow: 0 0 12px {color};">{p['name']}</div>
            <div class="poke-id">#{p['id']}</div>
            <div>{type_badges}</div>
        </div>"""

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
  body {{ margin: 0; background: transparent; font-family: 'Segoe UI', sans-serif; }}
  {all_keyframes}
  {sprite_css}
  .grid {{
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    gap: 16px;
    padding: 12px;
  }}
  .card {{
    flex: 1 1 140px;
    max-width: 170px;
    text-align: center;
    padding: 16px 10px 12px;
    box-sizing: border-box;
  }}
  .card img {{ display: block; margin: 0 auto; object-fit: contain; }}
  .name {{ color: #fff; font-weight: 700; font-size: 1.05em; margin: 8px 0 2px; }}
  .poke-id {{ color: #ccc; font-size: 0.8em; margin-bottom: 4px; }}
  .badge {{
    display: inline-block;
    color: #fff;
    border-radius: 20px;
    font-size: 0.72em;
    padding: 2px 8px;
    margin: 2px;
    font-weight: 600;
  }}
  .music-btn {{
    display: block;
    margin: 18px auto 6px;
    padding: 12px 36px;
    font-size: 1.1em;
    font-weight: bold;
    border: none;
    border-radius: 50px;
    cursor: pointer;
    transition: transform 0.15s, box-shadow 0.15s;
  }}
  .music-btn.off {{
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: #fff;
    box-shadow: 0 4px 18px #667eea88;
  }}
  .music-btn.on {{
    background: linear-gradient(135deg, #f5576c, #f093fb);
    color: #fff;
    box-shadow: 0 4px 18px #f5576c88;
  }}
  .music-btn:hover {{ transform: scale(1.06); }}
</style>
</head>
<body>
{MUSIC_JS}
<div class="grid">{cards_html}</div>
<button id="musicBtn" class="music-btn off" onclick="toggleMusic()">🎵 Start Muziek</button>
</body>
</html>"""


# ---------- UI ----------

st.markdown(
    "<h1 style='text-align:center;'>🕺 Pokemon Dansfeest! 🎉</h1>",
    unsafe_allow_html=True,
)

col_l, col_c, col_r = st.columns([1, 2, 1])
with col_c:
    start = st.button("🎲 Nieuwe Pokemon!", use_container_width=True)

if start:
    st.session_state.pokemon = get_random_pokemon(5)

if "pokemon" not in st.session_state:
    st.markdown(
        "<p style='text-align:center;color:#888;margin-top:60px;font-size:1.2em;'>"
        "Klik op 'Nieuwe Pokemon!' om het feest te starten! 🎊</p>",
        unsafe_allow_html=True,
    )
else:
    html = build_html(st.session_state.pokemon)
    st.components.v1.html(html, height=420, scrolling=False)
