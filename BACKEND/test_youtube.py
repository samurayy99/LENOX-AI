from youtube_tools import get_influencer_youtube_alpha

def test_influencer_alpha():
    try:
        result = get_influencer_youtube_alpha("latest")
        print(result)
    except Exception as e:
        print(f"Fehler: {str(e)}")

if __name__ == "__main__":
    test_influencer_alpha() 