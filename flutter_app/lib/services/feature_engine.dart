import 'dart:math' as math;

import '../config/app_config.dart';

class FeatureEngine {
  List<double> computeStatisticalFeatures(List<List<double>> frames) {
    _validateFrames(frames);

    final means = List<double>.filled(AppConfig.expectedFrameWidth, 0);
    final stds = List<double>.filled(AppConfig.expectedFrameWidth, 0);
    final mins = List<double>.filled(
      AppConfig.expectedFrameWidth,
      double.infinity,
    );
    final maxs = List<double>.filled(
      AppConfig.expectedFrameWidth,
      double.negativeInfinity,
    );

    for (final frame in frames) {
      for (var index = 0; index < AppConfig.expectedFrameWidth; index += 1) {
        final value = frame[index];
        means[index] += value;
        mins[index] = math.min(mins[index], value);
        maxs[index] = math.max(maxs[index], value);
      }
    }

    for (var index = 0; index < means.length; index += 1) {
      means[index] /= AppConfig.expectedFrameCount;
    }

    for (final frame in frames) {
      for (var index = 0; index < AppConfig.expectedFrameWidth; index += 1) {
        final diff = frame[index] - means[index];
        stds[index] += diff * diff;
      }
    }

    for (var index = 0; index < stds.length; index += 1) {
      stds[index] = math.sqrt(stds[index] / AppConfig.expectedFrameCount);
    }

    return <double>[
      ...means,
      ...stds,
      ...mins,
      ...maxs,
      ...frames.first,
      ...frames.last,
    ];
  }

  void _validateFrames(List<List<double>> frames) {
    if (frames.length != AppConfig.expectedFrameCount) {
      throw ArgumentError(
        'Expected ${AppConfig.expectedFrameCount} frames, found ${frames.length}.',
      );
    }

    for (var index = 0; index < frames.length; index += 1) {
      if (frames[index].length != AppConfig.expectedFrameWidth) {
        throw ArgumentError(
          'Frame $index must contain ${AppConfig.expectedFrameWidth} values, found ${frames[index].length}.',
        );
      }
    }
  }
}
