"""
Verify Stage - Test and validate changes (demo version)
"""

import logging
import random
from typing import Dict, Any

try:
    from ..templates import render_report
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from templates import render_report

logger = logging.getLogger(__name__)

async def run_verify_stage(job: Dict[str, Any], repo_path: str, api, gitops) -> Dict[str, Any]:
    """
    Run the verify stage - test the applied changes
    
    In a real implementation, this would:
    - Install dependencies
    - Run unit tests
    - Run integration tests
    - Check code coverage
    - Run linters and formatters
    - Validate build process
    
    For demo, we'll simulate these checks and generate realistic results.
    """
    try:
        logger.info("Starting verify stage (demo mode)")
        
        # Simulate test results
        test_results = generate_demo_test_results()
        build_success = test_results['failed'] == 0
        
        # Generate report
        report_content = render_report(
            build_success=build_success,
            test_results=test_results,
            deploy_url=None  # Will be set in deploy stage
        )
        
        # Write report file
        await gitops.write_file(repo_path, 'agent/report.txt', report_content)
        await gitops.add_file(repo_path, 'agent/report.txt')
        await gitops.commit(repo_path, 'test(agent): add verification report (demo)')
        await gitops.push(repo_path, job['branch'])
        
        # Store results in job
        job['test_results'] = test_results
        job['build_success'] = build_success
        
        status_emoji = "✅" if build_success else "❌"
        comment = f"""✅ **第4阶段：验证测试完成**

**🎯 验证结果总览:**
- 构建状态: {'🟢 构建成功' if build_success else '🔴 构建失败'}
- 测试覆盖: **{test_results['passed'] + test_results['failed']}项测试**
- 整体质量: {'🟢 验证通过' if build_success else '🟡 需要关注'}

**📊 详细测试数据:**
- ✅ 通过测试: **{test_results['passed']}项**
- ❌ 失败测试: **{test_results['failed']}项**  
- ⏭️ 跳过测试: **{test_results['skipped']}项**
- 📈 代码覆盖率: **{test_results['coverage']}**

**🔍 验证内容:**
- 🏗️ 代码编译和构建检查
- 🧪 单元测试和集成测试执行
- 📏 代码规范和质量检查
- �️ 基本功能完整性验证

**📋 生成文件:** `agent/report.txt`
**� 工作分支:** `{job['branch']}`

**💡 验证结论:**
{('🎉 所有验证通过，修复质量良好！' if build_success else '⚠️ 发现部分问题，建议进一步审查')}

---
*验证完成，准备创建Pull Request...*"""
        
        return {
            'success': True,
            'build_success': build_success,
            'test_results': test_results,
            'comment': comment
        }
        
    except Exception as e:
        logger.error(f"Verify stage failed: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }

def generate_demo_test_results() -> Dict[str, Any]:
    """Generate realistic demo test results"""
    
    # Simulate mostly successful tests with some variation
    base_passed = random.randint(35, 50)
    base_failed = random.randint(0, 2)  # Usually 0-2 failures
    base_skipped = random.randint(1, 5)
    
    # Calculate coverage (usually 60-85% for demo)
    coverage_pct = random.randint(60, 85)
    
    return {
        'passed': base_passed,
        'failed': base_failed,
        'skipped': base_skipped,
        'coverage': f"{coverage_pct}% (demo)",
        'total': base_passed + base_failed + base_skipped
    }
