import 'package:flutter_app/config/app_config.dart';
import 'package:flutter_app/services/landmark_buffer.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('LandmarkBuffer', () {
    test('accepts valid 126-value frames', () {
      final buffer = LandmarkBuffer();
      final frame = List<double>.filled(AppConfig.expectedFrameWidth, 0.5);

      final accepted = buffer.tryAdd(frame);

      expect(accepted, isTrue);
      expect(buffer.length, 1);
      expect(buffer.isComplete, isFalse);
    });

    test('rejects invalid frame widths', () {
      final buffer = LandmarkBuffer();
      final frame = List<double>.filled(AppConfig.expectedFrameWidth - 1, 0.5);

      final accepted = buffer.tryAdd(frame);

      expect(accepted, isFalse);
      expect(buffer.isEmpty, isTrue);
    });

    test('reports complete at 60 frames', () {
      final buffer = LandmarkBuffer();
      final frame = List<double>.filled(AppConfig.expectedFrameWidth, 0.5);

      for (var index = 0; index < AppConfig.expectedFrameCount; index += 1) {
        expect(buffer.tryAdd(frame), isTrue);
      }

      expect(buffer.length, AppConfig.expectedFrameCount);
      expect(buffer.isComplete, isTrue);
      expect(buffer.tryAdd(frame), isFalse);
    });
  });
}
