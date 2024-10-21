from dataclasses import dataclass
import os
from typing import List
import argparse
import numpy as np
from PIL import Image
from pathlib import Path
from coloraide import Color

@dataclass
class Point:
    r: float
    g: float
    b: float
    a: float
    pos: float

START_COLOR = Point(0, 0, 0, 0, 0)
END_COLOR = Point(255, 255, 255, 1, 1)


def find_closest(colors: List[Point], pos):
    left = None
    right = None

    for idx, color in enumerate(colors):
        c_pos = color.pos
        dif = c_pos - pos

        if dif >= 0:
            if idx == 0:
                left = color
                right = color
            else:
                left = colors[idx - 1]
                right = color
            break
    
    # All colors befire target pos, get last one
    if left == None:
        left = colors[-1]
    if right == None:
        right = colors[-1]

    return (left, right)



def comp_lut(colors: List[Point], lines = 16):
    colors.insert(0, START_COLOR)
    colors.append(END_COLOR)
    colors.sort(key = lambda p: p.pos)
    output = []

    for line in range(lines):
        pos = line / (lines - 1)
        left, right = find_closest(colors, pos)

        interpolate_factor = 0.5
        if left.pos != right.pos:
            interpolate_factor = (pos - left.pos) / (right.pos - left.pos)

        left_c = Color("srgb", [left.r, left.g, left.b], left.a)
        right_c = Color("srgb", [right.r, right.g, right.b], right.a)
        col = Color.interpolate((left_c, right_c), out_space="srgb")(interpolate_factor)
        
        interp_col = np.clip(np.array((col.get("red"), col.get("green"), col.get("blue"))) / 255, 0, 1).tolist()

        r = left.r + (right.r - left.r) * interpolate_factor
        g = left.g + (right.g - left.g) * interpolate_factor
        b = left.b + (right.b - left.b) * interpolate_factor
        a = left.a + (right.a - left.a) * interpolate_factor

        output.append(interp_col + [col.get("alpha")])

    return output



if __name__ == "__main__":
    parser = argparse.ArgumentParser("Generate volren compatible transferfunction with desired spread. Colors are 0..255, alpha 0..1. Implicitly starts with (0, 0, 0, 0) and ends with (255, 255, 255, 1).")
    parser.add_argument("-i", "--input", help="Color as list of 'pos r g b a', each color in quotes, in range [0..1] ", nargs="+", type=str)
    parser.add_argument("-f", "--infile", help="Load colors from this file instead of command input", type=str)
    parser.add_argument("-o", "--outfile", help="File to store lut in. Defaults to lut.txt", type=str, default="lut.txt")
    parser.add_argument("-l", "--lines", help="spread out to this many lines.", type=int, default=2048)
    parser.add_argument("-v", "--visualize", help="Show image of transfer func", action='store_true')
    args = parser.parse_args()

    colors = []

    if args.infile:
        contents = Path(args.infile).read_text().splitlines()
        for color in contents:
            params = color.split(",")
            p = Point(pos=float(params[0]), r=float(params[1]), g=float(params[2]), b=float(params[3]), a=float(params[4]))
            colors.append(p)
    if args.input:
        for input in args.input:
            params = input.split(" ")
            p = Point(pos=float(params[0]), r=float(params[1]), g=float(params[2]), b=float(params[3]), a=float(params[4]))
            colors.append(p)
        
    out = comp_lut(colors.copy(), args.lines)
    os.makedirs(os.path.dirname(args.outfile), exist_ok=True)
    with open(args.outfile, "w") as outfile:
        outlines = [f"{x[0]:.4f}, {x[1]:.4f}, {x[2]:.4f}, {x[3]:.4f}\n" for x in out]
        outfile.writelines(outlines)


    if args.visualize:
        data = np.array(comp_lut(colors.copy(), 1024))
        data_img = np.tile(data, (64, 1, 1))
        data_img = np.clip(data_img * 255, 0, 255).astype(dtype=np.uint8)

        img = Image.fromarray(data_img, mode="RGBA")
        img.show()