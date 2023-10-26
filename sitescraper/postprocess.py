import json, logging

with open("trusts.json") as trusts:
    raw = json.load(trusts)

SITE_LIMIT = 10

out = {}
errored = []

for raw_item in raw:
    if "status" in raw_item:
        errored.append({"domain": raw_item["domain"], "path": raw_item["path"], "reason": raw_item["status"]})
    elif "error" in raw_item:
        errored.append({"domain": raw_item["domain"], "path": raw_item["path"], "reason": raw_item["error"]})
    else:
        item = {raw_item["path"]: raw_item["body"]}
        out_item = out.get(raw_item["domain"])
        if out_item is None:
            out[raw_item["domain"]] = item
        else:
            out_item.update(item)

for k, v in out.items():
    if len(v) < SITE_LIMIT:
        logging.warning(f"Missing domains on url {k} (expected {SITE_LIMIT}, got {len(v)})")

with open("trusts_consolidated.json", "w") as outFile:
    json.dump(out, outFile, indent=4)

with open("trusts_errored.json", "w") as outFile:
    json.dump(errored, outFile, indent=4)