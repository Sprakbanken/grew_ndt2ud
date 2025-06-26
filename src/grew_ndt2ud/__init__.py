#!/usr/bin/env python3
import argparse
import logging
import shutil
import subprocess
from pathlib import Path
from subprocess import CompletedProcess

from grew_ndt2ud import utils
from grew_ndt2ud.morphological_features import convert_morphology
from grew_ndt2ud.parse_conllu import parse_conll_file, write_conll


def validate_language(value: str) -> str:
    """Validate that language is either 'nb' or 'nn'."""
    if value not in ["nb", "nn"]:
        raise argparse.ArgumentTypeError("Language must be either 'nb' or 'nn'")
    return value


def run_command(cmd: str | list, shell=False) -> CompletedProcess[bytes]:
    """Run a shell command and return the exit code."""
    logging.info(f"Running: {cmd if isinstance(cmd, str) else ' '.join(cmd)}")
    return subprocess.run(cmd, shell=shell, check=True)


def convert_ndt_to_ud(input_file: Path, language: str, output_file: Path) -> None:
    """Convert NDT treebank format to UD format."""
    temp_dir = Path("tmp")
    temp_dir.mkdir(exist_ok=True)

    print("-01- Convert morphology: feats and pos-tags")
    temp_file = temp_dir / "01_convert_morph_output.conllu"
    conllu_data = parse_conll_file(input_file)
    morphdata = convert_morphology(conllu_data)
    write_conll(morphdata, temp_file, drop_comments=False)

    print("-02- Add MISC annotation 'SpaceAfter=No'")
    temp_out = temp_dir / "02_udapy_spaceafter.conllu"
    utils.udapi_fixes(str(temp_file), str(temp_out))
    temp_file = temp_out

    print("-03- Convert dependency relations")
    temp_out = temp_dir / "03_grew_transform_deprels.conllu"

    run_command(
        [
            "grew",
            "transform",
            "-i",
            str(temp_file),
            "-o",
            str(temp_out),
            "-grs",
            "rules/NDT_to_UD.grs",
            "-strat",
            f"main_{language}",
            "-safe_commands",
        ]
    )
    temp_file = temp_out

    print("-04- Fix punctuation with udapy")
    temp_out = temp_dir / "04_udapy_fixpunct.conllu"
    utils.udapi_fixes(str(temp_file), str(temp_out))
    temp_file = temp_out

    print("-05- Postprocess with Grew to fix errors introduced by udapy")
    temp_out = temp_dir / "05_grew_transform_postprocess.conllu"

    run_command(
        [
            "grew",
            "transform",
            "-i",
            str(temp_file),
            "-o",
            str(temp_out),
            "-grs",
            "rules/NDT_to_UD.grs",
            "-strat",
            "postprocess",
            "-safe_commands",
        ]
    )
    temp_file = temp_out

    print("-06- Replace invalid newpar lines ---")
    temp_out = temp_dir / "06_replace_newpar.conllu"
    with open(temp_file, "r") as infile, open(temp_out, "w") as outfile:
        for line in infile:
            outfile.write(line.replace("#  = # newpar", "# newpar"))

    shutil.copy(temp_out, output_file)
    print(f"Done! UD treebank written to {output_file}")


def validate(
    treebank_file: Path, report_file: Path, path_to_script: str = "tools/validate.py"
):
    """Run the UD tools/validate.py script on a UD treebank"""
    if not Path(path_to_script).exists():
        logging.error(
            "Can't find the path to the validation script. "
            "Clone the UniversalDependencies tools repo:\n\n"
            "\tgit clone https://github.com/UniversalDependencies/tools.git"
        )
    validation_process = subprocess.run(
        [
            "python",
            path_to_script,
            "--max-err",
            "0",  # output all errors
            "--lang",
            "no",
            treebank_file,
        ],
        capture_output=True,
        text=True,
    )
    report_file.write_text(validation_process.stderr)
    utils.report_errors(report_file)


def convert_and_validate():
    import argparse

    parser = argparse.ArgumentParser(description="Convert NDT treebank to UD format")
    parser.add_argument(
        "-i", "--input", required=True, type=Path, help="Input NDT file"
    )
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
        type=Path,
        help="Output UD file (default: UD_output.conllu)",
    )
    parser.add_argument(
        "-r",
        "--report",
        default="validation-report.txt",
        type=Path,
        help="Validation report file (default: validation-report.txt)",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.ERROR,
        format="%(levelname)s | %(asctime)s | %(name)s | %(message)s",
        filename="log.txt",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.info(
        """START converting NDT treebank to UD
    Input NDT file: %s
    Output UD file: %s
    Language: %s
    Validation report: %s
    """,
        args.input,
        args.output,
        args.language,
        args.report,
    )

    # convert_ndt_to_ud(args.input, args.language, args.output)
    validate(args.output, args.report)
