import nltk

def download_nltk_data():
    """Download required NLTK data for the newspaper library"""
    print("Downloading NLTK data for newspaper library...")
    nltk.download('punkt')

if __name__ == "__main__":
    download_nltk_data()
    print("\nNLTK data download complete. Now you can run your tests.")
