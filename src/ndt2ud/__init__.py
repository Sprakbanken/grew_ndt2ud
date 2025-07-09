#!/usr/bin/env python3
import argparse
import logging
import shutil
import subprocess
from pathlib import Path

import grewpy
from grewpy import GRS, Corpus, CorpusDraft, Request

from ndt2ud import utils
from ndt2ud.morphological_features import convert_morphology
from ndt2ud.parse_conllu import parse_conll_file, write_conll

grewpy.set_config("ud")


def validate_language(value: str) -> str:
    """Validate that language is either 'nb' or 'nn'."""
    if value not in ["nb", "nn"]:
        raise argparse.ArgumentTypeError("Language must be either 'nb' or 'nn'")
    return value


def convert_ndt_to_ud(input_file: str, language: str, output_file: str) -> None:
    """Convert NDT treebank format to UD format."""
    temp_dir = "tmp"
    Path(temp_dir).mkdir(exist_ok=True)

    print("-01- Convert morphology: feats and pos-tags")
    temp_file = f"{temp_dir}/01_convert_morph_output.conllu"
    conllu_data = parse_conll_file(Path(input_file))
    morphdata = convert_morphology(conllu_data)
    write_conll(morphdata, temp_file, drop_comments=False)

    print("-02- Add MISC annotation 'SpaceAfter=No'")
    temp_out = f"{temp_dir}/02_udapy_spaceafter.conllu"
    utils.udapi_fixes(temp_file, temp_out)
    temp_file = temp_out

    print("-03- Convert dependency relations")
    temp_out = f"{temp_dir}/03_grew_transform_deprels.conllu"
    grs_file = "rules/NDT_to_UD.grs"

    corpus = Corpus(temp_file)
    if Path(grs_file).exists():
        print(f"Using Grew rules from {Path(grs_file)}")
    else:
        logging.error(
            f"Grew rules file   {Path(grs_file).absolute()} not found. "
            "Please ensure the rules are available in the specified path."
        )
        return
    grs = GRS(grs_file)

    corpus.apply(grs, strat=f"main_{language}")
    conll = corpus.to_conll()
    Path(temp_out).write_text(conll)  # type: ignore
    temp_file = temp_out

    print("-04- Fix punctuation with udapy")
    temp_out = f"{temp_dir}/04_udapy_fixpunct.conllu"
    utils.udapi_fixes(temp_file, temp_out)
    temp_file = temp_out

    print("-05- Postprocess with Grew to fix errors introduced by udapy")
    temp_out = f"{temp_dir}/05_grew_transform_postprocess.conllu"
    corpus = Corpus(temp_file)
    grs = GRS(grs_file)
    corpus.apply(grs, strat="postprocess")
    conll = corpus.to_conll()
    Path(temp_out).write_text(conll)  # type: ignore
    temp_file = temp_out

    print("-06- Replace invalid newpar lines ---")
    temp_out = f"{temp_dir}/06_replace_newpar.conllu"
    with open(temp_file, "r") as infile, open(temp_out, "w") as outfile:
        for line in infile:
            outfile.write(line.replace("#  = # newpar", "# newpar"))

    shutil.copy(temp_out, output_file)
    print(f"Done! UD treebank written to {output_file}")


def validate(
    treebank_file: Path,
    report_file: Path,
    path_to_script: str = "tools/validate.py",
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

    workspace_root = Path(__file__).parent.parent.parent

    parser = argparse.ArgumentParser(
        prog="ndt2ud", description="Convert NDT treebank to UD format"
    )
    parser.add_argument(
        "-l",
        "--language",
        required=True,
        type=validate_language,
        help="Language (must be nb or nn)",
    )
    parser.add_argument(
        "-i", "--input", required=True, type=Path, help="Input NDT file or folder"
    )
    parser.add_argument(
        "-o",
        "--output",
        default=workspace_root / "data" / "UD_output" / "UD_output.conllu",
        type=Path,
        help="Output UD file (default: UD_output.conllu)",
    )
    parser.add_argument(
        "-r",
        "--report",
        default=workspace_root / "validation-report.txt",
        type=Path,
        help="Validation report file (default: validation-report.txt)",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(levelname)s | %(asctime)s | %(name)s | %(message)s",
        filename="conversion.log",
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

    if args.input.is_dir():
        # If input is a directory, process all .conllu files in it
        input_files = list(args.input.glob("*.conll"))
        output_dir = args.output.parent
        if not output_dir.exists():
            output_dir.mkdir(parents=True)
        for file in input_files:
            convert_ndt_to_ud(file, args.language, output_dir / file.name)
            logging.info("Converted %s to %s", file, output_dir / file.name)
        if not input_files:
            logging.error("No .conllu files found in the specified directory.")
            return
        # validate
        for file in output_dir.glob("*.conllu"):
            validate(file, args.report)
            logging.info(
                "Validation report written to %s for file %s",
                args.report,
                file,
            )
    else:
        # If input is a file, ensure it exists
        if not args.input.exists():
            logging.error(f"Input file {args.input} does not exist.")
            return
        input_files = [args.input]

    convert_ndt_to_ud(args.input, args.language, args.output)
    validate(args.output, args.report)
