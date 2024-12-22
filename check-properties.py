#!/usr/bin/env python

import argparse
import pathlib
import re
from dataclasses import dataclass
from typing import Optional

@dataclass
class PropLine:
    """
    Represents a single line in a property file.
    
    Attributes:
        is_property (bool): Whether the line represents a property
        property_name (Optional[str]): Name of the property (if applicable)
        property_value (Optional[str]): Value of the property (if applicable)
        line (str): Original text of the line
    """
    is_property: bool
    property_name: Optional[str] = None
    property_value: Optional[str] = None
    line: str = ''

def parse_prop_file(file_path):
    """
    Parse a property file into a list of PropLine objects.
    
    Args:
        file_path (pathlib.Path): Path to the property file
    
    Returns:
        list: List of PropLine objects
    """
    prop_lines = []
    
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Empty line or line with comment
            if not line or line.startswith('#'):
                prop_lines.append(PropLine(is_property=False, line=line))
                continue
                        
            # Property
            match = re.match(r'^([^=]+)=(.*)$', line)
            if match:
                prop, value = match.groups()
                prop_lines.append(PropLine(
                    is_property=True, 
                    property_name=prop.strip(), 
                    property_value=value.strip(), 
                    line=line
                ))
            else:
                # Unrecognized line type
                raise Exception(f"Unrecognized line {line}")

    
    return prop_lines

def load_properties(prop_lines):
    """
    Extract properties from PropLine list.
    
    Args:
        prop_lines (list): List of PropLine objects
    
    Returns:
        dict: Dictionary of properties
    """
    return {
        line.property_name: line.property_value 
        for line in prop_lines 
        if line.is_property
    }

def find_prop_files(stock_rom_folder):
    """
    Recursively find all .prop files in the stock rom folder.
    
    Args:
        stock_rom_folder (pathlib.Path): Path to stock rom folder
    
    Returns:
        list: List of paths to .prop files
    """
    return list(stock_rom_folder.rglob('*.prop'))

def load_stock_properties(stock_prop_files):
    """
    Load properties from all stock ROM prop files.
    
    Args:
        stock_prop_files (list): List of .prop file paths
    
    Returns:
        dict: Merged properties from all stock ROM prop files
    """
    stock_properties = {}
    for prop_file in stock_prop_files:
        try:
            with open(prop_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    match = re.match(r'^([^=]+)=(.*)$', line)
                    if match:
                        prop, value = match.groups()
                        stock_properties[prop.strip()] = value.strip()
                    else:
                        print(f"Failed to parse {prop_file}: {line}")
        except Exception as e:
            print(f"Error reading {prop_file}: {e}")
    
    return stock_properties

def compare_properties(custom_props, stock_props):
    """
    Compare custom properties with stock properties.
    
    Args:
        custom_props (dict): Properties from custom file
        stock_props (dict): Properties from stock ROM
    
    Returns:
        dict: Differences between custom and stock properties
    """
    differences = {}
    for prop, custom_value in custom_props.items():
        if prop in stock_props:
            stock_value = stock_props[prop]
            if custom_value != stock_value:
                differences[prop] = {
                    'custom': custom_value,
                    'stock': stock_value
                }
        else:
            differences[prop] = {
                'custom': custom_value,
                'stock': 'NOT_FOUND'
            }
    
    return differences

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Compare custom properties with stock ROM properties')
    parser.add_argument('prop_file', type=pathlib.Path, help='Path to custom properties file')
    parser.add_argument('stock_rom_folder', type=pathlib.Path, help='Path to stock ROM folder')
    parser.add_argument('--output', type=pathlib.Path, help='Optional output file path')
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.prop_file.is_file():
        print(f"Error: Property file {args.prop_file} does not exist.")
        return
    
    if not args.stock_rom_folder.is_dir():
        print(f"Error: Stock ROM folder {args.stock_rom_folder} does not exist.")
        return
    
    # Load custom properties
    prop_lines = parse_prop_file(args.prop_file)
    custom_props = load_properties(prop_lines)
    
    # Find and load stock ROM properties
    stock_prop_files = find_prop_files(args.stock_rom_folder)
    stock_props = load_stock_properties(stock_prop_files)
    
    # Compare properties
    differences = compare_properties(custom_props, stock_props)
    
    # Print differences
    if differences:
        print("Property Differences Found:")
        for prop, vals in differences.items():
            if vals['stock'] == 'NOT_FOUND':
                print(f"- {prop}: Not found in stock ROM (Custom value: {vals['custom']})")
            else:
                print(f"- {prop}: Custom={vals['custom']} | Stock={vals['stock']}")
    else:
        print("No differences found between custom and stock properties.")
    
    # Optional output file generation
    if args.output:
        with open(args.output, 'w') as outfile:
            for line in prop_lines:
                if not line.is_property:
                    # Write comments, empty lines as they are
                    outfile.write(f"{line.line}\n")
                else:
                    # Check if property has differences
                    prop = line.property_name
                    if prop in differences:
                        # Use stock value if different, otherwise use custom value
                        if differences[prop]['stock'] != 'NOT_FOUND':
                            outfile.write(f"{prop}={differences[prop]['stock']}\n")
                        else:
                            outfile.write(f"{prop}={differences[prop]['custom']}\n")
                    else:
                        # No difference, write original line
                        outfile.write(f"{line.line}\n")
        
        print(f"Output file generated: {args.output}")

if __name__ == '__main__':
    main()