import os
import fnmatch

def load_wrenchignore(root):
    patterns = []
    try:
        with open(os.path.join(root, ".wrenchignore"), 'r', encoding="utf8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                patterns.append(line)
    except FileNotFoundError:
        pass
    return patterns

def is_ignored(filepath, patterns):
    filename = os.path.basename(filepath)
    for pattern in patterns:
        if pattern.endswith('/'):
            if pattern.rstrip('/') in filepath.split(os.sep):
                return True
        elif fnmatch.fnmatch(filename, pattern):
            return True
    return False
