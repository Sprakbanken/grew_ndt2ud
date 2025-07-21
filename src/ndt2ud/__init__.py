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


def convert_ndt_to_ud(
    input_file: str, language: str, output_file: str, grs_path: str
) -> None:
    """Convert NDT treebank format to UD format."""
    temp_dir = "tmp"
    Path(temp_dir).mkdir(exist_ok=True)
    logging.info("START converting NDT treebank to UD")

    logging.info("-01- Convert morphology: feats and pos-tags")
    temp_file = f"{temp_dir}/01_convert_morph_output.conllu"
    conllu_data = parse_conll_file(Path(input_file))
    morphdata = convert_morphology(conllu_data)
    write_conll(morphdata, temp_file, drop_comments=False)

    logging.info("-02- Add MISC annotation 'SpaceAfter=No'")
    temp_out = f"{temp_dir}/02_udapy_spaceafter.conllu"
    draft = CorpusDraft(temp_file)
    draft.map(utils.set_spaceafter_from_text, in_place=True)
    conll = Corpus(draft).to_conll()
    Path(temp_out).write_text(conll)  # type: ignore
    temp_file = temp_out

    logging.info("-03- Convert dependency relations")
    temp_out = f"{temp_dir}/03_grew_transform_deprels.conllu"
    corpus = Corpus(temp_file)
    if Path(grs_path).exists():
        logging.debug(f"Using Grew rules from {Path(grs_path)}")
    else:
        logging.error(
            f"Grew rules file {Path(grs_path).absolute()} not found. "
            "Please ensure the rules are available in the specified path."
        )
        return
    grs = GRS(str(grs_path))

    corpus = grs.apply(corpus, strat=f"main_{language}")
    conll = corpus.to_conll()  # type: ignore
    Path(temp_out).write_text(conll)  # type: ignore
    temp_file = temp_out

    logging.info("-04- Fix punctuation with udapy")
    temp_out = f"{temp_dir}/04_udapy_fixpunct.conllu"
    utils.udapi_fixes(temp_file, temp_out)
    temp_file = temp_out

    logging.info("-05- Fix errors introduced by udapy")
    temp_out = f"{temp_dir}/05_grew_transform_postprocess.conllu"
    corpus = Corpus(temp_file)
    grs = GRS(str(grs_path))
    corpus = grs.apply(corpus, strat="postprocess")
    conll = corpus.to_conll()  # type: ignore
    Path(temp_out).write_text(conll)  # type: ignore
    temp_file = temp_out

    logging.info("-06- Replace invalid newpar lines")
    temp_out = f"{temp_dir}/06_replace_newpar.conllu"
    with open(temp_file, "r") as infile, open(temp_out, "w") as outfile:
        for line in infile:
            outfile.write(line.replace("#  = # newpar", "# newpar"))

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(temp_out, output_file)
    logging.info(f"UD treebank written to {output_file}")


def convert(args):
    """Execute CLI subcommand to convert the NDT treebank to UD."""
    if args.ndt_file.is_dir():
        input_files = list(args.ndt_file.glob("*.conll*"))
        if not input_files:
            logging.error(
                "No .conll or .conllu files found in the specified directory."
            )
            return
    else:
        if not args.ndt_file.exists():
            logging.error(f"Input file {args.ndt_file} does not exist.")
            return
        input_files = [args.ndt_file]

    output_dir = args.output
    generated_files = []
    for file in input_files:
        output_file = output_dir / (file.stem + "_output.conllu")
        generated_files.append(output_file)
        convert_ndt_to_ud(file, args.language, output_file, args.grew_rules)
    if args.validate:
        print("Run the validation on the output.")
        args.ud_path = generated_files
        _validate(args)


def _validate(args):
    """Wrapper for the CLI call."""
    validate(
        ud_path=args.ud_path,
        report_file=args.report_file,
        validation_script=args.validation_script,
        summarize=bool(args.summarize),
    )


def validate(
    ud_path: Path | list[Path],
    report_file: Path,
    validation_script: str = "tools/validate.py",
    summarize: bool = True,
):
    """Run the UD tools/validate.py script on a UD treebank"""
    if not Path(validation_script).exists():
        logging.error(
            "Can't find the path to the validation script. "
            "Clone the UniversalDependencies tools repo:\n\n"
            "\tgit clone https://github.com/UniversalDependencies/tools.git"
        )
    if isinstance(ud_path, list):
        input_files = [str(file.absolute()) for file in ud_path]
    elif isinstance(ud_path, Path) and ud_path.is_dir():
        input_files = [str(file.absolute()) for file in ud_path.glob("*.conll*")]
    elif isinstance(ud_path, Path) and ud_path.is_file():
        input_files = [str(ud_path.absolute())]
    else:
        input_files = [ud_path]

    validation_process = subprocess.run(
        [
            "python",
            validation_script,
            "--max-err",
            "0",  # output all errors
            "--lang",
            "no",
        ]
        + input_files,
        capture_output=True,
        text=True,
    )
    with open(report_file, "w") as f:
        f.write(validation_process.stderr)
    logging.info(
        "Validation report written to %s",
        report_file,
    )
    if summarize:
        utils.report_errors(report_file)


def main():
    import argparse

    src_root = Path(__file__).parent.parent
    workspace_root = src_root.parent

    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        help=(
            "-v will set the logging level to INFO and -vv to DEBUG. "
            "Defaults to only show logging ERROR messages."
        ),
        default=0,
    )
    parser = argparse.ArgumentParser(
        prog="ndt2ud",
        description=(
            "Convert Norwegian Dependency Treebank (NDT) annotations "
            "to Universal Dependencies (UD) annotations "
            "in CONLL-U-formatted files and validate the output."
        ),
    )
    subparsers = parser.add_subparsers()
    # Subcommand options for conversion
    parser_convert = subparsers.add_parser(
        "convert", parents=[parent_parser], description="Convert NDT to UD"
    )
    parser_convert.add_argument(
        "-l",
        "--language",
        required=True,
        choices=["nb", "nn"],
        help="Language (must be nb or nn)",
    )
    parser_convert.add_argument(
        "-i", "--ndt_file", required=True, type=Path, help="Input NDT file or folder"
    )
    parser_convert.add_argument(
        "-o",
        "--output",
        default=workspace_root / "data" / "UD_output",
        type=Path,
        help="Output folder where UD conllu files are written.",
    )
    parser_convert.add_argument(
        "-g",
        "--grew_rules",
        default=src_root / "rules" / "NDT_to_UD.grs",
        type=Path,
        help="Grew GRS file with treebank conversion rules.",
    )
    parser_convert.add_argument(
        "--validate",
        action="store_true",
        help="Run the UD validation script on the output.",
    )
    parser_convert.set_defaults(
        func=convert,
        report_file=workspace_root / "validation-report.txt",
        validation_script=workspace_root / "tools" / "validate.py",
        summarize="validation_summary.txt",
    )

    # Subcommand options for validation
    parser_validate = subparsers.add_parser(
        "validate",
        parents=[parent_parser],
        description="Run the UD tools validation script on conllu-files",
    )
    parser_validate.add_argument(
        "-i",
        "--ud_path",
        type=Path,
        required=True,
        help="Path UD conllu files or folder to validate",
    )
    parser_validate.add_argument(
        "-r",
        "--report_file",
        nargs="?",
        default=workspace_root / "validation-report.txt",
        help="Validation report file",
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
        const="validation_summary.txt",
        help=("Sum up the error types in the validation report."),
    )
    parser_validate.set_defaults(func=_validate)

    args = parser.parse_args()

    log_levels = [logging.ERROR, logging.INFO, logging.DEBUG]

    logging.basicConfig(
        level=log_levels[min(args.verbose, len(log_levels) - 1)],
        format="%(levelname)s | %(asctime)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("ndt2ud.log", mode="w"),
        ],
    )
    logging.info(
        (
            "Parameters: \n"
            + "\n".join(f"\t{name}: {value}" for name, value in args._get_kwargs())
        )
    )

    args.func(args)

    print("Done!")
