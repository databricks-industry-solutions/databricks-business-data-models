"""Meridian Fluid Controls — bronze sample data generator.
Usage: python -m data_generator.generate_bronze
Deterministic (SEED in config). Writes CSVs to data_generator/output/<schema>/<table>.csv.
"""
import sys, shutil
from . import config, masters, validate
from . import gen_sap_sd, gen_salesforce, gen_edi, gen_returns, gen_fieldlink

def main():
    if config.OUTPUT_DIR.exists():
        for sc in config.SCHEMAS:
            p = config.OUTPUT_DIR / sc
            if p.exists(): shutil.rmtree(p)
    print("Building masters..."); m = masters.build()
    print("SAP SD...");        sap = gen_sap_sd.generate(m)
    print("Salesforce...");    gen_salesforce.generate(m, sap["_backbone"])
    print("EDI...");           gen_edi.generate(m, sap["_backbone"])
    print("Returns...");       gen_returns.generate(m, sap["_backbone"], sap["_vbap_full"])
    print("FieldLink...");     gen_fieldlink.generate(m, sap["_backbone"], sap["_vbap_full"])
    print("Validating...")
    fails = validate.run()
    if fails:
        print("VALIDATION FAILED:"); [print(" -",f) for f in fails]; sys.exit(1)
    print("DONE — all schemas generated and validated.")

if __name__ == "__main__":
    main()
