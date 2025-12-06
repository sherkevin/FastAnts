#!/usr/bin/env python3
"""
测试修改 fnames 配置后的行为
验证 "/workspaces/{workflow_name}/*" 格式是否能解决问题
"""

import os
import tempfile
import shutil
from pathlib import Path

def create_test_environment():
    """创建测试环境，模拟实际的项目结构"""
    test_root = Path(tempfile.mkdtemp(prefix="fnames_test_"))

    # 创建完整的项目结构
    project_root = test_root / "project"
    project_root.mkdir()

    # 创建 workspaces 结构
    workspaces_dir = project_root / "workspaces"
    workspaces_dir.mkdir()

    # 创建工作流目录
    workflow_dir = workspaces_dir / "hulatang"
    workflow_dir.mkdir()

    # 创建 collab 目录（工作流级别）
    collab_dir = workflow_dir / "collab"
    collab_dir.mkdir()

    # 创建 agent 目录
    client_dir = workflow_dir / "client"
    client_dir.mkdir()
    supplier_dir = workflow_dir / "supplier"
    supplier_dir.mkdir()

    # 创建测试文件
    (collab_dir / "test_file.txt").write_text("This is a test file in collab")
    (collab_dir / "another_file.md").write_text("# Another test file")
    (client_dir / "client_file.txt").write_text("Client specific file")
    (supplier_dir / "supplier_file.txt").write_text("Supplier specific file")

    # 创建根目录的collab（模拟当前的问题）
    root_collab = project_root / "collab"
    root_collab.mkdir()
    (root_collab / "root_file.txt").write_text("This should NOT be accessible")

    return test_root, project_root

def test_fnames_patterns():
    """测试不同的 fnames 配置模式"""

    print("🔍 测试 fnames 配置模式")
    print("=" * 60)

    test_root, project_root = create_test_environment()

    try:
        workflow_name = "hulatang"
        collab_dir = project_root / "workspaces" / workflow_name / "collab"

        # 测试不同的 fnames 模式
        fnames_patterns = [
            {
                "name": "当前配置（目录路径）",
                "pattern": [str(collab_dir)],  # ["workspaces/hulatang/collab"]
                "expected_files": ["test_file.txt", "another_file.md"],
                "should_skip": True  # aider 会跳过目录
            },
            {
                "name": "建议配置（通配符）",
                "pattern": [f"{collab_dir}/*"],  # ["workspaces/hulatang/collab/*"]
                "expected_files": ["test_file.txt", "another_file.md"],
                "should_skip": False
            },
            {
                "name": "具体文件列表",
                "pattern": [
                    str(collab_dir / "test_file.txt"),
                    str(collab_dir / "another_file.md")
                ],
                "expected_files": ["test_file.txt", "another_file.md"],
                "should_skip": False
            },
            {
                "name": "递归通配符",
                "pattern": [f"{collab_dir}/**/*"],
                "expected_files": ["test_file.txt", "another_file.md"],
                "should_skip": False
            }
        ]

        for pattern_config in fnames_patterns:
            print(f"\n🧪 测试模式: {pattern_config['name']}")
            print(f"   fnames: {pattern_config['pattern']}")

            # 模拟 aider 的文件发现逻辑
            discovered_files = []

            for fnames_item in pattern_config['pattern']:
                path = Path(fnames_item)

                if path.is_file():
                    # 直接是文件
                    discovered_files.append(path.name)
                    print(f"   📄 发现文件: {path.name}")

                elif path.is_dir():
                    # 是目录，检查是否会被跳过
                    if pattern_config['should_skip']:
                        print(f"   ⏭️  跳过目录: {path.name} (不是普通文件)")
                    else:
                        # 目录但不应该被跳过（这不应该发生）
                        print(f"   ⚠️  意外访问目录: {path.name}")

                elif "*" in str(path):
                    # 通配符模式
                    import glob
                    matches = glob.glob(str(path), recursive="**" in str(path))
                    for match in matches:
                        match_path = Path(match)
                        if match_path.is_file():
                            discovered_files.append(match_path.name)
                            print(f"   📄 通配符匹配: {match_path.name}")

                else:
                    print(f"   ❓ 未知路径类型: {path}")

            # 验证发现的文件
            expected = set(pattern_config['expected_files'])
            discovered = set(discovered_files)

            print(f"   ✅ 期望文件: {sorted(expected)}")
            print(f"   📋 发现文件: {sorted(discovered)}")

            if expected == discovered:
                print("   🎉 文件匹配正确")
            else:
                missing = expected - discovered
                extra = discovered - expected
                if missing:
                    print(f"   ❌ 缺失文件: {sorted(missing)}")
                if extra:
                    print(f"   ⚠️  多余文件: {sorted(extra)}")

    finally:
        shutil.rmtree(test_root, ignore_errors=True)

def analyze_real_scenario():
    """分析实际场景中的配置"""

    print("\n🎯 实际场景分析")
    print("=" * 60)

    # 模拟实际项目的配置
    project_root = Path("/mnt/d/Brains/Career Brain/Infra Base/Large Language Model/Engineering Application/Agent/hello-agents/trying/langgraph")
    workflow_name = "hulatang"
    collab_dir = project_root / "workspaces" / workflow_name / "collab"

    print(f"项目根目录: {project_root}")
    print(f"工作流名称: {workflow_name}")
    print(f"Collab目录: {collab_dir}")

    # 当前配置
    current_fnames = [str(collab_dir)]
    print("\n🔧 当前配置:")
    print(f"   fnames = {current_fnames}")

    # 检查当前collab目录的内容
    if collab_dir.exists():
        files = list(collab_dir.glob("*"))
        print(f"   📂 Collab目录内容: {[f.name for f in files]}")
    else:
        print("   ❌ Collab目录不存在")

    # 建议的配置
    suggested_fnames = [f"{collab_dir}/*"]
    print("\n💡 建议配置:")
    print(f"   fnames = {suggested_fnames}")

    # 模拟建议配置的行为
    print("\n🔮 建议配置模拟:")
    import glob
    matches = glob.glob(suggested_fnames[0])
    matched_files = [Path(f).name for f in matches if Path(f).is_file()]
    print(f"   📄 将匹配的文件: {matched_files}")

    # 分析效果
    print("\n📊 配置对比:")
    print("   当前配置问题:")
    print("   - fnames包含目录路径")
    print("   - Aider跳过目录，不建立文件索引")
    print("   - 相对路径解析容易出错")
    print()
    print("   建议配置优势:")
    print("   - 使用通配符明确指定文件")
    print("   - Aider能正确索引所有文件")
    print("   - 避免目录跳过问题")

def test_path_resolution():
    """测试路径解析行为"""

    print("\n🔬 路径解析测试")
    print("=" * 60)

    # 模拟实际场景
    project_root = Path("/mnt/d/Brains/Career Brain/Infra Base/Large Language Model/Engineering Application/Agent/hello-agents/trying/langgraph")
    workflow_name = "hulatang"

    # 建议的fnames配置
    collab_pattern = f"{project_root}/workspaces/{workflow_name}/*"

    print(f"建议的fnames模式: {collab_pattern}")

    # 模拟文件匹配
    import glob
    matches = glob.glob(collab_pattern)
    print(f"匹配的文件: {[Path(f).name for f in matches if Path(f).is_file()]}")

    # 测试相对路径解析
    print("\n🔗 相对路径解析:")
    print("   当prompt中提到 'collab/' 时:")
    print("   - 在agent工作目录中: workspaces/hulatang/supplier/collab/")
    print("   - 软链接指向: workspaces/hulatang/collab/")
    print("   - 实际可访问: 通过软链接访问工作流collab目录")

    print("\n✅ 预期效果:")
    print("   - Agent只能访问工作流collab目录的文件")
    print("   - 避免访问根目录或其他工作流的collab")
    print("   - 文件创建位置正确")

if __name__ == "__main__":
    test_fnames_patterns()
    analyze_real_scenario()
    test_path_resolution()

    print("\n" + "=" * 60)
    print("📋 测试完成")
    print("建议修改 fnames 为 '/workspaces/{workflow_name}/*' 格式")
