import '../config/app_config.dart';

class LiveLandmarkFrame {
  const LiveLandmarkFrame({
    required this.timestampMs,
    required this.landmarks,
    required this.handDetected,
    required this.leftDetected,
    required this.rightDetected,
  });

  final int timestampMs;
  final List<double> landmarks;
  final bool handDetected;
  final bool leftDetected;
  final bool rightDetected;

  bool get isValid {
    return handDetected && landmarks.length == AppConfig.expectedFrameWidth;
  }

  factory LiveLandmarkFrame.fromPlatformMap(Map<dynamic, dynamic> payload) {
    final rawLandmarks = payload['landmarks'];
    final landmarks = rawLandmarks is List
        ? rawLandmarks.map((value) => (value as num).toDouble()).toList()
        : <double>[];

    return LiveLandmarkFrame(
      timestampMs: (payload['timestampMs'] as num?)?.toInt() ?? 0,
      landmarks: landmarks,
      handDetected: payload['handDetected'] == true,
      leftDetected: payload['leftDetected'] == true,
      rightDetected: payload['rightDetected'] == true,
    );
  }
}
