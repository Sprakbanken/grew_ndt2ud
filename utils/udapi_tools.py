# %%
from udapi.block.ud.setspaceafterfromtext import SetSpaceAfterFromText
from udapi.core.document import Document

def set_space_after_from_text(input_file, output_file):
    # Load the input file into a Document object
    doc = Document()
    doc.load_conllu(input_file)

    # Apply the SetSpaceAfterFromText processor
    processor = SetSpaceAfterFromText()
    processor.process_document(doc)

    # Write the modified document to an output file
    doc.store_conllu(output_file)
# %%

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--inputfile")
    parser.add_argument("-o", "--outputfile")
    args = parser.parse_args()

    set_space_after_from_text(args.inputfile, args.outputfile)
