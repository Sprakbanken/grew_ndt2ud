# %%
from udapi.block.ud.setspaceafterfromtext import SetSpaceAfterFromText
from udapi.block.ud.fixpunct import FixPunct
from udapi.core.document import Document


def process_document(input_file, output_file, processor):
    # Load the input file into a Document object
    doc = Document()
    doc.load_conllu(input_file)

    # Apply the processor
    processor.process_document(doc)

    # Write the modified document to an output file
    doc.store_conllu(output_file)

# %%
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--inputfile")
    parser.add_argument("-o", "--outputfile")
    parser.add_argument(
        "-p",
        "--processor",
        choices=["space", "punct"],
        required=True,
        help='Use "space" to add SpaceAfter annotations in the MISC field, or "punct" to fix punctuation relations',
    )
    args = parser.parse_args()

    if args.processor == "space":
        processor = SetSpaceAfterFromText()
    elif args.processor == "punct":
        processor = FixPunct()

    process_document(args.inputfile, args.outputfile, processor)
