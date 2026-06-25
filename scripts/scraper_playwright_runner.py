import sys
import os
import json
import subprocess
import tempfile

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_growth_batch(terms: list, max_preco: float, max_per_scraper: int) -> dict:
    terms_json = json.dumps(terms)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    script = f'''
import sys
import json
sys.path.insert(0, "{base_dir}")

from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from scripts.scraper_growth import buscar_produtos as growth_buscar

terms = {terms_json}
max_preco = {max_preco}
max_per = {max_per_scraper}

resultados = {{}}
stealth = Stealth(
    navigator_languages_override=("pt-BR", "pt"),
    navigator_platform_override="Win32",
)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        locale="pt-BR"
    )

    for termo in terms:
        resultados[termo] = []
        try:
            page = ctx.new_page()
            stealth.apply_stealth_sync(page)
            produtos = growth_buscar(termo, max_preco, context=ctx)
            resultados[termo].extend(produtos[:max_per])
            page.close()
        except Exception:
            pass

    browser.close()

print(json.dumps(resultados, ensure_ascii=False))
'''
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(script)
        tmp_path = f.name

    try:
        proc = subprocess.run(
            ["python", tmp_path],
            capture_output=True, text=True, timeout=180,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        )
        if proc.returncode != 0:
            print(f"  Growth batch error: {proc.stderr[:200]}", file=sys.stderr)
            return {}
        return json.loads(proc.stdout)
    except subprocess.TimeoutExpired:
        print("  Growth batch timeout", file=sys.stderr)
        return {}
    except (json.JSONDecodeError, Exception) as e:
        print(f"  Growth batch parse error: {e}", file=sys.stderr)
        return {}
    finally:
        os.unlink(tmp_path)
