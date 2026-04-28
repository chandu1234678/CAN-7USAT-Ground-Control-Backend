"""
Comprehensive system diagnostics
Run this to verify all components are working
"""

import sys
import struct
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")

def check_module(name, import_name=None):
    """Check if a module is installed"""
    import_name = import_name or name
    try:
        module = __import__(import_name)
        version = getattr(module, '__version__', 'unknown')
        print(f"✅ {name:20s} {version}")
        return True
    except ImportError:
        print(f"❌ {name:20s} NOT INSTALLED")
        return False

def main():
    """Run diagnostics"""
    print_header("GITAM CAN-7USAT SYSTEM DIAGNOSTICS")
    
    # Python version
    print(f"Python Version: {sys.version.split()[0]}")
    print(f"Platform: {sys.platform}")
    print(f"Architecture: {sys.maxsize > 2**32 and '64-bit' or '32-bit'}")
    
    # Core dependencies
    print_header("CORE DEPENDENCIES")
    all_ok = True
    all_ok &= check_module("FastAPI", "fastapi")
    all_ok &= check_module("Uvicorn", "uvicorn")
    all_ok &= check_module("Pydantic", "pydantic")
    all_ok &= check_module("WebSockets", "websockets")
    
    # Data processing
    print_header("DATA PROCESSING")
    all_ok &= check_module("NumPy", "numpy")
    all_ok &= check_module("Pandas", "pandas")
    all_ok &= check_module("SciPy", "scipy")
    
    # Machine learning
    print_header("MACHINE LEARNING")
    all_ok &= check_module("PyTorch", "torch")
    # scikit-learn imports as 'sklearn' not 'scikit-learn'
    sklearn_ok = check_module("scikit-learn", "sklearn")
    if not sklearn_ok:
        # Try alternative check
        try:
            import sklearn
            print(f"✅ scikit-learn (retry)  {sklearn.__version__}")
            sklearn_ok = True
        except:
            pass
    all_ok &= sklearn_ok
    
    # Database
    print_header("DATABASE")
    all_ok &= check_module("asyncpg", "asyncpg")
    all_ok &= check_module("SQLAlchemy", "sqlalchemy")
    
    # Testing
    print_header("TESTING")
    all_ok &= check_module("pytest", "pytest")
    all_ok &= check_module("httpx", "httpx")
    
    # Serial communication
    print_header("SERIAL COMMUNICATION")
    all_ok &= check_module("pyserial", "serial")
    all_ok &= check_module("pyserial-asyncio", "serial_asyncio")
    
    # Custom modules
    print_header("CUSTOM MODULES")
    try:
        from app.telemetry_decoder import TelemetryDecoder
        print("✅ TelemetryDecoder")
    except Exception as e:
        print(f"❌ TelemetryDecoder: {e}")
        all_ok = False
    
    try:
        from app.kalman_filter import KalmanFilter
        print("✅ KalmanFilter")
    except Exception as e:
        print(f"❌ KalmanFilter: {e}")
        all_ok = False
    
    try:
        from app.flight_state_machine import FlightStateMachine
        print("✅ FlightStateMachine")
    except Exception as e:
        print(f"❌ FlightStateMachine: {e}")
        all_ok = False
    
    try:
        from app.mock_data_generator import MockDataGenerator
        print("✅ MockDataGenerator")
    except Exception as e:
        print(f"❌ MockDataGenerator: {e}")
        all_ok = False
    
    try:
        from app.database import DatabaseManager
        print("✅ DatabaseManager")
    except Exception as e:
        print(f"❌ DatabaseManager: {e}")
        all_ok = False
    
    try:
        from app.models import TelemetryPacket, FlightState
        print("✅ Models (TelemetryPacket, FlightState)")
    except Exception as e:
        print(f"❌ Models: {e}")
        all_ok = False
    
    try:
        from app.config import settings
        print("✅ Configuration (Settings)")
    except Exception as e:
        print(f"❌ Configuration: {e}")
        all_ok = False
    
    # Struct format validation
    print_header("BINARY PACKET FORMAT")
    fmt = '<B 3x I B 3x f f f f f f f f B x'
    size = struct.calcsize(fmt)
    print(f"Format: {fmt}")
    print(f"Size: {size} bytes")
    print(f"Target: 46 bytes")
    if size == 46:
        print("✅ Packet format correct!")
    else:
        print(f"❌ Packet format wrong! Expected 46, got {size}")
        all_ok = False
    
    # File structure
    print_header("FILE STRUCTURE")
    required_files = [
        "app/__init__.py",
        "app/main.py",
        "app/models.py",
        "app/config.py",
        "app/telemetry_decoder.py",
        "app/mock_data_generator.py",
        "app/kalman_filter.py",
        "app/flight_state_machine.py",
        "app/database.py",
        "tests/__init__.py",
        "tests/test_telemetry_decoder.py",
        "requirements.txt",
        ".env",
        "run_server.bat",
        "static/websocket_test.html"
    ]
    
    for file in required_files:
        path = Path(file)
        if path.exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - MISSING")
            all_ok = False
    
    # Test execution
    print_header("RUNNING TESTS")
    import subprocess
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✅ All tests passed!")
            # Count passed tests
            passed = result.stdout.count(" PASSED")
            print(f"   {passed} tests passed")
        else:
            print("❌ Some tests failed!")
            print(result.stdout[-500:])  # Last 500 chars
            all_ok = False
    except Exception as e:
        print(f"❌ Could not run tests: {e}")
        all_ok = False
    
    # Final summary
    print_header("DIAGNOSTIC SUMMARY")
    if all_ok:
        print("✅ ALL CHECKS PASSED!")
        print("\nSystem is ready for:")
        print("  • Frontend development")
        print("  • Hardware integration")
        print("  • Production deployment")
        print("\nNext steps:")
        print("  1. Start server: backend\\run_server.bat")
        print("  2. Open browser: http://localhost:8000/")
        print("  3. Test WebSocket streaming")
        print("  4. Begin frontend development")
    else:
        print("❌ SOME CHECKS FAILED")
        print("\nPlease review the errors above and fix them.")
        print("Run this diagnostic again after fixing.")
    
    print("\n" + "=" * 60)
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
