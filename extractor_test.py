from feature_extractor import URLFeatureExtractor

extractor = URLFeatureExtractor()

print(extractor.extract("https://youtube.com"))
print(extractor.extract("http://192.168.1.1/login"))