enum PredictionSource { testFeature, liveCamera }

extension PredictionSourceLabel on PredictionSource {
  String get displayName {
    switch (this) {
      case PredictionSource.testFeature:
        return 'Test Feature';
      case PredictionSource.liveCamera:
        return 'Live Camera';
    }
  }
}
