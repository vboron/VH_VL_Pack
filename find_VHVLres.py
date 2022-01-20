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

    pdb_dict = {}

    for structure_file in files:
        atom_lines = []
        with open(structure_file, "r") as text_file:

            # Remove the path and the extension from the name of the PDB file
            structure_file = structure_file.replace(f'{directory}/', '')
            structure_file = structure_file[:-4]

            # Search for lines that contain 'ATOM' and add to atom_lines list
            for line in text_file.read().split('\n'):
                if str(line).strip().startswith('ATOM'):
                    atom_lines.append(line)

            # Associate the name of the file with the relevant lines in a dictionary
            pdb_dict[structure_file] = atom_lines

    return pdb_dict


# *************************************************************************
def prep_table(dictionary):
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
    c = ['code', 'chain', 'residue', 'number', 'L/H position']

    # Locate specific residue information
    for key, value in dictionary.items():
        pdb_code = key
        for data in value:
            items = data.split()
            res_num = items[5]
            chain = items[4]
            residue = items[3]

            # Use defined dictionary to convert 3-letter res code to 1-letter
            try:
                res_one = str(one_letter_code(key, residue))
            except ValueError:
                continue

            # Create a column that reads the light/ heavy chain residue location e.g. L38 (for easy search)
            lhposition = str(f'{chain}{res_num}')
            res_info = [pdb_code, chain, res_one, res_num, lhposition]
            table.append(res_info)

    # Use pandas to build a data table from compiled residue info and column headers:
    ftable = pd.DataFrame(data=table, columns=c)

    # Remove all row duplicates
    ftable = ftable.drop_duplicates()
    return ftable


# *************************************************************************
def vh_vl_relevant_residues(vtable):
    """Filter table for residues relevant for VH-VL packing

    Input:  vtable        --- Sorted table that contains information about the chain, residues, positions of all atoms
    Return: out_table     --- Sorted table that contains the residue identities of the specified VH/L positions

    26.03.2021  Original   By: VAB
    """

    # Look for rows that contain the specified residue locations
    good_positions = ['L38', 'L40', 'L41', 'L44', 'L46', 'L87', 'H33', 'H42', 'H45', 'H60', 'H62', 'H91', 'H105']
    vtable = vtable[vtable['L/H position'].isin(good_positions)]

    # Create a table of the residue data for the specific locations
    out_table = vtable.loc[:, ('code', 'L/H position', 'residue')]
    return out_table


# *************************************************************************
# *** Main program                                                      ***
# *************************************************************************
parser = argparse.ArgumentParser(description='Program for extracting VH/VL relevant residues')
parser.add_argument('--directory', help='Directory of pdb files', required=True)
parser.add_argument('--csv_output', help='Name of the csv file that will be the output', required=True)
args = parser.parse_args()

csv_path = os.path.join(args.directory, (args.csv_output + '.csv'))

pdb_lines = read_pdbfiles_as_lines(args.directory)

init_table = prep_table(pdb_lines)

VHVLtable = vh_vl_relevant_residues(init_table)

# index= FALSE removes indexing column from the dataframe
VHVLtable.to_csv(csv_path, index=False)