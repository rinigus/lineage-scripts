#!/usr/bin/env python
 
import argparse
import re

class SELinuxPolicyGenerator:
    def __init__(self):
        # Dictionary to store compiled denials
        # Key: (scontext, tcontext, tclass)
        # Value: set of permissions
        self.denials = {}
        
    def parse_denial(self, denial_string):
        """Parse a SELinux denial string and add it to the policy compilation."""
        # Extract the permission(s)
        permission_start = denial_string.find("{ ") + 2
        permission_end = denial_string.find(" }", permission_start)
        if permission_start < 2 or permission_end < 0:
            raise ValueError("Invalid denial string format: couldn't find permission")
        permissions = denial_string[permission_start:permission_end].split()
        
        # Extract scontext
        scontext_start = denial_string.find("scontext=") + 9
        scontext_end = denial_string.find(" ", scontext_start)
        if scontext_start < 9 or scontext_end < 0:
            raise ValueError("Invalid denial string format: couldn't find scontext")
        scontext = denial_string[scontext_start:scontext_end]
        
        # Extract tcontext
        tcontext_start = denial_string.find("tcontext=") + 9
        tcontext_end = denial_string.find(" ", tcontext_start)
        if tcontext_start < 9 or tcontext_end < 0:
            raise ValueError("Invalid denial string format: couldn't find tcontext")
        tcontext = denial_string[tcontext_start:tcontext_end]
        
        # Extract tclass
        tclass_start = denial_string.find("tclass=") + 7
        tclass_end = denial_string.find(" ", tclass_start)
        if tclass_start < 7:
            raise ValueError("Invalid denial string format: couldn't find tclass")
        if tclass_end < 0:  # Might be the end of the string
            tclass = denial_string[tclass_start:]
        else:
            tclass = denial_string[tclass_start:tclass_end]
        
        # Create a key for the denial dictionary
        key = (scontext, tcontext, tclass)
        
        # Add or update permissions for this context pair
        if key in self.denials:
            self.denials[key].update(permissions)
        else:
            self.denials[key] = set(permissions)
            
        return key, permissions
    
    def get_policy_rules(self):
        """Generate policy rules from stored denials."""
        policies = []
        
        for (scontext, tcontext, tclass), permissions in self.denials.items():
            # Extract the role from scontext (the part between first and second colon)
            role_start = scontext.find(":r:") + 3
            role_end = scontext.find(":", role_start)
            if role_start < 3 or role_end < 0:
                role = scontext  # Fallback if we can't extract role
            else:
                role = scontext[role_start:role_end]
                
            # Extract object type from tcontext (the part between second and third colon)
            obj_start = tcontext.find(":object_r:") + 10
            obj_end = tcontext.find(":", obj_start)
            if obj_start < 10 or obj_end < 0:
                obj = tcontext  # Fallback if we can't extract object type
            else:
                obj = tcontext[obj_start:obj_end]
            
            # Format the policy rule
            permission_str = " ".join(sorted(permissions))
            policy = f"allow {role} {obj}:{tclass} {{ {permission_str} }};"
            policies.append(policy)
            
        return policies
    
    def write_policies(self, output_file):
        """Print all compiled policy rules."""
        policies = self.get_policy_rules()
        if not policies:
            print("No policies generated yet.")
            return
            
        with open(output_file, 'w', encoding='utf-8') as f:
            for policy in sorted(policies):
                f.write(policy + "\n")



def extract_unique_denials(log_file, output_file, verbose):
    avc_denials = dict()
    
    avc_pattern = re.compile(r'avc:  denied  \{.*?\} for .*?scontext=.*? tcontext=.*? tclass=.*? permissive=\d')
    
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            match = avc_pattern.search(line)
            if match:
                record = {}
                for s in match.group(0).split():
                    k = s.split("=", maxsplit=2)
                    if len(k) > 1:
                        record[k[0]] = k[1]
                    else:
                        record[k[0]] = None
                
                # check if we want to handle this record or just ignore it
                if record.get("path", "").startswith('"/dev/__properties__/u:object_r:') and \
                    record.get("scontext", "") == "u:r:hal_camera_default:s0":
                    continue # skip
                if record.get("path", "").startswith('"/dev/__properties__/u:object_r:') and \
                    record.get("scontext", "") == "u:r:odrefresh:s0":
                    continue # skip

                for k in ["pid", "uid", "ino"]:
                    record.pop(k, None)
                
                key = []
                for k, v in record.items():
                    if v is not None:
                        key.append(f"{k}={v}")
                    else:
                        key.append(k)
                
                key = " ".join(key)
                if key not in avc_denials:
                    avc_denials[key] = line
    
    with open(output_file, 'w', encoding='utf-8') as f:
        keys = sorted(avc_denials.keys())
        denials = [k for k in keys]
        for k in keys:
            if verbose:
                s = avc_denials[k].strip()
            else:
                s = k
            f.write(s + "\n")
    
    print(f"Extracted {len(avc_denials)} unique AVC denials into {output_file}")
    return denials


def main():
    parser = argparse.ArgumentParser(description='Extract unique AVC denials from logcat logs.')
    parser.add_argument('logfile', help='Path to the logcat log file')
    parser.add_argument('-o', '--output', default='unique_avc_denials.txt', help='Output file for unique AVC denials')
    parser.add_argument('-p', '--policy', default='policy.txt', help='Output SELinux policy file')
    parser.add_argument('-v', '--verbose', action='store_true')
    
    args = parser.parse_args()
    denials = extract_unique_denials(args.logfile, args.output, args.verbose)
    
    policy = SELinuxPolicyGenerator()
    for d in denials:
        policy.parse_denial(d)

    policy.write_policies(args.policy)

if __name__ == "__main__":
    main()
