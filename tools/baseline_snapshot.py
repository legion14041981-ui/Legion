#!/usr/bin/env python3
"""
Baseline Snapshot Tool - создание immutable snapshots архитектуры.

Использование:
    python tools/baseline_snapshot.py --out artifacts/snapshots/baseline-$(date +%s).json
"""

import sys
import json
import argparse
import hashlib
from datetime import datetime
from pathlib import Path
import subprocess

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


def get_git_info():
    """Получить информацию о Git."""
    try:
        branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).decode().strip()
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()
        return {'branch': branch, 'commit': commit}
    except:
        return {'branch': 'unknown', 'commit': 'unknown'}


def scan_directory_structure(base_path: Path):
    """Сканировать структуру проекта."""
    structure = {}
    
    # Пройти по src/legion
    legion_path = base_path / 'src' / 'legion'
    if legion_path.exists():
        for module_dir in legion_path.iterdir():
            if module_dir.is_dir() and not module_dir.name.startswith('_'):
                files = list(module_dir.glob('*.py'))
                structure[module_dir.name] = {
                    'file_count': len(files),
                    'files': [f.name for f in files]
                }
    
    return structure


def count_lines_of_code(base_path: Path):
    """Подсчитать LOC."""
    total_loc = 0
    src_path = base_path / 'src'
    
    if src_path.exists():
        for py_file in src_path.rglob('*.py'):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    total_loc += len(f.readlines())
            except:
                pass
    
    return total_loc


def create_snapshot(output_file: str):
    """Создать baseline snapshot."""
    base_path = Path(__file__).parent.parent
    git_info = get_git_info()
    
    snapshot = {
        'snapshot_id': f"baseline-{int(datetime.utcnow().timestamp())}",
        'timestamp': datetime.utcnow().isoformat(),
        'repository': 'legion14041981-ui/Legion',
        'branch': git_info['branch'],
        'commit_sha': git_info['commit'],
        'semantic_hash': hashlib.sha256(git_info['commit'].encode()).hexdigest()[:16],
        
        'architecture': {
            'version': '4.0.0-neuro',
            'modules': scan_directory_structure(base_path),
            'total_loc': count_lines_of_code(base_path)
        },
        
        'metadata': {
            'created_by': 'baseline_snapshot.py',
            'python_version': sys.version.split()[0]
        }
    }
    
    # Сохранить
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(snapshot, f, indent=2)
    
    print(f"✅ Baseline snapshot created: {output_file}")
    print(f"   Branch: {git_info['branch']}")
    print(f"   Commit: {git_info['commit'][:8]}")
    print(f"   LOC: {snapshot['architecture']['total_loc']}")


def main():
    parser = argparse.ArgumentParser(description='Create baseline architecture snapshot')
    parser.add_argument('--out', required=True, help='Output JSON file')
    
    args = parser.parse_args()
    create_snapshot(args.out)


if __name__ == '__main__':
    main()
