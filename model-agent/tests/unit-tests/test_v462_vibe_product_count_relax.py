import ast

from notebook_source_util import agent_version_line
import json
import re
from pathlib import Path


NB = Path(__file__).resolve().parents[2] / "agent" / "dbx_vibe_modelling_agent.ipynb"


def _coerce_helpers():
    """Slice the real coerce helpers from cell 25 so isolated class methods that
    reference _v466_coerce_llm_obj (v4.6.6 parse-site hardening) exec cleanly."""
    nb = json.loads(NB.read_text(encoding="utf-8"))
    cell25 = "".join(nb["cells"][25]["source"])
    tree = ast.parse(cell25)
    wanted = {"_coerce_dict", "_coerce_list_of_dicts", "_v466_coerce_llm_obj"}
    body = [
        n for n in tree.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in wanted
    ]
    ns = {"json": json, "re": re, "logging": __import__("logging")}
    exec(compile(ast.Module(body=body, type_ignores=[]), "<cell25>", "exec"), ns)
    return {k: ns[k] for k in wanted}


def _source():
    notebook = json.loads(NB.read_text(encoding="utf-8"))
    return "\n".join(
        "".join(cell.get("source", []))
        if isinstance(cell.get("source", []), list)
        else cell.get("source", "")
        for cell in notebook["cells"]
        if cell.get("cell_type") == "code"
    )


def _validator_class():
    source = _source()
    match = re.search(
        r"\nclass SmartWorkerValidator\b[\s\S]*?\n(?=\n(?:class |def )[A-Za-z_])",
        "\n" + source,
    )
    assert match
    namespace = {
        "json": json,
        "re": re,
        "_DOMAIN_CEILING_FACTOR": 1.5,
        "_vov_user_product_tokens": lambda config: set(),
        "_vibe_get_system_meta": lambda value, key: "",
        **_coerce_helpers(),
    }
    exec(match.group(0).lstrip("\n"), namespace)
    return namespace["SmartWorkerValidator"]


class Logger:
    def __init__(self):
        self.lines = []

    def info(self, message):
        self.lines.append(("INFO", str(message)))

    def warning(self, message):
        self.lines.append(("WARNING", str(message)))

    def error(self, message):
        self.lines.append(("ERROR", str(message)))

    def debug(self, message):
        self.lines.append(("DEBUG", str(message)))


def _config(with_vibe):
    business_config = {}
    if with_vibe:
        business_config["vibe_modelling_instructions"] = (
            "intentionally tiny — target 3 domains and ~15 products. do not expand."
        )
    return {
        "PROMPT_VARIABLES": {
            "business_config": business_config,
            "min_data_products_per_domain": 8,
            "max_data_products_per_domain": 8,
            "max_product_name_words": 4,
        },
        "_widgets_values": {},
    }


def _response(count, malformed=False):
    products = [
        {
            "product": f"item_{index}",
            "primary_key": f"item_{index}_id",
            "data_type": "master_data",
        }
        for index in range(count)
    ]
    if malformed:
        products[0]["data_type"] = "not_a_data_type"
    return {"domain": "inventory", "products": products}


def _validate(count, with_vibe, malformed=False):
    logger = Logger()
    validator = _validator_class()(logger, _config(with_vibe))
    response = _response(count, malformed=malformed)
    valid, errors = validator.validate_products(response, "inventory")
    return valid, errors, response, logger.lines


def test_v462_version_and_relaxation_alias():
    source = _source()
    assert agent_version_line() in source
    assert source.lstrip().splitlines()[0] == agent_version_line()
    assert "[vibe-product-count-relax FIRED v4.6.2]" in source


def test_v462_user_vibe_under_min_passes_without_error_log():
    valid, errors, response, lines = _validate(5, with_vibe=True)
    assert valid
    assert errors == []
    assert len(response["products"]) == 5
    assert any(
        level == "INFO"
        and "[vibe-product-count-relax FIRED v4.6.2]" in message
        and "domain=inventory" in message
        and "count=5" in message
        and "bounds=8-8" in message
        and "reason=below_min_free_text_vibe" in message
        for level, message in lines
    )
    assert not any(level == "ERROR" for level, _ in lines)


def test_v462_no_vibe_under_min_remains_strict():
    valid, errors, response, lines = _validate(5, with_vibe=False)
    assert not valid
    assert len(response["products"]) == 5
    assert any("minimum required: 8" in error for error in errors)
    assert any(level == "ERROR" and "below minimum 8" in message for level, message in lines)
    assert not any("vibe-product-count-relax" in message for _, message in lines)


def test_v462_user_vibe_small_overage_is_retained():
    valid, errors, response, lines = _validate(10, with_vibe=True)
    assert valid
    assert errors == []
    assert len(response["products"]) == 10
    assert any(
        level == "INFO"
        and "reason=above_max_free_text_vibe" in message
        and "count=10" in message
        for level, message in lines
    )
    assert not any("v205-deterministic-overcount-trim FIRED" in message for _, message in lines)
    assert not any(level == "ERROR" for level, _ in lines)


def test_v462_no_vibe_small_overage_still_trims():
    valid, errors, response, lines = _validate(10, with_vibe=False)
    assert valid
    assert errors == []
    assert len(response["products"]) == 8
    assert any("v205-deterministic-overcount-trim FIRED" in message for _, message in lines)
    assert not any("vibe-product-count-relax" in message for _, message in lines)


def test_v462_no_vibe_large_overage_remains_strict():
    valid, errors, response, lines = _validate(12, with_vibe=False)
    assert not valid
    assert len(response["products"]) == 12
    assert any("maximum allowed: 8" in error for error in errors)
    assert any(level == "ERROR" and "above maximum 8" in message for level, message in lines)
    assert not any("vibe-product-count-relax" in message for _, message in lines)


def test_v462_malformed_product_still_fails_with_vibe():
    valid, errors, response, lines = _validate(5, with_vibe=True, malformed=True)
    assert not valid
    assert len(response["products"]) == 5
    assert any("missing or invalid data_type" in error for error in errors)
    assert any("vibe-product-count-relax FIRED v4.6.2" in message for _, message in lines)
    assert not any(level == "ERROR" for level, _ in lines)
