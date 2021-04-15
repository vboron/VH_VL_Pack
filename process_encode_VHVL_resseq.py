#!/usr/bin/python3
"""
Program:    process_encode_VHVL_resseq
File:       process_encode_VHVL_resseq.py

Version:    V1.0
Date:       09.03.2021
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
# Import libraries

# sys to take args from commandline, os for reading directory, pandas for making dataframes
import sys
sys.path.append('/serv/www/html_lilian/libs')
sys.path.append('./CDRH3lib')
sys.path.append('~/sync_project/WWW/CDRH3loop')
import pandas as pd
import numpy as np



# *************************************************************************
def read_csv():
    """Read the file containing pdb id and the VHVL residue identity

        Return: res_file      --- Data file with residue identities read by column names

        15.03.2021  Original   By: VAB
        """

    # The column names contained in the .csv file
    col1 = ['code', 'L/H position', 'residue']

    # Take the commandline input as the directory, otherwise look in current directory
    if sys.argv[1] != '':
        res_file = pd.read_csv(sys.argv[1], usecols=col1)

    return res_file


# *************************************************************************
def make_res_seq(rfile):
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

    # Add all items under the 'residue' column into one field
    aggregation_func = {'residue': 'sum'}

    # Group rows  by pdb code and then combine them into one field
    #         residue
    # code
    # 12E8_1  QPGPLFYELVKYQ
    # 12E8_2  QPGPLFYELVKYQ

    seq_df = rfile.groupby(rfile['code']).aggregate(aggregation_func)

    # Reset the indices back to single row of column names for easier manipulation:
    #         code        residue
    # 0     12E8_1  QPGPLFYELVKYQ
    # 1     12E8_2  QPGPLFYELVKYQ

    seq_df = seq_df.reset_index()
    # seq_df.reset_index()['residue']
    return seq_df


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


def nr_side_chain_atoms(resi):
    # 1. total number of side-chain atoms
    nr_side_chain_atoms_dic = {'A': 1, 'R': 7, "N": 4, "D": 4, "C": 2, "Q": 5, "E": 5, "G": 0, "H": 6, "I": 4,
                               "L": 4, "K": 15, "M": 4, "F": 7, "P": 4,
                               "S": 2, "T": 3, "W": 10, "Y": 8, "V": 3, "X": 10.375}  # "X": 10.375
    nr_side_chain_atoms = nr_side_chain_atoms_dic[resi]
    return nr_side_chain_atoms


def compactness(resi):
    # 2. number of side-chain atoms in shortest path from Calpha to most distal atom
    compactness_dic = {'A': 1, 'R': 6, "N": 3, "D": 3, "C": 2, "Q": 4, "E": 4, "G": 0, "H": 4, "I": 3,
                       "L": 3, "K": 6, "M": 4, "F": 5, "P": 2,
                       "S": 2, "T": 2, "W": 6, "Y": 6, "V": 2, "X": 4.45}  # , "X": 4.45
    compactness = compactness_dic[resi]
    return compactness


def hydophobicity(resi):
    # 3. eisenberg consensus hydrophobicity
    # Consensus values: Eisenberg, et al 'Faraday Symp.Chem.Soc'17(1982)109
    Hydrophathy_index = {'A': 00.250, 'R': -1.800, "N": -0.640, "D": -0.720, "C": 00.040, "Q": -0.690, "E": -0.620,
                         "G": 00.160, "H": -0.400, "I": 00.730, "L": 00.530, "K": -1.100, "M": 00.260, "F": 00.610,
                         "P": -0.070,
                         "S": -0.260, "T": -0.180, "W": 00.370, "Y": 00.020, "V": 00.540, "X": -0.5}  # -0.5 is average

    hydrophobicity = Hydrophathy_index[resi]
    return hydrophobicity


def charge(resi):
    dic = {"D": -1, "K": 1, "R": 1, 'E': -1, 'H': 0.5}
    charge = 0
    if resi in dic:
        charge += dic[resi]
    return charge


# *************************************************************************
def combine_by_pdb_code(table):
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

        # the last comma and space had to be added to avoid deletion of of the first vector of each added residue
        res_encoded = '{}, {}, {}, {}, '.format(a, b, c, d)
        res = [code, res_encoded]
        itable.append(res)

    temp_df = pd.DataFrame(data=itable, columns=col)

    # Combine all of the encoded residues for a specific pdb file into a single row
    enc_df = temp_df.groupby(temp_df['code']).aggregate(np.sum)
    enc_df = enc_df.reset_index()
    #enc_df.reset_index()['encoded_res']

    # Re-make pdb codes as a single column
    pdb_code_df = pd.Series(enc_df.code, name='code')

    # Split combined codes into separate fields with the position and parameter as the column name
    # ('trash' column created because the adjustment above that corrects data removal
    # ends up creating a blank column)
    res_df = pd.DataFrame(enc_df.encoded_res.str.split(', ').tolist(),
                      columns=['L38a', 'L38b', 'L38c', 'L38d', 'L40a', 'L40b', 'L40c', 'L40d',
                               'L41a', 'L41b', 'L41c', 'L41d', 'L44a', 'L44b', 'L44c', 'L44d',
                               'L46a', 'L46b', 'L46c', 'L46d', 'L87a', 'L87b', 'L87c', 'L87d',
                               'H33a', 'H33b', 'H33c', 'H33d', 'H42a', 'H42b', 'H42c', 'H42d',
                               'H45a', 'H45b', 'H45c', 'H45d', 'H60a', 'H60b', 'H60c', 'H60d',
                               'H62a', 'H62b', 'H62c', 'H62d', 'H91a', 'H91b', 'H91c', 'H91d',
                               'H105a', 'H105b', 'H105c', 'H105d', 'trash'])

    # Remove the blank column
    res_df = res_df.iloc[:, :-1]

    # Add column containing pdb codes to the table of encoded residues
    encoded_df = pd.concat([pdb_code_df, res_df], axis=1)

    col2 = ['code', 'angle']

    # Take the second input from the commandline (which will be the table of pdb codes and their packing angles)
    if sys.argv[2] != '':
        angle_file = pd.read_csv(sys.argv[2], usecols=col2)
    # training_df = encoded_df.append([angle_file])

    # Angle column will be added to the table of encoded residues and the table is sorted by code
    # to make sure all the data is for the right pdb file
    training_df = pd.merge(encoded_df, angle_file, how="right", on=["code"], sort=True)
    return training_df


# *************************************************************************
# *** Main program                                                      ***
# *************************************************************************

read_file = read_csv()
# print(read_file)

res_seq = make_res_seq(read_file)
#print(res_seq)


parameters = encode(res_seq)
# print(parameters.groupby(['code']))

results = combine_by_pdb_code(parameters)
# results.to_csv('things.csv', index=False)