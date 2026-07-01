import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../config/app_config.dart';
import '../models/live_landmark_frame.dart';
import '../models/live_prediction_session.dart';
import 'landmark_buffer.dart';

typedef LiveFrameCallback = void Function(LiveLandmarkFrame frame);
typedef LiveCaptureProgressCallback =
    void Function(int validFrameCount, int requiredFrameCount);
typedef LiveCaptureCompleteCallback =
    void Function(List<List<double>> frames, LiveCaptureMetrics metrics);
typedef LiveStatusCallback = void Function(String message);
typedef LiveErrorCallback = void Function(String message);

class LiveLandmarkService {
  LiveLandmarkService({LandmarkBuffer? buffer})
    : _buffer = buffer ?? LandmarkBuffer() {
    _channel.setMethodCallHandler(_handleNativeEvent);
  }

  static const String viewType = 'signsync/live_camera_view';
  static const MethodChannel _channel = MethodChannel(
    'signsync/live_landmarks',
  );

  final LandmarkBuffer _buffer;
  Stopwatch? _captureWatch;
  bool _isCapturing = false;

  LiveFrameCallback? onFrame;
  LiveCaptureProgressCallback? onCaptureProgress;
  LiveCaptureCompleteCallback? onCaptureComplete;
  LiveStatusCallback? onStatus;
  LiveErrorCallback? onError;

  int get capturedFrameCount => _buffer.length;
  bool get isCapturing => _isCapturing;

  Widget buildPreview() {
    if (!Platform.isAndroid) {
      return const _UnsupportedPreview();
    }
    return const AndroidView(viewType: viewType);
  }

  Future<void> startCamera() async {
    if (!Platform.isAndroid) {
      onError?.call('Live camera prototype is available on Android only.');
      return;
    }
    await _channel.invokeMethod<void>('startCamera');
  }

  Future<void> stopCamera() async {
    if (!Platform.isAndroid) {
      return;
    }
    await _channel.invokeMethod<void>('stopCamera');
  }

  Future<void> startCapture() async {
    _buffer.reset();
    _isCapturing = true;
    _captureWatch = Stopwatch()..start();
    onCaptureProgress?.call(0, AppConfig.expectedFrameCount);
    if (Platform.isAndroid) {
      await _channel.invokeMethod<void>('startCapture');
    }
  }

  Future<void> resetCapture() async {
    _buffer.reset();
    _isCapturing = false;
    _captureWatch = null;
    onCaptureProgress?.call(0, AppConfig.expectedFrameCount);
    if (Platform.isAndroid) {
      await _channel.invokeMethod<void>('resetCapture');
    }
  }

  Future<void> dispose() async {
    _channel.setMethodCallHandler(null);
    await stopCamera();
  }

  Future<void> _handleNativeEvent(MethodCall call) async {
    switch (call.method) {
      case 'cameraStarted':
      case 'cameraStopped':
      case 'captureStarted':
      case 'captureReset':
        onStatus?.call(_stringMessage(call.arguments));
        break;
      case 'cameraError':
      case 'mediapipeError':
        onError?.call(_stringMessage(call.arguments));
        break;
      case 'liveFrame':
        _handleLiveFrame(call.arguments);
        break;
      default:
        break;
    }
  }

  void _handleLiveFrame(Object? arguments) {
    if (arguments is! Map) {
      return;
    }

    final frame = LiveLandmarkFrame.fromPlatformMap(arguments);
    onFrame?.call(frame);

    if (!_isCapturing || !frame.isValid) {
      return;
    }

    final accepted = _buffer.tryAdd(frame.landmarks);
    if (!accepted) {
      return;
    }

    onCaptureProgress?.call(_buffer.length, AppConfig.expectedFrameCount);
    if (!_buffer.isComplete) {
      return;
    }

    _isCapturing = false;
    final watch = _captureWatch;
    watch?.stop();
    final durationMs = watch?.elapsedMilliseconds ?? 0;
    final fps = durationMs > 0
        ? AppConfig.expectedFrameCount / (durationMs / 1000)
        : 0.0;

    onCaptureComplete?.call(
      _buffer.frames,
      LiveCaptureMetrics(
        validFrameCount: _buffer.length,
        frameDimension: AppConfig.expectedFrameWidth,
        captureDurationMs: durationMs,
        averageFps: fps,
      ),
    );
  }

  String _stringMessage(Object? arguments) {
    if (arguments is Map && arguments['message'] != null) {
      return arguments['message'].toString();
    }
    return arguments?.toString() ?? '';
  }
}

class _UnsupportedPreview extends StatelessWidget {
  const _UnsupportedPreview();

  @override
  Widget build(BuildContext context) {
    return const ColoredBox(
      color: Color(0xFFE2E8F0),
      child: Center(
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Text('Android live camera preview is not available here.'),
        ),
      ),
    );
  }
}
