"""
AWS Skills Web - テストスイート

このディレクトリにはすべてのテストが含まれています。
- Unit tests: 外部依存なしのテスト
- Integration tests: データベース等を含むテスト
- Security tests: セキュリティ関連のテスト
"""

import os
import sys

# モジュールパスを設定
test_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(test_dir)
sys.path.insert(0, project_root)
