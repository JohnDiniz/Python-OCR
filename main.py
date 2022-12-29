import pytesseract
from pytesseract import Output
from PIL import Image
import pandas as pd
import sys
import subprocess
import os


def main():

    os.system("maim -u -f png -s -b 2 /var/tmp/ocr.png")

    ImgSrc = "/var/tmp/ocr.png"

    # ImgSrc = sys.argv[1] # command line

    custom_config = r"-c preserve_interword_spaces=1 --oem 3 --psm 1 -l eng"

    d = pytesseract.image_to_data(
        Image.open(ImgSrc), config=custom_config, output_type=Output.DICT
    )
    df = pd.DataFrame(d)

    def copy_to_clipboard(text):
        process = subprocess.Popen(["xclip", "-selection", "c"], stdin=subprocess.PIPE)
        process.communicate(input=text.encode())

    text = ""

    # clean up blanks
    df1 = df[(df.conf != "-1") & (df.text != " ") & (df.text != "")]
    # sort blocks vertically
    sorted_blocks = df1.groupby("block_num").first().sort_values("top").index.tolist()
    for block in sorted_blocks:
        curr = df1[df1["block_num"] == block]
        sel = curr[curr.text.str.len() > 3]
        char_w = (sel.width / sel.text.str.len()).mean()
        prev_par, prev_line, prev_left = 0, 0, 0
        for ix, ln in curr.iterrows():
            # add new line when necessary
            if prev_par != ln["par_num"]:
                text += "\n"
                prev_par = ln["par_num"]
                prev_line = ln["line_num"]
                prev_left = 0
            elif prev_line != ln["line_num"]:
                text += "\n"
                prev_line = ln["line_num"]
                prev_left = 0

            added = 0  # num of spaces that should be added
            if ln["left"] / char_w > prev_left + 1:
                added = int((ln["left"]) / char_w) - prev_left
                text += " " * added
            text += ln["text"] + " "
            prev_left += len(ln["text"]) + added + 1
        text += "\n"

    print(text)
    copy_to_clipboard(text)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
