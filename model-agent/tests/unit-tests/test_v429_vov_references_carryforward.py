import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from notebook_source_util import exec_function_namespace


def _load_model_to_widgets_flat():
    ns = exec_function_namespace("model_to_widgets_flat")
    return ns["model_to_widgets_flat"]


def test_attribute_references_plural_key_is_carried_forward():
    """model.json stores attribute references under the plural key 'references'
    (see the model.json writer), while the loader historically read only the
    singular 'reference'. VOV v1->v2 therefore dropped every attribute
    reference. The loader must accept either key."""
    fn = _load_model_to_widgets_flat()
    model = {
        "domains": [
            {
                "name": "sales",
                "description": "Sales domain",
                "references": "Industry Standard - Sales",
                "products": [
                    {
                        "name": "order",
                        "description": "Order table",
                        "reference": "Industry Standard - Order",
                        "primary_key": "order_id",
                        "attributes": [
                            {
                                "name": "order_id",
                                "type": "BIGINT",
                                "description": "Order id",
                                "references": "Industry Standard - Order Identifier",
                            },
                            {
                                "name": "customer_id",
                                "type": "BIGINT",
                                "description": "FK to customer",
                                "reference": "Industry Standard - Customer FK",
                            },
                        ],
                    }
                ],
            }
        ]
    }
    domains_out, products_out, attributes_out, _mv = fn(model)

    by_name = {a["attribute"]: a for a in attributes_out}
    assert by_name["order_id"].get("reference") == "Industry Standard - Order Identifier"
    assert by_name["customer_id"].get("reference") == "Industry Standard - Customer FK"

    dom = domains_out[0]
    assert (dom.get("reference") or "") == "Industry Standard - Sales"


def test_singular_reference_still_supported():
    fn = _load_model_to_widgets_flat()
    model = {
        "domains": [
            {
                "name": "sales",
                "reference": "Ref D",
                "products": [
                    {
                        "name": "order",
                        "primary_key": "order_id",
                        "attributes": [
                            {"name": "order_id", "type": "BIGINT", "reference": "Ref A"}
                        ],
                    }
                ],
            }
        ]
    }
    _d, _p, attributes_out, _mv = fn(model)
    by_name = {a["attribute"]: a for a in attributes_out}
    assert by_name["order_id"].get("reference") == "Ref A"
