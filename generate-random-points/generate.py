import os
import argparse
import numpy as np
import read_write_model as rwm

if __name__ == "__main__":
    cwd = os.getcwd()
    parser = argparse.ArgumentParser("Gen Points from AABB and save as colmap points")
    parser.add_argument("xmin", help="Minimum X", type=float)
    parser.add_argument("ymin", help="Minimum Y", type=float)
    parser.add_argument("zmin", help="Minimum Z", type=float)
    parser.add_argument("xmax", help="Maximum X", type=float)
    parser.add_argument("ymax", help="Maximum Y", type=float)
    parser.add_argument("zmax", help="Maximum Z", type=float)
    parser.add_argument("-n", "--num", default=50000, type=int)
    args = parser.parse_args()

    points3D = {}
    rng = np.random.default_rng()

    for i in range(0, args.num):
        # Random xyz
        xyz = [rng.uniform(args.xmin, args.xmax), rng.uniform(args.ymin, args.ymax), rng.uniform(args.zmin, args.zmax)]
        rgb = rng.integers(0, 255, 3)
        point = rwm.Point3D(i, xyz, rgb, error=0, image_ids=np.array([]), point2D_idxs=np.array([]))
        points3D[i] = point

    rwm.write_points3D_text(points3D, os.path.join(cwd, "points3D.txt"))
