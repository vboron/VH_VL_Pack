#!/usr/bin/env python3
import pandas as pd
import argparse
from ordered_set import OrderedSet
import pickle
import os
import functools as ft


# *************************************************************************
def nr_side_chain_atoms(resi):
    # 1. total number of side-chain atoms
    nr_side_chain_atoms_dic = {'A': 1, 'R': 7, "N": 4, "D": 4, "C": 2, "Q": 5, "E": 5, "G": 0, "H": 6, "I": 4,
                               "L": 4, "K": 15, "M": 4, "F": 7, "P": 4,
                               "S": 2, "T": 3, "W": 10, "Y": 8, "V": 3, "X": 10.375}  # "X": 10.375
    if resi in list(nr_side_chain_atoms_dic.keys()):
        nr_side_chain_atoms = nr_side_chain_atoms_dic[resi]
    else:
        nr_side_chain_atoms = 0
    return nr_side_chain_atoms


def compactness(resi):
    # 2. number of side-chain atoms in shortest path from Calpha to most distal atom
    compactness_dic = {'A': 1, 'R': 6, "N": 3, "D": 3, "C": 2, "Q": 4, "E": 4, "G": 0, "H": 4, "I": 3,
                       "L": 3, "K": 6, "M": 4, "F": 5, "P": 2,
                       "S": 2, "T": 2, "W": 6, "Y": 6, "V": 2, "X": 4.45}  # , "X": 4.45
    if resi in list(compactness_dic.keys()):
        compactness = compactness_dic[resi]
    else:
        compactness = 0
    return compactness


def hydrophobicity(resi):
    # 3. eisenberg consensus hydrophobicity
    # Consensus values: Eisenberg, et al 'Faraday Symp.Chem.Soc'17(1982)109
    Hydrophathy_index = {'A': 00.250, 'R': -1.800, "N": -0.640, "D": -0.720, "C": 00.040, "Q": -0.690, "E": -0.620,
                         "G": 00.160, "H": -0.400, "I": 00.730, "L": 00.530, "K": -1.100, "M": 00.260, "F": 00.610,
                         "P": -0.070,
                         "S": -0.260, "T": -0.180, "W": 00.370, "Y": 00.020, "V": 00.540, "X": -0.5}  # -0.5 is average
    if resi in list(Hydrophathy_index.keys()):
        hydrophobicity = Hydrophathy_index[resi]
    else:
        hydrophobicity = 0
    return hydrophobicity


def charge(resi):
    dic = {"D": -1, "K": 1, "R": 1, 'E': -1, 'H': 0.5}
    charge = 0
    if resi in dic:
        charge += dic[resi]
    else:
        charge = 0
    
    return charge


# *************************************************************************
def encode_4d(df):
    for column in df:
        df[f'{column}a'] = df[column].apply(lambda x: nr_side_chain_atoms(x))
        df[f'{column}b'] = df[column].apply(lambda x: charge(x))
        df[f'{column}c'] = df[column].apply(lambda x: compactness(x))
        df[f'{column}d'] = df[column].apply(lambda x: hydrophobicity(x))
        del df[column]
    return df


# *************************************************************************
def seq2df(seq_file):
    res_info = []
    col = ['code', 'L/H position', 'residue']
    with open(seq_file) as f:
        pdb_code = seq_file[:-4]
        lines = f.readlines()
        for line in lines:
            if line.startswith('L') or line.startswith('H'):
                line_elements = line.split()
                lhposition = line_elements[0]
                residue = line_elements[1]
                data = [pdb_code, lhposition, residue]
                res_info.append(data)
    df = pd.DataFrame(data=res_info, columns=col)
    return df


# *************************************************************************
def loop_df(df):
    cdrL1_pos = [f'L{i}' for i in range(24, 35)]
    cdrH2_pos = [f'H{i}' for i in range(50, 59)]
    cdrH3_pos = [f'H{i}' for i in range(95, 103)]

    def calc_loop_length(pos_list, loop_name):
        df_loop = df[df['L/H position'].isin(pos_list)]
        df_loop = df_loop.groupby(['code']).sum()
        df_loop[f'{loop_name}_length'] = df_loop['residue'].str.len()
        df_loop = df_loop.drop(columns=['L/H position', 'residue'])
        return df_loop

    l1_df = calc_loop_length(cdrL1_pos, 'L1')
    h2_df = calc_loop_length(cdrH2_pos, 'H2')
    h3_df = calc_loop_length(cdrH3_pos, 'H3')

    loop_dfs = [l1_df, h2_df, h3_df]
    loop_df = ft.reduce(lambda left, right: pd.merge(
        left, right, on='code'), loop_dfs)
    loop_df = loop_df.reset_index()
    return loop_df


def encode_df(df):
    df = df.drop_duplicates(subset=['code', 'L/H position'], keep='first')
    df = df.drop(columns='code')
    good_positions = ['L32', 'L34', 'L36', 'L38', 'L40', 'L41', 'L43', 'L44', 'L46', 'L50', 'L86', 'L87', 'L89', 'L91', 
                      'L96', 'L98', 'H33', 'H35', 'H39', 'H42', 'H45', 'H47', 'H50', 'H60', 'H62', 'H91', 'H99', 'H100', 
                      'H100A', 'H100B', 'H100C', 'H100D', 'H100E', 'H100F', 'H1003G', 'H103', 'H105']
    df = df[df['L/H position'].isin(good_positions)]
    col_list = df['L/H position'].values.tolist()
    for pos in good_positions:
        if pos not in col_list:
            new_row = pd.Series({'L/H position': pos, 'residue': float('nan')})
            df = pd.concat([df, new_row.to_frame().T], ignore_index=True)
    df_piv = df.pivot_table(columns='L/H position', values='residue', aggfunc='sum')
    df = df_piv.reset_index()
    df = df.rename_axis(None, axis=1)
    df = df.drop(columns='index')
    df = encode_4d(df)
    return df



# *************************************************************************
def predict_angle(df, model_path):
    pdb_code = {'code'}
    predictors = list(OrderedSet(df.columns) - pdb_code)
    X_test = df[predictors].values
    pkl_filename = os.path.join(model_path)
    with open(pkl_filename, 'rb') as file:
        pickle_model = pickle.load(file)
    y_pred = pickle_model.predict(X_test)
    angle = y_pred[0]
    return angle




parser = argparse.ArgumentParser(description='Program for compiling angles')
parser.add_argument(
    '--resfile', help='file with the residue sequences', required=True)
parser.add_argument(
    '--model', help='path to trained model', required=True)
args = parser.parse_args()

data = seq2df(args.resfile)
loopdf = loop_df(data)
encdf = encode_df(data)
fulldf = pd.concat([encdf, loopdf], axis=1)
print(predict_angle(fulldf, args.modeldir))
