#!/usr/bin/env python
"""
テスト実行ユーティリティ

使用方法:
  python tests/run_tests.py              # すべてのテスト実行
  python tests/run_tests.py --unit       # ユニットテストのみ
  python tests/run_tests.py --coverage   # カバレッジ付き実行
  python tests/run_tests.py --security   # セキュリティテストのみ
  python tests/run_tests.py --fast       # 遅いテストを除外
"""

import subprocess
import sys
import argparse
from pathlib import Path


def run_command(cmd, description=None):
    """コマンドを実行して結果を表示"""
    if description:
        print(f"\n{'='*60}")
        print(f"🧪 {description}")
        print(f"{'='*60}\n")
    
    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description='テスト実行ユーティリティ')
    parser.add_argument('--unit', action='store_true', help='ユニットテストのみ')
    parser.add_argument('--integration', action='store_true', help='統合テストのみ')
    parser.add_argument('--security', action='store_true', help='セキュリティテストのみ')
    parser.add_argument('--coverage', action='store_true', help='カバレッジ付き実行')
    parser.add_argument('--fast', action='store_true', help='遅いテストを除外')
    parser.add_argument('--verbose', '-v', action='store_true', help='詳細出力')
    parser.add_argument('--html', action='store_true', help='HTML レポート生成')
    parser.add_argument('--parallel', '-n', type=int, help='並列実行スレッド数')
    parser.add_argument('--file', '-f', type=str, help='特定のテストファイル')
    parser.add_argument('--lf', action='store_true', help='最後に失敗したテスト')
    parser.add_argument('--failed-first', action='store_true', help='失敗を優先実行')
    
    args = parser.parse_args()
    
    # コマンド構築
    cmd_parts = ['pytest']
    
    # マーカーフィルタリング
    if args.unit:
        cmd_parts.append('-m unit')
    elif args.integration:
        cmd_parts.append('-m integration')
    elif args.security:
        cmd_parts.append('-m security')
    
    # 遅いテスト除外
    if args.fast:
        if '-m' in cmd_parts:
            # マーカーがある場合は修正
            idx = cmd_parts.index('-m')
            cmd_parts[idx + 1] += ' and not slow'
        else:
            cmd_parts.extend(['-m', 'not slow'])
    
    # 詳細出力
    if args.verbose:
        cmd_parts.append('-vv')
    else:
        cmd_parts.append('-v')
    
    # カバレッジ
    if args.coverage:
        cmd_parts.extend([
            '--cov=modules',
            '--cov=tools',
            '--cov-report=term-missing'
        ])
        if args.html:
            cmd_parts.append('--cov-report=html')
    
    # 並列実行
    if args.parallel:
        cmd_parts.extend(['-n', str(args.parallel)])
    
    # 最後に失敗したテスト
    if args.lf:
        cmd_parts.append('--lf')
    if args.failed_first:
        cmd_parts.append('--ff')
    
    # ファイル指定
    if args.file:
        cmd_parts.append(f'tests/{args.file}')
    
    cmd = ' '.join(cmd_parts)
    
    # テスト実行
    success = run_command(cmd, "テスト実行")
    
    # HTML レポート生成メッセージ
    if args.coverage and args.html:
        print("\n" + "="*60)
        print("📊 HTML カバレッジレポート生成完了")
        print("   htmlcov/index.html をブラウザで開いてください")
        print("="*60 + "\n")
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
