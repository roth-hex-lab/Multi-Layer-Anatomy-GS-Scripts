import argparse
import subprocess
import sys
import tempfile
import psutil 
from concurrent.futures import ProcessPoolExecutor
from itertools import repeat
from pathlib import Path


def calc_compression(filetype):
    if "png" in filetype:
        return "-define png:compression-level=1 "
    elif "jpg" in filetype or "jpeg" in filetype:
        return "-quality 95 "
    else:
        return " "


def denoise(idx, img, temppath, outpath):
    try:
        tempfile = temppath.joinpath(img.stem + ".pfm")

        # Try to convert to pfm. Only format supported by plain oidnDenoise. Must be little endian
        conv_cmd = f"convert {img.absolute()} -endian LSB {tempfile}"
        subprocess.run(conv_cmd, shell=True, check=True, stdout = subprocess.DEVNULL)
        
        # Denoise pfm
        denoised_tempfile = tempfile.parent / (img.stem + "_denoised.pfm")
        denoise_cmd = f"oidnDenoise --ldr {tempfile} -o {denoised_tempfile}"
        subprocess.run(denoise_cmd, shell=True, check=True, stdout = subprocess.DEVNULL)

        # Convert back
        output = outpath / img.name
        back_conv_cmd = f"convert {denoised_tempfile} {calc_compression(img.suffix)}{output}"
        subprocess.run(back_conv_cmd, shell=True, check=True, stdout = subprocess.DEVNULL)

        tempfile.unlink()
        denoised_tempfile.unlink()

        return f"({idx+1}/{num_files}) Saved {output}"


    except Exception as e:
        return f"({idx+1}/{num_files}) Error on input {img}: {e}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser("denoise image or folder of images")
    parser.add_argument("input", help="Input file or folder.", type=str)
    parser.add_argument("output", help="output folder for denoised files. Same names as input file(s).", type=str)
    parser.add_argument("-f", "--force", help="Allow writing to non-empty folder. Potentially overwrites files.", action='store_true')
    parser.add_argument("-s", "--silent", help="Don't output anyting while running", action='store_true')
    args = parser.parse_args()

    input = Path(args.input)
    outpath = Path(args.output)

    if not input.exists():
        raise FileNotFoundError(input)

    if not args.force and outpath.exists() and any(outpath.iterdir()):
        sys.exit("Non-empty output directory. Use --force to use ")


    inputfiles = []
    if input.is_dir():
        inputfiles = [entry for entry in input.iterdir() if entry.is_file()]
    else:
        inputfiles.append(input)


    num_files = len(inputfiles)
    with tempfile.TemporaryDirectory() as tempdir, ProcessPoolExecutor(min(num_files, psutil.cpu_count(logical = False))) as executor:
        temppath = Path(tempdir)
        outpath.mkdir(parents=True, exist_ok=True)
        if not args.silent:
            print(f"Denoising {num_files} images...")

        for result in executor.map(denoise, range(len(inputfiles)), inputfiles, repeat(temppath), repeat(outpath)):
            if not args.silent:
                print(result)

