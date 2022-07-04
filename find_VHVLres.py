#!/usr/bin/env python3
"""
Function:   Find the residue identities corresponding to the numbering for VH-VL-packing relevant residues

Description:
============
The program will take PDB files and extract a string of one letter residue codes for the VH-VL-Packing relevant region
and deposits into csv file
e.g.
      code L/H position residue
    5DMG_2          L38       Q
    5DMG_2          L40       P
    5DMG_2          L41       G
    5DMG_2          L44       P

--------------------------------------------------------------------------
"""
# *************************************************************************
import os
import pandas as pd
from utils import one_letter_code
import argparse

# *************************************************************************


def read_pdbfiles_as_lines(directory):
    """Read PDB files as lines, then make a dictionary of the PDB code and all the lines that start with 'ATOM'

    Return: pdb_dict    --- Dictionary of PDB names with all of the lines containing atom details
    e.g.
    {'5DMG_2': ['ATOM   4615  N   GLN L   2     -34.713  12.044 -12.438  1.00 44.10         N  ',...'], '5DQ9_3':...'}

    10.03.2021  Original   By: VAB
    """
    # Creates an empty list, then iterates over all files in the directory called from the
    # commandline. Adds all these .pdb  and .ent files to the list.
    files = []

    for file in os.listdir(directory):
        if file.endswith(".pdb") or file.endswith(".ent"):

            # Prepends the directory path to the front of the file name to create full filepath
            files.append(os.path.join(directory, file))

    # pdb_dict = {}
    atom_lines = []
    col = ['code', 'L/H position', 'residue']
    for structure_file in files:
        
        with open(structure_file, "r") as text_file:

            structure_file = structure_file.replace(directory, '')
            pdb_code = structure_file[:-4]

            for line in text_file.read().split('\n'):
                if str(line).strip().startswith('ATOM'):
                    # atom_lines.append(line)
                    items = line.split()
                    res_num = items[5]
                    chain = items[4]
                    residue = items[3]
                    lhposition = str(f'{chain}{res_num}')
                    data = [pdb_code, lhposition, residue]
                    atom_lines.append(data)

            # pdb_dict[structure_file] = atom_lines
            text_file.close()
    df = pd.DataFrame(data = data, columns=col)
    print(df)
    return df


# *************************************************************************
def prep_table(dictionary, residue_list_file):
    """Build table for atom information using pandas dataframes

    Input:  dict_list      --- Dictionary of PDB codes associated with 'ATOM' lines
    Return: ftable         --- Sorted table that contains the details needed to search for the relevant residues:
    e.g.
      PDB Code chain residue number L/H position
0       5DMG_2     L       Q      2           L2
9       5DMG_2     L       V      3           L3
16      5DMG_2     L       L      4           L4

    10.03.2021  Original   By: VAB
    26.03.2021  V2.0       By: VAB
    """

    table = []

    # Assign column names for residue table
    c = ['code', 'L/H position', 'residue']

    good_positions = [i.strip('\n')
                      for i in open(residue_list_file).readlines()]

    # Locate specific residue information
    for key, value in dictionary.items():
        print(value)
        pdb_code = key
        items = value.split()
        res_num = items[5]
        chain = items[4]
        residue = items[3]
        lhposition = str(f'{chain}{res_num}')
        if lhposition in good_positions:
            # Use defined dictionary to convert 3-letter res code to 1-letter
            try:
                res_one = str(one_letter_code(key, residue))
            except ValueError:
                continue

            # Create a column that reads the light/ heavy chain residue location e.g. L38 (for easy search)
            
            res_info = [pdb_code, lhposition, res_one]
            table.append(res_info)

    # Use pandas to build a data table from compiled residue info and column headers:
    ftable = pd.DataFrame(data=table, columns=c)
    print(ftable)
    # Remove all row duplicates
    ftable = ftable.drop_duplicates()
    return ftable


def extract_and_export_packing_residues(directory, csv_output, residue_positions):
    csv_path = os.path.join(directory, (csv_output + '.csv'))
    pdb_lines = read_pdbfiles_as_lines(directory)
    VHVLtable = prep_table(pdb_lines, residue_positions)
    VHVLtable.to_csv(csv_path, index=False)


# *************************************************************************
# *** Main program                                                      ***
# *************************************************************************
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Program for extracting VH/VL relevant residues')
    parser.add_argument(
        '--directory', help='Directory of pdb files', required=True)
    parser.add_argument(
        '--csv_output', help='Name of the csv file that will be the output', required=True)
    parser.add_argument(
        '--residue_positions', help='File containing a list of the residues to be used as features', required=True)
    args = parser.parse_args()

    extract_and_export_packing_residues(
        args.directory, args.csv_output, args.residue_positions)
