"""Script to download RNNoise models."""

import urllib.request
import ssl
from pathlib import Path
import sys

# RNNoise models from richardpl/arnndn-models repository
RNNOISE_MODELS = {
    "std.rnnn": {
        "url": "https://github.com/richardpl/arnndn-models/raw/master/std.rnnn",
        "description": "Standard (Original Xiph Model)"
    },
    "bd.rnnn": {
        "url": "https://github.com/richardpl/arnndn-models/raw/master/bd.rnnn",
        "description": "Broadband (General Purpose)"
    },
    "cb.rnnn": {
        "url": "https://github.com/richardpl/arnndn-models/raw/master/cb.rnnn", 
        "description": "Cassette Tape"
    },
    "mp.rnnn": {
        "url": "https://github.com/richardpl/arnndn-models/raw/master/mp.rnnn",
        "description": "Music Performance"
    },
    "sh.rnnn": {
        "url": "https://github.com/richardpl/arnndn-models/raw/master/sh.rnnn",
        "description": "Speech Heavy"
    },
    "lq.rnnn": {
        "url": "https://github.com/richardpl/arnndn-models/raw/master/lq.rnnn",
        "description": "Low Quality (Fast Processing)"
    }
}

def download_file(url: str, output_path: Path) -> bool:
    """Download a file from URL to local path."""
    try:
        print(f"Downloading {output_path.name}...")
        
        # Create SSL context that doesn't verify certificates (for GitHub)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Download with progress
        urllib.request.urlretrieve(url, output_path)
        
        print(f"✓ Downloaded {output_path.name}")
        return True
        
    except Exception as e:
        print(f"✗ Failed to download {output_path.name}: {e}")
        return False

def main():
    """Main function to download all RNNoise models."""
    print("RNNoise Models Downloader")
    print("=" * 40)
    
    # Create models directory
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    print(f"Models will be saved to: {models_dir.absolute()}\n")
    
    success_count = 0
    total_count = len(RNNOISE_MODELS)
    
    for filename, info in RNNOISE_MODELS.items():
        output_path = models_dir / filename
        
        # Skip if already exists
        if output_path.exists():
            print(f"⚠ {filename} already exists, skipping...")
            success_count += 1
            continue
        
        print(f"Model: {info['description']}")
        
        if download_file(info["url"], output_path):
            success_count += 1
        
        print()  # Empty line for readability
    
    # Summary
    print("=" * 40)
    print(f"Download complete: {success_count}/{total_count} models")
    
    if success_count == total_count:
        print("✓ All models downloaded successfully!")
        print("\nYou can now use RNNoise in the noise cancellation application.")
    else:
        print(f"✗ {total_count - success_count} models failed to download.")
        print("Please check your internet connection and try again.")
        sys.exit(1)
    
    # Display model info
    print("\nAvailable models:")
    for filename, info in RNNOISE_MODELS.items():
        model_path = models_dir / filename
        if model_path.exists():
            size_mb = model_path.stat().st_size / (1024 * 1024)
            print(f"  • {filename} - {info['description']} ({size_mb:.1f} MB)")

if __name__ == "__main__":
    main()