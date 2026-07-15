import sys
import os
import json
import subprocess
import tempfile

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _run_in_subprocess(script: str, timeout: int = 180) -> dict:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(script)
        tmp_path = f.name
    try:
        proc = subprocess.run(
            ["python", tmp_path],
            capture_output=True, text=True, timeout=timeout,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        )
        if proc.returncode != 0:
            print(f"  Subprocess error: {proc.stderr[:300]}", file=sys.stderr)
            return {}
        return json.loads(proc.stdout)
    except subprocess.TimeoutExpired:
        print(f"  Subprocess timeout ({timeout}s)", file=sys.stderr)
        return {}
    except (json.JSONDecodeError, Exception) as e:
        print(f"  Subprocess parse error: {e}", file=sys.stderr)
        return {}
    finally:
        os.unlink(tmp_path)


def _make_base_script() -> str:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return f'''
import sys
import json
sys.path.insert(0, "{base_dir}")
'''


def run_growth_batch(terms: list, max_preco: float, max_per_scraper: int) -> dict:
    terms_json = json.dumps(terms)
    script = _make_base_script() + f'''
from scripts.scraper_growth import buscar_produtos as growth_buscar

terms = {terms_json}
max_preco = {max_preco}
max_per = {max_per_scraper}

resultados = {{}}
for termo in terms:
    resultados[termo] = []
    try:
        produtos = growth_buscar(termo, max_preco)
        resultados[termo].extend(produtos[:max_per])
    except Exception:
        pass

print(json.dumps(resultados, ensure_ascii=False))
'''
    return _run_in_subprocess(script, timeout=180)


def run_playwright_scraper(scraper_name: str, terms: list, term_to_preco_max: dict, max_per_scraper: int) -> dict:
    """Roda um scraper Playwright em subprocess separado."""
    terms_json = json.dumps(terms)
    term_to_preco_json = json.dumps(term_to_preco_max)
    script = _make_base_script() + f'''
import logging
log = logging.getLogger("bot-ofertas")

terms = {terms_json}
term_to_preco_max = {term_to_preco_json}
max_per = {max_per_scraper}
resultados = {{}}

try:
'''
    if scraper_name == "procorrer":
        script += '''
    from scripts.scraper_procorrer import ProcorrerScraper
    scraper = ProcorrerScraper()
    for termo in terms:
        resultados[termo] = []
        try:
            pm = term_to_preco_max.get(termo, 999999)
            resultados[termo].extend(scraper.buscar(termo, pm)[:max_per])
        except Exception as e:
            log.warning("Procorrer falhou para '%s': %s", termo, e)
'''
    elif scraper_name == "decathlon":
        script += '''
    from scripts.scraper_decathlon import DecathlonScraper
    scraper = DecathlonScraper()
    for termo in terms:
        resultados[termo] = []
        try:
            pm = term_to_preco_max.get(termo, 999999)
            resultados[termo].extend(scraper.buscar(termo, pm)[:max_per])
        except Exception as e:
            log.warning("Decathlon falhou para '%s': %s", termo, e)
'''
    elif scraper_name == "ml":
        script += '''
    from scripts.scraper_mercadolivre import MercadoLivreScraper
    scraper = MercadoLivreScraper()
    unique_terms = list(dict.fromkeys(terms))
    try:
        ml_ofertas = scraper.buscar_ofertas(max_preco=max(term_to_preco_max.values()) if term_to_preco_max else None)
        for p in ml_ofertas:
            termo_match = None
            for termo in unique_terms:
                termo_lower = termo.lower()
                nome_lower = p.get("nome", "").lower()
                if termo_lower in nome_lower or any(w in nome_lower for w in termo_lower.split()):
                    termo_match = termo
                    break
            if termo_match:
                if termo_match not in resultados:
                    resultados[termo_match] = []
                resultados[termo_match].append(p)
            else:
                if unique_terms:
                    fallback = unique_terms[0]
                    if fallback not in resultados:
                        resultados[fallback] = []
                    resultados[fallback].append(p)
    except Exception as e:
        log.warning("ML ofertas falhou: %s", e)
'''
    elif scraper_name == "growth":
        script += '''
    from scripts.scraper_growth import buscar_produtos as growth_buscar
    growth_terms = [t for t in terms if t]
    if growth_terms:
        growth_preco_max = max(term_to_preco_max.get(t, 999999) for t in growth_terms)
        for termo in growth_terms:
            resultados[termo] = []
            try:
                produtos = growth_buscar(termo, growth_preco_max)
                resultados[termo].extend(produtos[:max_per])
            except Exception as e:
                log.warning("Growth falhou para '%s': %s", termo, e)
'''

    script += '''
except Exception as e:
    log.warning("Scraper falhou: %s", e)

print(json.dumps(resultados, ensure_ascii=False))
'''
    return _run_in_subprocess(script, timeout=180)


def run_amazon(terms: list, term_to_preco_max: dict, max_per_scraper: int) -> dict:
    """Roda Amazon scraper (HTTP, sem Playwright) em subprocess."""
    terms_json = json.dumps(terms)
    term_to_preco_json = json.dumps(term_to_preco_max)
    script = _make_base_script() + f'''
from scripts.scraper_amazon import AmazonScraper

terms = {terms_json}
term_to_preco_max = {term_to_preco_json}
max_per = {max_per_scraper}

scraper = AmazonScraper()
resultados = {{}}
for termo in terms:
    resultados[termo] = []
    try:
        pm = term_to_preco_max.get(termo, 999999)
        resultados[termo].extend(scraper.buscar(termo, pm)[:max_per])
    except Exception as e:
        pass

print(json.dumps(resultados, ensure_ascii=False))
'''
    return _run_in_subprocess(script, timeout=120)


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
