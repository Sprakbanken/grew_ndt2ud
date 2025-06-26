#!/usr/bin/env python3
import argparse
import logging
import shutil
import subprocess
from pathlib import Path
from subprocess import CompletedProcess

from grew_ndt2ud.morphological_features import convert_morphology
from grew_ndt2ud.parse_conllu import parse_conll_file, write_conll
from grew_ndt2ud.utils import udapi_fixes

logging.basicConfig(level=logging.INFO)


def validate_language(value: str) -> str:
    """Validate that language is either 'nb' or 'nn'."""
    if value not in ["nb", "nn"]:
        raise argparse.ArgumentTypeError("Language must be either 'nb' or 'nn'")
    return value


def run_command(cmd: str | list, shell=False) -> CompletedProcess[bytes]:
    """Run a shell command and return the exit code."""
    logging.info(f"Running: {cmd if isinstance(cmd, str) else ' '.join(cmd)}")
    return subprocess.run(cmd, shell=shell, check=True)


def convert_ndt_to_ud(
    input_file: Path, language, output_file: Path, report_file: Path
) -> None:
    """Convert NDT treebank format to UD format."""
    temp_dir = Path("tmp")
    temp_dir.mkdir(exist_ok=True)

    print("--- CONVERT NDT TREEBANK to UD ---")
    print("")
    print("--- Input parameters ---")
    print(f"  Language: {language}")
    print(f"  Input NDT file: {input_file}")
    print(f"  Output UD file: {output_file}")
    print(f"  Validation report: {report_file}")
    print("")

    print("--- Convert morphology: feats and pos-tags ---")
    temp_file = temp_dir / "01_convert_morph_output.conllu"
    conllu_data = parse_conll_file(input_file)
    morphdata = convert_morphology(conllu_data)
    write_conll(morphdata, temp_file, drop_comments=False)

    # Add MISC annotation 'SpaceAfter=No'
    temp_out = temp_dir / "02_udapy_spaceafter.conllu"
    udapi_fixes(temp_file, temp_out)
    temp_file = temp_out

    print("--- Convert dependency relations ---")
    temp_out = temp_dir / "03_grew_transform_deprels.conllu"

    run_command(
        [
            "grew",
            "transform",
            "-i",
            temp_file,
            "-o",
            temp_out,
            "-grs",
            "rules/NDT_to_UD.grs",
            "-strat",
            f"main_{language}",
            "-safe_commands",
        ]
    )
    temp_file = temp_out

    print("--- Fix punctuation ---")
    temp_out = temp_dir / "04_udapy_fixpunct.conllu"
    udapi_fixes(temp_file, temp_out)
    temp_file = temp_out

    print("--- Fix errors introduced by udapy ---")
    temp_out = temp_dir / "05_grew_transform_postprocess.conllu"

    run_command(
        [
            "grew",
            "transform",
            "-i",
            temp_file,
            "-o",
            temp_out,
            "-grs",
            "rules/NDT_to_UD.grs",
            "-strat",
            "postprocess",
            "-safe_commands",
        ]
    )
    temp_file = temp_out

    # replace invalid newpar lines
    temp_out = temp_dir / "06_replace_newpar.conllu"
    with open(temp_file, "r") as infile, open(temp_out, "w") as outfile:
        for line in infile:
            outfile.write(line.replace("#  = # newpar", "# newpar"))
    shutil.copy(temp_out, output_file)


def convert():
    import argparse

    parser = argparse.ArgumentParser(description="Convert NDT treebank to UD format")
    parser.add_argument("-i", "--input", required=True, help="Input NDT file")
    parser.add_argument(
        "-l",
        "--language",
        required=True,
        type=validate_language,
        help="Language (must be nb or nn)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="UD_output.conllu",
        help="Output UD file (default: UD_output.conllu)",
    )
    parser.add_argument(
        "-r",
        "--report",
        default="validation-report.txt",
        help="Validation report file (default: validation-report.txt)",
    )

    args = parser.parse_args()
    convert_ndt_to_ud(args.input, args.language, args.output, args.report)
