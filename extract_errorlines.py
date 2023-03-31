from pathlib import Path
import pandas as pd
import re
import sys


if __name__ == "__main__":
    import argparse
    from argparse import ArgumentParser

    argparser = ArgumentParser()
    argparser.add_argument("-e", "--errortype_name", type=str, required=False)
    argparser.add_argument("-f", "--filename", type=str, default="validation-report_ndt2ud.txt", required=False)
    args = argparser.parse_args()
    fpath = args.filename
    etype = args.errortype_name

    rows = Path(fpath).read_text(encoding="utf-8").split("\n")

    error_info_regx = re.compile(r"^\[Line (\d+)(?: Sent )?(\d+)?(?: Node )?(\d+)?\]\: \[(L.*)\] (.*)(\[[0-9]*, [0-9]*\])?(.*)?$", flags=re.DOTALL)
    errors = []
    print("Report summary:")
    for row in rows:
        m = error_info_regx.fullmatch(row)
        if m is None:
            print(row)
            continue
        errors.append(m.groups())

    df = pd.DataFrame(errors, columns=["line", "sent","node", "errortype", "message", "relevant_nodes", "message2"])

    print("Different types of errors:")
    type_counts = df.errortype.value_counts()
    print(type_counts)

    if etype is not None:
        df[df.errortype.str.contains(etype)].to_csv(f"error_{etype}.csv", index=False)
