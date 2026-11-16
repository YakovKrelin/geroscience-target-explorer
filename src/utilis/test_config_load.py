import os
import yaml

def verify_config_loading(config_path: str = "config/config.yaml") -> None:
    """
    Verifies the existence, readability, and correct syntax of config.yaml
    according to the v1.2.1-Implementation-Freeze standard.
    """
    if not os.path.exists(config_path):
        print(f"[ERROR] Configuration file not found at the path: {config_path}")
        print("Ensure that the file is named config.yaml and is located in the config/ folder.")
        return

    print(f"[INFO] Configuration file found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        try:
            config = yaml.safe_load(f)
            print("[OK] The YAML syntax is correct, the file was read successfully.")
            
            # Outputting key parameters for verifying a freeze
            proj_name = config.get("project", {}).get("name")
            proj_ver = config.get("project", {}).get("version")
            primary_method = config.get("test_c", {}).get("primary_method")
            seed = config.get("project", {}).get("random_seed")
            
            print("\n--- Freeze Parameters ---")
            print(f"  • Project: {proj_name}")
            print(f"  • Version: {proj_ver}")
            print(f"  • Random Seed: {seed}")
            print(f"  • Primary Test C Method: {primary_method}")
            print("----------------------------------------------")
            
        except yaml.YAMLError as exc:
            print(f"[ERROR] YAML parsing error: {exc}")

if __name__ == "__main__":
    verify_config_loading()