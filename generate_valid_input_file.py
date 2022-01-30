import sys
from pathlib import Path
import open_crypto_tax


# This script generates a valid input file from an unchecked one
def main(_unchecked_input: Path, _sheet_name: str = "input"):
    # new Validator object
    validator = open_crypto_tax.Validator(_unchecked_input, _sheet_name)
    # process the loaded inputs
    validator.process()
    print("[INFO] script complete :)")


argvs = sys.argv
unchecked_input = Path(argvs[1])
if len(argvs) == 3:
    sheet_name = argvs[2] if len(argvs) == 3 else None
main(unchecked_input, sheet_name)
