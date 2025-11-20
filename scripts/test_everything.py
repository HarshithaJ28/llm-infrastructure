"""
Comprehensive test script to verify all components are working.
"""

import requests
import subprocess
import sys
import time
from pathlib import Path

def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def check_docker_services():
    """Check if Docker services are running."""
    print_section("1. Checking Docker Services")
    
    try:
        result = subprocess.run(
            ['docker', 'ps', '--format', '{{.Names}}'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        services = result.stdout.strip().split('\n')
        services = [s for s in services if s]
        
        required = ['zookeeper', 'kafka', 'ollama-server']
        running = []
        missing = []
        
        for service in required:
            if service in services:
                print(f"  [OK] {service} - Running")
                running.append(service)
            else:
                print(f"  [FAIL] {service} - Not running")
                missing.append(service)
        
        if missing:
            print(f"\n  [WARN] Missing services: {', '.join(missing)}")
            print("  Start with: docker compose up -d")
            return False
        
        return True
        
    except FileNotFoundError:
        print("  [FAIL] Docker not found. Is Docker Desktop running?")
        return False
    except Exception as e:
        print(f"  [FAIL] Error checking Docker: {e}")
        return False

def check_kafka():
    """Check if Kafka is accessible."""
    print_section("2. Checking Kafka")
    
    try:
        from kafka import KafkaProducer
        producer = KafkaProducer(
            bootstrap_servers=['localhost:9092'],
            value_serializer=lambda v: v,
            request_timeout_ms=5000
        )
        producer.close()
        print("  [OK] Kafka is accessible on localhost:9092")
        return True
    except ImportError:
        print("  [FAIL] kafka-python not installed. Run: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"  [FAIL] Kafka not accessible: {e}")
        print("  Make sure Kafka is running: docker compose up -d kafka")
        return False

def check_ollama():
    """Check if Ollama is running."""
    print_section("3. Checking Ollama")
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"  [OK] Ollama is running on localhost:11434")
            if models:
                print(f"  [OK] Models available: {len(models)}")
                for model in models[:3]:  # Show first 3
                    print(f"     - {model.get('name', 'unknown')}")
            else:
                print("  [WARN] No models installed. Run: python scripts/setup_ollama.py --model llama2")
            return True
        else:
            print(f"  [FAIL] Ollama returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("  [FAIL] Ollama not accessible. Is it running?")
        print("  Start with: docker compose up -d ollama")
        return False
    except Exception as e:
        print(f"  [FAIL] Error checking Ollama: {e}")
        return False

def check_compliance_api():
    """Check if Compliance API is running."""
    print_section("4. Checking Compliance API")
    
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            print("  [OK] Compliance API is running on localhost:5000")
            
            # Check statistics
            try:
                stats_response = requests.get("http://localhost:5000/api/compliance/statistics", timeout=5)
                if stats_response.status_code == 200:
                    stats = stats_response.json()
                    print(f"  [OK] Audit logs: {stats.get('total_requests', 0)} requests logged")
            except:
                pass
            
            return True
        else:
            print(f"  [FAIL] Compliance API returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("  [FAIL] Compliance API not running")
        print("  Start with: python src/compliance_api.py")
        return False
    except Exception as e:
        print(f"  [FAIL] Error checking Compliance API: {e}")
        return False

def check_audit_database():
    """Check if audit database exists."""
    print_section("5. Checking Audit Database")
    
    db_path = Path('audit_logs.db')
    if db_path.exists():
        print(f"  [OK] Audit database exists: {db_path}")
        
        # Check size
        size_kb = db_path.stat().st_size / 1024
        print(f"  [OK] Database size: {size_kb:.2f} KB")
        
        return True
    else:
        print("  [WARN] Audit database not found (will be created on first use)")
        return True  # Not an error, will be created

def test_end_to_end():
    """Test end-to-end pipeline."""
    print_section("6. Testing End-to-End Pipeline")
    
    print("  To test the full pipeline:")
    print("     1. Terminal 1: python src/kafka_llm_processor.py")
    print("     2. Terminal 2: python src/test_producer.py --count 1")
    print("     3. Terminal 3: python src/test_consumer.py --max-messages 1")
    print("     4. Terminal 4: python src/test_compliance_api.py")
    
    return True

def main():
    """Run all checks."""
    print("\n" + "=" * 60)
    print("  LLM Infrastructure - System Check")
    print("=" * 60)
    
    results = {
        'docker': check_docker_services(),
        'kafka': check_kafka(),
        'ollama': check_ollama(),
        'compliance_api': check_compliance_api(),
        'audit_db': check_audit_database(),
        'e2e': test_end_to_end()
    }
    
    # Summary
    print_section("Summary")
    
    all_good = all([
        results['docker'],
        results['kafka'],
        results['ollama']
    ])
    
    if all_good:
        print("  [OK] Core services are running!")
        print("\n  Next steps:")
        print("    1. Start processor: python src/kafka_llm_processor.py")
        print("    2. Send test data: python src/test_producer.py --count 3")
        print("    3. View results: python src/test_consumer.py")
        print("    4. Query audit logs: python src/test_compliance_api.py")
    else:
        print("  [WARN] Some services are not running.")
        print("\n  Quick fixes:")
        if not results['docker']:
            print("    - Start Docker services: docker compose up -d")
        if not results['kafka']:
            print("    - Install dependencies: pip install -r requirements.txt")
        if not results['ollama']:
            print("    - Start Ollama: docker compose up -d ollama")
            print("    - Pull model: python scripts/setup_ollama.py --model llama2")
    
    if results['compliance_api']:
        print("\n  [OK] Compliance API is running - audit logs are accessible!")
    else:
        print("\n  [WARN] Compliance API not running (optional but recommended)")
        print("    Start with: python src/compliance_api.py")
    
    return 0 if all_good else 1

if __name__ == '__main__':
    sys.exit(main())

