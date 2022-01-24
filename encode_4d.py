#!/usr/bin/python3
"""
Function:   Encode VH/VL packing amino acids into 4d vectors for machine learning.

Description:
============
Program uses the residue identities for VH/VL relevant residues and encodes them using 4 vectors (hydrophobicity,
side chain size, charge, and compactness) then appends the packing angle to produce a data table:
e.g.

code	L38a	L38b	L38c	L38d	L40a	...     angle
12E8_1	0	       5	   4	-0.69	   0            -54.9
12E8_2	0	       5	   4	-0.69	   0            -48.5
15C8_1	0	       5	   4	-0.69	   0            -42.3
1A0Q_1	0.5	       6	   4	-0.4	   0            -45.6

------------------------------------------------
"""
# *************************************************************************
import argparse
import pandas as pd
import numpy as np
import os


# *************************************************************************
def make_res_seq(directory, res_csv):
    """Take all individual residue identities for a pdb file and combine them into a single sequence for
    each individual pdb

    Return: seq_df      --- Dataframe containing the pdb code and the sequence of VHVL residues for each pdb
    e.g.
        code        residue
0     12E8_1  QPGPLFYELVKYQ
1     12E8_2  QPGPLFYELVKYQ
2     15C8_1  QPGPLYYELDKYQ

    10.04.2021  Original   By: VAB
    """

    # read file with residues as a df
    col1 = ['code', 'L/H position', 'residue']
    path = os.path.join(directory, res_csv)
    res_df = pd.read_csv(path, usecols=col1)

    # Add all items under the 'residue' column into one field
    aggregation_func = {'residue': 'sum'}

    # Group rows  by pdb code and then combine them into one field
    #         residue
    # code
    # 12E8_1  QPGPLFYELVKYQ
    # 12E8_2  QPGPLFYELVKYQ

    seq_df = res_df.groupby(res_df['code']).aggregate(aggregation_func)

    # Reset the indices back to single row of column names for easier manipulation:
    #         code        residue
    # 0     12E8_1  QPGPLFYELVKYQ
    # 1     12E8_2  QPGPLFYELVKYQ

    seq_df = seq_df.reset_index()
    # seq_df.reset_index()['residue']
    return seq_df

# *************************************************************************
def nr_side_chain_atoms(resi):
    # 1. total number of side-chain atoms
    nr_side_chain_atoms_dic = {'A': 1, 'R': 7, "N": 4, "D": 4, "C": 2, "Q": 5, "E": 5, "G": 0, "H": 6, "I": 4,
                               "L": 4, "K": 15, "M": 4, "F": 7, "P": 4,
                               "S": 2, "T": 3, "W": 10, "Y": 8, "V": 3, "X": 10.375}  # "X": 10.375
    nr_side_chain_atoms = nr_side_chain_atoms_dic[resi]
    return nr_side_chain_atoms

# *************************************************************************
def compactness(resi):
    # 2. number of side-chain atoms in shortest path from Calpha to most distal atom
    compactness_dic = {'A': 1, 'R': 6, "N": 3, "D": 3, "C": 2, "Q": 4, "E": 4, "G": 0, "H": 4, "I": 3,
                       "L": 3, "K": 6, "M": 4, "F": 5, "P": 2,
                       "S": 2, "T": 2, "W": 6, "Y": 6, "V": 2, "X": 4.45}  # , "X": 4.45
    compactness = compactness_dic[resi]
    return compactness

# *************************************************************************
def hydophobicity(resi):
    # 3. eisenberg consensus hydrophobicity
    # Consensus values: Eisenberg, et al 'Faraday Symp.Chem.Soc'17(1982)109
    Hydrophathy_index = {'A': 00.250, 'R': -1.800, "N": -0.640, "D": -0.720, "C": 00.040, "Q": -0.690, "E": -0.620,
                         "G": 00.160, "H": -0.400, "I": 00.730, "L": 00.530, "K": -1.100, "M": 00.260, "F": 00.610,
                         "P": -0.070,
                         "S": -0.260, "T": -0.180, "W": 00.370, "Y": 00.020, "V": 00.540, "X": -0.5}  # -0.5 is average

    hydrophobicity = Hydrophathy_index[resi]
    return hydrophobicity

# *************************************************************************
def charge(resi):
    dic = {"D": -1, "K": 1, "R": 1, 'E': -1, 'H': 0.5}
    charge = 0
    if resi in dic:
        charge += dic[resi]
    return charge


# *************************************************************************
def encode(table):
    """Description:
    This program replicates the technique for amino - acid encoding used in the paper by Martin & Abhinandan 2010.
    The amino acids were encoded in 4d vectors for neural network input preparation.The four features calculated were:
        # 1. total number of side-chain atoms
        # 2. number of side-chain atoms in shortest path from Calpha to most distal atom
        # 3. eisenberg consensus hydrophobicity
        # 4. charge (histidine was assigned +0.5)

    Version:    V2.0
    Date:       10.04.21
    Copyright:  (c) UCL, Prof. Andrew C. R. Martin 1994-2021

    17.03.2021  Original   By: Lilian Denzler
    10.04.2021  V2.0       By: VAB
    """

    columns = ['code', "res_charge", "res_sc_nr", "res_compactness", "res_hydrophob"]
    seq_df = pd.DataFrame(columns=columns)

    # Iterate through all rows in the datatable as sets of tuples
    for row in table.itertuples():
        seq = row[2]
        for res in seq:
            code = row[1]
            charge_of_res = charge(res)
            hydrophobicity_res = hydophobicity(res)
            compactness_res = compactness(res)
            nr_side_chain_atoms_res = nr_side_chain_atoms(res)

            seq_df = seq_df.append(
                {'code': code, "res_charge": charge_of_res, "res_sc_nr": nr_side_chain_atoms_res,
                 "res_compactness": compactness_res, "res_hydrophob": hydrophobicity_res}, ignore_index=True)
    return seq_df


# *************************************************************************
def combine_by_pdb_code(directory, table, ang_csv, col_names):
    """Take all individual residue identities for a pdb file and combine them into a single sequence for
    each individual pdb

    Input:  table            --- Data frame containing the residue sequence for each pdb
    Return: training_df      --- Dataframe containing the pdb code, all encoded residues and the packing angle
    e.g.
        code L38a L38b L38c   L38d L40a  ...  H91d H105a H105b H105c  H105d angle
0     12E8_1    0    5    4  -0.69    0  ...  0.02     0     5     4  -0.69 -54.9
1     12E8_2    0    5    4  -0.69    0  ...  0.02     0     5     4  -0.69 -48.5

    10.04.2021  Original   By: VAB
    """

    col = ['code', 'encoded_res']
    itable = []
    for row in table.itertuples():
        code = row[1]

        # charge
        a = row[2]

        # side chain number
        b = row[3]

        # compactness
        c = row[4]

        # hydrophobicity
        d = row[5]

        # the last comma had to be added so that when the lines are combined, the first and last columns don't get merged
        # res_encoded = '{}, {}, {}, {}, '.format(a, b, c, d)
        res_encoded = f'{a},{b},{c},{d},'
        res = [code, res_encoded]
        itable.append(res)

    temp_df = pd.DataFrame(data=itable, columns=col)
    # print(temp_df)
    # Combine all of the encoded residues for a specific pdb file into a single row
    enc_df = temp_df.groupby(temp_df['code']).aggregate(np.sum)
    enc_df = enc_df.reset_index()

    # Re-make pdb codes as a single column
    pdb_code_df = pd.Series(enc_df.code, name='code')

    # Split combined codes into separate fields with the position and parameter as the column name
    # ('trash' column created because the adjustment above that corrects data removal
    # ends up creating a blank column)
    col2 = [i.strip('\n') for i in open(col_names).readlines()]

    col2.remove('code')
    col2.append('trash')
    col2.remove('angle')

    res_df = pd.DataFrame(enc_df.encoded_res.str.split(',').tolist(),
                          columns=col2)

    # Remove the blank column
    res_df = res_df.iloc[:, :-1]

    # Add column containing pdb codes to the table of encoded residues
    encoded_df = pd.concat([pdb_code_df, res_df], axis=1)

    col3 = ['code', 'angle']

    # Take the second input from the commandline (which will be the table of pdb codes and their packing angles)
    angle_file = pd.read_csv(os.path.join(directory, ang_csv), usecols=col3)

    # Angle column will be added to the table of encoded residues and the table is sorted by code
    # to make sure all the data is for the right pdb file
    training_df = pd.merge(encoded_df, angle_file, how="right", on=["code"], sort=True)

    # remove all rows that contain blank spaces
    nan_value = float('NaN')
    training_df.replace('', nan_value, inplace=True)
    training_df.dropna(axis=0, how='any', inplace=True)

    return training_df


# *************************************************************************
# *** Main program                                                      ***
# *************************************************************************
parser = argparse.ArgumentParser(description='Program for compiling angles')
parser.add_argument('--residue_csv', help='.csv file containing the residue identities for VHVL packing', required=True)
parser.add_argument('--angle_csv', help='.csv file containing VHVL packing angles', required=True)
parser.add_argument('--columns', help='.dat file with 4d column names for residues', required=True)
parser.add_argument('--directory', help='Directory of pdb files', required=True)
parser.add_argument('--csv_output', help='Name of the csv file that will be the output', required=True)
args = parser.parse_args()

res_seq = make_res_seq(args.directory, args.residue_csv)

parameters = encode(res_seq)

results = combine_by_pdb_code(args.directory, parameters, args.angle_csv, args.columns)

csv_path = os.path.join(args.directory, f'{args.csv_output}.csv')
results.to_csv(csv_path, index=False)
