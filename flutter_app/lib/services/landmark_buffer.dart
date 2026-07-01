import '../config/app_config.dart';

class LandmarkBuffer {
  LandmarkBuffer({
    this.requiredFrames = AppConfig.expectedFrameCount,
    this.frameWidth = AppConfig.expectedFrameWidth,
  });

  final int requiredFrames;
  final int frameWidth;
  final List<List<double>> _frames = <List<double>>[];

  int get length => _frames.length;
  bool get isComplete => _frames.length >= requiredFrames;
  bool get isEmpty => _frames.isEmpty;

  List<List<double>> get frames {
    return _frames
        .map((frame) => List<double>.unmodifiable(frame))
        .toList(growable: false);
  }

  void reset() {
    _frames.clear();
  }

  bool tryAdd(List<double> frame) {
    if (isComplete || frame.length != frameWidth) {
      return false;
    }
    _frames.add(List<double>.from(frame, growable: false));
    return true;
  }
}
