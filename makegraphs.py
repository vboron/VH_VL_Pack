#!/usr/bin/env python3

from graphing import *
import pandas as pd
import argparse

def makegraphs(csv, output, dire, df_stat):
    df = pd.read_csv(csv)
    error_distribution(dire, df, output)
    sq_error_vs_actual_angle(dire, df, output)
    actual_vs_predicted_from_df(df, dire, df_stat, output)


parser = argparse.ArgumentParser(description='Program for extracting VH/VL relevant residues')
parser.add_argument('--dir', required=True)
parser.add_argument('--out', required=True)
parser.add_argument('--csv', required=True)
parser.add_argument('--stats', required=True)
args = parser.parse_args()

makegraphs(args.csv, args.out, args.dir, args.stat)