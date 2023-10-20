import json

with open("trusts.json") as trusts:
    raw = json.load(trusts)

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

with open("trusts_consolidated.json", "w") as outFile:
    json.dump(out, outFile, indent=4)

with open("trusts_errored.json", "w") as outFile:
    json.dump(errored, outFile, indent=4)