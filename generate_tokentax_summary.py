import sys
from pathlib import Path
import open_crypto_tax


# This script generates a valid input file from an unchecked one
def main(_input_valid: Path, _output_file: Path, _output_balances_file: Path):
    # new Validator object
    processor = open_crypto_tax.Processor(_input_valid, True)
    # process the loaded inputs
    processor.process_tokentax()
    processor.generate_tokentax_summary(_output_file)
    processor.generate_balances_from_tokentax(_output_balances_file)
    print("[INFO] generate tokentax summary complete (: enjoy!")


argvs = sys.argv
input_valid = Path(argvs[1])
output_file = Path(argvs[2]) if len(argvs) == 3 else Path("out/summary_tokentax.csv")
output_balances_file = Path("out/summary_tokentax_balances.csv")
main(input_valid, output_file, output_balances_file)
