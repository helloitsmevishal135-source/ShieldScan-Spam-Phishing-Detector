from text_url_classifier import TextURLClassifier   # adjust filename

if __name__ == "__main__":
    import sys

    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    clf = TextURLClassifier(n_trees=20, seed=42)

    texts = [
        "I like playing games",
        "Machine learning is interesting",
        "bro I am tired"
    ]

    urls = [
        "youtube.com",
        "https://google.com/search?q=test",
        "facebook.com/profile.php?id=1"
    ]

    X = texts + urls
    y = [0]*len(texts) + [1]*len(urls)

    clf.fit(X, y)

    tests = [
        "youtube.com",
        "I am going to sleep now",
        "www.github.com",
        "random sentence with no meaning",
        "https://openai.com/research"
    ]

    for t in tests:
        print(t, "=>", clf.predict_one(t))