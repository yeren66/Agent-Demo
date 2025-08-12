#!/usr/bin/env python3
"""
GitCode configuration test script
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_gitcode_config():
    """测试 GitCode 配置"""
    print("\n=== GitCode 配置检查 ===")
    
    # 基本配置
    platform = os.getenv('PLATFORM', 'github')
    gitcode_token = os.getenv('GITCODE_TOKEN')
    gitcode_base = os.getenv('GITCODE_BASE', 'https://api.gitcode.com/api/v5')
    webhook_secret = os.getenv('WEBHOOK_SECRET')
    
    print(f"📍 平台: {platform}")
    print(f"🌐 API Base: {gitcode_base}")
    print(f"✅ GitCode Token: {'已配置' if gitcode_token else '❌ 未配置'}")
    print(f"✅ Webhook Secret: {'已配置' if webhook_secret else '❌ 未配置'}")
    
    # GitCode App 配置
    print("\n--- GitCode App 配置 (用于 @mention) ---")
    gitcode_app_config = {
        'GITCODE_APP_ID': os.getenv('GITCODE_APP_ID'),
        'GITCODE_APP_SECRET': os.getenv('GITCODE_APP_SECRET'),
        'GITCODE_PRIVATE_TOKEN': os.getenv('GITCODE_PRIVATE_TOKEN'),
        'GITCODE_APP_NAME': os.getenv('GITCODE_APP_NAME', 'agent'),
    }
    
    for key, value in gitcode_app_config.items():
        status = '✅ 已配置' if value else '❌ 未配置'
        if key in ['GITCODE_APP_SECRET', 'GITCODE_PRIVATE_TOKEN'] and value:
            display_value = value[:8] + '...'
        else:
            display_value = value or '未设置'
        print(f"{key}: {status} ({display_value})")
    
    # 检查配置完整性
    app_configured = bool(gitcode_app_config['GITCODE_APP_ID'] and gitcode_app_config['GITCODE_APP_SECRET'])
    private_token_configured = bool(gitcode_app_config['GITCODE_PRIVATE_TOKEN'])
    
    if app_configured or private_token_configured:
        print("🎉 GitCode App 配置完整 - 支持 @mention 功能")
        return True
    elif gitcode_token:
        print("⚠️  使用 Personal Access Token - @mention 功能受限")
        print("💡 建议：配置 GitCode App 或 Private Token")
        return True
    else:
        print("❌ 需要配置 GitCode 认证信息")
        return False

async def test_gitcode_api():
    """测试 GitCode API 连接"""
    print("\n=== GitCode API 测试 ===")
    
    try:
        # 测试 GitCode API 认证
        sys.path.append('.')
        from worker.gitcode_app_auth import GitCodeAppAuth
        
        auth = GitCodeAppAuth()
        if auth.is_app_available():
            print("✅ GitCode App 认证可用")
            # 测试认证
            if await asyncio.get_event_loop().run_in_executor(None, auth.test_authentication):
                print("✅ GitCode 认证测试成功")
                return True
            else:
                print("❌ GitCode 认证测试失败")
                return False
        else:
            print("❌ GitCode App 认证不可用")
            return False
            
    except ImportError as e:
        print(f"❌ 无法导入 GitCode 认证模块: {e}")
        return False
    except Exception as e:
        print(f"❌ GitCode API 测试失败: {e}")
        return False

def test_llm_config():
    """测试 LLM 配置"""
    print("\n=== LLM 配置检查 ===")
    
    llm_base_url = os.getenv('LLM_BASE_URL')
    llm_api_key = os.getenv('LLM_API_KEY')
    llm_model = os.getenv('LLM_MODEL', 'gpt-4o-mini')
    
    print(f"🌐 LLM Base URL: {llm_base_url or '❌ 未配置'}")
    print(f"🔑 LLM API Key: {'✅ 已配置' if llm_api_key else '❌ 未配置'}")
    print(f"🤖 LLM Model: {llm_model}")
    
    return bool(llm_base_url and llm_api_key)

def test_network():
    """测试网络配置"""
    print("\n=== 网络配置检查 ===")
    
    http_proxy = os.getenv('HTTP_PROXY')
    https_proxy = os.getenv('HTTPS_PROXY')
    
    print(f"🌐 HTTP Proxy: {http_proxy or '未配置'}")
    print(f"🔒 HTTPS Proxy: {https_proxy or '未配置'}")
    
    # 测试网络连通性
    try:
        import requests
        gitcode_base = os.getenv('GITCODE_BASE', 'https://api.gitcode.com/api/v5')
        
        proxies = {}
        if http_proxy:
            proxies['http'] = http_proxy
        if https_proxy:
            proxies['https'] = https_proxy
        
        response = requests.get(f"{gitcode_base}/user", timeout=10, proxies=proxies)
        print(f"✅ GitCode API 连通性测试: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ GitCode API 连通性测试失败: {e}")
        return False

def main():
    print("🧪 GitCode Bug Fix Agent 配置测试")
    print("=" * 50)
    
    # 检查平台配置
    platform = os.getenv('PLATFORM', 'github')
    if platform.lower() != 'gitcode':
        print(f"⚠️  当前平台设置为: {platform}")
        print("💡 要测试 GitCode，请设置 PLATFORM=gitcode")
        print()
    
    results = []
    
    # 运行各项测试
    results.append(("GitCode 配置", test_gitcode_config()))
    results.append(("LLM 配置", test_llm_config()))
    results.append(("网络连通性", test_network()))
    
    # 异步测试
    try:
        api_result = asyncio.run(test_gitcode_api())
        results.append(("GitCode API", api_result))
    except Exception as e:
        print(f"❌ GitCode API 测试出错: {e}")
        results.append(("GitCode API", False))
    
    # 汇总结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    
    all_passed = True
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 所有测试通过！GitCode Bug Fix Agent 已准备就绪")
        print("\n下一步:")
        print("1. 启动服务: python start_local.py")
        print("2. 设置 webhook URL")
        print("3. 在 Issue 中测试 @agent 提及")
    else:
        print("⚠️  部分测试未通过，请检查配置")
        print("\n建议:")
        print("1. 检查 .env 文件中的 GitCode 配置")
        print("2. 确保 GitCode Token 或 App 认证正确配置")
        print("3. 检查网络连接和代理设置")

if __name__ == "__main__":
    main()
