"""
auto_run.py - Wrapper otomatis untuk Verticals v3
Dijalankan oleh GitHub Actions setiap hari tanpa perlu input manual.

Cara kerja:
1. Baca konfigurasi niche dari env variable NICHE (default: tech)
2. Auto-discover trending topic sesuai niche
3. Jalankan full pipeline: research -> script -> visuals -> voice -> captions -> assemble -> upload
4. Log hasil ke console (terlihat di GitHub Actions log)
"""

import os
import sys
import subprocess
import logging
import json
import random
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger(__name__)


# ─── Konfigurasi ─────────────────────────────────────────────────────────────

NICHE = os.environ.get("NICHE", "tech")

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "gemini")

# Pilih provider secara otomatis berdasarkan API key yang tersedia
def detect_llm_provider() -> str:
    """Auto-detect provider dari API key yang tersedia."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "claude"
    if os.environ.get("GEMINI_API_KEY"):
        return "gemini"
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    log.warning("Tidak ada LLM API key! Coba pakai Ollama lokal.")
    return "ollama"

# Pilih visuals provider berdasarkan API key
def detect_visuals_provider() -> str:
    """Auto-detect visuals provider dari API key yang tersedia."""
    if os.environ.get("PEXELS_API_KEY"):
        return "pexels"    # gratis
    if os.environ.get("GEMINI_API_KEY"):
        return "gemini"    # gratis tier
    return "pexels"        # pexels tidak butuh key untuk basic usage


# ─── Validasi Environment ─────────────────────────────────────────────────────

def validate_env():
    """Cek semua kebutuhan sebelum jalan."""
    errors = []

    # Cek minimal satu LLM provider
    llm_keys = [
        "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
        "OPENAI_API_KEY"
    ]
    if not any(os.environ.get(k) for k in llm_keys):
        errors.append("❌ Tidak ada LLM API key. Set salah satu: ANTHROPIC_API_KEY, GEMINI_API_KEY, atau OPENAI_API_KEY")

    # Cek YouTube token
    token_path = Path.home() / ".config" / "verticals" / "youtube_token.json"
    client_secret_path = Path.home() / ".config" / "verticals" / "client_secret.json"

    if not token_path.exists():
        errors.append(f"❌ YouTube token tidak ditemukan di {token_path}. Jalankan setup_youtube_token.py dulu!")
    else:
        # Validasi isi token
        try:
            token_data = json.loads(token_path.read_text())
            if not token_data.get("refresh_token"):
                errors.append("❌ YouTube token tidak punya refresh_token. Generate ulang dengan setup_youtube_token.py")
        except Exception as e:
            errors.append(f"❌ YouTube token tidak valid: {e}")

    if not client_secret_path.exists():
        errors.append(f"❌ client_secret.json tidak ditemukan di {client_secret_path}.")

    # Cek FFmpeg
    result = subprocess.run(["ffmpeg", "-version"], capture_output=True)
    if result.returncode != 0:
        errors.append("❌ FFmpeg tidak terinstall!")

    if errors:
        log.error("Validasi gagal:\n" + "\n".join(errors))
        sys.exit(1)

    log.info("✅ Semua environment valid")


# ─── Jalankan Pipeline ────────────────────────────────────────────────────────

def run_pipeline():
    """Jalankan Verticals pipeline dengan auto-discover topic."""
    provider = detect_llm_provider()
    visuals = detect_visuals_provider()

    log.info(f"🚀 Mulai pipeline")
    log.info(f"   Niche    : {NICHE}")
    log.info(f"   Provider : {provider}")
    log.info(f"   Visuals  : {visuals}")
    log.info(f"   Waktu    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    cmd = [
        sys.executable, "-m", "verticals", "run",
        "--discover",           # auto-discover topic trending
        "--auto-pick",          # pilih topic terbaik otomatis
        "--niche", NICHE,
        "--provider", provider,
        "--visuals", visuals,
        "--voice", "edge",      # Edge TTS = gratis
        "--platform", "youtube",
        "--verbose"
    ]

    log.info(f"Command: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=False)

    if result.returncode == 0:
        log.info("✅ Pipeline selesai! Video sudah diupload ke YouTube.")
    else:
        log.error(f"❌ Pipeline gagal dengan exit code {result.returncode}")
        sys.exit(result.returncode)


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    log.info("=" * 60)
    log.info("  AUTO YOUTUBE SHORTS - GitHub Actions Runner")
    log.info("=" * 60)

    validate_env()
    run_pipeline()
