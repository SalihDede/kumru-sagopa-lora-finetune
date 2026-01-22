"""
Upload model to Hugging Face Hub
Run this script to upload your model to HF Hub for use in RunPod
"""

from huggingface_hub import HfApi, create_repo
import os

# Configuration
MODEL_PATH = "./SagoChatBOTAPI/kumru-sagopa-merged"
REPO_NAME = "SalihHub/kumru-sagopa-merged"
PRIVATE = True  # Set to False if you want public model

def upload_model():
    """Upload model to Hugging Face Hub"""

    # Initialize HF API
    api = HfApi()

    print("Logging in to Hugging Face...")
    print("Make sure you have HF_TOKEN environment variable set")
    print("or run: huggingface-cli login")

    # Create repo (will skip if exists)
    try:
        print(f"\nCreating repository: {REPO_NAME}")
        create_repo(
            repo_id=REPO_NAME,
            private=PRIVATE,
            exist_ok=True
        )
        print("Repository created/verified!")
    except Exception as e:
        print(f"Error creating repo: {e}")
        return

    # Upload all files in the model directory
    print(f"\nUploading model files from {MODEL_PATH}...")
    print("This may take a while (4.4 GB)...")

    try:
        api.upload_folder(
            folder_path=MODEL_PATH,
            repo_id=REPO_NAME,
            repo_type="model",
        )
        print("\n✅ Model uploaded successfully!")
        print(f"Model available at: https://huggingface.co/{REPO_NAME}")
        print("\nUpdate your Dockerfile with:")
        print(f'ENV MODEL_NAME="{REPO_NAME}"')

    except Exception as e:
        print(f"\n❌ Error uploading: {e}")
        print("\nMake sure you:")
        print("1. Have installed: pip install huggingface_hub")
        print("2. Are logged in: huggingface-cli login")
        print("3. Have a valid HF token with write permissions")

if __name__ == "__main__":
    print("=" * 60)
    print("Hugging Face Model Upload Script")
    print("=" * 60)

    # Check if model path exists
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Error: Model path not found: {MODEL_PATH}")
        exit(1)

    print(f"\nModel path: {MODEL_PATH}")
    print(f"Target repo: {REPO_NAME}")
    print(f"Private: {PRIVATE}")

    response = input("\nProceed with upload? (yes/no): ")
    if response.lower() in ['yes', 'y']:
        upload_model()
    else:
        print("Upload cancelled.")
