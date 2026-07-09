import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:permission_handler/permission_handler.dart';

import '../config/app_config.dart';
import '../models/live_landmark_frame.dart';
import '../models/live_prediction_session.dart';
import '../models/prediction_source.dart';
import '../models/sign_mode.dart';
import '../services/label_service.dart';
import '../services/live_landmark_service.dart';
import '../services/live_recognition_service.dart';
import '../services/stabilized_prediction_tracker.dart';
import '../services/tflite_sign_classifier.dart';
import 'widgets/mode_selector.dart';
import 'widgets/prediction_card.dart';
import 'widgets/top_predictions_list.dart';

class LiveCameraPage extends StatefulWidget {
  const LiveCameraPage({super.key});

  @override
  State<LiveCameraPage> createState() => _LiveCameraPageState();
}

class _LiveCameraPageState extends State<LiveCameraPage> {
  final LabelService _labelService = LabelService();
  final StabilizedPredictionTracker _stabilizedTracker =
      StabilizedPredictionTracker();
  late final LiveLandmarkService _landmarkService;

  TfliteSignClassifier? _classifier;
  LiveRecognitionService? _recognitionService;
  LiveLandmarkFrame? _lastFrame;
  LivePredictionSession? _session;
  StabilizedPrediction? _stabilizedPrediction;
  SignMode _selectedMode = SignMode.bankingIntent;

  String _statusMessage = 'Loading live camera prototype assets...';
  String? _errorMessage;
  bool _isLoading = true;
  bool _isCameraStarting = false;
  bool _isCameraStarted = false;
  bool _isCapturing = false;
  bool _isPredicting = false;
  int _validFrameCount = 0;

  @override
  void initState() {
    super.initState();
    _landmarkService = LiveLandmarkService()
      ..onStatus = _handleStatus
      ..onError = _handleError
      ..onFrame = _handleLiveFrame
      ..onCaptureProgress = _handleCaptureProgress
      ..onCaptureComplete = _handleCaptureComplete;
    _initialize();
  }

  @override
  void dispose() {
    _classifier?.close();
    unawaited(_landmarkService.dispose());
    super.dispose();
  }

  Future<void> _initialize() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
      _statusMessage = 'Loading label metadata and TFLite model...';
    });

    try {
      final metadata = await _labelService.load();
      final classifier = TfliteSignClassifier(metadata: metadata);
      await classifier.load();

      if (!mounted) {
        classifier.close();
        return;
      }

      setState(() {
        _classifier = classifier;
        _recognitionService = LiveRecognitionService(classifier: classifier);
        _isLoading = false;
        _statusMessage =
            'Ready. Start the Android camera, then capture 60 valid frames.';
      });
    } catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _isLoading = false;
        _errorMessage = error.toString();
        _statusMessage = 'Live camera setup could not finish.';
      });
    }
  }

  Future<void> _startCamera() async {
    if (!Platform.isAndroid) {
      setState(() {
        _errorMessage = 'Live camera capture is supported on Android only.';
      });
      return;
    }

    setState(() {
      _isCameraStarting = true;
      _errorMessage = null;
      _statusMessage = 'Requesting camera permission...';
    });

    final permission = await Permission.camera.request();
    if (!mounted) {
      return;
    }
    if (!permission.isGranted) {
      setState(() {
        _isCameraStarting = false;
        _errorMessage = 'Camera permission was denied.';
        _statusMessage = 'Grant camera permission to use live recognition.';
      });
      return;
    }

    try {
      await _landmarkService.startCamera();
      if (!mounted) {
        return;
      }
      setState(() {
        _isCameraStarted = true;
        _isCameraStarting = false;
        _statusMessage = 'Camera started. Present a hand sign in view.';
      });
    } catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _isCameraStarting = false;
        _errorMessage = error.toString();
        _statusMessage = 'Camera could not start.';
      });
    }
  }

  Future<void> _stopCamera() async {
    await _landmarkService.stopCamera();
    if (!mounted) {
      return;
    }
    setState(() {
      _isCameraStarted = false;
      _isCapturing = false;
      _statusMessage = 'Camera stopped.';
    });
  }

  Future<void> _startCapture() async {
    if (_classifier == null || _recognitionService == null) {
      setState(() {
        _errorMessage = 'TFLite model is not loaded yet.';
      });
      return;
    }
    if (!_isCameraStarted) {
      setState(() {
        _errorMessage = 'Start the Android camera before capturing frames.';
      });
      return;
    }

    setState(() {
      _validFrameCount = 0;
      _session = null;
      _isCapturing = true;
      _isPredicting = false;
      _errorMessage = null;
      _statusMessage = 'Capturing 60 valid MediaPipe landmark frames...';
    });
    await _landmarkService.startCapture();
  }

  Future<void> _resetCapture() async {
    await _landmarkService.resetCapture();
    if (!mounted) {
      return;
    }
    setState(() {
      _validFrameCount = 0;
      _isCapturing = false;
      _isPredicting = false;
      _session = null;
      _stabilizedTracker.reset();
      _stabilizedPrediction = _stabilizedTracker.current;
      _statusMessage = 'Capture buffer reset.';
    });
  }

  void _handleStatus(String message) {
    if (!mounted || message.isEmpty) {
      return;
    }
    setState(() {
      _statusMessage = message;
    });
  }

  void _handleError(String message) {
    if (!mounted) {
      return;
    }
    setState(() {
      _errorMessage = message.isEmpty ? 'Live camera error.' : message;
      _isCameraStarting = false;
    });
  }

  void _handleLiveFrame(LiveLandmarkFrame frame) {
    if (!mounted) {
      return;
    }
    setState(() {
      _lastFrame = frame;
    });
  }

  void _handleCaptureProgress(int validFrameCount, int requiredFrameCount) {
    if (!mounted) {
      return;
    }
    setState(() {
      _validFrameCount = validFrameCount;
      _isCapturing = validFrameCount < requiredFrameCount;
    });
  }

  Future<void> _handleCaptureComplete(
    List<List<double>> frames,
    LiveCaptureMetrics metrics,
  ) async {
    final recognitionService = _recognitionService;
    if (recognitionService == null) {
      return;
    }

    setState(() {
      _isCapturing = false;
      _isPredicting = true;
      _statusMessage = '60-frame buffer complete. Running TFLite inference...';
    });

    try {
      final session = recognitionService.predictFromFrames(
        frames: frames,
        mode: _selectedMode,
        captureMetrics: metrics,
      );
      final stabilizedPrediction = _stabilizedTracker.add(session.prediction);
      if (!mounted) {
        return;
      }
      setState(() {
        _session = session;
        _stabilizedPrediction = stabilizedPrediction;
        _isPredicting = false;
        _validFrameCount = metrics.validFrameCount;
        _statusMessage =
            stabilizedPrediction.completedCaptures >=
                stabilizedPrediction.requiredCaptures
            ? 'Stabilized prediction updated.'
            : 'Single capture prediction complete. Repeat for 3-capture stabilization.';
      });
    } catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _isPredicting = false;
        _errorMessage = error.toString();
        _statusMessage = 'Live prediction failed.';
      });
    }
  }

  void _updateMode(SignMode mode) {
    setState(() {
      _selectedMode = mode;
      _session = null;
      _stabilizedTracker.reset();
      _stabilizedPrediction = _stabilizedTracker.current;
    });
  }

  @override
  Widget build(BuildContext context) {
    final session = _session;
    final lastFrame = _lastFrame;

    return Scaffold(
      appBar: AppBar(title: const Text('Live Camera Prototype')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _Header(statusMessage: _statusMessage),
            if (_errorMessage != null) ...[
              const SizedBox(height: 12),
              _ErrorPanel(message: _errorMessage!),
            ],
            const SizedBox(height: 12),
            _CameraPreviewCard(preview: _landmarkService.buildPreview()),
            const SizedBox(height: 12),
            _LiveStatusCard(
              modelLoaded: _classifier?.isLoaded ?? false,
              cameraStarted: _isCameraStarted,
              lastFrame: lastFrame,
              validFrameCount: _validFrameCount,
              isCapturing: _isCapturing,
            ),
            const SizedBox(height: 12),
            ModeSelector(selectedMode: _selectedMode, onChanged: _updateMode),
            const SizedBox(height: 12),
            _ControlPanel(
              isLoading: _isLoading,
              isCameraStarting: _isCameraStarting,
              isCameraStarted: _isCameraStarted,
              isCapturing: _isCapturing,
              isPredicting: _isPredicting,
              onStartCamera: _startCamera,
              onStopCamera: _stopCamera,
              onStartCapture: _startCapture,
              onResetCapture: _resetCapture,
            ),
            const SizedBox(height: 12),
            PredictionCard(
              sample: null,
              prediction: session?.prediction,
              isPredicting: _isPredicting,
              source: PredictionSource.liveCamera,
            ),
            if (session != null) ...[
              const SizedBox(height: 12),
              _StabilizedPredictionCard(
                stabilizedPrediction: _stabilizedPrediction,
              ),
              const SizedBox(height: 12),
              _RuntimeMetricsCard(session: session),
              const SizedBox(height: 12),
              TopPredictionsList(
                title: '${_selectedMode.displayName} Live Top Predictions',
                predictions: session.prediction.topPredictions,
              ),
              const SizedBox(height: 12),
              TopPredictionsList(
                title: 'Raw Model Top Predictions',
                predictions: session.prediction.rawTopPredictions,
              ),
            ],
            const SizedBox(height: 12),
            const _PrivacyCard(),
          ],
        ),
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.statusMessage});

  final String statusMessage;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Sprint 2.15 Live Camera',
          style: Theme.of(
            context,
          ).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700),
        ),
        const SizedBox(height: 4),
        Text(
          statusMessage,
          style: const TextStyle(
            color: Color(0xFF0F766E),
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }
}

class _CameraPreviewCard extends StatelessWidget {
  const _CameraPreviewCard({required this.preview});

  final Widget preview;

  @override
  Widget build(BuildContext context) {
    return Card(
      clipBehavior: Clip.antiAlias,
      child: AspectRatio(aspectRatio: 3 / 4, child: preview),
    );
  }
}

class _LiveStatusCard extends StatelessWidget {
  const _LiveStatusCard({
    required this.modelLoaded,
    required this.cameraStarted,
    required this.lastFrame,
    required this.validFrameCount,
    required this.isCapturing,
  });

  final bool modelLoaded;
  final bool cameraStarted;
  final LiveLandmarkFrame? lastFrame;
  final int validFrameCount;
  final bool isCapturing;

  @override
  Widget build(BuildContext context) {
    final frame = lastFrame;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Live Pipeline Status',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 12),
            _StatusRow(
              label: 'TFLite model',
              value: modelLoaded ? 'Loaded' : 'Loading',
            ),
            _StatusRow(
              label: 'Camera preview',
              value: cameraStarted ? 'Started' : 'Stopped',
            ),
            _StatusRow(
              label: 'Hand detected',
              value: frame?.handDetected == true ? 'Yes' : 'No',
            ),
            _StatusRow(
              label: 'Frame dimension',
              value: frame?.isValid == true
                  ? AppConfig.expectedFrameWidth.toString()
                  : 'Waiting',
            ),
            _StatusRow(
              label: 'Valid frame buffer',
              value: '$validFrameCount / ${AppConfig.expectedFrameCount}',
            ),
            if (isCapturing) const SizedBox(height: 8),
            if (isCapturing)
              LinearProgressIndicator(
                value: validFrameCount / AppConfig.expectedFrameCount,
              ),
          ],
        ),
      ),
    );
  }
}

class _ControlPanel extends StatelessWidget {
  const _ControlPanel({
    required this.isLoading,
    required this.isCameraStarting,
    required this.isCameraStarted,
    required this.isCapturing,
    required this.isPredicting,
    required this.onStartCamera,
    required this.onStopCamera,
    required this.onStartCapture,
    required this.onResetCapture,
  });

  final bool isLoading;
  final bool isCameraStarting;
  final bool isCameraStarted;
  final bool isCapturing;
  final bool isPredicting;
  final VoidCallback onStartCamera;
  final VoidCallback onStopCamera;
  final VoidCallback onStartCapture;
  final VoidCallback onResetCapture;

  @override
  Widget build(BuildContext context) {
    final controlsDisabled = isLoading || isCameraStarting || isPredicting;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            FilledButton.icon(
              onPressed: controlsDisabled || isCameraStarted
                  ? null
                  : onStartCamera,
              icon: isCameraStarting
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.videocam),
              label: const Text('Start Camera'),
            ),
            OutlinedButton.icon(
              onPressed: controlsDisabled || !isCameraStarted
                  ? null
                  : onStopCamera,
              icon: const Icon(Icons.videocam_off),
              label: const Text('Stop'),
            ),
            FilledButton.icon(
              onPressed: controlsDisabled || !isCameraStarted || isCapturing
                  ? null
                  : onStartCapture,
              icon: const Icon(Icons.back_hand),
              label: const Text('Capture 60 Frames'),
            ),
            OutlinedButton.icon(
              onPressed: controlsDisabled ? null : onResetCapture,
              icon: const Icon(Icons.restart_alt),
              label: const Text('Reset'),
            ),
          ],
        ),
      ),
    );
  }
}

class _RuntimeMetricsCard extends StatelessWidget {
  const _RuntimeMetricsCard({required this.session});

  final LivePredictionSession session;

  @override
  Widget build(BuildContext context) {
    final metrics = session.captureMetrics;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Runtime Metrics',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 12),
            _StatusRow(
              label: 'Feature vector length',
              value: session.featureLength.toString(),
            ),
            _StatusRow(
              label: 'Captured frames',
              value: metrics.validFrameCount.toString(),
            ),
            _StatusRow(
              label: 'Frame dimension',
              value: metrics.frameDimension.toString(),
            ),
            _StatusRow(
              label: 'Capture duration',
              value: '${metrics.captureDurationMs} ms',
            ),
            _StatusRow(
              label: 'Average capture FPS',
              value: metrics.averageFps.toStringAsFixed(2),
            ),
            _StatusRow(
              label: 'Feature computation',
              value: '${session.featureComputationMs} ms',
            ),
            _StatusRow(
              label: 'TFLite inference',
              value: '${session.inferenceMs} ms',
            ),
            _StatusRow(
              label: 'End-to-end prediction',
              value: '${session.endToEndMs} ms',
            ),
          ],
        ),
      ),
    );
  }
}

class _StabilizedPredictionCard extends StatelessWidget {
  const _StabilizedPredictionCard({required this.stabilizedPrediction});

  final StabilizedPrediction? stabilizedPrediction;

  @override
  Widget build(BuildContext context) {
    final prediction = stabilizedPrediction;
    if (prediction == null) {
      return const SizedBox.shrink();
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Stabilized Prediction',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 12),
            _StatusRow(
              label: 'Captures',
              value:
                  '${prediction.completedCaptures} / ${prediction.requiredCaptures}',
            ),
            _StatusRow(
              label: 'Agreement',
              value:
                  '${prediction.agreementCount} / ${prediction.requiredAgreement}',
            ),
            _StatusRow(label: 'Output', value: prediction.displayLabel),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                for (
                  var index = 0;
                  index < prediction.captureLabels.length;
                  index += 1
                )
                  Chip(
                    label: Text(
                      'Capture ${index + 1}: ${prediction.captureLabels[index] ?? 'Try Again'}',
                    ),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _StatusRow extends StatelessWidget {
  const _StatusRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        children: [
          Expanded(child: Text(label)),
          Flexible(
            child: Text(
              value,
              textAlign: TextAlign.end,
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
          ),
        ],
      ),
    );
  }
}

class _ErrorPanel extends StatelessWidget {
  const _ErrorPanel({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: const Color(0xFFFFF1F2),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Icon(Icons.error_outline, color: Color(0xFFBE123C)),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                message,
                style: const TextStyle(color: Color(0xFF9F1239)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _PrivacyCard extends StatelessWidget {
  const _PrivacyCard();

  @override
  Widget build(BuildContext context) {
    return const Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.lock_outline, color: Color(0xFF0F766E)),
            SizedBox(width: 8),
            Expanded(
              child: Text(
                'Camera frames, landmarks, feature computation, and TFLite inference stay on the Android device. No video upload or server processing is used.',
              ),
            ),
          ],
        ),
      ),
    );
  }
}
