#!/usr/bin/python3
'''
Program:    findVHVLResidues
File:       findVHVLResidues.py

Version:    V1.0
Date:       25.03.2021
Function:   Find the residue identities corresponding to the numbering for VH-VL-packing relevant residues

Description:
============
The program will take PDB files and extract a string of one letter residue codes for the VH-VL-Packing relevant region
e.g.


--------------------------------------------------------------------------
'''
# *************************************************************************
# Import libraries

# sys to take args from commandline, os for reading directory, and subprocess for running external program
import os
import sys
import pandas as pd
import numpy as np

# *************************************************************************
def get_pdbdirectory():
    """Read the directory name from the commandline argument

    Return: pdb_directory      --- Directory of PBD files that will be processed for VH-VL packing angles

    15.03.2021  Original   By: VAB
    """

    # Take the commandline input as the directory, otherwise look in current directory
    if sys.argv[1] != '':
        pdb_direct = sys.argv[1]
    else:
        pdb_direct = '.'
    return pdb_direct

#*************************************************************************
def extract_pdb_name(pdb_direct):
    """Return a list of headers of PDB files in the called directory

    Input:  pdb_direct   --- Directory of PBD files that will be processed for VH-VL packing angles
    Return: pdb_name     --- Names of all PDB files in the directory


    18.03.2021  Original   By: VAB
    """

    # Iternates over all files in directory, checks if they are pdb files and returns the
    # name without the extension into a list.
    pdb_names = []
    for pdb in os.listdir(pdb_direct):
        if pdb.endswith(".pdb") or pdb.endswith(".ent"):
            pdb_name = os.path.splitext(pdb)[0]
            pdb_names.append(pdb_name)
    return pdb_names

#*************************************************************************
def read_directory_for_PDB_files(pdb_direct):
    """Print a list of all files that are PDB files in the called directory

    Input:  pdb_direct   --- Directory of PBD files that will be processed for VH-VL packing angles
    Return: files        --- All PDB files in the directory


    15.03.2021  Original   By: VAB
    """

    # Creates an empty list, then iterates over all files in the directory called from the
    # commandline. Adds all these .pdb files to the list.
    files = []
    for file in os.listdir(pdb_direct):
        if file.endswith(".pdb") or file.endswith(".ent"):
            files.append('{}/{}'.format(pdb_direct, file))
    return files


#*************************************************************************
def read_pdbfiles_as_lines(pdb_files):
    """Read PDB files as lines

    Input:  pdb_files   --- All PDB files in the directory
    Return: lines       --- PDB files split into lines


    10.03.2021  Original   By: VAB
    """
    lines = []
    for structure_file in pdb_files:
        text_file = open(structure_file, "r")
    # Splits the opened PDB file at '\n' (the end of a line of text) and returns those lines
        lines.append(text_file.read().split('\n'))
    lines = str(lines)
    return lines

#*************************************************************************
def pdb_lines_as_dictionary(directory, file_lines):
    """Print a list of all files that are PDB files in the called directory

    Input:  directory    --- Directory of PBD files that will be processed for VH-VL packing angles
    Return:         --- All PDB files in the directory


    28.03.2021  Original   By: VAB
    """

    for pdb_file in directory:
        for fline in file_lines:
            pdb_dict = {pdb_file: fline}
    return pdb_dict

#*************************************************************************
def one_letter_code(residue):

    """
    Go from the three-letter code to the one-letter code.

    Input:  residue      --- Three-letter residue identifier
    Return: one_letter   --- The one-letter residue identifier

    20.10.2020  Original   By: LD
    """

    dic = {'CYS': 'C', 'ASP': 'D', 'SER': 'S', 'GLN': 'Q', 'LYS': 'K', 'ILE': 'I', 'PRO': 'P', 'THR': 'T', 'PHE': 'F', 'ASN': 'N', 'GLY': 'G', 'HIS': 'H', 'LEU': 'L', 'ARG': 'R', 'TRP': 'W', 'ALA': 'A', 'VAL':'V', 'GLU': 'E', 'TYR': 'Y', 'MET': 'M','XAA': 'X', 'UNK':'X'}
    if len(residue) % 3 != 0:
        raise ValueError("error")
    one_letter = dic[residue]
    return one_letter

#*************************************************************************
def prep_table(lines):
    """Build table for atom information using pandas dataframes

    Input:  lines      --- All PDB files split into lines
    Return: ftable     --- Sorted table that contains the residue id:
    e.g.
          chain residue number L/H position
    0        L       D      1           L1
    8        L       I      2           L2
    16       L       V      3           L3
    23       L       L      4           L4
    31       L       T      5           L5

    10.03.2021  Original   By: VAB
    26.03.2021  V2.0       By: VAB
    """

    # Create blank lists for lines in file that contain atom information
    atom_lines = []
    table = []

    # Assign column names for residue table
    c = ['chain', "residue", 'number', 'L/H position']

    # Search for lines that contain 'ATOM' and add to atom_lines list
    for items in lines:
        if items.startswith('ATOM'):
            atom_lines.append(items)

    # Locate specific residue information, covert three-letter identifier into one-letter
    for res_data in atom_lines:
        res_num  = str(res_data[23:27]).strip()
        chain    = str(res_data[21:22]).strip()
        residue  = (res_data[17:20]).strip()
        res_one  = str(one_letter_code(residue))
        L_H_position = str("{}{}".format(chain, res_num))
        res_info = [chain, res_one, res_num, L_H_position]
        table.append(res_info)
    # Use pandas to build a data table from compiled residue info and column headers:
    ftable = pd.DataFrame(data=table, columns=c)

    # Remove all row duplicates
    ftable = ftable.drop_duplicates()
    return ftable

#*************************************************************************
def VH_VL_relevant_residues(vtable):
    """Filter table for residues relevant for VH-VL packing

    Input:  vtable     --- Sorted table that contains the residue id
    Return:  :
    e.g.

    26.03.2021  Original   By: VAB
    """

    # Find all of the key residues for VH/VL packing:
    # e.g  chain residue number L/H position
    # 267      L       Q     38          L38
    # 285      L       S     40          L40
    # 291      L       G     41          L41
    # 308      L       P     44          L44
    vtable = vtable[vtable['L/H position'].str.contains('L38|L40|L41|L44|L46|L87|H33|H42|H45|H60|H62|H91|H105')]
    #print(vtable)

    vtable['res_id'] = vtable['residue'].str.cat(vtable['number'], sep='')

    #create a table of just res_id values
    otable = vtable[['res_id']]
    #print(vtable)

    return otable
#*************************************************************************
#*** Main program                                                      ***
#*************************************************************************

pdb_direct = get_pdbdirectory()
#print('pdb_direct', pdb_direct)

generate_pdb_names = extract_pdb_name(pdb_direct)
#print('generate_pdb_names', generate_pdb_names)

pdb_files = read_directory_for_PDB_files(pdb_direct)
#print(pdb_files) # a list of all pdb files (full paths)

pdb_lines = read_pdbfiles_as_lines(pdb_files)
print('pdb_lines', pdb_lines)

#pdb_dictionary = pdb_lines_as_dictionary(pdb_direct, pdb_lines)
#print(pdb_dictionary)

ftable = prep_table(pdb_lines)
#print('ftable', ftable)

VHVLtable = VH_VL_relevant_residues(ftable)
#print(VHVLtable)