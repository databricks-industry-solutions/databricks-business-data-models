from notebook_source_util import exec_function_namespace, slice_function_source


class Logger:
    def __init__(self):
        self.lines = []

    def warning(self, message):
        self.lines.append(message)


def _load(cycle=False, bidirectional=False):
    return exec_function_namespace(
        "_v458_assign_fk_if_acyclic",
        {
            "_would_create_cycle": lambda *args, **kwargs: cycle,
            "_would_create_bidirectional_fk": lambda *args, **kwargs: (
                bidirectional,
                "reverse_id" if bidirectional else "",
            ),
        },
    )["_v458_assign_fk_if_acyclic"]


def test_create_autolink_cycle_is_skipped():
    assign = _load(cycle=True)
    attr = {"domain": "alpha", "product": "child", "attribute": "parent_id"}
    logger = Logger()

    assert assign(
        attr,
        "beta.parent.parent_id",
        [attr],
        logger,
        "create-autolink-cycle-skip",
    ) is False
    assert "foreign_key_to" not in attr
    assert any(
        "[create-autolink-cycle-skip FIRED v4.6.0]" in line
        for line in logger.lines
    )


def test_create_parent_bidirectional_edge_is_skipped():
    assign = _load(bidirectional=True)
    attr = {"domain": "alpha", "product": "child", "attribute": "parent_id"}

    assert assign(
        attr,
        "beta.parent.parent_id",
        [attr],
        Logger(),
        "create-parent-cycle-skip",
    ) is False
    assert "foreign_key_to" not in attr


def test_create_autolink_acyclic_edge_is_retained():
    assign = _load()
    attr = {"domain": "alpha", "product": "child", "attribute": "parent_id"}
    target = "beta.parent.parent_id"

    assert assign(
        attr,
        target,
        [attr],
        Logger(),
        "create-autolink-cycle-skip",
    ) is True
    assert attr["foreign_key_to"] == target


def test_post_7d_assignment_paths_use_shared_guard():
    find_missing = slice_function_source("_run_find_missing_fk_links")
    create_parent = slice_function_source(
        "_create_missing_parent_tables_for_unlinked_fks"
    )

    assert "create-autolink-cycle-skip" in find_missing
    assert "deferred-link-cycle-skip" in find_missing
    assert "create-sweep-cycle-skip" in find_missing
    assert find_missing.count("_v458_assign_fk_if_acyclic(") >= 3
    assert create_parent.count("_v458_assign_fk_if_acyclic(") >= 6
    assert "attr['foreign_key_to'] =" not in create_parent
