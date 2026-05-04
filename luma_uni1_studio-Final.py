import streamlit as st
import requests
import time
import base64
import json

st.set_page_config(page_title="Uni-1 Studio", page_icon="🌌", layout="wide")

st.markdown("""
<style>
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] div[data-baseweb="select"] {
    background:#fff !important; color:#111 !important; border-color:#ccc !important;
}
[data-testid="stSidebar"] { background:#f8f8f8; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──
with st.sidebar:
    st.title("🌌 Uni-1 Studio")
    api_key = st.text_input("Luma API Key", type="password", placeholder="luma-api-...")
    st.markdown("[Get API Key →](https://lumalabs.ai/api)")
    st.divider()
    st.caption("Model: `uni-1`  |  Endpoint: `agents.lumalabs.ai`")
    st.info("💡 **Pro Tip for Speed:** Keep uploaded images under 100 KB for near-instant generation.")

# ── Helpers ──
SUBMIT_URL = "https://agents.lumalabs.ai/v1/generations"

def headers(key):
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

def submit(key, payload):
    r = requests.post(SUBMIT_URL, headers=headers(key), json=payload, timeout=30)
    if r.status_code not in (200, 201, 202):
        raise Exception(f"HTTP {r.status_code}: {r.text[:300]}")
    data = r.json()
    gid = data.get("id") or data.get("generation_id")
    if not gid:
        raise Exception(f"No ID in response: {json.dumps(data)[:200]}")
    return gid

def poll(key, gid, status_el, timeout=180):
    url = f"{SUBMIT_URL}/{gid}"
    elapsed = 0
    interval = 3
    while elapsed < timeout:
        time.sleep(interval)
        elapsed += interval
        interval = min(interval * 1.3, 6)
        r = requests.get(url, headers=headers(key), timeout=15)
        data = r.json()
        state = (data.get("state") or data.get("status") or "").lower()
        status_el.info(f"⏳ Status: `{state}` ({elapsed}s elapsed…)")
        if state == "completed":
            out = data.get("output") or []
            if out:
                return out[0].get("url")
            assets = data.get("assets") or {}
            return assets.get("image") or data.get("image_url")
        if state in ("failed", "error"):
            raise Exception(data.get("failure_reason") or "Generation failed")
    raise Exception(f"Timed out after {timeout}s")

def file_to_b64(f):
    return base64.b64encode(f.read()).decode("utf-8")

# ── Tabs ──
tab1, tab2, tab3 = st.tabs(["🔥 Photo Restoration", "📦 Product Image Generator", "🎨 Slide Generator"])


# ════════════════════════════════════════════
# TAB 1 — PHOTO RESTORATION
# ════════════════════════════════════════════
with tab1:
    st.header("Vintage Photo Restoration")
    st.caption("Upload a damaged photo — Uni-1 restores it using causal scene reasoning.")

    col1, col2 = st.columns(2, gap="large")

    with col1:
        uploaded = st.file_uploader("Upload Damaged Photo *", type=["jpg","jpeg","png","webp"], key="p_upload")
        if uploaded:
            st.image(uploaded, caption="Original — damaged input", use_column_width=True)

    with col2:
        damage = st.selectbox("Damage Type", {
            "🔥 Fire / Char":      "restore charred edges, burnt areas, char marks; reconstruct destroyed regions with period-accurate content",
            "💧 Water / Stains":   "remove water stains, fix waterlogged blurring, restore washed-out sections and faded ink",
            "🕰️ Age / Fading":     "restore faded colors and contrast, recover fine detail lost to age, remove yellowing and foxing",
            "✂️ Torn / Missing":   "reconstruct physically torn or missing areas using contextual scene understanding",
            "🪡 Scratches":        "remove deep scratch artifacts, repair surface damage, restore the underlying image",
            "🌫️ Overexposed":      "rebalance exposure, recover blown highlights and crushed shadows, restore sharpness",
        }.keys())

        damage_map = {
            "🔥 Fire / Char":      "restore charred edges, burnt areas, char marks; reconstruct destroyed regions with period-accurate content",
            "💧 Water / Stains":   "remove water stains, fix waterlogged blurring, restore washed-out sections and faded ink",
            "🕰️ Age / Fading":     "restore faded colors and contrast, recover fine detail lost to age, remove yellowing and foxing",
            "✂️ Torn / Missing":   "reconstruct physically torn or missing areas using contextual scene understanding",
            "🪡 Scratches":        "remove deep scratch artifacts, repair surface damage, restore the underlying image",
            "🌫️ Overexposed":      "rebalance exposure, recover blown highlights and crushed shadows, restore sharpness",
        }

        rstyle_map = {
            "📷 Faithful — Match Original Era":  "authentic era-accurate restoration, preserve original film grain and tonal character",
            "🌈 Colorized — Add Natural Color":   "intelligently colorize with historically accurate, naturalistic color palette",
            "🔬 Enhanced HD — Modern Clarity":    "upscale to crisp high definition while retaining documentary authenticity",
            "🎨 Fine Art — Painterly Quality":    "fine-art restoration with rich tonal depth, slight hand-restoration aesthetic",
        }
        rstyle = st.selectbox("Restoration Style", list(rstyle_map.keys()))
        era = st.text_input("Era / Context Hint", placeholder="1950s South Asian studio portrait")
        subjects = st.text_input("Key Subjects to Preserve", placeholder="man with glasses and mustache, face centered")

    def build_restore_prompt():
        p = ["Restore this damaged historical photograph.",
             damage_map[damage] + ".",
             rstyle_map[rstyle] + "."]
        if era: p.append(f"Historical context: {era}.")
        if subjects: p.append(f"Key subjects to preserve: {subjects}.")
        p += ["Faithfully reconstruct missing content using contextual scene reasoning.",
              "Preserve all identifiable faces, subjects, and spatial relationships.",
              "Museum conservation quality. No AI artifacts. No anachronistic elements."]
        return " ".join(p)

    if st.button("🔧 Restore Photograph", type="primary"):
        if not api_key:
            st.error("Enter your Luma API key in the sidebar.")
        elif not uploaded:
            st.warning("Upload a damaged photo first.")
        else:
            status2 = st.empty()
            try:
                uploaded.seek(0)
                b64 = file_to_b64(uploaded)
                mt = uploaded.type or "image/jpeg"

                payload = {
                    "prompt": build_restore_prompt(),
                    "model": "uni-1",
                    "type": "image_edit",
                    "source": {"data": b64, "media_type": mt},
                }

                status2.info("⏳ Submitting to Uni-1…")
                gid = submit(api_key, payload)
                status2.info(f"🧠 Restoring… `(id: {gid[:12]}…)`")
                img_url = poll(api_key, gid, status2)
                status2.empty()

                if img_url:
                    st.success("✅ Restoration complete!")
                    r1, r2 = st.columns(2)
                    with r1:
                        uploaded.seek(0)
                        st.image(uploaded, caption="Before — Damaged", use_column_width=True)
                    with r2:
                        st.image(img_url, caption="After — Restored by Uni-1", use_column_width=True)
                    st.markdown(f"[↗ Open full resolution]({img_url})")
                else:
                    st.error("No image URL returned.")
            except Exception as e:
                status2.empty()
                st.error(f"❌ {e}")


# ════════════════════════════════════════════
# TAB 2 — PRODUCT IMAGE GENERATOR
# ════════════════════════════════════════════
with tab2:
    st.header("Product Image Generator")
    st.caption("Simple prompt-based product compositing.")

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        product_img = st.file_uploader("Upload Product Image *", type=["jpg","jpeg","png","webp"], key="prod_img")
        if product_img:
            st.image(product_img, caption="Product Reference", width=300)

    with col2:
        prod_prompt = st.text_area(
            "Instructions", 
            placeholder="Here is a product image. Can you place it in a modern gym setting on a workout bench?",
            height=150
        )

    if st.button("🎯 Generate Product Image", type="primary"):
        if not api_key:
            st.error("Enter your Luma API key in the sidebar.")
        elif not product_img:
            st.warning("Please upload a product image.")
        elif not prod_prompt.strip():
            st.warning("Please enter your prompt instructions.")
        else:
            status_p = st.empty()
            try:
                product_img.seek(0)
                b64 = file_to_b64(product_img)
                mt = product_img.type or "image/jpeg"

                payload = {
                    "prompt": prod_prompt,
                    "model": "uni-1",
                    "type": "image_edit",
                    "source": {"data": b64, "media_type": mt},
                }

                status_p.info("⏳ Submitting to Uni-1…")
                gid = submit(api_key, payload)
                status_p.info(f"🧠 Compositing scene… `(id: {gid[:12]}…)`")
                img_url = poll(api_key, gid, status_p)
                status_p.empty()

                if img_url:
                    st.success("✅ Product image ready!")
                    st.image(img_url, caption="Generated Product Image", use_column_width=True)
                    st.markdown(f"[↗ Open full resolution]({img_url})")
                else:
                    st.error("No image URL returned.")
            except Exception as e:
                status_p.empty()
                st.error(f"❌ {e}")


# ════════════════════════════════════════════
# TAB 3 — SLIDE GENERATOR
# ════════════════════════════════════════════
with tab3:
    st.header("Infographic Slide Generator")
    st.caption("Upload your template and give simple, conversational instructions.")

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        template_img = st.file_uploader("Upload Slide Template *", type=["jpg","jpeg","png","webp"], key="slide_template")
        if template_img:
            st.image(template_img, caption="Your template", width=300)

    with col2:
        slide_prompt = st.text_area(
            "Instructions", 
            value="Here is a template image for Explain Like I am 5 Series that I am running on LinkedIn. Can you use this template to create an image about Sample Ratio Mismatch?",
            height=150
        )

    if st.button("🎨 Generate Slide", type="primary"):
        if not api_key:
            st.error("Enter your Luma API key in the sidebar.")
        elif not template_img:
            st.warning("Please upload a slide template.")
        elif not slide_prompt.strip():
            st.warning("Please enter your prompt instructions.")
        else:
            slide_status = st.empty()
            try:
                template_img.seek(0)
                b64 = file_to_b64(template_img)
                mt = template_img.type or "image/jpeg"

                payload = {
                    "prompt": slide_prompt,
                    "model": "uni-1",
                    "type": "image_edit",
                    "source": {"data": b64, "media_type": mt},
                }

                slide_status.info("⏳ Submitting to Uni-1…")
                gid = submit(api_key, payload)
                slide_status.info(f"🧠 Rendering slide… `(id: {gid[:12]}…)`")
                img_url = poll(api_key, gid, slide_status)
                slide_status.empty()

                if img_url:
                    st.success("✅ Slide generated!")
                    st.image(img_url, caption="Generated Slide", use_column_width=True)
                    st.markdown(f"[↗ Open full resolution]({img_url})")
                else:
                    st.error("No image returned.")
            except Exception as e:
                slide_status.empty()
                st.error(f"❌ Slide generation failed: {e}")

st.divider()
st.caption("Every image generated by Uni-1 via the Luma API · lumalabs.ai/api")