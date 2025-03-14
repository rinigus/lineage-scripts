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
    file: str = ''

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
                prop_lines.append(PropLine(is_property=False, line=line, file=file_path))
                continue
                        
            # Property
            match = re.match(r'^([^=]+)=(.*)$', line)
            if match:
                prop, value = match.groups()
                prop_lines.append(PropLine(
                    is_property=True, 
                    property_name=prop.strip(), 
                    property_value=value.strip(), 
                    line=line,
                    file=file_path,
                ))
            else:
                # Unrecognized line type
                print(f"Failed to parse line in {file_path}: {line}")

    
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

def find_prop_files(rom_folder):
    """
    Recursively find all .prop files in the stock rom folder.
    
    Args:
        rom_folder (pathlib.Path): Path to stock rom folder
    
    Returns:
        list: List of paths to .prop files
    """
    return list(rom_folder.rglob('*.prop'))

def load_properties_from_files(prop_files):
    """
    Load properties from all prop files.
    
    Args:
        prop_files (list): List of .prop file paths
    
    Returns:
        dict: Merged properties from all stock ROM prop files
    """
    properties = []
    for prop_file in prop_files:
        properties.extend(parse_prop_file(prop_file))
    
    return properties

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
    parser.add_argument('--missing', action='store_true', help='Check which properties are missing from stock')
    parser.add_argument('--output', type=pathlib.Path, help='Optional output file path')
    
    args = parser.parse_args()
    
    # Validate inputs
    if args.missing and args.prop_file.is_dir():
        missing=True
    elif not args.missing and args.prop_file.is_file():
        missing=False
    else:
        print(f"Error: Property file/directory {args.prop_file} does not exist.")
        return
    
    if not args.stock_rom_folder.is_dir():
        print(f"Error: Stock ROM folder {args.stock_rom_folder} does not exist.")
        return
    
    # Load custom properties
    if missing:
        custom_prop_files = find_prop_files(args.prop_file)
        custom_prop_lines = load_properties_from_files(custom_prop_files)
    else:
        custom_prop_lines = parse_prop_file(args.prop_file)
    custom_props = load_properties(custom_prop_lines)
    
    # Find and load stock ROM properties
    stock_prop_files = find_prop_files(args.stock_rom_folder)
    stock_prop_lines = load_properties_from_files(stock_prop_files)
    stock_props = load_properties(stock_prop_lines)
    
    # Compare properties
    if missing:
        differences = compare_properties(stock_props, custom_props)
        ref, cust = "Custom", "Stock"
    else:
        differences = compare_properties(custom_props, stock_props)
        ref, cust = "Stock", "Custom"
    
    # Print differences
    if differences:
        print("Property Differences Found:")
        for prop, vals in differences.items():
            if vals['stock'] == 'NOT_FOUND':
                print(f"- {prop}: Not found in {ref} ROM ({cust} value: {vals['custom']})")
            else:
                print(f"- {prop}: {cust}={vals['custom']} | {ref}={vals['stock']}")
    else:
        print("No differences found between custom and stock properties.")
    
    # Optional output file generation
    if args.output:
        with open(args.output, 'w') as outfile:
            if missing:
                prev_file = None
                for line in stock_prop_lines:
                    prop = line.property_name
                    if prop in differences and differences[prop].get("stock", "same") == 'NOT_FOUND':
                        if prev_file != line.file:
                            outfile.write(f"\n# from {line.file}\n")
                            prev_file = line.file
                        outfile.write(f"{line.line}\n")
            else:
                for line in custom_prop_lines:
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
                                outfile.write(f"# Missing in stock \n# {prop}={differences[prop]['custom']}\n")
                        else:
                            # No difference, write original line
                            outfile.write(f"{line.line}\n")
        
        print(f"Output file generated: {args.output}")

if __name__ == '__main__':
    main()