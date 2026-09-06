from notebook_source_util import notebook_concat_source

import ast
import json
import os
import re
import tempfile
import unittest


REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
AGENT_NB = os.path.join(REPO_ROOT, 'agent', 'dbx_vibe_modelling_agent.ipynb')


def load_agent_source():
    with open(AGENT_NB) as f:
        nb = json.load(f)
    return ''.join(''.join(c.get('source', [])) for c in nb['cells'] if c.get('cell_type') == 'code')


def _extract_function_block(src, fn_name):
    """Slice a function definition out of agent source via ast for behavioral exec."""
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == fn_name:
            lines = src.splitlines()
            block = lines[node.lineno - 1: node.end_lineno]
            return '\n'.join(block)
    raise AssertionError(f'function {fn_name!r} not found in agent source')


_NAMESPACE_CACHE = None


def _build_lineage_namespace():
    """Exec the v0.9.3 vibe_lineage helpers + step into an isolated namespace and return it.
    Cached at module level so we only ast.parse the 5MB notebook source ONCE across all tests.
    Stubs out write_to_dbfs to capture writes into the namespace."""
    global _NAMESPACE_CACHE
    if _NAMESPACE_CACHE is not None:
        return _NAMESPACE_CACHE
    src = load_agent_source()
    fns = [
        'capture_vibe_lineage_snapshot',
        '_hydrate_lineage_snapshot_from_model_json',
        '_vibe_lineage_build_physical_fqn',
        '_vibe_lineage_lookup_db',
        '_vibe_lineage_lookup_table',
        '_vibe_lineage_emit',
        '_diff_lineage_snapshots',
        '_match_change_to_requirement',
        '_vibe_lineage_requirements_for_artifact',
        '_v304_vibe_outcome',
        '_v304_vibe_missed_rollup',
        'step_generate_vibe_lineage',
    ]
    glued = '\n\n'.join(_extract_function_block(src, fn) for fn in fns)

    ns = {'__name__': 'lineage_test', 'json': json}
    m = re.search(r'__AGENT_VERSION__\s*=\s*"([^"]+)"', src)
    assert m is not None, 'AGENT_VERSION constant missing from source'
    ns['__AGENT_VERSION__'] = m.group(1)
    ns['_writes'] = []

    def _write_to_dbfs(content, destination_path, logger):
        ns['_writes'].append((destination_path, content))
        if logger:
            logger.info(f'STUB wrote {len(content)} bytes to {destination_path}')

    ns['write_to_dbfs'] = _write_to_dbfs
    exec(glued, ns)
    _NAMESPACE_CACHE = ns
    return ns


class _MemLogger:
    """Minimal logger that captures info/warning/debug for behavioral assertions."""

    def __init__(self):
        self.info_lines = []
        self.warning_lines = []
        self.debug_lines = []
        self.error_lines = []

    def info(self, msg):
        self.info_lines.append(str(msg))

    def warning(self, msg):
        self.warning_lines.append(str(msg))

    def debug(self, msg):
        self.debug_lines.append(str(msg))

    def error(self, msg):
        self.error_lines.append(str(msg))


def _basic_after_state():
    """Synthetic after-state shared by several tests: 1 domain, 2 products, 4 attrs incl 1 FK."""
    domains = [{'domain': 'network', 'description': 'Telecom network domain', 'division': 'operations',
                'database_name': 'network', 'tags': ''}]
    products = [
        {'domain': 'network', 'product': 'device', 'description': 'Network device entity',
         'type': 'entity', 'primary_key': 'device_id', 'division': 'operations',
         'function': 'core', 'subdomain': 'inventory', 'tags': '', 'table_name': 'device'},
        {'domain': 'network', 'product': 'interface', 'description': 'Network interface entity',
         'type': 'entity', 'primary_key': 'interface_id', 'division': 'operations',
         'function': 'core', 'subdomain': 'inventory', 'tags': '', 'table_name': 'interface'},
    ]
    attributes = [
        {'domain': 'network', 'product': 'device', 'attribute': 'device_id', 'column_name': 'device_id',
         'type': 'BIGINT', 'tags': 'primary_key', 'description': 'PK', 'foreign_key_to': '',
         'is_primary_key': True, 'value_regex': ''},
        {'domain': 'network', 'product': 'device', 'attribute': 'name', 'column_name': 'name',
         'type': 'STRING', 'tags': '', 'description': 'Device name', 'foreign_key_to': '',
         'is_primary_key': False, 'value_regex': ''},
        {'domain': 'network', 'product': 'interface', 'attribute': 'interface_id', 'column_name': 'interface_id',
         'type': 'BIGINT', 'tags': 'primary_key', 'description': 'PK', 'foreign_key_to': '',
         'is_primary_key': True, 'value_regex': ''},
        {'domain': 'network', 'product': 'interface', 'attribute': 'parent_device_id',
         'column_name': 'parent_device_id', 'type': 'BIGINT', 'tags': 'foreign_key',
         'description': 'FK to device', 'foreign_key_to': 'network.device.device_id',
         'is_primary_key': False, 'value_regex': ''},
    ]
    metric_views = [
        {'view_name': 'device_count_mv', 'owner_domain': 'network', 'owner_product': 'device',
         'sql': 'SELECT COUNT(*) FROM network.device', 'description': 'Device count',
         'dimensions_count': 0, 'measures_count': 1},
    ]
    return domains, products, attributes, metric_views


def _build_widgets_values(operation='new base model', vibes='', requirements=None,
                          master_actions=None, deployment_catalog=None,
                          domains=None, products=None, attributes=None, metric_views=None,
                          prior_model_json=None, target_volume=None,
                          current_version='1', model_scope='ecm'):
    return {
        'logger': _MemLogger(),
        'operation': operation,
        '_widget_raw_values': {'operation': operation, 'deployment_catalog': deployment_catalog or ''},
        'vibe_modelling_instructions': vibes,
        'vibe_requirements_checklist': requirements or [],
        'vibe_master_actions': master_actions or [],
        'deployment_catalog': deployment_catalog or '',
        'config': {'TARGET_VOLUME': target_volume or '/tmp/lineage_test_vol'},
        'domains': domains or [],
        'products': products or [],
        'attributes': attributes or [],
        'metric_views': metric_views or [],
        'business_context_raw': prior_model_json,
        'current_version': current_version,
        'model_scope': model_scope,
    }


# --------------------------------------------------------------------------- #
# 1. Version + alias sentinel checks (cheap, prove the version bumped)         #
# --------------------------------------------------------------------------- #

class TestV93VersionAndAliases(unittest.TestCase):
    def setUp(self):
        self.src = load_agent_source()

    def test_version_is_0_9_3(self):
        # v0.9.6 advanced the version constant; verify v0.9.5 lineage feature is preserved
        # in the header chain AND the constant is >= 0.9.5.
        m = re.search(r'__AGENT_VERSION__\s*=\s*"([^"]+)"', self.src)
        self.assertIsNotNone(m, 'AGENT_VERSION constant missing')
        parts = m.group(1).split('.')
        self.assertEqual(len(parts), 3)
        major, minor, patch = (int(p) for p in parts)
        self.assertGreaterEqual((major, minor, patch), (0, 9, 5),
                                f'Version regressed below 0.9.5: got {m.group(1)}')
        self.assertIn('v0.9.5', self.src,
                      'v0.9.5 lineage marker not preserved in header chain')

    def test_version_single_digit_segments(self):
        m = re.search(r'__AGENT_VERSION__\s*=\s*"([^"]+)"', self.src)
        for seg in m.group(1).split('.'):
            self.assertEqual(len(seg), 1, f'Segment {seg!r} is not single-digit (CLAUDE.md \u00a73a)')
            self.assertTrue(seg.isdigit(), f'Segment {seg!r} is not numeric')

    def test_artifact_alias_present(self):
        self.assertIn('vibe-lineage-artifact FIRED', self.src,
                      'alias=vibe-lineage-artifact log-line missing')

    def test_diff_helper_defined(self):
        self.assertIn('def _diff_lineage_snapshots', self.src)
        self.assertIn('def _match_change_to_requirement', self.src)
        self.assertIn('def _hydrate_lineage_snapshot_from_model_json', self.src)

    def test_step_function_wired_in_pipeline(self):
        # 2 occurrences = function definition + main-flow call site.
        self.assertEqual(self.src.count('step_generate_vibe_lineage('), 2,
                         'step_generate_vibe_lineage must be defined once and called once')


# --------------------------------------------------------------------------- #
# 2. capture_vibe_lineage_snapshot extracts per-field values                   #
# --------------------------------------------------------------------------- #

class TestV93CaptureSnapshot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = _build_lineage_namespace()

    def test_snapshot_captures_attribute_type_tags_description(self):
        doms, prods, attrs, mvs = _basic_after_state()
        snap = self.ns['capture_vibe_lineage_snapshot'](doms, prods, attrs, mvs)
        a = snap['attributes']['network.device.device_id']
        self.assertEqual(a['type'], 'BIGINT')
        self.assertEqual(a['tags'], 'primary_key')
        self.assertEqual(a['description'], 'PK')
        self.assertTrue(a['is_primary_key'])
        self.assertEqual(a['column_name'], 'device_id')

    def test_snapshot_captures_foreign_key_to(self):
        doms, prods, attrs, mvs = _basic_after_state()
        snap = self.ns['capture_vibe_lineage_snapshot'](doms, prods, attrs, mvs)
        a = snap['attributes']['network.interface.parent_device_id']
        self.assertEqual(a['foreign_key_to'], 'network.device.device_id')
        self.assertFalse(a['is_primary_key'])

    def test_snapshot_captures_product_subdomain_and_division(self):
        doms, prods, attrs, mvs = _basic_after_state()
        snap = self.ns['capture_vibe_lineage_snapshot'](doms, prods, attrs, mvs)
        p = snap['products']['network.device']
        self.assertEqual(p['subdomain'], 'inventory')
        self.assertEqual(p['division'], 'operations')
        self.assertEqual(p['table_name'], 'device')

    def test_snapshot_captures_domain_division_and_db_name(self):
        doms, prods, attrs, mvs = _basic_after_state()
        snap = self.ns['capture_vibe_lineage_snapshot'](doms, prods, attrs, mvs)
        d = snap['domains']['network']
        self.assertEqual(d['division'], 'operations')
        self.assertEqual(d['database_name'], 'network')

    def test_snapshot_captures_metric_views(self):
        doms, prods, attrs, mvs = _basic_after_state()
        snap = self.ns['capture_vibe_lineage_snapshot'](doms, prods, attrs, mvs)
        self.assertIn('device_count_mv', snap['metric_views'])
        self.assertEqual(snap['metric_views']['device_count_mv']['owner_product'], 'device')

    def test_snapshot_handles_empty_inputs(self):
        snap = self.ns['capture_vibe_lineage_snapshot']([], [], [])
        self.assertEqual(snap, {'domains': {}, 'products': {}, 'attributes': {}, 'metric_views': {}})

    def test_snapshot_skips_malformed_entries(self):
        snap = self.ns['capture_vibe_lineage_snapshot'](
            [{'description': 'no domain key'}, 'not a dict'],
            [{'domain': '', 'product': 'p'}, {'domain': 'd', 'product': ''}],
            [{'domain': 'd', 'product': 'p', 'attribute': ''}],
        )
        self.assertEqual(snap['domains'], {})
        self.assertEqual(snap['products'], {})
        self.assertEqual(snap['attributes'], {})


# --------------------------------------------------------------------------- #
# 3. _hydrate_lineage_snapshot_from_model_json reads nested model.json shape   #
# --------------------------------------------------------------------------- #

class TestV93HydrateFromModelJson(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = _build_lineage_namespace()

    def test_hydrates_from_nested_model_json(self):
        mj = {
            'agent_version': '0.9.2',
            'model': {
                'domains': [{
                    'name': 'network', 'description': 'Net',
                    'division': 'operations', 'database_name': 'network',
                    'products': [{
                        'name': 'device', 'description': 'Device', 'type': 'entity',
                        'primary_key': 'device_id', 'subdomain': 'inventory',
                        'table_name': 'device',
                        'attributes': [{
                            'name': 'device_id', 'type': 'BIGINT', 'tags': 'primary_key',
                            'description': 'PK', 'is_primary_key': True, 'column_name': 'device_id',
                            'foreign_key_to': '',
                        }]
                    }]
                }],
                'metric_views': [{
                    'view_name': 'mv1', 'owner_domain': 'network', 'owner_product': 'device',
                    'sql': 'SELECT 1', 'description': 'demo', 'dimensions_count': 0, 'measures_count': 1,
                }]
            }
        }
        snap = self.ns['_hydrate_lineage_snapshot_from_model_json'](mj)
        self.assertIn('network', snap['domains'])
        self.assertEqual(snap['domains']['network']['division'], 'operations')
        self.assertIn('network.device', snap['products'])
        self.assertEqual(snap['products']['network.device']['subdomain'], 'inventory')
        self.assertIn('network.device.device_id', snap['attributes'])
        self.assertEqual(snap['attributes']['network.device.device_id']['type'], 'BIGINT')
        self.assertIn('mv1', snap['metric_views'])

    def test_hydrate_handles_bare_model_dict(self):
        mj = {'domains': [{'name': 'd1', 'products': []}]}
        snap = self.ns['_hydrate_lineage_snapshot_from_model_json'](mj)
        self.assertIn('d1', snap['domains'])

    def test_hydrate_returns_none_for_invalid_input(self):
        self.assertIsNone(self.ns['_hydrate_lineage_snapshot_from_model_json'](None))
        self.assertIsNone(self.ns['_hydrate_lineage_snapshot_from_model_json']('not a dict'))

    def test_hydrate_accepts_data_products_alias(self):
        mj = {'model': {'domains': [{'name': 'd1', 'data_products': [
            {'name': 'p1', 'attributes': []}]}]}}
        snap = self.ns['_hydrate_lineage_snapshot_from_model_json'](mj)
        self.assertIn('d1.p1', snap['products'])


# --------------------------------------------------------------------------- #
# 4. _diff_lineage_snapshots — the core diff engine                            #
# --------------------------------------------------------------------------- #

class TestV93DiffEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = _build_lineage_namespace()

    def _capture(self, doms, prods, attrs, mvs=None):
        return self.ns['capture_vibe_lineage_snapshot'](doms, prods, attrs, mvs)

    def test_added_attribute_records_summary_only(self):
        before = self._capture([{'domain': 'd1'}], [{'domain': 'd1', 'product': 'p1'}], [])
        after = self._capture(
            [{'domain': 'd1'}],
            [{'domain': 'd1', 'product': 'p1'}],
            [{'domain': 'd1', 'product': 'p1', 'attribute': 'a1', 'type': 'STRING'}],
        )
        objs = self.ns['_diff_lineage_snapshots'](before, after, catalog=None)
        attr_adds = [o for o in objs if o['type'] == 'attribute' and o['action'] == 'added']
        self.assertEqual(len(attr_adds), 1)
        self.assertIsNone(attr_adds[0]['before'])
        self.assertIsInstance(attr_adds[0]['after'], dict)
        self.assertEqual(attr_adds[0]['after']['type'], 'STRING')

    def test_removed_attribute_records_before_only(self):
        before = self._capture(
            [{'domain': 'd1'}], [{'domain': 'd1', 'product': 'p1'}],
            [{'domain': 'd1', 'product': 'p1', 'attribute': 'a1', 'type': 'STRING'}])
        after = self._capture([{'domain': 'd1'}], [{'domain': 'd1', 'product': 'p1'}], [])
        objs = self.ns['_diff_lineage_snapshots'](before, after, catalog=None)
        attr_rems = [o for o in objs if o['type'] == 'attribute' and o['action'] == 'removed']
        self.assertEqual(len(attr_rems), 1)
        self.assertIsNone(attr_rems[0]['after'])
        self.assertIsInstance(attr_rems[0]['before'], dict)

    def test_one_entry_per_field_changed_on_modified_attribute(self):
        """v0.9.3 atomic-granularity: changing type+description+tags emits 3 entries with same FQN."""
        before = self._capture(
            [{'domain': 'd1'}], [{'domain': 'd1', 'product': 'p1'}],
            [{'domain': 'd1', 'product': 'p1', 'attribute': 'a1',
              'type': 'STRING', 'tags': '', 'description': 'old desc'}])
        after = self._capture(
            [{'domain': 'd1'}], [{'domain': 'd1', 'product': 'p1'}],
            [{'domain': 'd1', 'product': 'p1', 'attribute': 'a1',
              'type': 'INT', 'tags': 'pii', 'description': 'new desc'}])
        objs = self.ns['_diff_lineage_snapshots'](before, after, catalog=None)
        attr_mods = [o for o in objs if o['type'] == 'attribute' and o['action'] == 'modified']
        self.assertEqual(len(attr_mods), 3,
                         f'expected 3 atomic modified entries, got {len(attr_mods)}: {attr_mods}')
        fields = sorted(o['field'] for o in attr_mods)
        self.assertEqual(fields, ['description', 'tags', 'type'])
        # All share the same logical_fqn
        fqns = {o['logical_fqn'] for o in attr_mods}
        self.assertEqual(fqns, {'d1.p1.a1'})

    def test_relationship_entry_emitted_on_fk_add(self):
        """Attribute exists pre/post but FK field went '' -> value: emits added (afk truthy, bfk falsy)."""
        before = self._capture(
            [{'domain': 'd1'}], [{'domain': 'd1', 'product': 'p1'},
                                  {'domain': 'd1', 'product': 'p2'}],
            [{'domain': 'd1', 'product': 'p1', 'attribute': 'fk', 'type': 'BIGINT'}])
        after = self._capture(
            [{'domain': 'd1'}], [{'domain': 'd1', 'product': 'p1'},
                                  {'domain': 'd1', 'product': 'p2'}],
            [{'domain': 'd1', 'product': 'p1', 'attribute': 'fk',
              'type': 'BIGINT', 'foreign_key_to': 'd1.p2.p2_id'}])
        objs = self.ns['_diff_lineage_snapshots'](before, after, catalog=None)
        rels = [o for o in objs if o['type'] == 'relationship']
        self.assertEqual(len(rels), 1)
        self.assertEqual(rels[0]['action'], 'added',
                         'FK going from empty to value on existing attribute should record as added relationship')
        self.assertEqual(rels[0]['field'], 'foreign_key_to')
        self.assertEqual(rels[0]['after'], 'd1.p2.p2_id')
        self.assertIsNone(rels[0]['before'])

    def test_relationship_modified_when_fk_redirects(self):
        """FK going from one valid target to another valid target should record as modified."""
        before = self._capture(
            [{'domain': 'd1'}],
            [{'domain': 'd1', 'product': 'p1'}, {'domain': 'd1', 'product': 'p2'},
             {'domain': 'd1', 'product': 'p3'}],
            [{'domain': 'd1', 'product': 'p1', 'attribute': 'fk',
              'type': 'BIGINT', 'foreign_key_to': 'd1.p2.p2_id'}])
        after = self._capture(
            [{'domain': 'd1'}],
            [{'domain': 'd1', 'product': 'p1'}, {'domain': 'd1', 'product': 'p2'},
             {'domain': 'd1', 'product': 'p3'}],
            [{'domain': 'd1', 'product': 'p1', 'attribute': 'fk',
              'type': 'BIGINT', 'foreign_key_to': 'd1.p3.p3_id'}])
        objs = self.ns['_diff_lineage_snapshots'](before, after, catalog=None)
        rels = [o for o in objs if o['type'] == 'relationship']
        self.assertEqual(len(rels), 1)
        self.assertEqual(rels[0]['action'], 'modified')
        self.assertEqual(rels[0]['before'], 'd1.p2.p2_id')
        self.assertEqual(rels[0]['after'], 'd1.p3.p3_id')

    def test_relationship_entry_emitted_on_brand_new_fk_attribute(self):
        """When the attribute itself is brand-new AND carries an FK, a relationship entry fires too."""
        before = self._capture([{'domain': 'd1'}], [{'domain': 'd1', 'product': 'p1'},
                                                     {'domain': 'd1', 'product': 'p2'}], [])
        after = self._capture(
            [{'domain': 'd1'}], [{'domain': 'd1', 'product': 'p1'},
                                  {'domain': 'd1', 'product': 'p2'}],
            [{'domain': 'd1', 'product': 'p1', 'attribute': 'fk',
              'type': 'BIGINT', 'foreign_key_to': 'd1.p2.p2_id'}])
        objs = self.ns['_diff_lineage_snapshots'](before, after, catalog=None)
        rels = [o for o in objs if o['type'] == 'relationship']
        self.assertEqual(len(rels), 1)
        self.assertEqual(rels[0]['action'], 'added')
        self.assertEqual(rels[0]['after'], 'd1.p2.p2_id')
        self.assertIsNone(rels[0]['before'])

    def test_relationship_removed_on_fk_drop(self):
        before = self._capture(
            [{'domain': 'd1'}], [{'domain': 'd1', 'product': 'p1'},
                                  {'domain': 'd1', 'product': 'p2'}],
            [{'domain': 'd1', 'product': 'p1', 'attribute': 'fk',
              'type': 'BIGINT', 'foreign_key_to': 'd1.p2.p2_id'}])
        after = self._capture(
            [{'domain': 'd1'}], [{'domain': 'd1', 'product': 'p1'},
                                  {'domain': 'd1', 'product': 'p2'}],
            [{'domain': 'd1', 'product': 'p1', 'attribute': 'fk',
              'type': 'BIGINT', 'foreign_key_to': ''}])
        objs = self.ns['_diff_lineage_snapshots'](before, after, catalog=None)
        rels = [o for o in objs if o['type'] == 'relationship']
        self.assertEqual(len(rels), 1)
        self.assertEqual(rels[0]['action'], 'removed')
        self.assertEqual(rels[0]['before'], 'd1.p2.p2_id')

    def test_metric_view_add_drop_modify(self):
        before_mvs = [{'view_name': 'v1', 'sql': 'SELECT 1', 'dimensions_count': 0, 'measures_count': 1}]
        after_mvs = [{'view_name': 'v1', 'sql': 'SELECT 2', 'dimensions_count': 0, 'measures_count': 1},
                     {'view_name': 'v2', 'sql': 'SELECT 3', 'dimensions_count': 1, 'measures_count': 0}]
        before = self._capture([{'domain': 'd1'}], [], [], before_mvs)
        after = self._capture([{'domain': 'd1'}], [], [], after_mvs)
        objs = self.ns['_diff_lineage_snapshots'](before, after, catalog=None)
        mv_objs = [o for o in objs if o['type'] == 'metric_view']
        added = [o for o in mv_objs if o['action'] == 'added']
        modified = [o for o in mv_objs if o['action'] == 'modified']
        self.assertEqual([o['logical_fqn'] for o in added], ['v2'])
        # sql change on v1 -> one modified field entry
        self.assertEqual([(o['logical_fqn'], o['field']) for o in modified], [('v1', 'sql')])

    def test_division_change_attributed_to_domain_type(self):
        """v0.9.3 spec: division/subdomain/tags/description changes appear as modified field on parent entity."""
        before = self._capture([{'domain': 'd1', 'division': 'operations'}], [], [])
        after = self._capture([{'domain': 'd1', 'division': 'business'}], [], [])
        objs = self.ns['_diff_lineage_snapshots'](before, after, catalog=None)
        dom_mods = [o for o in objs if o['type'] == 'domain' and o['action'] == 'modified']
        self.assertEqual(len(dom_mods), 1)
        self.assertEqual(dom_mods[0]['field'], 'division')
        self.assertEqual(dom_mods[0]['before'], 'operations')
        self.assertEqual(dom_mods[0]['after'], 'business')

    def test_subdomain_change_attributed_to_product_type(self):
        before = self._capture(
            [{'domain': 'd1'}],
            [{'domain': 'd1', 'product': 'p1', 'subdomain': 'subA'}], [])
        after = self._capture(
            [{'domain': 'd1'}],
            [{'domain': 'd1', 'product': 'p1', 'subdomain': 'subB'}], [])
        objs = self.ns['_diff_lineage_snapshots'](before, after, catalog=None)
        prod_mods = [o for o in objs if o['type'] == 'product' and o['action'] == 'modified']
        sub_mods = [o for o in prod_mods if o['field'] == 'subdomain']
        self.assertEqual(len(sub_mods), 1)
        self.assertEqual(sub_mods[0]['before'], 'subA')
        self.assertEqual(sub_mods[0]['after'], 'subB')

    def test_physical_fqn_present_when_catalog_set(self):
        before = self._capture([], [], [])
        after = self._capture(
            [{'domain': 'network', 'database_name': 'net_db'}],
            [{'domain': 'network', 'product': 'device', 'table_name': 'device_tbl'}],
            [{'domain': 'network', 'product': 'device', 'attribute': 'device_id',
              'column_name': 'device_id', 'type': 'BIGINT'}],
        )
        objs = self.ns['_diff_lineage_snapshots'](before, after, catalog='acme_main')
        attr_adds = [o for o in objs if o['type'] == 'attribute' and o['action'] == 'added']
        self.assertEqual(len(attr_adds), 1)
        self.assertEqual(attr_adds[0]['physical_fqn'], 'acme_main.net_db.device_tbl.device_id')
        self.assertEqual(attr_adds[0]['logical_fqn'], 'network.device.device_id')

    def test_physical_fqn_omitted_when_catalog_missing(self):
        before = self._capture([], [], [])
        after = self._capture(
            [{'domain': 'network'}],
            [{'domain': 'network', 'product': 'device'}],
            [{'domain': 'network', 'product': 'device', 'attribute': 'device_id'}])
        objs = self.ns['_diff_lineage_snapshots'](before, after, catalog=None)
        for o in objs:
            self.assertNotIn('physical_fqn', o,
                             f'physical_fqn must be ABSENT (not None) when catalog unset, got {o}')

    def test_relationship_physical_fqn_arrow_notation(self):
        before = self._capture([], [], [])
        after = self._capture(
            [{'domain': 'network', 'database_name': 'network'}],
            [{'domain': 'network', 'product': 'device', 'table_name': 'device'},
             {'domain': 'network', 'product': 'interface', 'table_name': 'interface'}],
            [{'domain': 'network', 'product': 'interface', 'attribute': 'parent_device_id',
              'column_name': 'parent_device_id', 'type': 'BIGINT',
              'foreign_key_to': 'network.device.device_id'}])
        objs = self.ns['_diff_lineage_snapshots'](before, after, catalog='acme_main')
        rels = [o for o in objs if o['type'] == 'relationship']
        self.assertEqual(len(rels), 1)
        self.assertEqual(rels[0]['physical_fqn'],
                         'acme_main.network.interface.parent_device_id -> acme_main.network.device.device_id')


# --------------------------------------------------------------------------- #
# 5. _match_change_to_requirement attribution                                  #
# --------------------------------------------------------------------------- #

class TestV93Attribution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = _build_lineage_namespace()

    def test_attribution_via_mapped_req_ids(self):
        obj = {'type': 'attribute', 'logical_fqn': 'network.device.serial_no'}
        master_actions = [{'name': 'network.device', 'mapped_req_ids': ['VREQ-001']}]
        rid = self.ns['_match_change_to_requirement'](obj, [], master_actions)
        self.assertEqual(rid, 'VREQ-001')

    def test_attribution_via_scope_targets_prefix(self):
        obj = {'type': 'attribute', 'logical_fqn': 'network.device.serial_no'}
        reqs = [{'req_id': 'VREQ-002', 'scope_targets': ['network']}]
        rid = self.ns['_match_change_to_requirement'](obj, reqs, [])
        self.assertEqual(rid, 'VREQ-002')

    def test_attribution_falls_back_to_unattributed(self):
        obj = {'type': 'attribute', 'logical_fqn': 'unrelated.product.col'}
        reqs = [{'req_id': 'VREQ-003', 'scope_targets': ['network']}]
        rid = self.ns['_match_change_to_requirement'](obj, reqs, [])
        self.assertEqual(rid, '_unattributed')

    def test_master_actions_outrank_scope_targets(self):
        obj = {'type': 'attribute', 'logical_fqn': 'network.device.serial_no'}
        reqs = [{'req_id': 'VREQ-SCOPE', 'scope_targets': ['network']}]
        master_actions = [{'name': 'network.device', 'mapped_req_ids': ['VREQ-MASTER']}]
        rid = self.ns['_match_change_to_requirement'](obj, reqs, master_actions)
        self.assertEqual(rid, 'VREQ-MASTER',
                         'master_actions.mapped_req_ids must outrank scope_targets prefix match')

    def test_relationship_logical_fqn_uses_source_side(self):
        obj = {'type': 'relationship',
               'logical_fqn': 'network.interface.parent_device_id -> network.device.device_id'}
        reqs = [{'req_id': 'VREQ-IF', 'scope_targets': ['network.interface']}]
        rid = self.ns['_match_change_to_requirement'](obj, reqs, [])
        self.assertEqual(rid, 'VREQ-IF')

    def test_empty_inputs_default_to_unattributed(self):
        obj = {'type': 'attribute', 'logical_fqn': 'd.p.a'}
        rid = self.ns['_match_change_to_requirement'](obj, [], [])
        self.assertEqual(rid, '_unattributed')

    def test_missing_logical_fqn_defaults_to_unattributed(self):
        obj = {'type': 'attribute'}
        rid = self.ns['_match_change_to_requirement'](obj, [], [])
        self.assertEqual(rid, '_unattributed')


# --------------------------------------------------------------------------- #
# 6. step_generate_vibe_lineage end-to-end (writes file, asserts content)      #
# --------------------------------------------------------------------------- #

class TestV93StepGenerateLineage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = _build_lineage_namespace()

    def _run_step(self, wv):
        # Reset write capture for each invocation.
        self.ns['_writes'] = []
        self.ns['step_generate_vibe_lineage'](wv)
        return list(self.ns['_writes'])

    def test_lineage_written_for_new_base_model(self):
        doms, prods, attrs, mvs = _basic_after_state()
        wv = _build_widgets_values(
            operation='new base model',
            vibes='Build me a network model with device and interface tables.',
            requirements=[{'req_id': 'VREQ-1', 'text': 'Build network model',
                           'scope': 'model', 'scope_targets': []}],
            domains=doms, products=prods, attributes=attrs, metric_views=mvs,
            target_volume='/tmp/lineage_test_new_base',
        )
        writes = self._run_step(wv)
        self.assertEqual(len(writes), 1, f'expected 1 file write, got {len(writes)}')
        path, content = writes[0]
        self.assertEqual(path, '/tmp/lineage_test_new_base/vibes/vibe_lineage.json')
        artifact = json.loads(content)
        self.assertIsNone(artifact['from_version'], 'new base model has no from_version')
        self.assertEqual(artifact['operation'], 'new base model')
        self.assertEqual(artifact['to_version'], 'v1_ecm')
        # Every affected_object is action=added (no prior state)
        for entry in artifact['lineage']:
            for obj in entry['affected_objects']:
                if obj['type'] != 'relationship':
                    self.assertEqual(obj['action'], 'added',
                                     f'new base model should produce only added entries, got {obj}')

    def test_lineage_written_for_vov(self):
        doms, prods, attrs, mvs = _basic_after_state()
        # Mutate after-state: rename device -> asset (drop device, add asset)
        new_prods = [{'domain': 'network', 'product': 'asset',
                      'description': 'Renamed from device',
                      'type': 'entity', 'primary_key': 'asset_id',
                      'subdomain': 'inventory', 'table_name': 'asset'},
                     prods[1]]
        new_attrs = [
            {'domain': 'network', 'product': 'asset', 'attribute': 'asset_id',
             'column_name': 'asset_id', 'type': 'BIGINT', 'tags': 'primary_key',
             'description': 'PK', 'is_primary_key': True},
            attrs[2],
            {'domain': 'network', 'product': 'interface', 'attribute': 'parent_device_id',
             'column_name': 'parent_device_id', 'type': 'BIGINT', 'tags': 'foreign_key',
             'description': 'FK to asset', 'foreign_key_to': 'network.asset.asset_id'},
        ]
        # Prior model.json (matches _basic_after_state)
        prior_mj = {
            'model': {
                'domains': [{'name': 'network', 'division': 'operations',
                             'database_name': 'network',
                             'products': [
                                 {'name': 'device', 'subdomain': 'inventory',
                                  'table_name': 'device',
                                  'attributes': [
                                      {'name': 'device_id', 'type': 'BIGINT',
                                       'tags': 'primary_key', 'is_primary_key': True,
                                       'column_name': 'device_id'},
                                      {'name': 'name', 'type': 'STRING',
                                       'column_name': 'name'},
                                  ]},
                                 {'name': 'interface', 'subdomain': 'inventory',
                                  'table_name': 'interface',
                                  'attributes': [
                                      {'name': 'interface_id', 'type': 'BIGINT',
                                       'tags': 'primary_key', 'is_primary_key': True,
                                       'column_name': 'interface_id'},
                                      {'name': 'parent_device_id', 'type': 'BIGINT',
                                       'tags': 'foreign_key',
                                       'column_name': 'parent_device_id',
                                       'foreign_key_to': 'network.device.device_id'},
                                  ]},
                             ]}],
                'metric_views': []
            }
        }
        wv = _build_widgets_values(
            operation='vibe modeling of version',
            vibes='Rename device to asset.',
            requirements=[{'req_id': 'VREQ-RENAME', 'text': 'Rename device to asset',
                           'scope': 'product', 'scope_targets': ['network.device']}],
            domains=doms, products=new_prods, attributes=new_attrs,
            metric_views=[], prior_model_json=prior_mj,
            target_volume='/tmp/lineage_test_vov',
            current_version='2',
        )
        writes = self._run_step(wv)
        self.assertEqual(len(writes), 1)
        artifact = json.loads(writes[0][1])
        self.assertEqual(artifact['from_version'], 'v1_ecm')
        self.assertEqual(artifact['to_version'], 'v2_ecm')
        # We expect at least one added product (asset), one removed (device),
        # and a relationship modified (FK redirected).
        all_objs = [o for e in artifact['lineage'] for o in e['affected_objects']]
        added_products = [o for o in all_objs if o['type'] == 'product' and o['action'] == 'added']
        removed_products = [o for o in all_objs if o['type'] == 'product' and o['action'] == 'removed']
        rel_changes = [o for o in all_objs if o['type'] == 'relationship']
        self.assertTrue(any(o['logical_fqn'] == 'network.asset' for o in added_products),
                        f'asset product not added: {added_products}')
        self.assertTrue(any(o['logical_fqn'] == 'network.device' for o in removed_products),
                        f'device product not removed: {removed_products}')
        self.assertTrue(rel_changes, f'expected relationship changes, got {all_objs}')

    def test_install_operation_does_not_write_lineage(self):
        wv = _build_widgets_values(
            operation='install model',
            vibes='Install the model.',
            requirements=[{'req_id': 'VREQ-X', 'text': 'install'}],
            target_volume='/tmp/lineage_test_install',
        )
        writes = self._run_step(wv)
        self.assertEqual(writes, [], 'install must not write vibe_lineage.json')
        skip_logged = any('[vibe-lineage-skip FIRED]' in m for m in wv['logger'].info_lines)
        self.assertTrue(skip_logged, 'expected vibe-lineage-skip log line for install op')

    def test_uninstall_operation_does_not_write_lineage(self):
        wv = _build_widgets_values(
            operation='uninstall model version',
            requirements=[{'req_id': 'VREQ-X', 'text': 'uninstall'}],
            target_volume='/tmp/lineage_test_uninstall',
        )
        writes = self._run_step(wv)
        self.assertEqual(writes, [])

    def test_empty_vibes_and_empty_requirements_no_artifact(self):
        wv = _build_widgets_values(
            operation='new base model',
            vibes='',
            requirements=[],
            target_volume='/tmp/lineage_test_empty',
        )
        writes = self._run_step(wv)
        self.assertEqual(writes, [], 'empty vibes + no requirements should not write')

    def test_unattributed_bucket_emitted_when_changes_have_no_matching_requirement(self):
        doms, prods, attrs, mvs = _basic_after_state()
        wv = _build_widgets_values(
            operation='new base model',
            vibes='Some vibe',
            requirements=[{'req_id': 'VREQ-NOMATCH', 'text': 'wrong scope',
                           'scope': 'attribute', 'scope_targets': ['other_domain.other_table']}],
            domains=doms, products=prods, attributes=attrs, metric_views=mvs,
            target_volume='/tmp/lineage_test_unattributed',
        )
        writes = self._run_step(wv)
        artifact = json.loads(writes[0][1])
        unattr = [e for e in artifact['lineage'] if e['requirement_id'] == '_unattributed']
        self.assertEqual(len(unattr), 1, 'expected exactly one _unattributed bucket')
        self.assertGreater(len(unattr[0]['affected_objects']), 0, 'bucket should hold the orphan changes')
        # All affected_objects under _unattributed get source='pipeline'
        for o in unattr[0]['affected_objects']:
            self.assertEqual(o['source'], 'pipeline',
                             f'unattributed entries should be relabelled to source=pipeline, got {o}')

    def test_physical_fqn_appears_when_deployment_catalog_set(self):
        doms, prods, attrs, mvs = _basic_after_state()
        wv = _build_widgets_values(
            operation='new base model',
            vibes='Build network',
            requirements=[{'req_id': 'VREQ-1', 'text': 'Build', 'scope': 'model', 'scope_targets': []}],
            domains=doms, products=prods, attributes=attrs, metric_views=mvs,
            deployment_catalog='acme_main',
            target_volume='/tmp/lineage_test_physical_fqn',
        )
        writes = self._run_step(wv)
        artifact = json.loads(writes[0][1])
        attr_objs = [o for e in artifact['lineage'] for o in e['affected_objects']
                     if o['type'] == 'attribute']
        self.assertTrue(attr_objs, 'expected attribute objects')
        self.assertTrue(any('physical_fqn' in o and o['physical_fqn'].startswith('acme_main.')
                            for o in attr_objs),
                        f'expected physical_fqn under acme_main., got {attr_objs}')

    def test_no_physical_fqn_when_catalog_absent(self):
        doms, prods, attrs, mvs = _basic_after_state()
        wv = _build_widgets_values(
            operation='new base model',
            vibes='Build network',
            requirements=[{'req_id': 'VREQ-1', 'text': 'Build', 'scope': 'model', 'scope_targets': []}],
            domains=doms, products=prods, attributes=attrs, metric_views=mvs,
            deployment_catalog='',
            target_volume='/tmp/lineage_test_no_physical_fqn',
        )
        writes = self._run_step(wv)
        artifact = json.loads(writes[0][1])
        for entry in artifact['lineage']:
            for o in entry['affected_objects']:
                self.assertNotIn('physical_fqn', o,
                                 f'physical_fqn must be ABSENT (not None) when catalog blank, got {o}')

    def test_artifact_includes_agent_version_and_metadata(self):
        doms, prods, attrs, mvs = _basic_after_state()
        wv = _build_widgets_values(
            operation='new base model',
            vibes='Build network',
            requirements=[{'req_id': 'VREQ-1', 'text': 'Build', 'scope': 'model', 'scope_targets': []}],
            domains=doms, products=prods, attributes=attrs, metric_views=mvs,
            target_volume='/tmp/lineage_test_metadata',
        )
        writes = self._run_step(wv)
        artifact = json.loads(writes[0][1])
        self.assertEqual(artifact['agent_version'], self.ns['__AGENT_VERSION__'])
        self.assertIn('generated_at', artifact)
        self.assertIn('source_vibes_raw', artifact)
        self.assertEqual(artifact['source_vibes_raw'], 'Build network')

    def test_fired_log_line_emitted_on_successful_write(self):
        doms, prods, attrs, mvs = _basic_after_state()
        wv = _build_widgets_values(
            operation='new base model',
            vibes='Build network',
            requirements=[{'req_id': 'VREQ-1', 'text': 'Build', 'scope': 'model', 'scope_targets': []}],
            domains=doms, products=prods, attributes=attrs, metric_views=mvs,
            target_volume='/tmp/lineage_test_fired',
        )
        writes = self._run_step(wv)
        self.assertEqual(len(writes), 1)
        fired = [m for m in wv['logger'].info_lines if '[vibe-lineage-artifact FIRED]' in m]
        self.assertEqual(len(fired), 1, f'expected exactly one FIRED log line, got: {wv["logger"].info_lines}')

    def test_lineage_entry_has_all_required_fields(self):
        doms, prods, attrs, mvs = _basic_after_state()
        wv = _build_widgets_values(
            operation='new base model',
            vibes='Build',
            requirements=[{'req_id': 'VREQ-1', 'text': 'Build network',
                           'scope': 'model', 'scope_targets': ['network']}],
            domains=doms, products=prods, attributes=attrs, metric_views=mvs,
            target_volume='/tmp/lineage_test_required_fields',
        )
        writes = self._run_step(wv)
        artifact = json.loads(writes[0][1])
        for entry in artifact['lineage']:
            for key in ('requirement_id', 'vibe', 'interpretation', 'affected_objects'):
                self.assertIn(key, entry, f'entry missing {key}: {entry}')
            for obj in entry['affected_objects']:
                for key in ('type', 'logical_fqn', 'before', 'after', 'action', 'source'):
                    self.assertIn(key, obj, f'affected_object missing {key}: {obj}')


# --------------------------------------------------------------------------- #
# 7. Pre-patch fail-check (§8.10 anti-tautology gate)                          #
#    Confirms each helper / step exists ONLY in the post-v0.9.3 source.        #
#    If any of these alias strings ever appears in pre-v0.9.3 backup, the      #
#    static-grep test is a tautology and must be re-written behaviorally.      #
# --------------------------------------------------------------------------- #

class TestV93AntiTautologyGate(unittest.TestCase):
    """Per CLAUDE.md \u00a78.10: every behavioral test above does WORK against the helpers.
    Verifying that the helpers DID NOT EXIST pre-patch is the runtime equivalent of the
    `git stash` requirement (we can't actually stash in CI). The .v95pre.bak file is the
    pre-patch snapshot the injection script writes; if it's present we cross-check.
    Skipped when no backup is available (e.g. fresh checkout)."""

    BACKUP = AGENT_NB + '.v95pre.bak'

    def setUp(self):
        if not os.path.exists(self.BACKUP):
            self.skipTest('no v95pre.bak snapshot available — cannot prove pre-patch failure')
        with open(self.BACKUP) as f:
            nb = json.load(f)
        self.pre_src = ''.join(''.join(c.get('source', []))
                                for c in nb['cells'] if c.get('cell_type') == 'code')

    def test_step_function_absent_pre_patch(self):
        self.assertNotIn('def step_generate_vibe_lineage', self.pre_src,
                         'step_generate_vibe_lineage existed pre-v0.9.3 \u2192 §8.10 tautology risk')

    def test_diff_helper_absent_pre_patch(self):
        self.assertNotIn('def _diff_lineage_snapshots', self.pre_src,
                         '_diff_lineage_snapshots existed pre-v0.9.3 \u2192 §8.10 tautology risk')

    def test_attribution_helper_absent_pre_patch(self):
        self.assertNotIn('def _match_change_to_requirement', self.pre_src,
                         '_match_change_to_requirement existed pre-v0.9.3 \u2192 §8.10 tautology risk')

    def test_artifact_alias_absent_pre_patch(self):
        self.assertNotIn('vibe-lineage-artifact', self.pre_src,
                         'alias existed pre-v0.9.3 \u2192 §8.10 tautology risk')


if __name__ == '__main__':
    unittest.main()
