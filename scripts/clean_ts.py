import re
import glob
import os

def clean_ts_file(file_path):
    print(f"Processing: {os.path.basename(file_path)}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 1. Fix XML declaration (previously changed to single quotes)
    content = content.replace("<?xml version='1.0' encoding='utf-8'?>", '<?xml version="1.0" encoding="utf-8"?>')
    
    # 2. Fix the extra space in self-closing tags we added before (only if any left)
    # We only target location tags to be safe
    content = re.sub(r'(<location[^>]+) />', r'\1/>', content)
    
    # 3. Restore any unescaped entities that were touched by previous runs (approximation)
    # Qt .ts files usually prefer &apos; for ' in source and translation nodes
    # We will search for single quotes inside <source> and <translation> tags and restore &apos;
    # (Only if they are not part of an attribute)
    
    def restore_entities(match):
        tag_content = match.group(2)
        restored = tag_content.replace("'", "&apos;")
        return f"<{match.group(1)}>{restored}</{match.group(1)}>"
    
    content = re.compile(r'<(source|translation)([^>]*)>(.*?)</\1>', re.DOTALL).sub(
        lambda m: f"<{m.group(1)}{m.group(2)}>{m.group(3).replace("'", "&apos;")}</{m.group(1)}>", content)

    # 4. Correct unfinished tags (previously changed from <tag></tag> to <tag/>)
    # Qt linguist prefers <translation type="unfinished"></translation>
    content = re.sub(r'<translation type="unfinished"/>', '<translation type="unfinished"></translation>', content)

    # 5. Remove obsolete message blocks
    # We look for <message> ... <translation type="obsolete"> ... </message>
    # We use a pattern that matches the whole <message> block including potential surrounding whitespace
    pattern = re.compile(r'\n?\s*<message[^>]*>(?:(?!</message>).)*?<translation[^>]*type="obsolete"[^>]*>.*?</message>', re.DOTALL)
    
    new_content, count = pattern.subn('', content)
    
    if new_content != original_content:
        # Use CRLF as it's common on Windows and likely what these files use
        with open(file_path, 'w', encoding='utf-8', newline='\r\n') as f:
            f.write(new_content)
        if count > 0:
            print(f"  Done. Removed {count} obsolete entries and fixed formatting.")
        else:
            print("  Done. Restored original formatting (quotes, entities, etc).")
    else:
        print("  No changes needed.")

def run():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    i18n_dir = os.path.join(script_dir, '..', 'i18n')
    ts_files = glob.glob(os.path.join(i18n_dir, "*.ts"))
    
    for ts_file in ts_files:
        clean_ts_file(ts_file)

if __name__ == "__main__":
    run()
