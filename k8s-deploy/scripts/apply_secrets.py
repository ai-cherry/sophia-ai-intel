import base64
import yaml
import os
import subprocess
import tempfile

SECRET_FILES = [
    "k8s-deploy/secrets/database-secrets.yaml",
    "k8s-deploy/secrets/llm-secrets.yaml",
    "k8s-deploy/secrets/infrastructure-secrets.yaml",
    "k8s-deploy/secrets/business-secrets.yaml",
    "k8s-deploy/secrets/tls-secrets.yaml", # Include TLS secrets to be created dynamically
]

NAMESPACE = "sophia"

def log_info(message):
    print(f"[INFO] {message}")

def log_warning(message):
    print(f"[WARNING] {message}")

def log_error(message):
    print(f"[ERROR] {message}")

def apply_secrets_programmatically():
    log_info("🔐 Programmatically applying granular Kubernetes secrets...")

    for file_path in SECRET_FILES:
        if not os.path.exists(file_path):
            log_warning(f"Skipping {file_path}: File not found.")
            continue

        with open(file_path, 'r') as f:
            try:
                yaml_documents = list(yaml.safe_load_all(f))
            except yaml.YAMLError as e:
                log_error(f"Error parsing YAML in {file_path}: {e}")
                continue

        for doc in yaml_documents:
            if not doc or 'kind' not in doc or doc['kind'] != 'Secret':
                continue

            secret_name = doc['metadata']['name']
            secret_type = doc.get('type', 'Opaque') # Default to Opaque if type is not specified
            
            # Delete existing secret if it exists before creating/updating
            subprocess.run(['kubectl', 'delete', 'secret', secret_name, '-n', NAMESPACE, '--ignore-not-found'], capture_output=True)
            log_info(f"Updating secret: {secret_name}")

            base_command = ['kubectl', 'create', 'secret']
            
            if secret_type == 'kubernetes.io/tls':
                # Special handling for TLS secrets: write to temporary files for --from-file
                tls_cert = doc['data'].get('tls.crt')
                tls_key = doc['data'].get('tls.key')

                if tls_cert and tls_key:
                    with tempfile.NamedTemporaryFile(delete=False) as cert_file:
                        cert_file.write(base64.b64decode(tls_cert))
                        cert_path = cert_file.name
                    with tempfile.NamedTemporaryFile(delete=False) as key_file:
                        key_file.write(base64.b64decode(tls_key))
                        key_path = key_file.name
                    
                    cmd = base_command + ['tls', secret_name, f'--cert={cert_path}', f'--key={key_path}', '-n', NAMESPACE]
                    try:
                        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                        log_info(result.stdout.strip())
                    except subprocess.CalledProcessError as e:
                        log_error(f"Error creating TLS secret {secret_name}: {e.stderr.strip()}")
                    finally:
                        os.remove(cert_path)
                        os.remove(key_path)
                else:
                    log_warning(f"TLS secret {secret_name} in {file_path} is missing tls.crt or tls.key data. Skipping.")
                
            else:
                # Generic secret creation: always use --from-file
                # Write each key-value pair to a temporary file
                temp_files = []
                from_file_args = []

                if 'data' in doc:
                    for key, b64_value in doc['data'].items():
                        with tempfile.NamedTemporaryFile(delete=False) as temp_f:
                            temp_f.write(base64.b64decode(b64_value))
                            temp_files.append(temp_f.name)
                        from_file_args.append(f'--from-file={key}={temp_f.name}')
                
                if 'stringData' in doc: # Handle stringData if present (no base64 encoding needed)
                    for key, str_value in doc['stringData'].items():
                        with tempfile.NamedTemporaryFile(delete=False) as temp_f:
                            temp_f.write(str_value.encode('utf-8')) # stringData is plain text
                            temp_files.append(temp_f.name)
                        from_file_args.append(f'--from-file={key}={temp_f.name}')

                cmd = base_command + ['generic', secret_name, '-n', NAMESPACE] + from_file_args
                
                try:
                    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                    log_info(result.stdout.strip())
                except subprocess.CalledProcessError as e:
                    log_error(f"Error creating generic secret {secret_name}: {e.stderr.strip()}")
                finally:
                    # Clean up temporary files
                    for tf in temp_files:
                        os.remove(tf)
    log_info("✅ All secrets processed.")

if __name__ == "__main__":
    apply_secrets_programmatically()
