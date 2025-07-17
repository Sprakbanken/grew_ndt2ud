#!/usr/bin/env python3
import argparse
import logging
import shutil
import subprocess
from pathlib import Path

import grewpy
from grewpy import GRS, Corpus, CorpusDraft

from ndt2ud import utils
from ndt2ud.morphological_features import convert_morphology
from ndt2ud.parse_conllu import parse_conll_file, write_conll

grewpy.set_config("ud")


def validate_language(value: str) -> str:
    """Validate that language is either 'nb' or 'nn'."""
    if value not in ["nb", "nn"]:
        raise argparse.ArgumentTypeError(
            "Language must be either 'nb' for bokmål or 'nn' for nynorsk"
        )
    return value


def convert_ndt_to_ud(
    input_file: str, language: str, output_file: str, grs_path: str
) -> None:
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
    draft = CorpusDraft(temp_file)
    draft.map(utils.set_spaceafter_from_text, in_place=True)
    conll = Corpus(draft).to_conll()
    Path(temp_out).write_text(conll)  # type: ignore
    temp_file = temp_out

    print("-03- Convert dependency relations")
    temp_out = f"{temp_dir}/03_grew_transform_deprels.conllu"

    corpus = Corpus(temp_file)
    if Path(grs_path).exists():
        print(f"Using Grew rules from {Path(grs_path)}")
    else:
        logging.error(
            f"Grew rules file   {Path(grs_path).absolute()} not found. "
            "Please ensure the rules are available in the specified path."
        )
        return
    grs = GRS(str(grs_path))

    corpus = grs.apply(corpus, strat=f"main_{language}")
    conll = corpus.to_conll()  # type: ignore
    Path(temp_out).write_text(conll)  # type: ignore
    temp_file = temp_out

    print("-04- Fix punctuation with udapy")
    temp_out = f"{temp_dir}/04_udapy_fixpunct.conllu"
    utils.udapi_fixes(temp_file, temp_out)
    temp_file = temp_out

    print("-05- Postprocess with Grew to fix errors introduced by udapy")
    temp_out = f"{temp_dir}/05_grew_transform_postprocess.conllu"
    corpus = Corpus(temp_file)
    grs = GRS(str(grs_path))
    corpus = grs.apply(corpus, strat="postprocess")
    conll = corpus.to_conll()  # type: ignore
    Path(temp_out).write_text(conll)  # type: ignore
    temp_file = temp_out

    print("-06- Replace invalid newpar lines")
    temp_out = f"{temp_dir}/06_replace_newpar.conllu"
    with open(temp_file, "r") as infile, open(temp_out, "w") as outfile:
        for line in infile:
            outfile.write(line.replace("#  = # newpar", "# newpar"))

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(temp_out, output_file)
    print(f"Done! UD treebank written to {output_file}")


def validate(
    treebank_file: Path,
    report_file: Path,
    path_to_script: str = "tools/validate.py",
    overwrite: bool = True,
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
    write_mode = "w" if overwrite else "a"
    with open(report_file, write_mode) as f:
        f.write(validation_process.stderr)


def main():
    import argparse

    workspace_root = Path(__file__).parent.parent.parent
    src_root = Path(__file__).parent.parent

    parser = argparse.ArgumentParser(
        prog="ndt2ud",
        description=(
            "Convert Norwegian Dependency Treebank (NDT) annotations to "
            "Universal Dependencies (UD) annotations in CONLL-U-formatted files."
        ),
    )
    # subparsers = parser.add_subparsers(title="Subcommands", dest='subcommand')
    parser_convert = parser.add_argument_group("convert")
    parser_convert.add_argument(
        "-l",
        "--language",
        required=True,
        type=validate_language,
        help="Language (must be nb or nn)",
    )
    parser_convert.add_argument(
        "-i", "--input", required=True, type=Path, help="Input NDT file or folder"
    )
    parser_convert.add_argument(
        "-o",
        "--output",
        default=workspace_root / "data" / "UD_output" / "UD.conllu",
        type=Path,
        help="Output UD file (default: UD_output.conllu)",
    )
    parser_convert.add_argument(
        "-g",
        "--grew_rules",
        default=src_root / "rules" / "NDT_to_UD.grs",
        type=Path,
        help="File path to the grew GRS file with treebank conversion rules.",
    )

    parser_validate = parser.add_argument_group(
        "validate", description="Run the UD tools validation script on conllu-files"
    )

    parser_validate.add_argument(
        "-r",
        "--report",
        nargs="?",
        const=workspace_root / "validation-report.txt",
        # type=Path,
        help="Validation report file (default: validation-report.txt)",
    )
    parser_validate.add_argument(
        "-val",
        "--validation_script",
        default=workspace_root / "tools" / "validate.py",
        type=Path,
        help="path to the UD tools validation script",
    )
    parser_validate.add_argument(
        "-s",
        "--summarize",
        nargs="?",
        const="validation_error_summary.txt",
        help=(
            "Aggregate the error types in the validation report"
            " and store the summary in a new file."
        ),
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
    Grew rules: %s
    """,
        args.input,
        args.output,
        args.language,
        args.grew_rules,
    )
    print(args)

    if args.input.is_dir():
        # If input is a directory, process all .conllu files in it
        input_files = list(args.input.glob("*.conll*"))
        if not input_files:
            logging.error(
                "No .conll or .conllu files found in the specified directory."
            )
            return
    else:
        # If input is a file, ensure it exists
        if not args.input.exists():
            logging.error(f"Input file {args.input} does not exist.")
            return
        input_files = [args.input]

    output_dir = args.output.parent
    if not output_dir.exists():
        output_dir.mkdir(parents=True)

    for file in input_files:
        output_file = output_dir / (file.stem + "_output.conllu")
        convert_ndt_to_ud(file, args.language, output_file, args.grew_rules)
        logging.info("Converted %s to %s", file, output_dir / file.name)

    if args.report:
        for file in output_dir.glob("*.conll*"):
            validate(file, args.report, args.validation_script, overwrite=False)
            logging.info(
                "Validation report written to %s for file %s",
                args.report,
                file,
            )
        if args.summarize:
            utils.report_errors(args.report)
