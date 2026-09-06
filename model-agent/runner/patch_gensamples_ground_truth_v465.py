import json, sys

NB = "agent/dbx_vibe_modelling_agent.ipynb"
nb = json.load(open(NB))

def cell(i):
    return nb["cells"][i]["source"]

def setcell(i, s):
    nb["cells"][i]["source"] = s

# ---- 1) version bump 4.6.4 -> 4.6.5 (cell 1) ----
c1 = cell(1)
assert c1.startswith('__AGENT_VERSION__ = "4.6.4"'), "unexpected version head"
c1 = c1.replace('__AGENT_VERSION__ = "4.6.4"', '__AGENT_VERSION__ = "4.6.5"', 1)
setcell(1, c1)

# ---- 2) shared helper in cell 25 (before _strip_baked_catalog_from_model) ----
HELPER = '''def _resolve_existing_physical_table(spark, catalogs, schemas, table_name, logger=None):
    """Return (fqn, catalog, schema) for the FIRST physically-existing table matching
    table_name, trying explicit (catalog, schema) DESCRIBE candidates first, then an
    information_schema.tables fallback per catalog that locates the ACTUAL schema hosting
    the table regardless of prefix/suffix/subdomain/casing drift between the stored
    database_name and what install physically created. Returns (None, None, None) when the
    table does not physically exist in any candidate catalog. Serverless-safe (pure
    DESCRIBE / SELECT; no cache/persist/sparkcontext). alias=gensamples-physical-ground-truth"""
    _cats, _seen = [], set()
    for _c in (catalogs or []):
        _c = (_c or "").strip()
        if _c and _c not in _seen:
            _seen.add(_c); _cats.append(_c)
    _schs, _seen_s = [], set()
    for _s in (schemas or []):
        _s = (_s or "").strip()
        if _s and _s not in _seen_s:
            _seen_s.add(_s); _schs.append(_s)
    _tbl = (table_name or "").strip()
    if not _tbl or not _cats:
        return (None, None, None)
    for _c in _cats:
        for _s in _schs:
            _fqn = f"`{_c}`.`{_s}`.`{_tbl}`"
            try:
                spark.sql(f"DESCRIBE TABLE {_fqn}")
                return (_fqn, _c, _s)
            except Exception:
                continue
    _tbl_esc = _tbl.replace("'", "''")
    for _c in _cats:
        try:
            _rows = spark.sql(
                f"SELECT table_schema FROM `{_c}`.information_schema.tables "
                f"WHERE lower(table_name) = lower('{_tbl_esc}')"
            ).collect()
            _found = [r[0] for r in _rows if r and r[0]]
            if _found:
                _pick = next((s for s in _found if s in _schs), _found[0])
                if logger:
                    logger.info(f"[gensamples-physical-ground-truth FIRED v4.6.5] '{_tbl}' located via information_schema -> {_c}.{_pick} (resolver candidate schemas={_schs}) alias=gensamples-physical-ground-truth")
                return (f"`{_c}`.`{_pick}`.`{_tbl}`", _c, _pick)
        except Exception:
            continue
    return (None, None, None)

'''
c25 = cell(25)
anchor = "\ndef _strip_baked_catalog_from_model(data_model, logger=None):"
assert c25.count(anchor) == 1, f"cell25 anchor count={c25.count(anchor)}"
c25 = c25.replace(anchor, "\n" + HELPER + "\ndef _strip_baked_catalog_from_model(data_model, logger=None):", 1)
setcell(25, c25)

# ---- 3) write path (cell 164): replace candidate loop ----
c164 = cell(164)
OLD_W = '''            _sg_sch_prefix = (config.get('SCHEMA_PREFIX', '') or '').strip()
            _sg_tbl = p_dict['table_name']
            _sg_cand_schemas = []
            if _sg_sch_prefix and not _resolved_db.startswith(_sg_sch_prefix):
                _sg_cand_schemas.append(f"{_sg_sch_prefix}{_resolved_db}")
            _sg_cand_schemas.append(_resolved_db)
            db_name = _resolved_db
            target_table = f"`{_sample_effective_catalog}`.`{db_name}`.`{_sg_tbl}`"
            for _sg_cs in _sg_cand_schemas:
                _sg_cand_tt = f"`{_sample_effective_catalog}`.`{_sg_cs}`.`{_sg_tbl}`"
                try:
                    spark.sql(f"DESCRIBE TABLE {_sg_cand_tt}")
                    db_name = _sg_cs
                    target_table = _sg_cand_tt
                    if _sg_cs != _resolved_db:
                        logger.info(f"[v421-gensamples-schema-prefix FIRED] '{product_name}' -> physical schema '{_sg_cs}' (schema_prefix='{_sg_sch_prefix}'); logical resolve was '{_resolved_db}' alias=v421-gensamples-schema-prefix")
                    break
                except Exception:
                    continue'''
NEW_W = '''            _sg_sch_prefix = (config.get('SCHEMA_PREFIX', '') or '').strip()
            _sg_tbl = p_dict['table_name']
            _sg_cand_schemas = []
            if _sg_sch_prefix and not _resolved_db.startswith(_sg_sch_prefix):
                _sg_cand_schemas.append(f"{_sg_sch_prefix}{_resolved_db}")
            _sg_cand_schemas.append(_resolved_db)
            # v4.6.5 alias=gensamples-physical-ground-truth — resolve the ACTUAL physical
            # target (catalog.schema) from the live catalog: DESCRIBE candidates first, then an
            # information_schema.tables fallback that finds WHERE the table really lives
            # regardless of prefix/suffix/subdomain/casing drift between the stored
            # database_name and what install physically created. ROOT CAUSE of tester 05/08
            # 0-row landings: the single resolver-derived schema missed the physical schema,
            # DESCRIBE failed for every product, all inserts were skipped, and the op reported
            # 0 rows written. Grounding in information_schema cannot false-target (it reads the
            # real catalog) and is Serverless-safe (pure SELECT).
            _sg_cand_cats = []
            for _sg_cc in (_sample_effective_catalog, _sample_shared_resolver.resolve_catalog(_domain_dict_proxy)):
                if _sg_cc and _sg_cc not in _sg_cand_cats:
                    _sg_cand_cats.append(_sg_cc)
            _sg_fqn, _sg_fcat, _sg_fsch = _resolve_existing_physical_table(spark, _sg_cand_cats, _sg_cand_schemas, _sg_tbl, logger=logger)
            if _sg_fqn:
                target_table = _sg_fqn
                db_name = _sg_fsch
                _sample_effective_catalog = _sg_fcat
            else:
                db_name = _resolved_db
                target_table = f"`{_sample_effective_catalog}`.`{db_name}`.`{_sg_tbl}`"
                logger.error(f"[gensamples-physical-ground-truth] '{product_name}' - NO physical table '{_sg_tbl}' found in catalogs={_sg_cand_cats} schemas={_sg_cand_schemas}; insert will be skipped (0 rows) alias=gensamples-physical-ground-truth")'''
assert c164.count(OLD_W) == 1, f"cell164 write-block count={c164.count(OLD_W)}"
c164 = c164.replace(OLD_W, NEW_W, 1)
setcell(164, c164)

# ---- 4) landing check (cell 206) ----
c206 = cell(206)
OLD_L = '''                _lcands = []
                if _land_sp and not _lschema.startswith(_land_sp):
                    _lcands.append(f"{_land_sp}{_lschema}")
                _lcands.append(_lschema)
                _lcnt = 0
                _lfound = False
                for _lcs in _lcands:
                    try:
                        _lr = execute_sql(spark, f"SELECT COUNT(*) AS c FROM `{_lcat}`.`{_lcs}`.`{_ltbl}`", None)
                        if _lr:
                            _lcnt = int(_lr[0].asDict().get('c', 0))
                            _lfound = True
                            break
                    except Exception:
                        continue
                _land_checked += 1
                _land_total += _lcnt
                if _lcnt == 0:
                    _land_empty.append(f"{_lcat}.{_lcands[0]}.{_ltbl}" + ("" if _lfound else " (table not found)"))
            print(f"[gensamples-landing-hardfail FIRED v4.6.4] checked={_land_checked} table(s), total_rows={_land_total}, empty={len(_land_empty)}")'''
NEW_L = '''                _lcands = []
                if _land_sp and not _lschema.startswith(_land_sp):
                    _lcands.append(f"{_land_sp}{_lschema}")
                _lcands.append(_lschema)
                # v4.6.5 alias=gensamples-physical-ground-truth — count rows at the ACTUAL
                # physical location resolved from the live catalog (DESCRIBE candidates then
                # information_schema fallback), the SAME resolver the writer now uses, so the
                # landing verdict reads the real after-state and cannot false-fail on a
                # schema-name-shape mismatch between the stored database_name and the physical
                # schema install created.
                _lcand_cats = []
                for _lcc in (_lcat, _sample_gen_resolver.resolve_catalog(_ldobj)):
                    if _lcc and _lcc not in _lcand_cats:
                        _lcand_cats.append(_lcc)
                _lfqn, _lfcat, _lfsch = _resolve_existing_physical_table(spark, _lcand_cats, _lcands, _ltbl, logger=logger)
                _lcnt = 0
                _lfound = bool(_lfqn)
                if _lfqn:
                    try:
                        _lr = execute_sql(spark, f"SELECT COUNT(*) AS c FROM {_lfqn}", None)
                        if _lr:
                            _lcnt = int(_lr[0].asDict().get('c', 0))
                    except Exception:
                        _lcnt = 0
                _land_checked += 1
                _land_total += _lcnt
                if _lcnt == 0:
                    _land_empty.append((_lfqn or f"{_lcat}.{_lcands[0]}.{_ltbl}") + ("" if _lfound else " (table not found)"))
            logger.info(f"[gensamples-landing-hardfail FIRED v4.6.5] checked={_land_checked} table(s), total_rows={_land_total}, empty={len(_land_empty)} empty_targets={_land_empty[:10]} alias=gensamples-landing-hardfail")
            print(f"[gensamples-landing-hardfail FIRED v4.6.5] checked={_land_checked} table(s), total_rows={_land_total}, empty={len(_land_empty)}")'''
assert c206.count(OLD_L) == 1, f"cell206 landing-block count={c206.count(OLD_L)}"
c206 = c206.replace(OLD_L, NEW_L, 1)

# add logger.error before the raise
OLD_R = '''            if _land_checked > 0 and _land_total == 0:
                raise ValueError('''
NEW_R = '''            if _land_checked > 0 and _land_total == 0:
                logger.error(f"[gensamples-landing-hardfail] ZERO rows across {_land_checked} table(s); empty_targets={_land_empty[:10]} alias=gensamples-landing-hardfail")
                raise ValueError('''
assert c206.count(OLD_R) == 1, f"cell206 raise-block count={c206.count(OLD_R)}"
c206 = c206.replace(OLD_R, NEW_R, 1)
setcell(206, c206)

with open(NB, "w") as f:
    json.dump(nb, f, indent=1, ensure_ascii=True)

print("PATCH OK: version->4.6.5, helper added, write+landing rewired to information_schema ground truth")
