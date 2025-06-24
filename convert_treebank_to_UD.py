#!/usr/bin/env python3
# filepath: /home/ingeridd/prosjekter/trebank/grew_ndt2ud/convert_ndt2ud.py
import argparse
import os
import subprocess
import shutil


def validate_language(value):
    """Validate that language is either 'nb' or 'nn'."""
    if value not in ["nb", "nn"]:
        raise argparse.ArgumentTypeError("Language must be either 'nb' or 'nn'")
    return value


def run_command(cmd, shell=False):
    """Run a shell command and return the exit code."""
    print(f"Running: {cmd if isinstance(cmd, str) else ' '.join(cmd)}")
    return subprocess.run(cmd, shell=shell, check=True)


def convert_ndt_to_ud(input_file, language, output_file, report_file):
    """Convert NDT treebank format to UD format."""
    # Create temporary directory
    temp_dir = "tmp"
    os.makedirs(temp_dir, exist_ok=True)

    print("--- CONVERT NDT TREEBANK to UD ---")
    print("")
    print("--- Input parameters ---")
    print(f"  Language: {language}")
    print(f"  Input NDT file: {input_file}")
    print(f"  Output UD file: {output_file}")
    print(f"  Validation report: {report_file}")
    print("")

    # START CONVERSION
    print("--- Convert morphology: feats and pos-tags ---")
    temp_file = f"{temp_dir}/01_convert_morph_output.conllu"
    run_command(["python", "utils/convert_morph.py", "-f", input_file, "-o", temp_file])

    # Add MISC annotation 'SpaceAfter=No'
    temp_out = f"{temp_dir}/02_udapy_spaceafter.conllu"
    run_command(
        [
            "python",
            "utils/udapi_tools.py",
            "-i",
            temp_file,
            "-o",
            temp_out,
            "-p",
            "space",
        ]
    )
    temp_file = temp_out

    print("--- Convert dependency relations ---")
    temp_out = f"{temp_dir}/03_grew_transform_deprels.conllu"
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
    temp_out = f"{temp_dir}/04_udapy_fixpunct.conllu"
    run_command(
        [
            "python",
            "utils/udapi_tools.py",
            "-i",
            temp_file,
            "-o",
            temp_out,
            "-p",
            "punct",
        ]
    )
    temp_file = temp_out

    print("--- Fix errors introduced by udapy ---")
    temp_out = f"{temp_dir}/05_grew_transform_postprocess.conllu"
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

    # Remove comment line with column names and replace invalid newpar lines
    temp_out = f"{temp_dir}/06_replace_newpar.conllu"
    with open(temp_file, "r") as infile, open(temp_out, "w") as outfile:
        for line in infile:
            outfile.write(line.replace("#  = # newpar", "# newpar"))
    temp_file = temp_out
    shutil.copy(temp_file, output_file)

    # EVALUATION
    print("--- Validate treebank with UD validation script ---")
    with open(report_file, "w") as report:
        validation_process = subprocess.run(
            [
                "python",
                "tools/validate.py",
                "--max-err",
                "0",
                "--lang",
                "no",
                output_file,
            ],
            capture_output=True,
            text=True,
        )
        report.write(validation_process.stdout)
        report.write(validation_process.stderr)
        print(validation_process.stdout)
        print(validation_process.stderr)

    run_command(["python", "utils/extract_errorlines.py", "-f", report_file])

    print("--- Conversion finished ---")


def main():
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


if __name__ == "__main__":
    main()
