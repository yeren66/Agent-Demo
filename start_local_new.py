#!/usr/bin/env python3
"""
Bug Fix Agent - Local Development Server
启动本地开发服务器
"""

import os
import sys
import signal
from pathlib import Path

def load_env_file():
    """Load environment variables from .env file"""
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        print("📋 加载环境配置...")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print("✅ 环境配置加载完成")
    else:
        print("⚠️  未找到 .env 文件，使用默认配置")

def check_config():
    """Check configuration"""
    print("\n📊 配置检查...")
    
    platform = os.getenv('PLATFORM', 'github')
    github_token = os.getenv('GITHUB_TOKEN')
    github_app_id = os.getenv('GITHUB_APP_ID')
    webhook_secret = os.getenv('WEBHOOK_SECRET')
    
    print(f"🔧 平台: {platform}")
    print(f"🔑 GitHub Token: {'已配置' if github_token else '未配置'}")
    print(f"🤖 GitHub App ID: {'已配置' if github_app_id else '未配置'}")
    print(f"🔐 Webhook Secret: {'已配置' if webhook_secret else '未配置'}")
    
    if github_app_id:
        app_name = os.getenv('GITHUB_APP_NAME', 'your-app-name')
        print(f"✨ 支持 @{app_name} 提及")
    elif github_token:
        print("⚠️  仅支持 Personal Token 认证")
    else:
        print("❌ 需要配置认证信息")
        return False
    
    return True

def start_server():
    """Start the FastAPI server"""
    print("\n🚀 启动 Bug Fix Agent 服务...")
    print("   地址: http://localhost:8080")
    print("   健康检查: http://localhost:8080/health")
    print("   Webhook: http://localhost:8080/api/webhook")
    print("\n💡 提示:")
    print("   - 使用 Ctrl+C 停止服务")
    print("   - 使用 ngrok 暴露到公网: ./scripts/ngrok.sh")
    print("   - 运行测试: python test_github_app.py")
    print("\n" + "="*50)
    
    # Change to gateway directory and start uvicorn
    gateway_dir = Path(__file__).parent / 'gateway'
    
    try:
        os.chdir(gateway_dir)
        # Use exec to replace the current process, allowing proper signal handling
        os.execvp('uvicorn', ['uvicorn', 'app:app', '--host', '0.0.0.0', '--port', '8080', '--reload'])
    except FileNotFoundError:
        print("❌ uvicorn not found. Install with: pip install uvicorn")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

def main():
    """Main entry point"""
    print("🤖 Bug Fix Agent - GitHub App")
    print("="*50)
    
    # Load environment
    load_env_file()
    
    # Check configuration
    if not check_config():
        print("\n❌ 配置检查失败")
        print("💡 请参考 GITHUB_APP_SETUP.md 进行配置")
        sys.exit(1)
    
    # Start server
    start_server()

if __name__ == '__main__':
    main()
