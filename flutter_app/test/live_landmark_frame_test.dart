import 'package:flutter_app/config/app_config.dart';
import 'package:flutter_app/models/live_landmark_frame.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('left-hand-only frame keeps the right slot zero', () {
    final landmarks = <double>[
      ...List<double>.filled(63, 0.25),
      ...List<double>.filled(63, 0),
    ];
    final frame = _frame(
      landmarks: landmarks,
      leftDetected: true,
      rightDetected: false,
    );

    expect(frame.isValid, isTrue);
    expect(frame.landmarks.sublist(0, 63), everyElement(0.25));
    expect(frame.landmarks.sublist(63), everyElement(0.0));
  });

  test('right-hand-only frame keeps the left slot zero', () {
    final landmarks = <double>[
      ...List<double>.filled(63, 0),
      ...List<double>.filled(63, 0.75),
    ];
    final frame = _frame(
      landmarks: landmarks,
      leftDetected: false,
      rightDetected: true,
    );

    expect(frame.isValid, isTrue);
    expect(frame.landmarks.sublist(0, 63), everyElement(0.0));
    expect(frame.landmarks.sublist(63), everyElement(0.75));
  });

  test('two-hand frames preserve stable left and right ordering', () {
    final first = _frame(
      landmarks: <double>[
        ...List<double>.filled(63, 0.2),
        ...List<double>.filled(63, 0.8),
      ],
      leftDetected: true,
      rightDetected: true,
    );
    final second = _frame(
      landmarks: <double>[
        ...List<double>.filled(63, 0.3),
        ...List<double>.filled(63, 0.7),
      ],
      leftDetected: true,
      rightDetected: true,
    );

    expect(first.landmarks.sublist(0, 63), everyElement(0.2));
    expect(first.landmarks.sublist(63), everyElement(0.8));
    expect(second.landmarks.sublist(0, 63), everyElement(0.3));
    expect(second.landmarks.sublist(63), everyElement(0.7));
  });

  test('no-hand frame is rejected from valid capture accumulation', () {
    final frame = LiveLandmarkFrame.fromPlatformMap(<String, Object?>{
      'timestampMs': 1,
      'landmarks': <double>[],
      'handDetected': false,
      'leftDetected': false,
      'rightDetected': false,
    });

    expect(frame.isValid, isFalse);
    expect(frame.landmarks, isEmpty);
  });

  test('stored frame contract remains exactly 126 values', () {
    final frame = _frame(
      landmarks: List<double>.generate(
        AppConfig.expectedFrameWidth,
        (index) => index.toDouble(),
      ),
      leftDetected: true,
      rightDetected: true,
    );

    expect(frame.landmarks, hasLength(126));
  });
}

LiveLandmarkFrame _frame({
  required List<double> landmarks,
  required bool leftDetected,
  required bool rightDetected,
}) {
  return LiveLandmarkFrame.fromPlatformMap(<String, Object?>{
    'timestampMs': 1,
    'landmarks': landmarks,
    'handDetected': leftDetected || rightDetected,
    'leftDetected': leftDetected,
    'rightDetected': rightDetected,
  });
}
