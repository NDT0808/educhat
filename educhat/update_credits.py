
import re
import os

def normalize_name(name):
    """Normalize string for fuzzy matching."""
    name = name.lower().strip()
    name = re.sub(r'\s+', ' ', name)
    name = name.replace('–', '-').replace('—', '-') # Normalize dashes
    return name

def parse_curriculum_txt(file_path):
    credits_map = {}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    # Regex to capture: Order, Name, Credits, Theory, Practice
    # Example: 1         Triết học Mác - LêNin                3       2         1
    # Example: 16    Thống kê y sinh học               1     1         0
    # Group 1: Name (greedy to allow spaces), Group 2: Credits
    
    # Strategy: Look for the credit number column. 
    # Usually it's a float or int followed by two other numbers.
    # Pattern: Name <spaces> Credits <spaces> Theory <spaces> Practice
    
    pattern = re.compile(r'^\s*\d+\s+(.+?)\s+(\d+(\.\d+)?)\s+(\d+(\.\d+)?)\s+(\d+(\.\d+)?)')
    
    for line in lines:
        match = pattern.search(line)
        if match:
            # Check if it's a header line
            if "Tên môn học" in line or "Số tín chỉ" in line:
                continue
                
            name = match.group(1).strip()
            credits = match.group(2)
            
            # Clean up name (sometimes has leading dots or numbers if regex failed slightly)
            name = re.sub(r'^\.*\s*', '', name)
            
            norm_name = normalize_name(name)
            credits_map[norm_name] = float(credits)
            # print(f"Found: '{name}' -> {credits}")
            
    # Manual overrides/additions based on inspection if regex misses complex Multi-line
    # Looking at the file, most important ones seem to be captured.
    return credits_map

def update_sql_file(txt_path, sql_path, output_path):
    credits_map = parse_curriculum_txt(txt_path)
    print(f"Extracted {len(credits_map)} courses with credits.")
    
    with open(sql_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
        
    # Pattern to find INSERT values in SQL
    # ('Name', block_id, type_id, credits)
    # INSERT INTO Courses (name, knowledge_block_id, course_type_id, credits) VALUES 
    # ('Triết học Mác – LêNin', 1, 1, 3),
    
    # We will process line by line to be safe with regex replacement
    new_lines = []
    lines = sql_content.split('\n')
    
    # Regex for a value tuple: ('Name', ..., credits)
    # Matches: ('Name', 1, 1, 3) or ('Name', 1, 1, 3),
    tuple_pattern = re.compile(r"\('([^']+)',\s*\d+,\s*\d+,\s*(\d+(\.\d+)?)\)")
    
    # Regex for named column insert: (id, 'Name', ..., credits)
    # (200, 'Truyền nhiễm', 16, 1, 2),
    named_tuple_pattern = re.compile(r"\((\d+),\s*'([^']+)',\s*\d+,\s*\d+,\s*(\d+(\.\d+)?)\)")
    
    updated_count = 0
    
    for line in lines:
        new_line = line
        
        # Check for standard insert: ('Name', ...)
        match = tuple_pattern.search(line)
        if match:
            original_name = match.group(1)
            old_credits = match.group(2)
            norm_name = normalize_name(original_name)
            
            # Try exact match first
            if norm_name in credits_map:
                new_credits = credits_map[norm_name]
                if float(old_credits) != float(new_credits):
                    # Replace the credit value in the string
                    # We have to be careful not to replace other numbers.
                    # Reconstruct the tuple string
                    # Or just regex replace the specific match
                    # Valid pattern found: ('Name', x, y, OLD)
                    # We want: ('Name', x, y, NEW)
                    
                    # Construct regex specific to this line to replace only the credits at the end of tuple
                    # The match group 2 is the credits.
                    # We replace the last occurrence of old_credits before the closing paren
                    
                    # Safer: Rebuild the matched string
                    span = match.span()
                    full_match = match.group(0) # ('Name', 1, 1, 3)
                    
                    # Replace the last number
                    new_tuple = full_match.replace(f", {old_credits})", f", {new_credits})")
                    new_line = line.replace(full_match, new_tuple)
                    updated_count += 1
                    # print(f"Updated '{original_name}': {old_credits} -> {new_credits}")
            else:
                 # Try to match with "Thực hành" prefix removal if it's a practice course
                 # In SQL: 'Thực hành Tin học'
                 # In PDF: 'Thực hành Tin học' is usually there.
                 pass

        # Check for ID insert: (200, 'Name', ...)
        match_id = named_tuple_pattern.search(line)
        if match_id:
             original_name = match_id.group(2)
             old_credits = match_id.group(3)
             norm_name = normalize_name(original_name)
             
             if norm_name in credits_map:
                new_credits = credits_map[norm_name]
                if float(old_credits) != float(new_credits):
                    span = match_id.span()
                    full_match = match_id.group(0)
                    new_tuple = full_match.replace(f", {old_credits})", f", {new_credits})")
                    new_line = line.replace(full_match, new_tuple)
                    updated_count += 1
                    # print(f"Updated '{original_name}' (ID): {old_credits} -> {new_credits}")

        new_lines.append(new_line)
        
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
        
    print(f"Total updated lines: {updated_count}")

if __name__ == "__main__":
    update_sql_file("curriculum.txt", "curriculum_schema.sql", "curriculum_schema_updated.sql")
